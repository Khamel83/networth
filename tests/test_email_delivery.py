"""Tests for the canonical email delivery ledger and batch outcomes."""

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _message_rows():
    return [{
        'action': 'send_final_reminder',
        'period_label': 'July 2026',
        'message_key': 'send_final_reminder:July 2026:p1',
        'recipient_emails': ['p1@example.com'],
        'template': 'final_reminder',
        'idempotency_key': 'networth:send_final_reminder:July 2026:batch:0',
    }]


def _table_with_insert(rows=None, error=None):
    table = Mock()
    table.insert.return_value.execute.return_value = SimpleNamespace(
        data=rows or [], error=error
    )
    return table


def test_stable_delivery_keys():
    from api.email_delivery import delivery_idempotency_key, delivery_message_key

    message_key = delivery_message_key('final', 'July 2026', 'player-1')
    assert message_key == 'final:July 2026:player-1'
    assert delivery_idempotency_key('final', 'July 2026', 'player-1') == (
        'networth:final:July 2026:player-1'
    )


def test_delivery_summary_counts_only_known_states():
    from api.email_delivery import delivery_summary

    assert delivery_summary([
        {'delivery_status': 'pending'},
        {'delivery_status': 'accepted'},
        {'delivery_status': 'accepted'},
        {'delivery_status': 'failed'},
        {'delivery_status': 'unknown'},
        {'delivery_status': 'other'},
    ]) == {
        'pending': 1,
        'accepted': 2,
        'failed': 1,
        'unknown': 1,
    }


def test_claim_failure_prevents_provider_call():
    from api.email_delivery import deliver_batch

    table = _table_with_insert(error='HTTP 409: duplicate message key')
    provider = Mock()

    result = deliver_batch(
        messages=[{'to': ['p1@example.com']}],
        ledger_rows=_message_rows(),
        provider_sender=provider,
        table_client=table,
        mode='live',
    )

    assert result['outcome'] == 'pre_send_failure'
    assert result['success'] is False
    provider.assert_not_called()


def test_failed_claim_can_retry_same_stable_message_key():
    from api.email_delivery import deliver_batch

    rows = _message_rows()
    table = Mock()
    table.insert.return_value.execute.return_value = SimpleNamespace(
        data=[], error='HTTP 409: duplicate key value violates unique constraint'
    )
    existing = dict(rows[0], id='ledger-1', delivery_status='failed')
    table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[existing], error=None
    )
    table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[], error=None
    )
    provider = Mock(return_value={
        'outcome': 'accepted',
        'deliveries': [{'id': 'resend-1', 'to': ['p1@example.com']}],
    })

    result = deliver_batch(
        messages=[{'to': ['p1@example.com']}],
        ledger_rows=rows,
        provider_sender=provider,
        table_client=table,
        mode='live',
    )

    assert result['outcome'] == 'accepted'
    provider.assert_called_once_with(
        [{'to': ['p1@example.com']}],
        idempotency_key=rows[0]['idempotency_key'],
    )


def test_accepted_provider_result_with_ledger_failure_is_reconciliation_needed():
    from api.email_delivery import deliver_batch

    rows = _message_rows()
    table = _table_with_insert(rows=rows)
    table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[], error='database unavailable'
    )
    provider = Mock(return_value={
        'outcome': 'accepted',
        'deliveries': [{'id': 'resend-1', 'to': ['p1@example.com']}],
        'sent': 1,
    })

    result = deliver_batch(
        messages=[{'to': ['p1@example.com']}],
        ledger_rows=rows,
        provider_sender=provider,
        table_client=table,
        mode='live',
    )

    assert result['success'] is True
    assert result['outcome'] == 'accepted_needs_reconciliation'
    provider.assert_called_once_with(
        [{'to': ['p1@example.com']}],
        idempotency_key=rows[0]['idempotency_key'],
    )


def test_unknown_provider_result_preserves_exact_batch_key():
    from api.email_delivery import deliver_batch

    rows = _message_rows()
    table = _table_with_insert(rows=rows)
    table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[], error=None
    )
    provider = Mock(return_value={
        'outcome': 'unknown_needs_reconciliation',
        'deliveries': [],
        'errors': ['provider timeout'],
        'sent': 0,
        'idempotency_key': rows[0]['idempotency_key'],
    })

    result = deliver_batch(
        messages=[{'to': ['p1@example.com']}],
        ledger_rows=rows,
        provider_sender=provider,
        table_client=table,
        mode='live',
    )

    assert result['success'] is True
    assert result['outcome'] == 'unknown_needs_reconciliation'
    assert result['idempotency_key'] == rows[0]['idempotency_key']
    provider.assert_called_once_with(
        [{'to': ['p1@example.com']}],
        idempotency_key=rows[0]['idempotency_key'],
    )


def test_reconciliation_uses_existing_batch_key_without_reclaiming_rows():
    from api.email_delivery import reconcile_batch

    rows = _message_rows()
    rows[0]['id'] = 'ledger-1'
    table = Mock()
    table.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[], error=None
    )
    provider = Mock(return_value={
        'outcome': 'accepted',
        'deliveries': [{'id': 'resend-1', 'to': ['p1@example.com']}],
        'sent': 1,
    })

    result = reconcile_batch(
        messages=[{'to': ['p1@example.com']}],
        ledger_rows=rows,
        provider_sender=provider,
        table_client=table,
        mode='live',
    )

    assert result['outcome'] == 'accepted'
    assert result['idempotency_key'] == rows[0]['idempotency_key']
    table.insert.assert_not_called()
    provider.assert_called_once_with(
        [{'to': ['p1@example.com']}],
        idempotency_key=rows[0]['idempotency_key'],
    )


def test_disabled_batch_reports_targets_without_claiming_or_provider_call():
    from api.email_delivery import deliver_batch

    table = Mock()
    provider = Mock()
    result = deliver_batch(
        messages=[{'to': ['p1@example.com']}, {'to': ['p2@example.com']}],
        ledger_rows=_message_rows() * 2,
        provider_sender=provider,
        table_client=table,
        mode='disabled',
    )

    assert result['success'] is True
    assert result['outcome'] == 'delivery_disabled'
    assert result['would_send'] == 2
    table.insert.assert_not_called()
    provider.assert_not_called()


def test_reconciliation_query_returns_pending_and_unknown_rows():
    from api.email_delivery import find_reconciliation_required

    rows = [
        {'message_key': 'pending-1', 'delivery_status': 'pending'},
        {'message_key': 'unknown-1', 'delivery_status': 'unknown'},
    ]
    table = Mock()
    query = table.select.return_value
    query.in_.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.execute.return_value = SimpleNamespace(data=rows, error=None)

    result = find_reconciliation_required(
        action='send_final_reminder',
        period_label='July 2026',
        table_client=table,
    )

    assert result['success'] is True
    assert result['rows'] == rows
    assert result['summary']['pending'] == 1
    assert result['summary']['unknown'] == 1


def test_automation_run_lock_uses_unique_conflict_as_lock(monkeypatch):
    from api.reliability import try_start_run

    table = _table_with_insert(error='HTTP 409: duplicate key value violates unique constraint')
    monkeypatch.setattr('api.supabase_http.table', lambda _name: table)

    run_id, lock_error = try_start_run('send_final_reminder', 'July 2026')

    assert run_id is None
    assert 'already exists' in lock_error
    table.select.assert_not_called()


def test_hardening_migration_supports_existing_and_absent_ledger_tables():
    source = Path('migrations/04_email_automation_hardening.sql').read_text()

    assert 'CREATE TABLE IF NOT EXISTS public.email_delivery_log' in source
    assert 'ADD COLUMN IF NOT EXISTS message_key' in source
    assert 'ADD COLUMN IF NOT EXISTS recipient_emails' in source
    assert 'ADD COLUMN IF NOT EXISTS idempotency_key' in source
    assert 'ADD COLUMN IF NOT EXISTS updated_at' in source
    assert 'ADD COLUMN IF NOT EXISTS accepted_at' in source
    assert "SET delivery_status = 'accepted'" in source
    assert 'DROP INDEX IF EXISTS public.idx_email_delivery_idempotency' in source
    assert 'idx_email_delivery_message_key' in source
    assert 'idx_automation_runs_action_period_active' in source
    assert 'information_schema.columns' in source
    assert "table_name = 'email_log'" in source
