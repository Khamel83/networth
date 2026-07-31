"""
Vercel Serverless Function: Join Request API
Handles new player requests to join the ladder.
Creates player in database with password authentication.
Uses hashlib for password hashing, HTTP calls for Supabase (no heavy dependencies)
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hashlib
import base64

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
init_sentry()


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()


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
            password = data.get('password', '')
            membership_tier = data.get('membership_tier', 'player').strip()
            favorite_players = data.get('favorite_players', '').strip()

            if not password or len(password) < 6:
                self._send_error(400, "Password must be at least 6 characters")
                return

            password_hash = hash_password(password)

            avail_weekday_early = data.get('avail_weekday_early', False)
            avail_weekday_day = data.get('avail_weekday_day', False)
            avail_weekday_late = data.get('avail_weekday_late', False)
            avail_weekend_early = data.get('avail_weekend_early', False)
            avail_weekend_day = data.get('avail_weekend_day', False)
            avail_weekend_late = data.get('avail_weekend_late', False)

            if not name or not email:
                self._send_error(400, "Name and email are required")
                return

            if '@' not in email:
                self._send_error(400, "Please enter a valid email address")
                return

            # Reject test/disposable email patterns
            _test_tlds = ('.invalid', '.test', '.example', '.localhost', '.onion')
            _test_words = ('test', 'probe', 'example', 'fake', 'dummy', 'nobody', 'null', 'devnull')
            _email_domain = email.split('@')[-1].lower()
            if any(_email_domain.endswith(t) for t in _test_tlds):
                self._send_error(400, "Please use a real email address")
                return
            if any(w in email.lower() for w in _test_words) and not any(c.isdigit() for c in email):
                self._send_error(400, "Please use a real email address")
                return

            # Import HTTP helper
            from api.supabase_http import table

            player_data = {
                'name': name,
                'email': email,
                'phone': phone if phone else None,
                'password_hash': password_hash,
                'password_changed': True,
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
                'rank': None
            }

            try:
                existing = table('players').select('id, is_active').eq('email', email).execute()

                if existing.data and len(existing.data) > 0:
                    existing_player = existing.data[0]

                    if existing_player.get('is_active'):
                        self._send_error(400, "This email is already registered. Try logging in instead!")
                        return

                    result = table('players').update(player_data).eq('id', existing_player['id']).execute()
                else:
                    try:
                        result = table('players').insert(player_data).execute()
                    except Exception as insert_error:
                        error_msg = str(insert_error).lower()
                        if 'duplicate' in error_msg or 'unique' in error_msg or 'already exists' in error_msg:
                            self._send_error(400, "This email is already registered. Try logging in instead!")
                            return
                        raise

                if result.data and len(result.data) > 0:
                    email_sent = False
                    email_error = None
                    email_delivery_mode = None
                    try:
                        from api.email import send_email, get_welcome_email_html
                        welcome_html = get_welcome_email_html(name, membership_tier)
                        email_result = send_email(email, "Welcome to Net Worth Tennis!", welcome_html)
                        email_sent = bool(email_result.get('sent', False))
                        email_delivery_mode = email_result.get('delivery_mode')
                        if not email_sent and not email_result.get('blocked'):
                            email_error = email_result.get('error', 'Unknown email error')
                    except Exception as e:
                        email_error = str(e)
                        print(f"Failed to send welcome email: {e}")

                    self._send_success({
                        "message": "You're in! You can now sign in to access your dashboard.",
                        "player_created": True,
                        "is_active": True,
                        "welcome_email_sent": email_sent,
                        "email_delivery_mode": email_delivery_mode,
                        "email_error": email_error
                    })
                else:
                    self._send_error(500, "Failed to create account. Please try again.")

            except Exception as e:
                print(f"Join account creation error: {e}")
                self._send_error(500, "Unable to create account. Please try again.")

        except Exception as e:
            print(f"Join error: {e}")
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
