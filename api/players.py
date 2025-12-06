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


# Real player data fallback - NET WORTH Tennis East Side LA
SAMPLE_PLAYERS = [
    {"id": 1, "rank": 1, "name": "Kim Ndombe", "skill_level": "4.5 Advanced+", "points": 1510, "wins": 18, "losses": 0, "trend": "up"},
    {"id": 2, "rank": 2, "name": "Natalie Coffen", "skill_level": "4.5 Advanced+", "points": 1500, "wins": 16, "losses": 1, "trend": "up"},
    {"id": 3, "rank": 3, "name": "Sara Chrisman", "skill_level": "4.5 Advanced+", "points": 1490, "wins": 14, "losses": 2, "trend": "neutral"},
    {"id": 4, "rank": 4, "name": "Arianna Hairston", "skill_level": "4.5 Advanced+", "points": 1480, "wins": 12, "losses": 3, "trend": "neutral"},
    {"id": 5, "rank": 5, "name": "Hannah Shin", "skill_level": "4.5 Advanced+", "points": 1450, "wins": 10, "losses": 4, "trend": "up"},
    {"id": 6, "rank": 6, "name": "Alik Apelian", "skill_level": "4.5 Advanced+", "points": 1450, "wins": 8, "losses": 5, "trend": "neutral"},
    {"id": 7, "rank": 7, "name": "Hanna Pavlova", "skill_level": "4.2 Advanced", "points": 1410, "wins": 6, "losses": 6, "trend": "down"},
    {"id": 8, "rank": 8, "name": "Maddy Whitby", "skill_level": "4.1 Advanced", "points": 1380, "wins": 4, "losses": 7, "trend": "neutral"},
    {"id": 9, "rank": 9, "name": "Allison Dunne", "skill_level": "4.0 Advanced", "points": 1370, "wins": 2, "losses": 8, "trend": "up"},
    {"id": 10, "rank": 10, "name": "Ashley Brooke Kaufman", "skill_level": "4.0 Advanced", "points": 1330, "wins": 0, "losses": 9, "trend": "neutral"},
    {"id": 11, "rank": 11, "name": "Kaitlin Kelly", "skill_level": "4.0 Advanced", "points": 1320, "wins": 0, "losses": 10, "trend": "neutral"},
    {"id": 12, "rank": 12, "name": "Page Eaton", "skill_level": "4.0 Advanced", "points": 1300, "wins": 0, "losses": 11, "trend": "neutral"},
    {"id": 13, "rank": 13, "name": "Sarah Yun", "skill_level": "3.8 Intermediate+", "points": 1290, "wins": 0, "losses": 12, "trend": "neutral"},
    {"id": 14, "rank": 14, "name": "Laurie Berger", "skill_level": "3.7 Intermediate+", "points": 1260, "wins": 0, "losses": 13, "trend": "neutral"},
    {"id": 15, "rank": 15, "name": "Katie Morey", "skill_level": "3.6 Intermediate", "points": 1240, "wins": 0, "losses": 14, "trend": "neutral"},
    {"id": 16, "rank": 16, "name": "Alyssa Perry", "skill_level": "3.5 Intermediate", "points": 1200, "wins": 0, "losses": 15, "trend": "neutral"},
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
