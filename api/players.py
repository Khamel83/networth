"""
Vercel Serverless Function: Players API
Handles player listing with Supabase
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


# Sample data fallback
SAMPLE_PLAYERS = [
    {"id": 1, "rank": 1, "name": "Kim Ndombe", "skill_level": "4.0+ Advanced", "points": 51, "wins": 8, "losses": 1, "trend": "neutral"},
    {"id": 2, "rank": 2, "name": "Sarah Kaplan", "skill_level": "4.0 Advanced", "points": 47, "wins": 7, "losses": 2, "trend": "up"},
    {"id": 3, "rank": 3, "name": "Jessica Chen", "skill_level": "3.5-4.0 Int-Adv", "points": 43, "wins": 6, "losses": 2, "trend": "up"},
    {"id": 4, "rank": 4, "name": "Maria Rodriguez", "skill_level": "4.0 Advanced", "points": 41, "wins": 6, "losses": 3, "trend": "down"},
    {"id": 5, "rank": 5, "name": "Emily Watson", "skill_level": "3.5 Intermediate+", "points": 38, "wins": 5, "losses": 3, "trend": "neutral"},
    {"id": 6, "rank": 6, "name": "Lisa Park", "skill_level": "3.5-4.0 Int-Adv", "points": 35, "wins": 5, "losses": 4, "trend": "up"},
    {"id": 7, "rank": 7, "name": "Anna Thompson", "skill_level": "3.5 Intermediate+", "points": 32, "wins": 4, "losses": 4, "trend": "neutral"},
    {"id": 8, "rank": 8, "name": "Rachel Kim", "skill_level": "3.0-3.5 Intermediate", "points": 28, "wins": 4, "losses": 5, "trend": "down"},
    {"id": 9, "rank": 9, "name": "Diana Lee", "skill_level": "3.5 Intermediate+", "points": 25, "wins": 3, "losses": 5, "trend": "up"},
    {"id": 10, "rank": 10, "name": "Michelle Brown", "skill_level": "3.0-3.5 Intermediate", "points": 22, "wins": 3, "losses": 6, "trend": "neutral"},
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
                response = supabase.table('players').select('*').eq('is_active', True).order('rank').execute()
                players = response.data
                source = "supabase"
            else:
                players = SAMPLE_PLAYERS
                source = "sample"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "players": players,
                "source": source
            }).encode())

        except Exception as e:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "players": SAMPLE_PLAYERS,
                "source": "sample_fallback",
                "error": str(e)
            }).encode())
