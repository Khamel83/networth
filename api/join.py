"""
Vercel Serverless Function: Join Request API
Handles new player requests to join the ladder.
Creates player in database, admin approves via dashboard.
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

            # Get Supabase client
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            # Prepare player data
            player_data = {
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
                'is_active': True,  # Active immediately - no approval needed
                'total_games': 0,
                'matches_played': 0,
                'rank': None
            }

            # Check if email already exists
            try:
                existing = supabase.table('players').select('id, is_active').eq('email', email).execute()

                if existing.data:
                    existing_player = existing.data[0]

                    if existing_player.get('is_active'):
                        # Active account exists - tell them to log in
                        self._send_error(400, "This email is already registered. Try logging in instead!")
                        return

                    # Inactive account exists - UPDATE it with new registration data
                    # This handles re-registration after rejection or abandoned signup
                    result = supabase.table('players').update(player_data).eq('id', existing_player['id']).execute()
                else:
                    # No existing account - INSERT new one
                    try:
                        result = supabase.table('players').insert(player_data).execute()
                    except Exception as insert_error:
                        error_msg = str(insert_error).lower()
                        # Handle race condition: another request may have inserted same email
                        if 'duplicate' in error_msg or 'unique' in error_msg or 'already exists' in error_msg:
                            self._send_error(400, "This email is already registered. Try logging in instead!")
                            return
                        raise  # Re-raise if it's a different error

                if result.data:
                    # Send welcome email
                    email_sent = False
                    email_error = None
                    try:
                        from api.email import send_email, get_welcome_email_html
                        welcome_html = get_welcome_email_html(name)
                        email_result = send_email(email, "Welcome to Net Worth Tennis!", welcome_html)
                        email_sent = email_result.get('success', False)
                        if not email_sent:
                            email_error = email_result.get('error', 'Unknown email error')
                    except Exception as e:
                        email_error = str(e)
                        print(f"Failed to send welcome email: {e}")

                    self._send_success({
                        "message": "You're in! You can now sign in to access your dashboard.",
                        "player_created": True,
                        "is_active": True,
                        "welcome_email_sent": email_sent,
                        "email_error": email_error
                    })
                else:
                    self._send_error(500, "Failed to create account. Please try again.")

            except Exception as e:
                self._send_error(500, f"Unable to create account: {str(e)}")

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
