"""Canonical delivery-ledger helpers for scheduled email automation.

The ledger is message-shaped, while the provider idempotency key is batch-shaped.
Every row in one provider request therefore shares the same ``idempotency_key``.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from api.email_policy import blocked_delivery_result, delivery_mode


DELIVERY_STATES = ('pending', 'accepted', 'failed', 'unknown')


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def delivery_message_key(action, period_label, logical_id):
    return f'{action}:{period_label}:{logical_id}'


def delivery_idempotency_key(action, period_label, logical_id):
    return f'networth:{delivery_message_key(action, period_label, logical_id)}'


def delivery_summary(rows):
    counts = {state: 0 for state in DELIVERY_STATES}
    for row in rows or []:
        status = row.get('delivery_status')
        if status in counts:
            counts[status] += 1
    return counts


def build_delivery_rows(
    action: str,
    period_label: str,
    messages: Iterable[Dict[str, Any]],
    template: str,
    provider_batch_key: str,
    run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Build deterministic pending rows for one provider batch."""
    rows = []
    for message in messages:
        logical_id = message.get('logical_id')
        if logical_id is None:
            raise ValueError('logical_id is required for every delivery message')
        recipients = message.get('recipient_emails') or message.get('to') or []
        if isinstance(recipients, str):
            recipients = [recipients]
        recipients = [str(email).strip() for email in recipients if str(email).strip()]
        if not recipients:
            raise ValueError(f'No recipients for delivery message {logical_id}')
        rows.append({
            'run_id': run_id,
            'action': action,
            'period_label': period_label,
            'recipient_email': recipients[0],
            'recipient_emails': recipients,
            'message_key': delivery_message_key(action, period_label, logical_id),
            'template': template,
            'delivery_status': 'pending',
            'idempotency_key': provider_batch_key,
        })
    return rows


def _table(table_client=None):
    if table_client is not None:
        return table_client
    from api.supabase_http import table
    return table('email_delivery_log')


def _execute(operation):
    execute = getattr(operation, 'execute', None)
    return execute() if callable(execute) else operation


def _row_filter(query, row):
    if row.get('id'):
        return query.eq('id', row['id'])
    return query.eq('action', row['action']).eq(
        'period_label', row['period_label']
    ).eq('message_key', row['message_key'])


def _normalize_row(row, now=None):
    normalized = dict(row)
    normalized.setdefault('delivery_status', 'pending')
    normalized.setdefault('created_at', now or _utc_now_iso())
    normalized['updated_at'] = now or _utc_now_iso()
    if not normalized.get('recipient_emails'):
        recipient = normalized.get('recipient_email')
        normalized['recipient_emails'] = [recipient] if recipient else []
    if not normalized.get('recipient_email') and normalized['recipient_emails']:
        normalized['recipient_email'] = normalized['recipient_emails'][0]
    return normalized


def _is_unique_conflict(error):
    text = str(error or '').lower()
    return '409' in text or 'duplicate' in text or 'unique constraint' in text or '23505' in text


def _reopen_failed_claim(rows, table_client=None):
    """Reuse a failed row's stable key; never reopen pending/unknown/accepted."""
    reopened = []
    for row in rows:
        try:
            query = _table(table_client).select(
                'id,action,period_label,message_key,delivery_status,idempotency_key,recipient_emails,template'
            )
            result = _execute(_row_filter(query, row))
        except Exception:
            return None
        if result.error or not result.data:
            return None
        existing = result.data[0]
        if existing.get('delivery_status') != 'failed':
            return None
        try:
            update = _row_filter(
                _table(table_client).update({
                    'delivery_status': 'pending',
                    'error': None,
                    'updated_at': _utc_now_iso(),
                }),
                existing,
            )
            update_result = _execute(update)
        except Exception:
            return None
        if update_result.error:
            return None
        reopened.append({**existing, 'delivery_status': 'pending'})
    return reopened


def claim_pending_messages(messages, run_id=None, table_client=None):
    """Insert pending rows before provider submission.

    The message-key unique index makes a duplicate claim a hard pre-send stop.
    """
    rows = [_normalize_row(row) for row in (messages or [])]
    if run_id:
        for row in rows:
            row['run_id'] = run_id
    message_keys = [row.get('message_key') for row in rows]
    if not rows or any(not key for key in message_keys) or len(set(message_keys)) != len(message_keys):
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'error': 'Delivery rows must have unique message keys',
            'rows': [],
        }

    try:
        result = _execute(_table(table_client).insert(rows))
    except Exception as exc:
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'error': str(exc),
            'rows': [],
        }
    if result.error:
        if _is_unique_conflict(result.error):
            reopened = _reopen_failed_claim(rows, table_client=table_client)
            if reopened:
                return {
                    'success': True,
                    'outcome': 'claimed',
                    'rows': reopened,
                    'summary': delivery_summary(reopened),
                }
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'error': str(result.error),
            'rows': [],
        }
    return {
        'success': True,
        'outcome': 'claimed',
        'rows': result.data or rows,
        'summary': delivery_summary(result.data or rows),
    }


def _update_rows(rows, status, table_client=None, provider_ids=None, error=None):
    provider_ids = list(provider_ids or [])
    updated = []
    errors = []
    for index, row in enumerate(rows or []):
        payload = {
            'delivery_status': status,
            'updated_at': _utc_now_iso(),
        }
        if status == 'accepted':
            provider = provider_ids[index] if index < len(provider_ids) else None
            if isinstance(provider, dict):
                provider = provider.get('id')
            if not provider:
                errors.append(f"Missing provider ID for {row.get('message_key')}")
                continue
            payload['provider_id'] = provider
            payload['accepted_at'] = payload['updated_at']
        if error:
            payload['error'] = str(error)
        try:
            query = _row_filter(_table(table_client).update(payload), row)
            result = _execute(query)
        except Exception as exc:
            errors.append(str(exc))
            continue
        if result.error:
            errors.append(str(result.error))
            continue
        updated.append({**row, **payload})
    return updated, errors


def mark_accepted(rows, provider_ids, table_client=None):
    updated, errors = _update_rows(
        rows, 'accepted', table_client=table_client, provider_ids=provider_ids
    )
    if errors:
        return {
            'success': False,
            'outcome': 'accepted_needs_reconciliation',
            'rows': updated,
            'errors': errors,
            'summary': delivery_summary(updated),
        }
    return {
        'success': True,
        'outcome': 'accepted',
        'rows': updated,
        'errors': [],
        'summary': delivery_summary(updated),
    }


def mark_failed(rows, error, table_client=None):
    updated, errors = _update_rows(rows, 'failed', table_client=table_client, error=error)
    return {
        'success': not errors,
        'outcome': 'pre_send_failure',
        'rows': updated,
        'errors': errors,
        'summary': delivery_summary(updated),
    }


def mark_unknown(rows, error, table_client=None):
    updated, errors = _update_rows(rows, 'unknown', table_client=table_client, error=error)
    return {
        'success': True,
        'outcome': 'unknown_needs_reconciliation',
        'rows': updated,
        'errors': errors,
        'summary': delivery_summary(updated),
    }


def deliver_batch(
    messages,
    ledger_rows,
    provider_sender,
    table_client=None,
    mode=None,
):
    """Claim, submit, and record one provider batch without false failures."""
    rows = list(ledger_rows or [])
    selected_mode = mode or delivery_mode()
    provider_batch_key = rows[0].get('idempotency_key') if rows else None

    if selected_mode != 'live':
        result = blocked_delivery_result(len(messages or []), selected_mode)
        result.update({
            'outcome': 'delivery_disabled',
            'idempotency_key': provider_batch_key,
            'delivery_summary': delivery_summary(rows),
        })
        return result

    if not rows or len(rows) != len(messages or []) or any(
        row.get('idempotency_key') != provider_batch_key for row in rows
    ):
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'error': 'Batch messages and ledger rows do not match one idempotency key',
            'sent': 0,
            'failed': len(messages or []),
            'idempotency_key': provider_batch_key,
        }

    claim = claim_pending_messages(rows, table_client=table_client)
    if not claim['success']:
        return {
            **claim,
            'sent': 0,
            'failed': len(messages or []),
            'idempotency_key': provider_batch_key,
        }

    try:
        provider_result = provider_sender(
            messages, idempotency_key=provider_batch_key
        ) or {}
    except Exception as exc:
        provider_result = {
            'outcome': 'unknown_needs_reconciliation',
            'errors': [str(exc)],
            'sent': 0,
            'deliveries': [],
        }

    outcome = provider_result.get('outcome')
    deliveries = provider_result.get('deliveries') or []
    if outcome == 'accepted' or (
        provider_result.get('success') is True
        and not provider_result.get('errors')
        and len(deliveries) == len(messages)
    ):
        marked = mark_accepted(claim['rows'], deliveries, table_client=table_client)
        if marked['outcome'] == 'accepted_needs_reconciliation':
            return {
                'success': True,
                'outcome': 'accepted_needs_reconciliation',
                'sent': len(deliveries),
                'failed': 0,
                'errors': marked['errors'],
                'idempotency_key': provider_batch_key,
                'delivery_summary': marked['summary'],
            }
        return {
            'success': True,
            'outcome': 'accepted',
            'sent': len(deliveries),
            'failed': 0,
            'errors': [],
            'deliveries': deliveries,
            'idempotency_key': provider_batch_key,
            'delivery_summary': marked['summary'],
        }

    if outcome == 'unknown_needs_reconciliation' or provider_result.get('unknown'):
        marked = mark_unknown(
            claim['rows'],
            (provider_result.get('errors') or ['Provider outcome unknown'])[0],
            table_client=table_client,
        )
        return {
            'success': True,
            'outcome': 'unknown_needs_reconciliation',
            'sent': 0,
            'failed': 0,
            'errors': provider_result.get('errors') or marked['errors'],
            'idempotency_key': provider_batch_key,
            'delivery_summary': marked['summary'],
        }

    marked = mark_failed(
        claim['rows'],
        (provider_result.get('errors') or [provider_result.get('error', 'Provider send failed')])[0],
        table_client=table_client,
    )
    return {
        'success': False,
        'outcome': 'pre_send_failure',
        'sent': 0,
        'failed': len(messages or []),
        'errors': provider_result.get('errors') or marked['errors'],
        'idempotency_key': provider_batch_key,
        'delivery_summary': marked['summary'],
    }


def reconcile_batch(
    messages,
    ledger_rows,
    provider_sender,
    table_client=None,
    mode=None,
):
    """Retry one existing pending/unknown batch with its original key only."""
    rows = list(ledger_rows or [])
    selected_mode = mode or delivery_mode()
    keys = {row.get('idempotency_key') for row in rows}
    provider_batch_key = next(iter(keys), None)
    if len(keys) != 1 or not provider_batch_key or len(rows) != len(messages or []):
        return {
            'success': False,
            'outcome': 'manual_review_required',
            'sent': 0,
            'failed': len(messages or []),
            'errors': ['Cannot deterministically reconstruct one original provider batch'],
            'idempotency_key': provider_batch_key,
        }
    if selected_mode != 'live':
        result = blocked_delivery_result(len(messages or []), selected_mode)
        result.update({
            'outcome': 'delivery_disabled',
            'idempotency_key': provider_batch_key,
            'reconciliation_required': True,
            'delivery_summary': delivery_summary(rows),
        })
        return result

    try:
        provider_result = provider_sender(
            messages, idempotency_key=provider_batch_key
        ) or {}
    except Exception as exc:
        provider_result = {
            'outcome': 'unknown_needs_reconciliation',
            'errors': [str(exc)],
            'deliveries': [],
        }
    deliveries = provider_result.get('deliveries') or []
    if provider_result.get('outcome') == 'accepted' or (
        provider_result.get('success') is True
        and not provider_result.get('errors')
        and len(deliveries) == len(messages)
    ):
        marked = mark_accepted(rows, deliveries, table_client=table_client)
        if marked['outcome'] == 'accepted_needs_reconciliation':
            return {
                'success': True,
                'outcome': 'accepted_needs_reconciliation',
                'sent': len(deliveries),
                'failed': 0,
                'errors': marked['errors'],
                'idempotency_key': provider_batch_key,
                'delivery_summary': marked['summary'],
            }
        return {
            'success': True,
            'outcome': 'accepted',
            'sent': len(deliveries),
            'failed': 0,
            'errors': [],
            'deliveries': deliveries,
            'idempotency_key': provider_batch_key,
            'delivery_summary': marked['summary'],
        }

    marked = mark_unknown(
        rows,
        (provider_result.get('errors') or ['Provider outcome unknown'])[0],
        table_client=table_client,
    )
    return {
        'success': True,
        'outcome': 'unknown_needs_reconciliation',
        'sent': 0,
        'failed': 0,
        'errors': provider_result.get('errors') or marked['errors'],
        'idempotency_key': provider_batch_key,
        'delivery_summary': marked['summary'],
    }


def find_reconciliation_required(action=None, period_label=None, table_client=None):
    try:
        query = _table(table_client).select('*').in_('delivery_status', ['pending', 'unknown'])
        if action:
            query = query.eq('action', action)
        if period_label:
            query = query.eq('period_label', period_label)
        query = query.order('created_at')
        result = _execute(query)
    except Exception as exc:
        return {'success': False, 'rows': [], 'summary': delivery_summary([]), 'error': str(exc)}
    if result.error:
        return {
            'success': False,
            'rows': [],
            'summary': delivery_summary([]),
            'error': str(result.error),
        }
    rows = result.data or []
    batch_keys = sorted({row.get('idempotency_key') for row in rows if row.get('idempotency_key')})
    if batch_keys:
        try:
            all_query = _table(table_client).select('*')
            if action:
                all_query = all_query.eq('action', action)
            if period_label:
                all_query = all_query.eq('period_label', period_label)
            all_query = all_query.in_('idempotency_key', batch_keys).order('message_key')
            all_result = _execute(all_query)
            if not all_result.error and all_result.data:
                # Reconciliation is batch-level. Include already-accepted rows
                # when a post-provider ledger update only partially succeeded.
                rows = all_result.data
        except Exception:
            pass
    return {'success': True, 'rows': rows, 'summary': delivery_summary(rows)}
