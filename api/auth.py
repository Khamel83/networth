"""
Vercel Serverless Function: Authentication API
Password-based authentication (magic links removed)
Uses hashlib for password hashing, HTTP calls for Supabase (no heavy dependencies)
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta, timezone

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
init_sentry()


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        decoded = base64.b64decode(stored_hash)
        salt = decoded[:32]
        stored_key = decoded[32:]
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return new_key == stored_key
    except Exception:
        return False


def verify_session(token: str):
    """
    Validate a session token. Returns player email if valid and not expired, else None.
    Used by all endpoints that require authentication.
    """
    if not token or not token.strip():
        return None
    try:
        from api.supabase_http import table
        result = (
            table('session_tokens')
            .select('player_email,expires_at')
            .eq('token', token.strip())
            .execute()
        )
        if result.error or not result.data:
            return None
        row = result.data[0] if isinstance(result.data, list) else result.data
        expires = row.get('expires_at', '')
        if expires:
            try:
                exp_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > exp_dt:
                    return None
            except Exception:
                pass
        return row.get('player_email')
    except Exception as e:
        print(f"verify_session error: {e}")
        return None


def _safe_player(player: dict) -> dict:
    """Strip sensitive fields before returning player data to client."""
    sensitive = ('password_hash', 'password_reset_token', 'password_reset_expires')
    return {k: v for k, v in player.items() if k not in sensitive}


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

            # Import HTTP helper
            from api.supabase_http import table

            if action == 'login':
                password = data.get('password', '')

                if not email or not password:
                    self._send_error(400, "Email and password required")
                    return

                try:
                    result = table('players').select('*').eq('email', email).single().execute()
                except Exception:
                    self._send_error(401, "Invalid email or password")
                    return

                if not result.data or len(result.data) == 0:
                    self._send_error(401, "Invalid email or password")
                    return

                player = result.data[0] if isinstance(result.data, list) else result.data

                stored_hash = player.get('password_hash')
                if not stored_hash:
                    self._send_error(401, "No password set. Please reset your password.")
                    return

                if verify_password(password, stored_hash):
                    session_token = secrets.token_urlsafe(32)

                    # Store token server-side
                    table('session_tokens').insert({
                        'token': session_token,
                        'player_id': player['id'],
                        'player_email': email,
                    }).execute()

                    self._send_success({
                        "authenticated": True,
                        "player": _safe_player(player),
                        "token": session_token,
                        "password_changed": player.get('password_changed', False)
                    })
                    return
                else:
                    self._send_error(401, "Invalid email or password")
                    return

            elif action == 'change_password':
                old_password = data.get('old_password', '')
                new_password = data.get('new_password', '')

                if not email or not old_password or not new_password:
                    self._send_error(400, "All fields required")
                    return

                try:
                    result = table('players').select('*').eq('email', email).single().execute()
                except Exception:
                    self._send_error(404, "Player not found")
                    return

                if not result.data or len(result.data) == 0:
                    self._send_error(404, "Player not found")
                    return

                player = result.data[0] if isinstance(result.data, list) else result.data

                stored_hash = player.get('password_hash')
                if not stored_hash or not verify_password(old_password, stored_hash):
                    self._send_error(401, "Current password is incorrect")
                    return

                new_hash = hash_password(new_password)

                update_result = table('players').update({
                    'password_hash': new_hash,
                    'password_changed': True
                }).eq('email', email).execute()
                if update_result.error:
                    self._send_error(500, "Failed to update password")
                    return

                self._send_success({"message": "Password updated"})
                return

            elif action == 'request_password_reset':
                if not email:
                    self._send_error(400, "Email required")
                    return

                try:
                    result = table('players').select('*').eq('email', email).single().execute()
                except Exception:
                    self._send_success({"message": "If an account exists, a reset link will be sent."})
                    return

                if not result.data or len(result.data) == 0:
                    self._send_success({"message": "If an account exists, a reset link will be sent."})
                    return

                player = result.data[0] if isinstance(result.data, list) else result.data

                reset_token = secrets.token_urlsafe(32)
                expires = datetime.now(timezone.utc) + timedelta(hours=1)

                reset_token_result = table('players').update({
                    'password_reset_token': reset_token,
                    'password_reset_expires': expires.isoformat()
                }).eq('email', email).execute()
                if reset_token_result.error:
                    self._send_error(500, "Failed to initiate password reset")
                    return

                try:
                    from api.email import send_email

                    site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')
                    reset_link = f"{site_url}/reset-password?token={reset_token}"

                    html = f"""
                        <h2>Reset Your Password</h2>
                        <p>Click the link below to reset your password:</p>
                        <p><a href="{reset_link}">Reset Password</a></p>
                        <p>Or copy this link:</p>
                        <p>{reset_link}</p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request this, you can ignore this email.</p>
                    """

                    result = send_email(email, "Reset Your Net Worth Tennis Password", html)

                    if result.get('sent'):
                        self._send_success({"message": "Password reset email sent"})
                    elif result.get('blocked'):
                        self._send_success({
                            "message": "If an account exists, a reset link will be sent.",
                            "email_delivery_mode": result.get('delivery_mode'),
                        })
                    else:
                        self._send_error(500, "Failed to send reset email")
                    return
                except Exception as e:
                    print(f"Reset email error: {e}")
                    self._send_error(500, "Failed to send reset email")
                    return

            elif action == 'reset_password':
                reset_token = data.get('token')
                new_password = data.get('new_password', '')

                if not reset_token or not new_password:
                    self._send_error(400, "Token and password required")
                    return

                try:
                    result = table('players').select('*').eq('password_reset_token', reset_token).single().execute()
                except Exception:
                    self._send_error(400, "Invalid or expired reset link")
                    return

                if not result.data or len(result.data) == 0:
                    self._send_error(400, "Invalid or expired reset link")
                    return

                player = result.data[0] if isinstance(result.data, list) else result.data

                expires = player.get('password_reset_expires')
                if expires:
                    expire_time = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expire_time:
                        self._send_error(400, "Reset link has expired")
                        return

                new_hash = hash_password(new_password)

                reset_update_result = table('players').update({
                    'password_hash': new_hash,
                    'password_changed': True,
                    'password_reset_token': None,
                    'password_reset_expires': None
                }).eq('id', player['id']).execute()
                if reset_update_result.error:
                    self._send_error(500, "Failed to save new password")
                    return

                self._send_success({"message": "Password reset successful"})
                return

            elif action == 'logout':
                # Invalidate session token if provided
                token = self.headers.get('Authorization', '').replace('Bearer ', '').strip()
                if token:
                    try:
                        table('session_tokens').delete().eq('token', token).execute()
                    except Exception:
                        pass
                self._send_success({"message": "Logged out"})
                return

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            print(f"Auth error: {e}")
            self._send_error(500, "An unexpected error occurred")

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
