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
        if isinstance(to_email, list):
            recipients = to_email
        else:
            recipients = [to_email]

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

        return {'success': True, 'sent_to': recipients, 'id': response.get('id')}

    except resend.exceptions.RateLimitError as e:
        if _retry:
            _time.sleep(1)
            return send_email(to_email, subject, html_content, reply_to, _retry=False)
        return {'success': False, 'error': f'Rate limit: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_bulk_emails(messages, idempotency_key=None, _retry=True):
    """Send up to 100 individualized messages per Resend batch request.

    The old bulk paths made one provider request and one database write per
    recipient. That made a normal reminder batch capable of running past
    Vercel's 60-second function limit after Resend had already accepted the
    messages. Resend's batch endpoint keeps each recipient isolated while
    reducing the provider round trips to one per 100 messages.
    """
    import resend

    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        return {
            'success': False,
            'sent': 0,
            'failed': len(messages),
            'deliveries': [],
            'errors': ['RESEND_API_KEY not configured in environment variables'],
        }

    if not messages:
        return {'success': True, 'sent': 0, 'failed': 0, 'deliveries': [], 'errors': []}

    batch_sender = getattr(resend, 'Batch', None)
    if batch_sender is None or not hasattr(batch_sender, 'send'):
        return {
            'success': False,
            'sent': 0,
            'failed': len(messages),
            'deliveries': [],
            'errors': ['Resend SDK does not support batch email sends'],
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
        'sent': len(deliveries),
        'failed': len(messages) - len(deliveries),
        'deliveries': deliveries,
        'errors': errors,
    }


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

            action = data.get('action', 'send')
            self._run_action = action
            self._run_period = data.get('period_label', datetime.now().strftime('%B %Y'))
            strict_mode = bool(data.get('strict', True))

            # Auth check for mass-send actions (GitHub Actions must pass CRON_SECRET)
            PROTECTED_ACTIONS = {
                'send_availability_check', 'send_final_reminder',
                'send_midmonth_reminders', 'send_admin_alert',
                'resend_match_emails',
                'test_auth_check',
            }
            if action in PROTECTED_ACTIONS:
                cron_secret = os.environ.get('CRON_SECRET', '')
                if not cron_secret:
                    self._send_error(500, 'CRON_SECRET not configured')
                    return
                auth = self.headers.get('Authorization', '').replace('Bearer ', '')
                if auth != cron_secret:
                    self._send_error(401, 'Unauthorized')
                    return

            RUN_TRACKED_ACTIONS = {
                'send_availability_check',
                'send_final_reminder',
                'send_midmonth_reminders',
                'resend_match_emails',
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
                if result['success']:
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

                if result['success']:
                    self._send_success({"message": "Welcome email sent", **result})
                else:
                    self._send_error(500, result.get('error'))

            elif action == 'send_availability_check':
                # Send availability check to all players (including paused - they need to know to reactivate!)
                from api.supabase_http import table

                # Get all players with 'player' tier (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('email, name').eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No active players to email", "sent": 0})
                    return

                html = get_availability_check_email_html()
                period = datetime.now().strftime('%B %Y')

                messages = [{
                    'from': SENDER_EMAIL,
                    'to': [player['email']],
                    'subject': 'Quick check: are you playing next month?',
                    'html': html,
                    'reply_to': REPLY_TO_EMAIL,
                } for player in players.data]
                result = send_bulk_emails(
                    messages,
                    idempotency_key=f'networth:{action}:{period}',
                )
                sent = result.get('sent', 0)
                errors = result.get('errors', [])
                deliveries = result.get('deliveries', [])

                if deliveries:
                    log_rows = [{
                        'action': action,
                        'to_emails': delivery['to'],
                        'period_label': period,
                        'resend_email_id': delivery['id'],
                    } for delivery in deliveries]
                    log_result = table('email_log').insert(log_rows).execute()
                    if log_result.error:
                        errors.append(f'Failed to write email_log: {log_result.error}')

                if errors and strict_mode:
                    self._send_error(500, f"Sent {sent}, failed {len(errors)}: {errors[0]}",
                                     extra={"sent": sent, "failed": len(errors), "errors": errors})
                    return
                self._send_success({
                    "message": f"Sent availability check to {sent} players",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'send_final_reminder':
                from api.supabase_http import table

                # All players (including paused - they need to know to reactivate!)
                # Players with 'player' tier only (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('email, name').eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No players to email", "sent": 0})
                    return

                html = get_final_reminder_email_html()
                period = datetime.now().strftime('%B %Y')

                messages = [{
                    'from': SENDER_EMAIL,
                    'to': [player['email']],
                    'subject': 'Last call: update your playing status',
                    'html': html,
                    'reply_to': REPLY_TO_EMAIL,
                } for player in players.data]
                result = send_bulk_emails(
                    messages,
                    idempotency_key=f'networth:{action}:{period}',
                )
                sent = result.get('sent', 0)
                errors = result.get('errors', [])
                deliveries = result.get('deliveries', [])

                if deliveries:
                    log_rows = [{
                        'action': action,
                        'to_emails': delivery['to'],
                        'period_label': period,
                        'resend_email_id': delivery['id'],
                    } for delivery in deliveries]
                    log_result = table('email_log').insert(log_rows).execute()
                    if log_result.error:
                        errors.append(f'Failed to write email_log: {log_result.error}')

                if errors and strict_mode:
                    self._send_error(500, f"Sent {sent}, failed {len(errors)}: {errors[0]}",
                                     extra={"sent": sent, "failed": len(errors), "errors": errors})
                    return
                self._send_success({
                    "message": f"Sent final reminder to {sent} players",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'send_availability_check_paused_only':
                # Send availability check ONLY to paused players (catch-up for those who missed it)
                from api.supabase_http import table

                # Get paused players with 'player' tier only (excludes 'social_butterfly' and 'admin' tiers)
                players = table('players').select('email, name').eq('is_active', False).eq('membership_tier', 'player').execute()

                if players.error:
                    self._send_error(500, f"Failed to load players: {players.error}")
                    return
                if not players.data:
                    self._send_success({"message": "No paused players to email", "sent": 0})
                    return

                import time
                html = get_availability_check_email_html()
                sent = 0
                errors = []

                for i, player in enumerate(players.data):
                    # Rate limit: Resend allows 2 req/sec
                    if i > 0:
                        time.sleep(0.6)
                    result = send_email(player['email'], "Quick check: are you playing next month?", html)
                    if result['success']:
                        sent += 1
                    else:
                        errors.append(f"{player['email']}: {result.get('error')}")

                self._send_success({
                    "message": f"Sent availability check to {sent} paused players",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'send_midmonth_reminders':
                from api.supabase_http import table

                # Get current month's pending matches that haven't been reminded yet
                month = datetime.now().strftime('%B %Y')
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

                bulk_result = send_bulk_emails(
                    [message for _, message in email_jobs],
                    idempotency_key=f'networth:{action}:{month}',
                )
                sent = bulk_result.get('sent', 0)
                errors.extend(bulk_result.get('errors', []))
                log_rows = []

                for (match, message), delivery in zip(email_jobs, bulk_result.get('deliveries', [])):
                    table('match_assignments').update({
                        'reminder_sent_at': datetime.now(timezone.utc).isoformat(),
                        'reminder_email_id': delivery['id'],
                    }).eq('id', match.get('id')).execute()
                    log_rows.append({
                        'action': 'send_midmonth_reminders',
                        'to_emails': delivery['to'],
                        'period_label': month,
                        'match_id': match.get('id'),
                        'resend_email_id': delivery['id'],
                    })

                if log_rows:
                    log_result = table('email_log').insert(log_rows).execute()
                    if log_result.error:
                        errors.append(f'Failed to write email_log: {log_result.error}')

                if errors and strict_mode:
                    self._send_error(500, f"Sent {sent}, failed {len(errors)}: {errors[0]}",
                                     extra={"sent": sent, "failed": len(errors), "errors": errors})
                    return
                self._send_success({
                    "message": f"Sent mid-month reminders to {sent} match pairs",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'resend_match_emails':
                # Resend match assignment emails for current month
                import time
                from api.supabase_http import table

                month = datetime.now().strftime('%B %Y')
                matches = table('match_assignments').select('*').eq('period_label', month).execute()

                if not matches.data:
                    self._send_success({"message": "No matches found for current month", "sent": 0})
                    return

                # Get all players
                players_result = table('players').select('id, name, email, phone, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late').execute()
                players_map = {p['id']: p for p in players_result.data}

                sent = 0
                errors = []

                for i, match in enumerate(matches.data):
                    if i > 0:
                        time.sleep(0.6)

                    p1 = players_map.get(match.get('player1_id'), {})
                    p2 = players_map.get(match.get('player2_id'), {})

                    if not p1 or not p2:
                        errors.append(f"Match {match.get('id')}: Player not found")
                        continue

                    # Build availability text
                    def get_avail(p):
                        parts = []
                        wd = []
                        if p.get('avail_weekday_early'): wd.append('before 9am')
                        if p.get('avail_weekday_day'): wd.append('9-5')
                        if p.get('avail_weekday_late'): wd.append('after 5pm')
                        if wd: parts.append(f"Weekdays: {', '.join(wd)}")
                        we = []
                        if p.get('avail_weekend_early'): we.append('before 9am')
                        if p.get('avail_weekend_day'): we.append('9-5')
                        if p.get('avail_weekend_late'): we.append('after 5pm')
                        if we: parts.append(f"Weekends: {', '.join(we)}")
                        return ' | '.join(parts) if parts else ''

                    html = get_match_assignment_email_html(
                        p1['name'], p2['name'], month,
                        get_avail(p1), get_avail(p2),
                        p1.get('phone', ''), p2.get('phone', '')
                    )
                    subject = f"{p1['name']}, meet {p2['name']} - You're matched for {month}!"

                    result = send_email([p1['email'], p2['email']], subject, html, reply_to=p1['email'])
                    if result.get('success'):
                        sent += 1
                        # Update match_email_id and write to universal email log
                        table('match_assignments').update({
                            'match_email_id': result.get('id'),
                        }).eq('id', match.get('id')).execute()
                        table('email_log').insert({
                            'action': 'resend_match_emails',
                            'to_emails': [p1['email'], p2['email']],
                            'period_label': month,
                            'match_id': match.get('id'),
                            'resend_email_id': result.get('id'),
                        }).execute()
                    else:
                        errors.append(f"{p1['name']} & {p2['name']}: {result.get('error')}")

                if errors and strict_mode:
                    self._send_error(500, f"Sent {sent}, failed {len(errors)}: {errors[0]}",
                                     extra={"sent": sent, "failed": len(errors), "errors": errors})
                    return
                self._send_success({
                    "message": f"Sent match emails to {sent} pairs",
                    "sent": sent,
                    "errors": errors if errors else None
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

                if result['success']:
                    self._send_success({
                        "message": "Alert sent to sysadmin",
                        "sent_to": admin_email
                    })
                else:
                    self._send_error(500, result.get('error'))

            elif action == 'check_recent_send':
                # Check email_log to verify if a bulk action was sent today
                # Used by GitHub Actions to validate after a 504 (was the send real or not?)
                # Auth: same CRON_SECRET required
                cron_secret = os.environ.get('CRON_SECRET', '')
                auth = self.headers.get('Authorization', '').replace('Bearer ', '')
                if not cron_secret or auth != cron_secret:
                    self._send_error(401, 'Unauthorized')
                    return

                from api.supabase_http import table
                check_action = data.get('email_action', '')
                if not check_action:
                    self._send_error(400, "email_action required")
                    return

                # Find rows for this action sent since midnight UTC today
                today_start = datetime.now(timezone.utc).strftime('%Y-%m-%dT00:00:00+00:00')
                result = table('email_log').select('resend_email_id,sent_at').eq('action', check_action).gte('sent_at', today_start).execute()
                if result.error:
                    self._send_error(500, "Failed to query email_log")
                    return

                count = len(result.data) if result.data else 0
                self._send_success({
                    "already_sent": count > 0,
                    "sent": count,
                    "email_action": check_action
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
