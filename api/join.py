"""
Vercel Serverless Function: Join Request API
Handles new player requests to join the ladder.
Sends notification email to league administrators.
"""
from http.server import BaseHTTPRequestHandler
import json
import os


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


def send_admin_notification(name, email, phone, membership_tier):
    """Send email to admin about new player joining"""
    try:
        import requests
        api_key = os.environ.get('RESEND_API_KEY')
        admin_email = os.environ.get('ADMIN_EMAIL', 'support@networthtennis.com')

        if not api_key:
            return {'success': False, 'error': 'RESEND_API_KEY not configured'}

        # Check kill switch
        email_enabled = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
        if not email_enabled:
            return {'success': True, 'blocked': True, 'message': 'Email disabled'}

        # Build phone HTML if provided
        phone_html = f"""
                    <div class="label">Phone</div>
                    <div class="value">{phone}</div>
        """ if phone else ""

        tier_display = 'Player ($35)' if membership_tier == 'player' else 'Social Butterfly ($45)'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e8e8e8; padding: 40px; }}
                .container {{ max-width: 500px; margin: 0 auto; }}
                .header {{ color: #D4AF37; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
                .card {{ background: #121212; border: 1px solid #D4AF37; padding: 25px; }}
                .label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }}
                .value {{ color: #CCFF00; font-size: 18px; margin-bottom: 20px; }}
                .note {{ color: #888; font-size: 13px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">New Player Joined!</div>
                <div class="card">
                    <div class="label">Name</div>
                    <div class="value">{name}</div>

                    <div class="label">Email</div>
                    <div class="value">{email}</div>
                    {phone_html}
                    <div class="label">Membership</div>
                    <div class="value">{tier_display}</div>

                    <div class="note">
                        They've been automatically added to the players table.
                        Verify their Venmo payment before the next match assignment.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'from': os.environ.get('EMAIL_FROM', 'NET WORTH Tennis <noreply@networthtennis.com>'),
                'to': [admin_email],
                'subject': f'New Player Request: {name}',
                'html': html
            }
        )

        if response.status_code == 200:
            return {'success': True}
        else:
            return {'success': False, 'error': response.text}

    except Exception as e:
        return {'success': False, 'error': str(e)}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            name = data.get('name', '').strip()
            email = data.get('email', '').strip().lower()
            phone = data.get('phone', '').strip()
            membership_tier = data.get('membership_tier', 'player').strip()
            favorite_players = data.get('favorite_players', '').strip()

            # Availability fields
            avail_weekday_early = data.get('avail_weekday_early', False)
            avail_weekday_day = data.get('avail_weekday_day', False)
            avail_weekday_late = data.get('avail_weekday_late', False)
            avail_weekend_early = data.get('avail_weekend_early', False)
            avail_weekend_day = data.get('avail_weekend_day', False)
            avail_weekend_late = data.get('avail_weekend_late', False)

            # Validate - only name and email are required
            if not name or not email:
                self._send_error(400, "Name and email are required")
                return

            if '@' not in email:
                self._send_error(400, "Please enter a valid email address")
                return

            # Check if already exists
            supabase = get_supabase_client()
            if supabase:
                try:
                    existing = supabase.table('players').select('id').eq('email', email).execute()
                    if existing.data:
                        self._send_error(400, "This email is already registered. Try logging in instead!")
                        return
                except Exception:
                    pass  # Continue anyway

            # Insert the new player into Supabase
            player_inserted = False
            if supabase:
                try:
                    import uuid
                    player_data = {
                        'id': str(uuid.uuid4()),
                        'name': name,
                        'email': email,
                        'phone': phone if phone else None,
                        'membership_tier': membership_tier,
                        'favorite_players': favorite_players if favorite_players else None,
                        'avail_weekday_early': avail_weekday_early,
                        'avail_weekday_day': avail_weekday_day,
                        'avail_weekday_late': avail_weekday_late,
                        'avail_weekend_early': avail_weekend_early,
                        'avail_weekend_day': avail_weekend_day,
                        'avail_weekend_late': avail_weekend_late,
                        'is_active': True,
                        'total_games': 0,
                        'matches_played': 0,
                        'rank': None,
                        'rating': 1500  # Default ELO rating
                    }
                    supabase.table('players').insert(player_data).execute()
                    player_inserted = True
                except Exception as e:
                    print(f"Failed to insert player: {e}")

            # Send notification to admin
            result = send_admin_notification(name, email, phone, membership_tier)

            # Send welcome email to new player
            welcome_sent = False
            if player_inserted:
                try:
                    from api.email import get_welcome_email_html, send_email as send_email_fn
                    welcome_html = get_welcome_email_html(name, membership_tier)
                    welcome_result = send_email_fn(email, 'Welcome to Net Worth Tennis!', welcome_html)
                    welcome_sent = welcome_result.get('success', False)
                except Exception as e:
                    print(f"Failed to send welcome email: {e}")

            if player_inserted:
                self._send_success({
                    "message": "Welcome to Net Worth! Check your email for next steps.",
                    "player_created": True,
                    "welcome_email_sent": welcome_sent
                })
            elif result.get('success'):
                self._send_success({
                    "message": "Join request sent! We'll be in touch soon.",
                    "email_sent": not result.get('blocked', False)
                })
            else:
                self._send_success({
                    "message": "Join request received! We'll be in touch soon.",
                    "email_sent": False
                })

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
