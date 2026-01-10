"""
Vercel Serverless Function: Authentication API
Uses Supabase Magic Links (passwordless email login)
Free tier: 50,000 emails/month
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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'magic_link')
            email = data.get('email', '').lower().strip() if data.get('email') else ''

            supabase = get_supabase_client()

            # Email required only for magic_link action
            if action == 'magic_link' and not email:
                self._send_error(400, "Email is required")
                return

            if action == 'magic_link':
                # Send magic link email
                if supabase:
                    try:
                        # Check if player exists in our database
                        player = supabase.table('players').select('id, name, email').eq('email', email).single().execute()

                        if not player.data:
                            self._send_error(404, "Email not found. Contact the league organizer to join.")
                            return

                        # Send magic link
                        site_url = os.environ.get('SITE_URL', 'https://networthtennis.com')
                        response = supabase.auth.sign_in_with_otp({
                            "email": email,
                            "options": {
                                "email_redirect_to": f"{site_url}/dashboard"
                            }
                        })

                        self._send_success({
                            "message": f"Magic link sent to {email}! Check your inbox.",
                            "player_name": player.data.get('name', '')
                        })
                        return

                    except Exception as e:
                        # Return real error instead of silent demo mode
                        print(f"Magic link error: {e}")
                        self._send_error(500, f"Failed to send login email. Please try again.")
                        return
                else:
                    # No Supabase connection - return error
                    self._send_error(503, "Email service unavailable. Please try again later.")
                    return

            elif action == 'verify':
                # Verify session token (called after clicking magic link)
                token = data.get('token')
                if supabase and token:
                    try:
                        # Get user from session
                        user = supabase.auth.get_user(token)
                        if user and user.user:
                            # Lowercase email to match how join.py stores it
                            email = user.user.email.lower()
                            # Get player data
                            player = supabase.table('players').select('*').eq('email', email).single().execute()

                            if player.data:
                                self._send_success({
                                    "authenticated": True,
                                    "player": player.data
                                })
                                return
                            else:
                                # Supabase Auth succeeded but no player record exists
                                # This means they authenticated but haven't registered via /join
                                self._send_error(404, "No account found. Please register first at /join")
                                return
                    except Exception as e:
                        print(f"Verify error: {e}")
                        pass

                self._send_error(401, "Invalid or expired session")
                return

            elif action == 'refresh':
                # Refresh access token using refresh token
                refresh_token = data.get('refresh_token')
                if supabase and refresh_token:
                    try:
                        # Use refresh token to get new access token
                        response = supabase.auth.refresh_session(refresh_token)
                        if response and response.session:
                            self._send_success({
                                "access_token": response.session.access_token,
                                "refresh_token": response.session.refresh_token,
                                "expires_in": response.session.expires_in
                            })
                            return
                    except Exception as e:
                        print(f"Token refresh failed: {e}")
                        pass

                self._send_error(401, "Token refresh failed")
                return

            elif action == 'logout':
                if supabase:
                    try:
                        supabase.auth.sign_out()
                    except Exception:
                        pass
                self._send_success({"message": "Logged out"})
                return

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
