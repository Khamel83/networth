"""
Vercel Serverless Function: Report Issue
Handles user-submitted bug reports and feature requests.
Sends email to admins via Resend API.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Handle issue report submission"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            reporter_email = data.get('reporter_email', 'Anonymous')
            reporter_name = data.get('reporter_name', '')
            page_path = data.get('page_path', 'Unknown')
            message = data.get('message', '')

            if not message:
                self._send_error(400, "Missing 'message' field")
                return

            # Import email sender
            import resend

            api_key = os.environ.get('RESEND_API_KEY')
            if not api_key:
                self._send_error(500, "Email service not configured")
                return

            resend.api_key = api_key

            # Get admin emails
            from api.supabase_http import table
            admins = table('players').select('email').eq('is_admin', True).execute()

            if not admins.data:
                self._send_error(500, "No admins configured")
                return

            admin_emails = [a['email'] for a in admins.data]

            # Build email
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .header h1 {{ color: #d165a4; margin: 0; }}
                    .content {{ background: #f9f9f9; border-radius: 10px; padding: 30px; }}
                    .field {{ margin-bottom: 20px; }}
                    .field-label {{ font-weight: 600; color: #d165a4; }}
                    .field-value {{ margin-top: 5px; }}
                    .message {{ background: white; padding: 15px; border-radius: 5px; border-left: 3px solid #d165a4; }}
                    .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎾 Issue Report</h1>
                    </div>
                    <div class="content">
                        <div class="field">
                            <div class="field-label">From:</div>
                            <div class="field-value">{reporter_name} ({reporter_email})</div>
                        </div>
                        <div class="field">
                            <div class="field-label">Page:</div>
                            <div class="field-value">{page_path}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">Time:</div>
                            <div class="field-value">{timestamp}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">Message:</div>
                            <div class="message">{message}</div>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Net Worth Tennis - User Report</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send email to admins
            params = {
                "from": "Net Worth Tennis <hello@networthtennis.com>",
                "to": admin_emails,
                "subject": f"🎾 Issue Report from {reporter_name or 'User'}",
                "html": html,
                "reply_to": reporter_email if reporter_email != 'Anonymous' else 'ashleybrooke.kaufman@gmail.com'
            }

            response = resend.Emails.send(params)

            self._send_success({
                "message": "Issue report sent to admins",
                "id": response.get('id')
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
