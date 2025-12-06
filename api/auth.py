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
            email = data.get('email', '').lower().strip()

            if not email:
                self._send_error(400, "Email is required")
                return

            supabase = get_supabase_client()

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
                        # If Supabase auth fails, fall back to demo mode
                        self._send_success({
                            "message": f"Demo mode: Magic link would be sent to {email}",
                            "demo": True
                        })
                        return
                else:
                    # Demo mode - no Supabase
                    self._send_success({
                        "message": f"Demo mode: Magic link would be sent to {email}",
                        "demo": True
                    })
                    return

            elif action == 'verify':
                # Verify session token (called after clicking magic link)
                token = data.get('token')
                if supabase and token:
                    try:
                        # Get user from session
                        user = supabase.auth.get_user(token)
                        if user and user.user:
                            email = user.user.email
                            # Get player data
                            player = supabase.table('players').select('*').eq('email', email).single().execute()
                            self._send_success({
                                "authenticated": True,
                                "player": player.data if player.data else None
                            })
                            return
                    except Exception:
                        pass

                self._send_error(401, "Invalid or expired session")
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
