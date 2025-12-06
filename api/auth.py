"""
Vercel Serverless Function: Authentication API
Handles login with demo fallback
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import secrets


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

            email = data.get('email', '')
            password = data.get('password', '')

            supabase = get_supabase_client()

            if supabase:
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    if response.user:
                        player = supabase.table('players').select('*').eq('email', email).single().execute()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": True,
                            "token": response.session.access_token,
                            "player": player.data if player.data else None
                        }).encode())
                        return
                except Exception:
                    pass

            # Demo fallback
            default_password = os.environ.get('PLAYER_PASSWORD', 'tennis123')
            if password == default_password:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "token": secrets.token_hex(32),
                    "player": {
                        "id": 1,
                        "name": email.split('@')[0].title() if email else "Demo Player",
                        "email": email,
                        "rank": 5,
                        "points": 38,
                        "wins": 5,
                        "losses": 3,
                        "is_admin": email == "admin@networthtennis.com"
                    }
                }).encode())
                return

            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "Invalid credentials"
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())
