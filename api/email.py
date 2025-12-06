"""
Vercel Serverless Function: Email Notifications
Uses Resend (free 3,000 emails/month) for sending:
- Monthly pairing notifications
- Match reminders
- Score confirmations
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


def get_supabase_client():
    """Lazy initialization of Supabase client"""
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_ANON_KEY')
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def send_email(to_email, subject, html_content, reply_to=None):
    """
    Send email via Resend API

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        reply_to: Optional reply-to address (used for pairing emails so replies go to opponent)
    """
    try:
        # KILL SWITCH - DO NOT SEND EMAILS UNLESS EXPLICITLY ENABLED
        email_enabled = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
        if not email_enabled:
            return {
                'success': True,
                'blocked': True,
                'message': 'Email sending is disabled (EMAIL_ENABLED=false)'
            }

        import requests
        api_key = os.environ.get('RESEND_API_KEY')

        if not api_key:
            return {'success': False, 'error': 'RESEND_API_KEY not configured'}

        email_payload = {
            'from': os.environ.get('EMAIL_FROM', 'NET WORTH Tennis <noreply@networthtennis.com>'),
            'to': [to_email],
            'subject': subject,
            'html': html_content
        }

        # Reply-To trick: if set, replies go directly to opponent instead of noreply
        if reply_to:
            email_payload['reply_to'] = reply_to

        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=email_payload
        )

        if response.status_code == 200:
            return {'success': True, 'id': response.json().get('id')}
        else:
            return {'success': False, 'error': response.text}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pairing_email_html(player_name, opponent_name, opponent_email, period_label,
                           player_availability="Any time", opponent_availability="Any time"):
    """
    Generate HTML for pairing notification email

    Args:
        player_name: Name of the recipient
        opponent_name: Name of their opponent
        opponent_email: Opponent's email (for contact info)
        period_label: e.g., "January 2025"
        player_availability: Recipient's time preferences
        opponent_availability: Opponent's time preferences
    """
    # Import config for branding
    try:
        from api.config import LEAGUE_NAME, LEAGUE_TAGLINE, COLORS, EMAIL_COPY, COURTS_DISPLAY, get_site_url
        site_url = get_site_url()
    except ImportError:
        # Fallback if config not available
        LEAGUE_NAME = "NET WORTH"
        LEAGUE_TAGLINE = "East Side LA Women's Tennis"
        COLORS = {
            'background': '#0a0a0a', 'card_bg': '#121212', 'border': '#2a2a2a',
            'text_primary': '#e8e8e8', 'text_secondary': '#888888',
            'gold': '#D4AF37', 'lime': '#CCFF00', 'red': '#DC143C'
        }
        EMAIL_COPY = {'pairing_instructions': 'Coordinate with your opponent to schedule your match this month. Play 2 sets and report your score when done.'}
        COURTS_DISPLAY = "Vermont Canyon • Griffith Park • Echo Park • Hermon Park • Eagle Rock • Cheviot Hills • Poinsettia Park"
        site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: {COLORS['background']}; color: {COLORS['text_primary']}; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: {COLORS['gold']}; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .card {{ background: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; padding: 30px; margin: 20px 0; }}
            .match-title {{ color: {COLORS['gold']}; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
            .opponent {{ font-size: 24px; color: {COLORS['lime']}; margin-bottom: 10px; }}
            .contact {{ color: {COLORS['text_secondary']}; font-size: 14px; }}
            .availability {{ background: {COLORS['background']}; padding: 15px; margin: 20px 0; border-left: 3px solid {COLORS['gold']}; }}
            .availability-title {{ color: {COLORS['gold']}; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
            .availability-row {{ color: {COLORS['text_secondary']}; font-size: 14px; margin: 5px 0; }}
            .availability-name {{ color: {COLORS['lime']}; }}
            .btn {{ display: inline-block; background: {COLORS['gold']}; color: {COLORS['background']}; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .courts {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid {COLORS['border']}; }}
            .courts-title {{ color: {COLORS['text_secondary']}; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
            .court-list {{ color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.8; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
            .reply-note {{ color: {COLORS['lime']}; font-size: 13px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">{LEAGUE_NAME}</div>
                <p style="color: {COLORS['text_secondary']}; margin-top: 5px;">{LEAGUE_TAGLINE}</p>
            </div>

            <div class="card">
                <div class="match-title">Your {period_label} Match</div>
                <div class="opponent">{opponent_name}</div>
                <div class="contact">Contact: {opponent_email}</div>

                <div class="availability">
                    <div class="availability-title">Availability</div>
                    <div class="availability-row"><span class="availability-name">{opponent_name}:</span> {opponent_availability}</div>
                    <div class="availability-row"><span class="availability-name">You:</span> {player_availability}</div>
                </div>

                <p style="margin-top: 20px; color: {COLORS['text_secondary']}; line-height: 1.6;">
                    {EMAIL_COPY.get('pairing_instructions', 'Coordinate with your opponent to schedule your match this month. Play 2 sets and report your score when done.')}
                </p>

                <p class="reply-note">
                    💡 Just hit reply to email {opponent_name} directly!
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>

                <div class="courts">
                    <div class="courts-title">Approved Courts</div>
                    <div class="court-list">
                        {COURTS_DISPLAY}
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>{LEAGUE_NAME} Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_reminder_email_html(player_name, opponent_name, period_label, days_left):
    """Generate HTML for reminder email"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #D4AF37; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .card {{ background: #121212; border: 1px solid #DC143C; padding: 30px; margin: 20px 0; }}
            .reminder {{ color: #DC143C; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
            .days {{ font-size: 48px; color: #DC143C; font-weight: bold; }}
            .btn {{ display: inline-block; background: #D4AF37; color: #0a0a0a; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NET WORTH</div>
            </div>

            <div class="card">
                <div class="reminder">Match Reminder</div>
                <div class="days">{days_left} days left</div>

                <p style="margin-top: 20px; color: #888; line-height: 1.6;">
                    Hey {player_name}! You haven't reported your {period_label} match with <strong style="color: #CCFF00;">{opponent_name}</strong> yet.
                </p>

                <p style="color: #888; line-height: 1.6;">
                    Please play and report your score before the month ends.
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>NET WORTH Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_welcome_email_html(player_name):
    """Generate HTML for welcome email when new player joins"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #D4AF37; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .welcome {{ color: #CCFF00; font-size: 32px; margin: 20px 0; }}
            .card {{ background: #121212; border: 1px solid #2a2a2a; padding: 30px; margin: 20px 0; }}
            .section-title {{ color: #D4AF37; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
            .btn {{ display: inline-block; background: #D4AF37; color: #0a0a0a; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NET WORTH</div>
                <p style="color: #888; margin-top: 5px;">East Side LA Women's Tennis</p>
            </div>

            <div class="welcome">Welcome, {player_name}!</div>

            <div class="card">
                <div class="section-title">How It Works</div>
                <p style="color: #888; line-height: 1.8;">
                    1. Each month you'll be paired with another player<br>
                    2. Coordinate with them to schedule your match<br>
                    3. Play 2 sets at any approved court<br>
                    4. Report your score on the dashboard<br>
                    5. Climb the ladder based on games won!
                </p>
            </div>

            <div class="card">
                <div class="section-title">Next Steps</div>
                <p style="color: #888; line-height: 1.6;">
                    Set your availability so we can match you with players who have similar schedules.
                </p>
                <a href="{site_url}/dashboard" class="btn">Set Availability →</a>
            </div>

            <div class="footer">
                <p>Questions? Reply to this email.</p>
                <p style="margin-top: 10px;">NET WORTH Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_score_confirmation_email_html(player_name, opponent_name, score_display, games_won, period_label):
    """Generate HTML for score confirmation email after match is reported"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #D4AF37; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .card {{ background: #121212; border: 1px solid #CCFF00; padding: 30px; margin: 20px 0; }}
            .confirmed {{ color: #CCFF00; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
            .score {{ font-size: 36px; color: #e8e8e8; font-weight: bold; margin: 15px 0; }}
            .games {{ color: #D4AF37; font-size: 18px; }}
            .opponent {{ color: #888; font-size: 14px; margin-top: 10px; }}
            .btn {{ display: inline-block; background: #D4AF37; color: #0a0a0a; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NET WORTH</div>
            </div>

            <div class="card">
                <div class="confirmed">Match Recorded</div>
                <div class="score">{score_display}</div>
                <div class="games">+{games_won} games added to your total</div>
                <div class="opponent">vs {opponent_name} • {period_label}</div>

                <a href="{site_url}" class="btn">View Ladder →</a>
            </div>

            <div class="footer">
                <p>Thanks for playing!</p>
                <p style="margin-top: 10px;">NET WORTH Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_outstanding_match_email_html(player_name, opponent_name, opponent_email, period_label):
    """Generate HTML for outstanding match reminder (from previous months that weren't completed)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #D4AF37; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .card {{ background: #121212; border: 1px solid #2a2a2a; padding: 30px; margin: 20px 0; }}
            .checkin {{ color: #D4AF37; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
            .message {{ color: #e8e8e8; font-size: 16px; line-height: 1.6; }}
            .opponent {{ color: #CCFF00; }}
            .period {{ color: #D4AF37; font-weight: bold; }}
            .options {{ background: #1a1a1a; padding: 20px; margin: 20px 0; }}
            .options-title {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 15px; }}
            .option {{ color: #888; font-size: 14px; margin: 10px 0; }}
            .btn {{ display: inline-block; background: #D4AF37; color: #0a0a0a; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; margin-right: 10px; }}
            .btn-secondary {{ background: transparent; border: 1px solid #888; color: #888; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
            .no-pressure {{ color: #888; font-style: italic; font-size: 14px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NET WORTH</div>
            </div>

            <div class="card">
                <div class="checkin">Quick check-in</div>
                <p class="message">
                    Hey {player_name}! Just wanted to check in about your <span class="period">{period_label}</span> match with <span class="opponent">{opponent_name}</span>.
                </p>

                <div class="options">
                    <div class="options-title">Did you get to play?</div>
                    <div class="option">✓ <strong>Yes!</strong> Report the score anytime - better late than never</div>
                    <div class="option">✗ <strong>Didn't work out?</strong> No worries at all - we'll pair you fresh next month</div>
                </div>

                <p class="no-pressure">
                    No pressure either way. Life happens! This is just a friendly check-in.
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>NET WORTH Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_last_chance_email_html(player_name, opponent_name, opponent_email, period_label):
    """Generate HTML for last chance reminder (2-3 days before month ends)"""
    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #D4AF37; font-size: 28px; font-weight: bold; letter-spacing: 3px; }}
            .card {{ background: #121212; border: 2px solid #DC143C; padding: 30px; margin: 20px 0; }}
            .urgent {{ color: #DC143C; font-size: 16px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; font-weight: bold; }}
            .message {{ color: #e8e8e8; font-size: 18px; line-height: 1.6; }}
            .opponent {{ color: #CCFF00; }}
            .contact {{ background: #1a1a1a; padding: 15px; margin: 20px 0; border-left: 3px solid #D4AF37; }}
            .btn {{ display: inline-block; background: #DC143C; color: #fff; padding: 12px 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NET WORTH</div>
            </div>

            <div class="card">
                <div class="urgent">Last Chance!</div>
                <p class="message">
                    Hey {player_name}, {period_label} ends in just a few days and you still haven't played your match with <span class="opponent">{opponent_name}</span>.
                </p>

                <div class="contact">
                    <strong style="color: #D4AF37;">Reach out now:</strong><br>
                    <span style="color: #888;">{opponent_email}</span>
                </div>

                <p style="color: #888; line-height: 1.6;">
                    If you can't make it work, no worries - just let us know and we'll pair you with someone else next month.
                </p>

                <a href="{site_url}/dashboard" class="btn">Report Score →</a>
            </div>

            <div class="footer">
                <p>NET WORTH Tennis © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Send emails based on action type"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action')

            if action == 'send_pairings':
                # Send pairing emails for current month
                result = self._send_pairing_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_reminders':
                # Send reminder emails for unpaid matches
                result = self._send_reminder_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_welcome':
                # Send welcome email to new player
                result = self._send_welcome_email(
                    data.get('player_email'),
                    data.get('player_name')
                )
                self._send_success(result)

            elif action == 'send_score_confirmation':
                # Send score confirmation to both players after match reported
                result = self._send_score_confirmations(
                    data.get('match_id'),
                    data.get('period_label')
                )
                self._send_success(result)

            elif action == 'send_last_chance':
                # Send last chance reminders (for end of month)
                result = self._send_last_chance_emails(data.get('period_label'))
                self._send_success(result)

            elif action == 'send_outstanding_reminders':
                # Send reminders for matches from previous months that weren't completed
                result = self._send_outstanding_match_emails()
                self._send_success(result)

            elif action == 'send_single':
                # Send a single email (for testing or custom notifications)
                result = send_email(
                    data.get('to'),
                    data.get('subject'),
                    data.get('html')
                )
                if result['success']:
                    self._send_success(result)
                else:
                    self._send_error(500, result['error'])

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            self._send_error(500, str(e))

    def _send_pairing_emails(self, period_label=None):
        """Send pairing notification to all players with assignments"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get all pending assignments for this period (with availability fields)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(id, name, email, available_morning, available_afternoon, available_evening), player2:players!player2_id(id, name, email, available_morning, available_afternoon, available_evening)')\
            .eq('period_label', period_label)\
            .eq('status', 'pending')\
            .execute()

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Build availability text for each player
            p1_avail = self._get_availability_text(p1)
            p2_avail = self._get_availability_text(p2)

            # Send to player 1 (with reply-to set to player 2)
            html1 = get_pairing_email_html(
                p1['name'], p2['name'], p2['email'], period_label,
                player_availability=p1_avail,
                opponent_availability=p2_avail
            )
            result1 = send_email(
                p1['email'],
                f'Your {period_label} Tennis Match',
                html1,
                reply_to=p2['email']  # Reply goes to opponent!
            )
            if result1['success']:
                sent_count += 1
            else:
                errors.append(f"{p1['email']}: {result1.get('error', 'Unknown error')}")

            # Send to player 2 (with reply-to set to player 1)
            html2 = get_pairing_email_html(
                p2['name'], p1['name'], p1['email'], period_label,
                player_availability=p2_avail,
                opponent_availability=p1_avail
            )
            result2 = send_email(
                p2['email'],
                f'Your {period_label} Tennis Match',
                html2,
                reply_to=p1['email']  # Reply goes to opponent!
            )
            if result2['success']:
                sent_count += 1
            else:
                errors.append(f"{p2['email']}: {result2.get('error', 'Unknown error')}")

        return {
            'sent': sent_count,
            'assignments': len(assignments.data),
            'errors': errors if errors else None
        }

    def _get_availability_text(self, player):
        """Build human-readable availability string"""
        morning = player.get('available_morning', True)
        afternoon = player.get('available_afternoon', True)
        evening = player.get('available_evening', True)

        if morning and afternoon and evening:
            return "Any time"
        if not morning and not afternoon and not evening:
            return "No times specified"

        times = []
        if morning:
            times.append("Mornings")
        if afternoon:
            times.append("Afternoons")
        if evening:
            times.append("Evenings")
        return ", ".join(times)

    def _send_reminder_emails(self, period_label=None):
        """Send reminders for matches not yet completed"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get pending assignments (not completed)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('period_label', period_label)\
            .in_('status', ['pending', 'accepted'])\
            .execute()

        # Calculate days left in month
        now = datetime.now()
        import calendar
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_left = days_in_month - now.day

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Send reminder to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_reminder_email_html(
                    player['name'],
                    opponent['name'],
                    period_label,
                    days_left
                )
                result = send_email(
                    player['email'],
                    f'⏰ {days_left} days left to play your match!',
                    html
                )
                if result['success']:
                    sent_count += 1
                else:
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'pending_matches': len(assignments.data),
            'days_left': days_left,
            'errors': errors if errors else None
        }

    def _send_welcome_email(self, player_email, player_name):
        """Send welcome email to new player"""
        if not player_email or not player_name:
            return {'sent': 0, 'error': 'Missing player_email or player_name'}

        html = get_welcome_email_html(player_name)
        result = send_email(player_email, 'Welcome to NET WORTH Tennis!', html)

        return {
            'sent': 1 if result.get('success') else 0,
            'blocked': result.get('blocked', False),
            'error': result.get('error')
        }

    def _send_score_confirmations(self, match_id, period_label=None):
        """Send score confirmation emails to both players after match reported"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        if not match_id:
            return {'sent': 0, 'error': 'Missing match_id'}

        # Get match details
        match = supabase.table('matches')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('id', match_id)\
            .single()\
            .execute()

        if not match.data:
            return {'sent': 0, 'error': 'Match not found'}

        m = match.data
        p1 = m['player1']
        p2 = m['player2']

        # Format scores
        score_for_p1 = f"{m['set1_p1']}-{m['set1_p2']}, {m['set2_p1']}-{m['set2_p2']}"
        score_for_p2 = f"{m['set1_p2']}-{m['set1_p1']}, {m['set2_p2']}-{m['set2_p1']}"

        # Calculate games won
        p1_games = m['set1_p1'] + m['set2_p1']
        p2_games = m['set1_p2'] + m['set2_p2']

        sent_count = 0
        errors = []

        # Send to player 1
        html1 = get_score_confirmation_email_html(p1['name'], p2['name'], score_for_p1, p1_games, period_label)
        result1 = send_email(p1['email'], 'Match Recorded!', html1)
        if result1.get('success'):
            sent_count += 1
        elif result1.get('error'):
            errors.append(f"{p1['email']}: {result1['error']}")

        # Send to player 2
        html2 = get_score_confirmation_email_html(p2['name'], p1['name'], score_for_p2, p2_games, period_label)
        result2 = send_email(p2['email'], 'Match Recorded!', html2)
        if result2.get('success'):
            sent_count += 1
        elif result2.get('error'):
            errors.append(f"{p2['email']}: {result2['error']}")

        return {
            'sent': sent_count,
            'match_id': match_id,
            'errors': errors if errors else None
        }

    def _send_outstanding_match_emails(self):
        """Send reminders for matches from previous months that weren't completed.

        This finds all assignments from past periods (not current month) that are
        still pending/accepted and haven't been completed yet.
        """
        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        current_period = datetime.now().strftime('%B %Y')

        # Get all pending/accepted assignments from PREVIOUS periods (not current month)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .in_('status', ['pending', 'accepted'])\
            .neq('period_label', current_period)\
            .execute()

        sent_count = 0
        errors = []
        periods_reminded = set()

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']
            period_label = assignment['period_label']
            periods_reminded.add(period_label)

            # Send to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_outstanding_match_email_html(
                    player['name'],
                    opponent['name'],
                    opponent['email'],
                    period_label
                )
                result = send_email(
                    player['email'],
                    f"Did you finish your {period_label} match?",
                    html
                )
                if result.get('success'):
                    sent_count += 1
                elif result.get('error'):
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'outstanding_matches': len(assignments.data),
            'periods': list(periods_reminded),
            'errors': errors if errors else None
        }

    def _send_last_chance_emails(self, period_label=None):
        """Send last chance reminders for matches not yet completed (end of month)"""
        if not period_label:
            period_label = datetime.now().strftime('%B %Y')

        supabase = get_supabase_client()
        if not supabase:
            return {'sent': 0, 'error': 'Database not configured'}

        # Get pending assignments (not completed)
        assignments = supabase.table('match_assignments')\
            .select('*, player1:players!player1_id(*), player2:players!player2_id(*)')\
            .eq('period_label', period_label)\
            .in_('status', ['pending', 'accepted'])\
            .execute()

        sent_count = 0
        errors = []

        for assignment in assignments.data:
            p1 = assignment['player1']
            p2 = assignment['player2']

            # Send to both players
            for player, opponent in [(p1, p2), (p2, p1)]:
                html = get_last_chance_email_html(
                    player['name'],
                    opponent['name'],
                    opponent['email'],
                    period_label
                )
                result = send_email(
                    player['email'],
                    'Last chance to play your match!',
                    html
                )
                if result.get('success'):
                    sent_count += 1
                elif result.get('error'):
                    errors.append(f"{player['email']}: {result['error']}")

        return {
            'sent': sent_count,
            'pending_matches': len(assignments.data),
            'errors': errors if errors else None
        }

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
