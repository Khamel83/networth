"""
Vercel Serverless Function: Matches API
Handles match reporting and history with Supabase
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone


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


SAMPLE_MATCHES = [
    {"id": 1, "winner": {"name": "Kim Ndombe"}, "loser": {"name": "Natalie Coffen"}, "winner_score": "6-4, 6-3", "loser_score": "4-6, 3-6", "played_at": "2025-01-05T14:00:00Z", "court": "Vermont Canyon"},
    {"id": 2, "winner": {"name": "Sara Chrisman"}, "loser": {"name": "Arianna Hairston"}, "winner_score": "7-5, 6-4", "loser_score": "5-7, 4-6", "played_at": "2025-01-03T10:00:00Z", "court": "Griffith Park"},
    {"id": 3, "winner": {"name": "Kim Ndombe"}, "loser": {"name": "Hannah Shin"}, "winner_score": "6-2, 6-4", "loser_score": "2-6, 4-6", "played_at": "2025-01-01T16:00:00Z", "court": "Echo Park"},
    {"id": 4, "winner": {"name": "Natalie Coffen"}, "loser": {"name": "Alik Apelian"}, "winner_score": "6-3, 6-2", "loser_score": "3-6, 2-6", "played_at": "2024-12-28T11:00:00Z", "court": "Silver Lake"},
    {"id": 5, "winner": {"name": "Hannah Shin"}, "loser": {"name": "Hanna Pavlova"}, "winner_score": "6-4, 7-5", "loser_score": "4-6, 5-7", "played_at": "2024-12-22T15:00:00Z", "court": "Los Feliz"},
]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        try:
            supabase = get_supabase_client()
            if supabase:
                response = supabase.table('matches').select('*, winner:players!winner_id(*), loser:players!loser_id(*)').order('played_at', desc=True).limit(20).execute()
                matches = response.data
                source = "supabase"
            else:
                matches = SAMPLE_MATCHES
                source = "sample"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "matches": matches,
                "source": source
            }).encode())

        except Exception as e:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "matches": SAMPLE_MATCHES,
                "source": "sample_fallback",
                "error": str(e)
            }).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            supabase = get_supabase_client()
            if supabase:
                match_data = {
                    "winner_id": data['winner_id'],
                    "loser_id": data['loser_id'],
                    "winner_score": data['winner_score'],
                    "loser_score": data['loser_score'],
                    "court": data.get('court', 'Unknown'),
                    "played_at": data.get('played_at', datetime.now(timezone.utc).isoformat())
                }
                response = supabase.table('matches').insert(match_data).execute()

                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "match": response.data[0] if response.data else None
                }).encode())
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Match recorded (demo mode)",
                    "match": data
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
