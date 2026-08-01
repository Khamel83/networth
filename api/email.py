"""
Vercel Serverless Function: Email Notifications
Sends emails via Resend API for better deliverability.
Uses Supabase REST API (no Python supabase client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import time as _time
from datetime import datetime, timezone

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
from api.reliability import preflight, try_start_run, append_event, update_run
from api.email_policy import (
    CRON_PROTECTED_ACTIONS,
    DISABLED_PUBLIC_ACTIONS,
    blocked_delivery_result,
    delivery_mode,
    require_cron_secret,
)
from api.email_delivery import (
    build_delivery_rows,
    deliver_batch,
    delivery_idempotency_key,
    delivery_summary,
    find_reconciliation_required,
    reconcile_batch,
)
init_sentry()

# Email Configuration
SENDER_NAME = 'Net Worth Tennis'
SENDER_EMAIL = f'{SENDER_NAME} <hello@networthtennis.com>'
REPLY_TO_EMAIL = 'ashleybrooke.kaufman@gmail.com'
RESEND_BATCH_SIZE = 100
RESEND_BATCH_DELAY_SECONDS = 0.6


def _normalize_reply_to(reply_to):
    """Normalize reply_to for Resend API - accepts string or list"""
    if not reply_to:
        return None
    if isinstance(reply_to, (list, tuple, set)):
        # Resend accepts array of emails directly
        cleaned = [str(item).strip() for item in reply_to if item and str(item).strip()]
        return cleaned if cleaned else None
    value = str(reply_to).strip()
    return value or None


def send_email(to_email, subject, html_content, reply_to=None, _retry=True):
    """
    Send email via Resend API

    Args:
        to_email: Recipient email (string or list)
        subject: Email subject
        html_content: HTML email body
        reply_to: Optional reply-to address (defaults to Ashley's email)
        _retry: Internal flag — retries once on 429 rate limit

    Returns:
        dict with success status
    """
    recipients = to_email if isinstance(to_email, list) else [to_email]
    mode = delivery_mode()
    if mode != 'live':
        result = blocked_delivery_result(1, mode)
        result['sent_to'] = recipients
        return result

    import resend

    api_key = os.environ.get('RESEND_API_KEY')

    if not api_key:
        return {
            'success': False,
            'error': 'RESEND_API_KEY not configured in environment variables'
        }

    resend.api_key = api_key

    try:
        # Handle single email or list
        reply_to_value = _normalize_reply_to(reply_to) or REPLY_TO_EMAIL

        # Build email params
        params = {
            "from": SENDER_EMAIL,
            "to": recipients,
            "subject": subject,
            "html": html_content,
            "reply_to": reply_to_value
        }

        # Send via Resend
        response = resend.Emails.send(params)

        return {'success': True, 'sent': True, 'sent_to': recipients, 'id': response.get('id')}

    except resend.exceptions.RateLimitError as e:
        if _retry:
            _time.sleep(1)
            return send_email(to_email, subject, html_content, reply_to, _retry=False)
        return {'success': False, 'sent': False, 'error': f'Rate limit: {str(e)}'}
    except Exception as e:
        return {'success': False, 'sent': False, 'error': str(e)}


def send_bulk_emails(messages, idempotency_key=None, _retry=True):
    """Send up to 100 individualized messages per Resend batch request.

    The old bulk paths made one provider request and one database write per
    recipient. That made a normal reminder batch capable of running past
    Vercel's 60-second function limit after Resend had already accepted the
    messages. Resend's batch endpoint keeps each recipient isolated while
    reducing the provider round trips to one per 100 messages.
    """
    if not messages:
        return {
            'success': True,
            'sent': 0,
            'failed': 0,
            'deliveries': [],
            'errors': [],
            'delivery_mode': delivery_mode(),
        }

    mode = delivery_mode()
    if mode != 'live':
        result = blocked_delivery_result(len(messages), mode)
        result['outcome'] = 'delivery_disabled'
        result['idempotency_key'] = idempotency_key
        return result

    import resend

    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'sent': 0,
            'failed': len(messages),
            'deliveries': [],
            'errors': ['RESEND_API_KEY not configured in environment variables'],
            'idempotency_key': idempotency_key,
        }

    batch_sender = getattr(resend, 'Batch', None)
    if batch_sender is None or not hasattr(batch_sender, 'send'):
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'sent': 0,
            'failed': len(messages),
            'deliveries': [],
            'errors': ['Resend SDK does not support batch email sends'],
            'idempotency_key': idempotency_key,
        }

    resend.api_key = api_key
    deliveries = []
    errors = []
    batch_count = (len(messages) + RESEND_BATCH_SIZE - 1) // RESEND_BATCH_SIZE

    for batch_index in range(0, len(messages), RESEND_BATCH_SIZE):
        batch = messages[batch_index:batch_index + RESEND_BATCH_SIZE]
        if batch_index > 0:
            _time.sleep(RESEND_BATCH_DELAY_SECONDS)

        options = {'batch_validation': 'strict'}
        if idempotency_key:
            options['idempotency_key'] = (
                idempotency_key
                if batch_count == 1
                else f'{idempotency_key}:{batch_index // RESEND_BATCH_SIZE}'
            )

        try:
            response = batch_sender.send(batch, options)
            response_data = response.get('data', []) if isinstance(response, dict) else []
            if len(response_data) != len(batch):
                raise RuntimeError(
                    f'Resend batch returned {len(response_data)} IDs for {len(batch)} messages'
                )

            batch_deliveries = []
            for message, provider_response in zip(batch, response_data):
                provider_id = provider_response.get('id') if isinstance(provider_response, dict) else None
                if not provider_id:
                    raise RuntimeError('Resend batch response omitted an email ID')
                recipients = message.get('to', [])
                if isinstance(recipients, str):
                    recipients = [recipients]
                batch_deliveries.append({
                    'success': True,
                    'to': recipients,
                    'id': provider_id,
                })
            deliveries.extend(batch_deliveries)
        except resend.exceptions.RateLimitError as e:
            if _retry:
                _time.sleep(1)
                return send_bulk_emails(messages, idempotency_key=idempotency_key, _retry=False)
            errors.append(f'Rate limit: {str(e)}')
            break
        except Exception as e:
            errors.append(str(e))
            break

    return {
        'success': not errors,
        'outcome': 'accepted' if not errors else 'unknown_needs_reconciliation',
        'sent': len(deliveries),
        'failed': len(messages) - len(deliveries),
        'deliveries': deliveries,
        'errors': errors,
        'idempotency_key': idempotency_key,
    }


def _deliver_scheduled_batches(
    action,
    period_label,
    template,
    logical_messages,
    provider_messages,
    run_id=None,
):
    """Deliver scheduled messages through the canonical ledger in <=100 chunks."""
    if len(logical_messages) != len(provider_messages):
        return {
            'success': False,
            'outcome': 'pre_send_failure',
            'sent': 0,
            'failed': len(provider_messages),
            'errors': ['Logical and provider message counts do not match'],
            'reconciliation_required': False,
            'delivery_summary': delivery_summary([]),
        }

    if not provider_messages:
        return {
            'success': True,
            'outcome': 'no_targets',
            'sent': 0,
            'failed': 0,
            'would_send': 0,
            'errors': [],
            'reconciliation_required': False,
            'delivery_summary': delivery_summary([]),
        }

    results = []
    for start in range(0, len(provider_messages), RESEND_BATCH_SIZE):
        batch_index = start // RESEND_BATCH_SIZE
        batch_provider_messages = provider_messages[start:start + RESEND_BATCH_SIZE]
        batch_logical_messages = logical_messages[start:start + RESEND_BATCH_SIZE]
        provider_batch_key = delivery_idempotency_key(
            action, period_label, f'batch:{batch_index}'
        )
        ledger_rows = build_delivery_rows(
            action,
            period_label,
            batch_logical_messages,
            template,
            provider_batch_key,
            run_id=run_id,
        )
        results.append(deliver_batch(
            batch_provider_messages,
            ledger_rows,
            provider_sender=send_bulk_emails,
        ))

    errors = [error for result in results for error in result.get('errors', [])]
    sent = sum(result.get('sent', 0) for result in results)
    would_send = sum(result.get('would_send', 0) for result in results)
    summaries = [result.get('delivery_summary', {}) for result in results]
    summary = {
        state: sum(item.get(state, 0) for item in summaries)
        for state in ('pending', 'accepted', 'failed', 'unknown')
    }
    outcomes = {result.get('outcome') for result in results}
    reconciliation_required = bool(
        outcomes & {'accepted_needs_reconciliation', 'unknown_needs_reconciliation'}
    )
    if 'pre_send_failure' in outcomes:
        outcome = 'pre_send_failure'
        success = False
    elif 'unknown_needs_reconciliation' in outcomes:
        outcome = 'unknown_needs_reconciliation'
        success = True
    elif 'accepted_needs_reconciliation' in outcomes:
        outcome = 'accepted_needs_reconciliation'
        success = True
    elif 'delivery_disabled' in outcomes:
        outcome = 'delivery_disabled'
        success = True
    else:
        outcome = 'accepted'
        success = True
    return {
        'success': success,
        'outcome': outcome,
        'sent': sent,
        'failed': sum(result.get('failed', 0) for result in results),
        'would_send': would_send,
        'errors': errors,
        'reconciliation_required': reconciliation_required,
        'delivery_summary': summary,
        'batch_results': results,
    }


def _rebuild_reconciliation_messages(action, period_label, rows):
    """Rebuild only templates whose original payload is deterministic."""
    ordered_rows = sorted(rows, key=lambda row: row.get('message_key', ''))
    templates = {row.get('template') for row in ordered_rows}
    if action in {'send_availability_check', 'send_availability_check_paused_only'} and templates == {'availability_check'}:
        html = get_availability_check_email_html()
        return [
            {
                'from': SENDER_EMAIL,
                'to': row.get('recipient_emails', []),
                'subject': 'Quick check: are you playing next month?',
                'html': html,
                'reply_to': REPLY_TO_EMAIL,
            }
            for row in ordered_rows
        ], None
    if action == 'generate_pairings' and templates == {'match_assignment'}:
        prefix = f'generate_pairings:{period_label}:'
        assignment_ids = []
        for row in ordered_rows:
            message_key = row.get('message_key', '')
            if not message_key.startswith(prefix):
                return None, 'Pairing delivery row has an invalid stable message key'
            assignment_id = message_key[len(prefix):]
            if not assignment_id or ':' in assignment_id:
                return None, 'Pairing delivery row is missing its assignment id'
            assignment_ids.append(assignment_id)

        # The ledger intentionally stores delivery metadata, not the whole
        # HTML payload. Rebuild pairing messages from the immutable assignment
        # id and the current player profile, while preserving the original
        # recipient list and first-recipient reply-to address.
        from api.supabase_http import table
        assignments_result = table('match_assignments').select(
            'id, player1_id, player2_id, period_label'
        ).in_('id', assignment_ids).eq('period_label', period_label).execute()
        if assignments_result.error:
            return None, f'Failed to load pairing assignments: {assignments_result.error}'
        assignments = {
            assignment.get('id'): assignment
            for assignment in (assignments_result.data or [])
        }
        if len(assignments) != len(set(assignment_ids)):
            return None, 'One or more pairing assignments are missing for reconciliation'

        player_ids = []
        for assignment_id in assignment_ids:
            assignment = assignments.get(assignment_id)
            player_ids.extend([
                assignment.get('player1_id'),
                assignment.get('player2_id'),
            ])
        player_ids = [player_id for player_id in player_ids if player_id]
        players_result = table('players').select(
            'id, name, email, phone, '
            'avail_weekday_early, avail_weekday_day, avail_weekday_late, '
            'avail_weekend_early, avail_weekend_day, avail_weekend_late, '
            'available_morning, available_afternoon, available_evening'
        ).in_('id', sorted(set(player_ids))).execute()
        if players_result.error:
            return None, f'Failed to load pairing players: {players_result.error}'
        players = {
            player.get('id'): player
            for player in (players_result.data or [])
        }

        # Keep this helper local to avoid importing the HTTP handler module at
        # import time. pairings.py already owns the six-slot formatting rules.
        from api.pairings import get_availability_text

        messages = []
        for row, assignment_id in zip(ordered_rows, assignment_ids):
            assignment = assignments[assignment_id]
            player1 = players.get(assignment.get('player1_id'))
            player2 = players.get(assignment.get('player2_id'))
            if not player1 or not player2:
                return None, f'One or more players are missing for assignment {assignment_id}'
            recipients = row.get('recipient_emails') or []
            if isinstance(recipients, str):
                recipients = [recipients]
            if len(recipients) < 2:
                return None, f'Pairing delivery row has incomplete recipients for {assignment_id}'
            messages.append({
                'from': SENDER_EMAIL,
                'to': recipients,
                'subject': (
                    f"{player1.get('name', '')}, meet {player2.get('name', '')} - "
                    f"You're matched for {period_label}!"
                ),
                'html': get_match_assignment_email_html(
                    player1.get('name', ''),
                    player2.get('name', ''),
                    period_label,
                    get_availability_text(player1),
                    get_availability_text(player2),
                    player1.get('phone', ''),
                    player2.get('phone', ''),
                ),
                'reply_to': recipients[0],
            })
        return messages, None
    if action == 'send_final_reminder' and templates == {'final_reminder'}:
        html = get_final_reminder_email_html()
        return [
            {
                'from': SENDER_EMAIL,
                'to': row.get('recipient_emails', []),
                'subject': 'Last call: update your playing status',
                'html': html,
                'reply_to': REPLY_TO_EMAIL,
            }
            for row in ordered_rows
        ], None
    return None, 'Original message payload is not deterministic for reconciliation'


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================

def get_email_styles():
    """Common CSS styles for all emails"""
    return """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #d165a4; margin: 0; }
        .content { background: #f9f9f9; border-radius: 10px; padding: 30px; margin-bottom: 20px; }
        .button { display: inline-block; background: linear-gradient(135deg, #d165a4, #ec613e); color: white; padding: 14px 28px; text-decoration: none; border-radius: 50px; font-weight: 600; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; }
        .signature { color: #d165a4; font-weight: 600; }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
    </style>
    """


def get_welcome_email_html(player_name, membership_tier='player'):
    """
    Welcome email sent to new signups
    """
    # Show correct price based on tier
    price = '$45' if membership_tier == 'social_butterfly' else '$35'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Net Worth Tennis!</h1>
            </div>
            <div class="content">
                <p>Hi {player_name or 'there'},</p>

                <p>Thanks for signing up for the Net Worth Tennis League! We're so excited to have you.</p>

                <p>If you haven't sent your membership fee yet, please send <strong>{price}</strong> via Venmo to <strong>@NCOFFEN</strong> (Natalie) to complete your registration.</p>

                <p>You'll receive emails from us about match assignments, events, and league updates soon. Feel free to sign in to your player dashboard.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/login" class="button">Sign In to Your Dashboard</a>
                </p>

                <p>See you on the court!</p>

                <p class="signature">xoxo,<br>Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_match_assignment_email_html(player1_name, player2_name, month,
                                     avail1="", avail2="", phone1="", phone2=""):
    """
    Match assignment email sent to both players when paired
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>You're Matched!</h1>
            </div>
            <div class="content">
                <p>Hi {player1_name} and {player2_name},</p>

                <p>You're matched for a Net Worth game in <strong>{month}</strong>!</p>

                <p>Go ahead... make the first move ;)</p>

                <p>Please <strong>reply all</strong> to this email to start coordinating a time to play.</p>

                <p>Here's some info to help get things started:</p>

                <ul>
                    <li><strong>{player1_name}'s availability:</strong> {avail1 or 'Check their profile'}</li>
                    <li><strong>{player2_name}'s availability:</strong> {avail2 or 'Check their profile'}</li>
                </ul>

                <p>You're always free to coordinate directly, and texting works too:</p>

                <ul>
                    <li><strong>{player1_name}:</strong> {phone1 or 'See profile'}</li>
                    <li><strong>{player2_name}:</strong> {phone2 or 'See profile'}</li>
                </ul>

                <p>You can also view your current match and match history in your player profile.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Visit Your Dashboard</a>
                </p>

                <p>Have fun and happy hitting!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_availability_check_email_html():
    """
    Monthly availability check sent on the 27th
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Quick Check</h1>
            </div>
            <div class="content">
                <p>Hi there,</p>

                <p>Quick housekeeping note as we head into next month.</p>

                <p>If you'd like to play next month, please make sure you're marked as <strong>active</strong> in your player profile.</p>

                <p>If you need to sit next month out, head to your profile and mark yourself as <strong>unavailable</strong>.</p>

                <p>A few things to keep in mind:</p>

                <ul>
                    <li>Availability is player-controlled and does not reset automatically</li>
                    <li>If you pause, you'll stay paused until you turn playing back on</li>
                    <li>Pausing ensures you won't be assigned a match while you're away</li>
                </ul>

                <p>We ask everyone to be thoughtful about updating their status so match assignments stay smooth for the whole league.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Update Your Status</a>
                </p>

                <p>Thanks!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_final_reminder_email_html():
    """
    Final availability reminder sent on the last day of the month
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Last Call!</h1>
            </div>
            <div class="content">
                <p>Hi there,</p>

                <p>This is your <strong>final reminder</strong> to check your playing status for next month.</p>

                <p>Match assignments will be created <strong>tomorrow</strong>, so please visit your player profile today to confirm:</p>

                <ul>
                    <li>You're marked <strong>active</strong> if you want to play, or</li>
                    <li>You're marked <strong>unavailable</strong> if you need to sit next month out</li>
                </ul>

                <p>If no changes are made, your current status will carry over.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Update Your Status</a>
                </p>

                <p>Thanks for helping keep things running smoothly!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_midmonth_reminder_email_html(player1_name, player2_name, month):
    """
    Mid-month reminder to play your match
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Friendly Reminder</h1>
            </div>
            <div class="content">
                <p>Hi {player1_name} and {player2_name},</p>

                <p>Just a friendly reminder to get your <strong>{month}</strong> match on the calendar.</p>

                <p>If you've already played, feel free to ignore this note (and nice work!).</p>

                <p>If not, there's still plenty of time to coordinate and get out on the court.</p>

                <p>You can always find match details in your player profile.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Visit Your Dashboard</a>
                </p>

                <p>See you out there!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_sitout_confirmation_email_html(player_name, period_label):
    """Confirmation when player marks themselves as sitting out"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>You're Sitting Out</h1>
            </div>
            <div class="content">
                <p>Hi {player_name},</p>

                <p>This confirms that you're sitting out starting <strong>{period_label}</strong>.</p>

                <p>You won't be assigned any matches until you mark yourself as active again.</p>

                <p>When you're ready to play, just visit your dashboard and click "I'm Back!"</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Visit Your Dashboard</a>
                </p>

                <p>See you when you're back!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_rejoin_confirmation_email_html(player_name, eligible_month):
    """Confirmation when player marks themselves as active again"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome Back!</h1>
            </div>
            <div class="content">
                <p>Hi {player_name},</p>

                <p>Great news! You're back in the game.</p>

                <p>You'll be eligible for matches starting <strong>{eligible_month}</strong>.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/dashboard" class="button">Visit Your Dashboard</a>
                </p>

                <p>See you on the court!</p>

                <p class="signature">Net Worth Girlies</p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - East Side LA Women's Tennis League</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_admin_alert_email_html(subject, message):
    """Alert email sent to admins on system failures"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>{get_email_styles()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Alert</h1>
            </div>
            <div class="content">
                <p><strong>Subject:</strong> {subject}</p>

                <p><strong>Message:</strong></p>
                <p style="white-space: pre-wrap;">{message}</p>

                <p style="margin-top: 30px;">Please log in to the admin dashboard to investigate.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://networthtennis.com/admin" class="button">Admin Dashboard</a>
                </p>
            </div>
            <div class="footer">
                <p>Net Worth Tennis - System Alert</p>
            </div>
        </div>
    </body>
    </html>
    """


# =============================================================================
# API HANDLER
# =============================================================================

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Return email system status"""
        resend_configured = bool(os.environ.get('RESEND_API_KEY'))
        self._send_success({
            "status": "ready" if resend_configured else "not_configured",
            "delivery_mode": delivery_mode(),
            "sender": SENDER_EMAIL,
            "reply_to": REPLY_TO_EMAIL,
            "message": "Email system ready (Resend)" if resend_configured else "RESEND_API_KEY not set in environment"
        })

    def do_POST(self):
        """Handle email sending requests"""
        self._run_id = None
        self._run_action = None
        self._run_period = None
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action')
            if not action:
                self._send_error(400, "Missing 'action' field")
                return
            self._run_action = action
            self._run_period = data.get('period_label', datetime.now().strftime('%B %Y'))
            strict_mode = bool(data.get('strict', True))

            if action in CRON_PROTECTED_ACTIONS and not require_cron_secret(self):
                return
            if action in DISABLED_PUBLIC_ACTIONS:
                self._send_error(403, 'Action is not publicly available')
                return
            if action == 'resend_match_emails':
                self._send_error(
                    410,
                    'Deprecated. Use reconcile_email_delivery with the original action and period.',
                )
                return

            RUN_TRACKED_ACTIONS = {
                'send_availability_check',
                'send_final_reminder',
                'send_midmonth_reminders',
            }
            if action in RUN_TRACKED_ACTIONS:
                run_id, lock_error = try_start_run(action, self._run_period, {'source': 'api/email'})
                self._run_id = run_id
                if lock_error:
                    self._send_error(409, lock_error)
                    return
                ok, preflight_details = preflight(
                    required_env=['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'RESEND_API_KEY'],
                    check_db=True
                )
                if not ok:
                    append_event(self._run_id, 'preflight', 'error', 'Preflight failed', preflight_details)
                    self._send_error(500, f"Preflight failed: {preflight_details}")
                    return
                append_event(self._run_id, 'preflight', 'info', 'Preflight passed', preflight_details)

            if action == 'send':
                # Direct email send
                to_email = data.get('to')
                subject = data.get('subject')
                html = data.get('html')
                reply_to = data.get('reply_to')

                if not all([to_email, subject, html]):
                    self._send_error(400, "Missing required fields: to, subject, html")
                    return

                result = send_email(to_email, subject, html, reply_to)
                if result.get('sent'):
                    self._send_success(result)
                else:
                    self._send_error(500, result.get('error', 'Failed to send email'))

            elif action == 'send_welcome':
                # Send welcome email to new signup
                to_email = data.get('to')
                player_name = data.get('player_name', '')

                if not to_email:
                    self._send_error(400, "Missing 'to' email address")
                    return

                html = get_welcome_email_html(player_name)
                result = send_email(to_email, "Welcome to Net Worth Tennis!", html)

                if result.get('sent'):
                    self._send_success({"message": "Welcome email sent", **result})
                else:
                    self._send_error(500, result.get('error'))

            elif action == 'send_availability_check':
                # Send availability check to all players (including paused - they need to know to reactivate!)
                from api.supabase_http import table

                # Get all players with 'player' tier (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('id, email, name').eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No active players to email", "sent": 0})
                    return

                html = get_availability_check_email_html()
                period = self._run_period

                messages = [{
                    'from': SENDER_EMAIL,
                    'to': [player['email']],
                    'subject': 'Quick check: are you playing next month?',
                    'html': html,
                    'reply_to': REPLY_TO_EMAIL,
                } for player in players.data]
                logical_messages = [{
                    'logical_id': player.get('id') or player['email'],
                    'recipient_emails': [player['email']],
                } for player in players.data]
                result = _deliver_scheduled_batches(
                    action,
                    period,
                    'availability_check',
                    logical_messages,
                    messages,
                    run_id=self._run_id,
                )

                if result['outcome'] == 'pre_send_failure' and strict_mode:
                    self._send_error(
                        500,
                        f"Email delivery failed: {result['errors'][0] if result['errors'] else 'unknown error'}",
                        extra=result,
                    )
                    return
                self._send_success({
                    "message": f"Processed availability check for {len(players.data)} players",
                    "sent": result['sent'],
                    "failed": result['failed'],
                    "would_send": result.get('would_send', 0),
                    "outcome": result['outcome'],
                    "reconciliation_required": result['reconciliation_required'],
                    "delivery_summary": result['delivery_summary'],
                    "errors": result['errors'] or None,
                })

            elif action == 'send_final_reminder':
                from api.supabase_http import table

                # All players (including paused - they need to know to reactivate!)
                # Players with 'player' tier only (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('id, email, name').eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No players to email", "sent": 0})
                    return

                html = get_final_reminder_email_html()
                period = self._run_period

                messages = [{
                    'from': SENDER_EMAIL,
                    'to': [player['email']],
                    'subject': 'Last call: update your playing status',
                    'html': html,
                    'reply_to': REPLY_TO_EMAIL,
                } for player in players.data]
                logical_messages = [{
                    'logical_id': player.get('id') or player['email'],
                    'recipient_emails': [player['email']],
                } for player in players.data]
                result = _deliver_scheduled_batches(
                    action,
                    period,
                    'final_reminder',
                    logical_messages,
                    messages,
                    run_id=self._run_id,
                )

                if result['outcome'] == 'pre_send_failure' and strict_mode:
                    self._send_error(
                        500,
                        f"Email delivery failed: {result['errors'][0] if result['errors'] else 'unknown error'}",
                        extra=result,
                    )
                    return
                self._send_success({
                    "message": f"Processed final reminder for {len(players.data)} players",
                    "sent": result['sent'],
                    "failed": result['failed'],
                    "would_send": result.get('would_send', 0),
                    "outcome": result['outcome'],
                    "reconciliation_required": result['reconciliation_required'],
                    "delivery_summary": result['delivery_summary'],
                    "errors": result['errors'] or None,
                })

            elif action == 'send_availability_check_paused_only':
                # Send availability check ONLY to paused players (catch-up for those who missed it)
                from api.supabase_http import table

                # Get paused players with 'player' tier only (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('id, email, name').eq('is_active', False).eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No paused players to email", "sent": 0})
                    return

                html = get_availability_check_email_html()
                period = self._run_period
                messages = [{
                    'from': SENDER_EMAIL,
                    'to': [player['email']],
                    'subject': 'Quick check: are you playing next month?',
                    'html': html,
                    'reply_to': REPLY_TO_EMAIL,
                } for player in players.data]
                logical_messages = [{
                    'logical_id': player.get('id') or player['email'],
                    'recipient_emails': [player['email']],
                } for player in players.data]
                result = _deliver_scheduled_batches(
                    action,
                    period,
                    'availability_check',
                    logical_messages,
                    messages,
                    run_id=self._run_id,
                )

                if result['outcome'] == 'pre_send_failure' and strict_mode:
                    self._send_error(
                        500,
                        f"Email delivery failed: {result['errors'][0] if result['errors'] else 'unknown error'}",
                        extra=result,
                    )
                    return

                self._send_success({
                    "message": f"Processed availability check for {len(players.data)} paused players",
                    "sent": result['sent'],
                    "failed": result['failed'],
                    "would_send": result.get('would_send', 0),
                    "outcome": result['outcome'],
                    "reconciliation_required": result['reconciliation_required'],
                    "delivery_summary": result['delivery_summary'],
                    "errors": result['errors'] or None,
                })

            elif action == 'send_midmonth_reminders':
                from api.supabase_http import table

                # Get current month's pending matches that haven't been reminded yet
                month = self._run_period
                matches_result = table('match_assignments').select('*').eq('period_label', month).eq('status', 'pending').is_('reminder_sent_at', 'null').execute()

                if matches_result.error:
                    self._send_error(500, f"Failed to load match assignments: {matches_result.error}")
                    return
                if not matches_result.data:
                    self._send_success({"message": "No pending matches to remind", "sent": 0})
                    return

                # Get player IDs to look up player details
                player_ids = set()
                for match in matches_result.data:
                    player_ids.add(match.get('player1_id'))
                    player_ids.add(match.get('player2_id'))

                # Get all relevant players
                players_result = table('players').select('id, email, name').execute()
                if players_result.error:
                    self._send_error(500, f"Failed to load players: {players_result.error}")
                    return
                players_map = {pl['id']: pl for pl in players_result.data if pl['id'] in player_ids}

                errors = []
                logical_messages = []
                email_jobs = []
                for match in matches_result.data:
                    p1 = players_map.get(match.get('player1_id'), {})
                    p2 = players_map.get(match.get('player2_id'), {})

                    if not p1 or not p2:
                        errors.append(f"Match {match.get('id')}: Player not found")
                        continue

                    html = get_midmonth_reminder_email_html(
                        p1.get('name', 'Player'),
                        p2.get('name', 'Player'),
                        month
                    )
                    email_jobs.append((match, {
                        'from': SENDER_EMAIL,
                        'to': [p1['email'], p2['email']],
                        'subject': f"Friendly reminder to play your {month} match",
                        'html': html,
                        'reply_to': p1['email'],
                    }))
                    logical_messages.append({
                        'logical_id': match.get('id'),
                        'recipient_emails': [p1['email'], p2['email']],
                    })

                result = _deliver_scheduled_batches(
                    action,
                    month,
                    'midmonth_reminder',
                    logical_messages,
                    [message for _, message in email_jobs],
                    run_id=self._run_id,
                )

                errors.extend(result.get('errors', []))
                if result['outcome'] == 'accepted':
                    accepted_deliveries = [
                        delivery
                        for batch_result in result.get('batch_results', [])
                        for delivery in batch_result.get('deliveries', [])
                    ]
                    for (match, _message), delivery in zip(email_jobs, accepted_deliveries):
                        table('match_assignments').update({
                            'reminder_sent_at': datetime.now(timezone.utc).isoformat(),
                            'reminder_email_id': delivery['id'],
                        }).eq('id', match.get('id')).execute()

                if result['outcome'] == 'pre_send_failure' and strict_mode:
                    self._send_error(
                        500,
                        f"Email delivery failed: {errors[0] if errors else 'unknown error'}",
                        extra=result,
                    )
                    return
                self._send_success({
                    "message": f"Processed mid-month reminders for {len(email_jobs)} match pairs",
                    "sent": result['sent'],
                    "failed": result['failed'],
                    "would_send": result.get('would_send', 0),
                    "outcome": result['outcome'],
                    "reconciliation_required": result['reconciliation_required'],
                    "delivery_summary": result['delivery_summary'],
                    "errors": errors or None,
                })

            elif action == 'reconcile_email_delivery':
                target_action = data.get('email_action') or data.get('target_action')
                period = data.get('period_label', self._run_period)
                if not target_action:
                    self._send_error(400, "email_action required")
                    return

                pending = find_reconciliation_required(
                    action=target_action,
                    period_label=period,
                )
                if not pending['success']:
                    self._send_error(500, pending['error'])
                    return
                if not pending['rows']:
                    self._send_success({
                        'outcome': 'already_complete',
                        'reconciliation_required': False,
                        'delivery_summary': pending['summary'],
                        'email_action': target_action,
                        'period_label': period,
                    })
                    return

                rows_by_key = {}
                for row in pending['rows']:
                    rows_by_key.setdefault(row.get('idempotency_key'), []).append(row)

                results = []
                for provider_batch_key, rows in rows_by_key.items():
                    messages, rebuild_error = _rebuild_reconciliation_messages(
                        target_action, period, rows
                    )
                    if rebuild_error:
                        results.append({
                            'success': True,
                            'outcome': 'manual_review_required',
                            'sent': 0,
                            'failed': 0,
                            'errors': [rebuild_error],
                            'idempotency_key': provider_batch_key,
                            'delivery_summary': delivery_summary(rows),
                        })
                        continue
                    results.append(reconcile_batch(
                        messages,
                        rows,
                        provider_sender=send_bulk_emails,
                    ))

                outcomes = {result.get('outcome') for result in results}
                if 'manual_review_required' in outcomes:
                    outcome = 'manual_review_required'
                elif 'unknown_needs_reconciliation' in outcomes:
                    outcome = 'unknown_needs_reconciliation'
                elif 'accepted_needs_reconciliation' in outcomes:
                    outcome = 'accepted_needs_reconciliation'
                elif 'delivery_disabled' in outcomes:
                    outcome = 'delivery_disabled'
                else:
                    outcome = 'accepted'
                self._send_success({
                    'outcome': outcome,
                    'reconciliation_required': outcome != 'accepted',
                    'sent': sum(result.get('sent', 0) for result in results),
                    'would_send': sum(result.get('would_send', 0) for result in results),
                    'errors': [error for result in results for error in result.get('errors', [])] or None,
                    'delivery_summary': {
                        state: sum(
                            result.get('delivery_summary', {}).get(state, 0)
                            for result in results
                        )
                        for state in ('pending', 'accepted', 'failed', 'unknown')
                    },
                    'email_action': target_action,
                    'period_label': period,
                })

            elif action == 'send_admin_alert':
                # Send alert email to sysadmin only (ADMIN_EMAIL env var)
                # Other league admins (Ashley, Natalie) don't need technical alerts
                subject = data.get('subject', 'Admin Alert')
                message = data.get('message', '')

                if not message:
                    self._send_error(400, "Missing 'message' field")
                    return

                admin_email = os.environ.get('ADMIN_EMAIL')
                if not admin_email:
                    self._send_error(500, "ADMIN_EMAIL not configured")
                    return

                html = get_admin_alert_email_html(subject, message)
                result = send_email(admin_email, f"Net Worth Alert: {subject}", html)

                if result.get('sent'):
                    self._send_success({
                        "message": "Alert sent to sysadmin",
                        "sent_to": admin_email,
                        **result,
                    })
                elif result.get('blocked'):
                    self._send_success({
                        "message": "Admin alert delivery disabled",
                        "sent": 0,
                        "outcome": "delivery_disabled",
                        "delivery_mode": result.get('delivery_mode'),
                    })
                else:
                    self._send_error(500, result.get('error'))

            elif action == 'check_recent_send':
                # Read the canonical delivery ledger for post-timeout inspection.
                from api.supabase_http import table
                check_action = data.get('email_action', '')
                if not check_action:
                    self._send_error(400, "email_action required")
                    return

                # Find rows for this action since midnight UTC today.
                today_start = datetime.now(timezone.utc).strftime('%Y-%m-%dT00:00:00+00:00')
                result = table('email_delivery_log').select(
                    'delivery_status,provider_id,created_at'
                ).eq('action', check_action).gte('created_at', today_start).execute()
                if result.error:
                    self._send_error(500, "Failed to query email_delivery_log")
                    return

                rows = result.data or []
                summary = delivery_summary(rows)
                count = summary['accepted']
                self._send_success({
                    "already_sent": count > 0,
                    "sent": count,
                    "email_action": check_action,
                    "delivery_summary": summary,
                    "reconciliation_required": bool(
                        summary['pending'] or summary['unknown'] or summary['failed']
                    ),
                })

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            print(f"Email error: {e}")
            self._send_error(500, "An unexpected error occurred")

    def _send_success(self, data):
        run_id = getattr(self, '_run_id', None)
        if run_id:
            append_event(run_id, 'complete', 'info', 'Email action completed', data if isinstance(data, dict) else {})
            update_run(run_id, 'succeeded', summary=data if isinstance(data, dict) else {"result": str(data)})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": True, **data}
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())

    def _send_error(self, status, message, extra=None):
        run_id = getattr(self, '_run_id', None)
        if run_id:
            append_event(run_id, 'error', 'error', message, {"status": status, "action": getattr(self, '_run_action', None)})
            update_run(run_id, 'failed_terminal', error={"status": status, "message": message})
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": False, "error": message}
        if extra:
            payload.update(extra)
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())
