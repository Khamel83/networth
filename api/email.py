"""
Vercel Serverless Function: Email Notifications
Sends emails via Resend API for better deliverability.
Uses Supabase REST API (no Python supabase client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# Email Configuration
SENDER_NAME = 'Net Worth Tennis'
SENDER_EMAIL = f'{SENDER_NAME} <noreply@networthtennis.com>'
REPLY_TO_EMAIL = 'ashleybrooke.kaufman@gmail.com'


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


def send_email(to_email, subject, html_content, reply_to=None):
    """
    Send email via Resend API

    Args:
        to_email: Recipient email (string or list)
        subject: Email subject
        html_content: HTML email body
        reply_to: Optional reply-to address (defaults to Ashley's email)

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

    except Exception as e:
        return {'success': False, 'error': str(e)}


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


def get_welcome_email_html(player_name):
    """
    Welcome email sent to new signups
    """
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

                <p>If you haven't sent your membership fee yet, please send <strong>$35</strong> via Venmo to <strong>@NCOFFEN</strong> (Natalie) to complete your registration.</p>

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
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'send')

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
                # Send availability check to all active players
                from api.supabase_http import table

                # Get all active players
                players = table('players').select('email, name').eq('is_active', True).execute()

                if not players.data:
                    self._send_success({"message": "No active players to email", "sent": 0})
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
                    "message": f"Sent availability check to {sent} players",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'send_final_reminder':
                from api.supabase_http import table

                players = table('players').select('email, name').eq('is_active', True).execute()

                if not players.data:
                    self._send_success({"message": "No active players to email", "sent": 0})
                    return

                import time
                html = get_final_reminder_email_html()
                sent = 0
                errors = []

                for i, player in enumerate(players.data):
                    # Rate limit: Resend allows 2 req/sec
                    if i > 0:
                        time.sleep(0.6)
                    result = send_email(player['email'], "Last call: update your playing status", html)
                    if result['success']:
                        sent += 1
                    else:
                        errors.append(f"{player['email']}: {result.get('error')}")

                self._send_success({
                    "message": f"Sent final reminder to {sent} players",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            elif action == 'send_midmonth_reminders':
                from api.supabase_http import table

                # Get current month's pending matches
                month = datetime.now().strftime('%B %Y')
                matches_result = table('match_assignments').select('*').eq('period_label', month).eq('status', 'pending').execute()

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
                players_map = {pl['id']: pl for pl in players_result.data if pl['id'] in player_ids}

                sent = 0
                errors = []

                for match in matches_result.data:
                    p1 = players_map.get(match.get('player1_id'), {})
                    p2 = players_map.get(match.get('player2_id'), {})

                    if p1 and p2:
                        html = get_midmonth_reminder_email_html(
                            p1.get('name', 'Player'),
                            p2.get('name', 'Player'),
                            month
                        )
                        # Reply-to first player so they can coordinate
                        reply_to = p1['email']
                        result = send_email(
                            [p1['email'], p2['email']],
                            f"Friendly reminder to play your {month} match",
                            html,
                            reply_to=reply_to
                        )
                        if result['success']:
                            sent += 1
                        else:
                            errors.append(f"Match {match.get('id')}: {result.get('error')}")

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
                    else:
                        errors.append(f"{p1['name']} & {p2['name']}: {result.get('error')}")

                self._send_success({
                    "message": f"Sent match emails to {sent} pairs",
                    "sent": sent,
                    "errors": errors if errors else None
                })

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            self._send_error(500, str(e))

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, **data}).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode())
