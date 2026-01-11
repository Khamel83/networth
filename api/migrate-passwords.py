"""
One-time migration: Set initial passwords for all players
Password = 10-digit phone number OR tennis123
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import bcrypt


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

    def do_GET(self):
        supabase = get_supabase_client()
        if not supabase:
            self._send_error(500, "Supabase not available")
            return

        try:
            players = supabase.table('players').select('id, email, phone').execute()

            results = {"updated": 0, "skipped": 0, "errors": []}

            for player in players.data:
                try:
                    if player.get('password_hash'):
                        results["skipped"] += 1
                        continue

                    phone = player.get('phone', '')

                    if phone:
                        # Strip to 10 digits only
                        digits = ''.join(c for c in phone if c.isdigit())
                        if len(digits) > 10:
                            digits = digits[-10:]
                        password = digits
                    else:
                        password = 'tennis123'

                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                    supabase.table('players').update({
                        'password_hash': hashed,
                        'password_changed': False
                    }).eq('id', player['id']).execute()

                    results["updated"] += 1

                except Exception as e:
                    results["errors"].append(f"{player.get('email', 'unknown')}: {str(e)}")

            self._send_success(results)

        except Exception as e:
            self._send_error(500, f"Migration failed: {str(e)}")

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
