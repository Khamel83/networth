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


# Sample matches using new schema (set scores, games won per player)
SAMPLE_MATCHES = [
    {"id": 1, "player1": {"name": "Kim Ndombe"}, "player2": {"name": "Natalie Coffen"},
     "set1_p1": 6, "set1_p2": 4, "set2_p1": 6, "set2_p2": 3,
     "player1_games": 12, "player2_games": 7, "period_label": "January 2025", "court": "Vermont Canyon"},
    {"id": 2, "player1": {"name": "Sara Chrisman"}, "player2": {"name": "Arianna Hairston"},
     "set1_p1": 7, "set1_p2": 5, "set2_p1": 6, "set2_p2": 4,
     "player1_games": 13, "player2_games": 9, "period_label": "January 2025", "court": "Griffith Park"},
    {"id": 3, "player1": {"name": "Kim Ndombe"}, "player2": {"name": "Hannah Shin"},
     "set1_p1": 6, "set1_p2": 2, "set2_p1": 6, "set2_p2": 4,
     "player1_games": 12, "player2_games": 6, "period_label": "December 2024", "court": "Echo Park"},
    {"id": 4, "player1": {"name": "Natalie Coffen"}, "player2": {"name": "Alik Apelian"},
     "set1_p1": 6, "set1_p2": 3, "set2_p1": 6, "set2_p2": 2,
     "player1_games": 12, "player2_games": 5, "period_label": "December 2024", "court": "Silver Lake"},
    {"id": 5, "player1": {"name": "Hannah Shin"}, "player2": {"name": "Hanna Pavlova"},
     "set1_p1": 6, "set1_p2": 4, "set2_p1": 7, "set2_p2": 5,
     "player1_games": 13, "player2_games": 9, "period_label": "December 2024", "court": "Los Feliz"},
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
                response = supabase.table('matches').select('*, player1:players!player1_id(*), player2:players!player2_id(*)').order('created_at', desc=True).limit(20).execute()
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
                # Calculate total games from set scores
                set1_p1 = int(data.get('set1_p1', 0))
                set1_p2 = int(data.get('set1_p2', 0))
                set2_p1 = int(data.get('set2_p1', 0))
                set2_p2 = int(data.get('set2_p2', 0))

                match_data = {
                    "player1_id": data['player1_id'],
                    "player2_id": data['player2_id'],
                    "set1_p1": set1_p1,
                    "set1_p2": set1_p2,
                    "set2_p1": set2_p1,
                    "set2_p2": set2_p2,
                    "player1_games": set1_p1 + set2_p1,
                    "player2_games": set1_p2 + set2_p2,
                    "period_type": data.get('period_type', 'month'),
                    "period_label": data.get('period_label', datetime.now().strftime('%B %Y')),
                    "court": data.get('court', 'Unknown'),
                    "match_date": data.get('match_date'),
                    "is_forfeit": data.get('is_forfeit', False)
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
