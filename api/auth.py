"""
Vercel Serverless Function: Authentication API
Handles login, logout, and session management with Supabase Auth
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hashlib
import secrets
from urllib.parse import parse_qs

try:
    from supabase import create_client, Client
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None


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

            action = data.get('action', 'login')
            email = data.get('email', '')
            password = data.get('password', '')

            if action == 'login':
                if supabase:
                    # Use Supabase Auth
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })

                    if response.user:
                        # Get player info
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
                else:
                    # Fallback - simple password check for demo
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
                                "name": "Demo Player",
                                "email": email,
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
