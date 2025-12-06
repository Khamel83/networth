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


def send_admin_notification(name, email, skill_level):
    """Send email to admin about new join request"""
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
                <div class="header">New Player Request</div>
                <div class="card">
                    <div class="label">Name</div>
                    <div class="value">{name}</div>

                    <div class="label">Email</div>
                    <div class="value">{email}</div>

                    <div class="label">Skill Level</div>
                    <div class="value">{skill_level}</div>

                    <div class="note">
                        Add them to the players table in Supabase to approve.
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
            skill_level = data.get('skill_level', '').strip()

            # Validate
            if not name or not email or not skill_level:
                self._send_error(400, "Name, email, and skill level are required")
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

            # Store the request (optional - could add a join_requests table)
            # For now, just email the admin

            # Send notification to admin
            result = send_admin_notification(name, email, skill_level)

            if result.get('success'):
                self._send_success({
                    "message": "Join request sent! We'll be in touch soon.",
                    "email_sent": not result.get('blocked', False)
                })
            else:
                # Still show success to user even if email fails
                # (they don't need to know about our email issues)
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
