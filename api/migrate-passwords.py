"""
One-time migration: Set initial passwords for all players
Password = 10-digit phone number OR tennis123
Uses hashlib for password hashing (no bcrypt dependency to keep bundle size small)
Uses Supabase REST API (no Python supabase client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hashlib
import base64


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256"""
    salt = os.urandom(32)  # Random salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        from api.supabase_http import table

        try:
            result = table('players').select('id, email, phone').execute()

            if not result.data:
                self._send_error(500, "No players found")
                return

            players = result.data
            results = {"updated": 0, "skipped": 0, "errors": []}

            for player in players:
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

                    hashed = hash_password(password)

                    table('players').update({
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
