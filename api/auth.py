"""
Vercel Serverless Function: Authentication API
Password-based authentication (magic links removed)
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
import bcrypt
from datetime import datetime, timedelta


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


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', '')
            email = data.get('email', '').lower().strip() if data.get('email') else ''

            supabase = get_supabase_client()

            if action == 'login':
                # Password login
                password = data.get('password', '')

                if not email or not password:
                    self._send_error(400, "Email and password required")
                    return

                if not supabase:
                    self._send_error(503, "Database unavailable")
                    return

                player = supabase.table('players').select('*').eq('email', email).single().execute()

                if not player.data:
                    self._send_error(401, "Invalid email or password")
                    return

                stored_hash = player.data.get('password_hash')
                if not stored_hash:
                    self._send_error(401, "No password set. Please reset your password.")
                    return

                if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    # Generate session token
                    session_token = secrets.token_urlsafe(32)

                    self._send_success({
                        "authenticated": True,
                        "player": player.data,
                        "token": session_token,
                        "password_changed": player.data.get('password_changed', False)
                    })
                    return
                else:
                    self._send_error(401, "Invalid email or password")
                    return

            elif action == 'change_password':
                # Change password (requires old password)
                old_password = data.get('old_password', '')
                new_password = data.get('new_password', '')

                if not email or not old_password or not new_password:
                    self._send_error(400, "All fields required")
                    return

                if not supabase:
                    self._send_error(503, "Database unavailable")
                    return

                player = supabase.table('players').select('*').eq('email', email).single().execute()
                if not player.data:
                    self._send_error(404, "Player not found")
                    return

                stored_hash = player.data.get('password_hash')
                if not stored_hash or not bcrypt.checkpw(old_password.encode(), stored_hash.encode()):
                    self._send_error(401, "Current password is incorrect")
                    return

                new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

                supabase.table('players').update({
                    'password_hash': new_hash,
                    'password_changed': True
                }).eq('email', email).execute()

                self._send_success({"message": "Password updated"})
                return

            elif action == 'request_password_reset':
                # Send password reset email via Resend
                if not email:
                    self._send_error(400, "Email required")
                    return

                if not supabase:
                    self._send_error(503, "Database unavailable")
                    return

                player = supabase.table('players').select('*').eq('email', email).single().execute()

                if not player.data:
                    # Don't reveal if email exists or not
                    self._send_success({"message": "If an account exists, a reset link will be sent."})
                    return

                # Generate reset token (valid for 1 hour)
                reset_token = secrets.token_urlsafe(32)
                expires = datetime.utcnow() + timedelta(hours=1)

                supabase.table('players').update({
                    'password_reset_token': reset_token,
                    'password_reset_expires': expires.isoformat()
                }).eq('email', email).execute()

                # Send reset email via Resend
                try:
                    from resend import Resend
                    resend = Resend(os.environ.get('RESEND_API_KEY'))

                    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')
                    reset_link = f"{site_url}/reset-password?token={reset_token}"

                    resend.emails.send({
                        "from": "Net Worth Tennis <noreply@networthtennis.com>",
                        "to": email,
                        "subject": "Reset Your Net Worth Tennis Password",
                        "html": f"""
                            <h2>Reset Your Password</h2>
                            <p>Click the link below to reset your password:</p>
                            <p><a href="{reset_link}">Reset Password</a></p>
                            <p>Or copy this link:</p>
                            <p>{reset_link}</p>
                            <p>This link will expire in 1 hour.</p>
                            <p>If you didn't request this, you can ignore this email.</p>
                        """
                    })

                    self._send_success({"message": "Password reset email sent"})
                    return
                except Exception as e:
                    print(f"Reset email error: {e}")
                    self._send_error(500, "Failed to send reset email")
                    return

            elif action == 'reset_password':
                # Complete password reset with token
                reset_token = data.get('token')
                new_password = data.get('new_password', '')

                if not reset_token or not new_password:
                    self._send_error(400, "Token and password required")
                    return

                if not supabase:
                    self._send_error(503, "Database unavailable")
                    return

                # Find player with valid reset token
                player = supabase.table('players').select('*').eq('password_reset_token', reset_token).single().execute()

                if not player.data:
                    self._send_error(400, "Invalid or expired reset link")
                    return

                # Check if token is expired
                expires = player.data.get('password_reset_expires')
                if expires:
                    expire_time = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                    if datetime.utcnow() > expire_time:
                        self._send_error(400, "Reset link has expired")
                        return

                # Set new password and clear reset token
                new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

                supabase.table('players').update({
                    'password_hash': new_hash,
                    'password_changed': True,
                    'password_reset_token': None,
                    'password_reset_expires': None
                }).eq('id', player.data['id']).execute()

                self._send_success({"message": "Password reset successful"})
                return

            elif action == 'logout':
                self._send_success({"message": "Logged out"})
                return

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            print(f"Auth error: {e}")
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
