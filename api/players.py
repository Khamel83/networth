"""
Vercel Serverless Function: Players API
Handles player listing with Supabase REST API
"""
from http.server import BaseHTTPRequestHandler
import json
import os

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
init_sentry()


# Real player data fallback - NET WORTH Tennis East Side LA (games-won system)
SAMPLE_PLAYERS = [
    {"id": 1, "rank": 1, "name": "Kim Ndombe", "skill_level": "4.5 Advanced+", "total_games": 51, "matches_played": 5, "trend": "up"},
    {"id": 2, "rank": 2, "name": "Natalie Coffen", "skill_level": "4.5 Advanced+", "total_games": 50, "matches_played": 6, "trend": "up"},
    {"id": 3, "rank": 3, "name": "Sara Chrisman", "skill_level": "4.5 Advanced+", "total_games": 49, "matches_played": 5, "trend": "neutral"},
    {"id": 4, "rank": 4, "name": "Arianna Hairston", "skill_level": "4.5 Advanced+", "total_games": 48, "matches_played": 4, "trend": "neutral"},
    {"id": 5, "rank": 5, "name": "Alik Apelian", "skill_level": "4.5 Advanced+", "total_games": 45, "matches_played": 5, "trend": "neutral"},
    {"id": 6, "rank": 6, "name": "Hannah Shin", "skill_level": "4.5 Advanced+", "total_games": 45, "matches_played": 4, "trend": "up"},
    {"id": 7, "rank": 7, "name": "Hanna Pavlova", "skill_level": "4.0 Advanced", "total_games": 41, "matches_played": 6, "trend": "neutral"},
    {"id": 8, "rank": 8, "name": "Maddy Whitby", "skill_level": "4.0 Advanced", "total_games": 38, "matches_played": 5, "trend": "neutral"},
    {"id": 9, "rank": 9, "name": "Allison Dunne", "skill_level": "4.0 Advanced", "total_games": 37, "matches_played": 4, "trend": "up"},
    {"id": 10, "rank": 10, "name": "Ashley Brooke Kaufman", "skill_level": "3.5+ Intermediate", "total_games": 33, "matches_played": 7, "trend": "neutral"},
    {"id": 11, "rank": 11, "name": "Kaitlin Kelly", "skill_level": "3.5+ Intermediate", "total_games": 32, "matches_played": 4, "trend": "neutral"},
    {"id": 12, "rank": 12, "name": "Page Eaton", "skill_level": "3.5+ Intermediate", "total_games": 30, "matches_played": 4, "trend": "neutral"},
    {"id": 13, "rank": 13, "name": "Sarah Yun", "skill_level": "3.5+ Intermediate", "total_games": 29, "matches_played": 3, "trend": "neutral"},
    {"id": 14, "rank": 14, "name": "Camille Tsalik", "skill_level": "3.5+ Intermediate", "total_games": 29, "matches_played": 3, "trend": "neutral"},
    {"id": 15, "rank": 15, "name": "Laurie Berger", "skill_level": "3.5+ Intermediate", "total_games": 26, "matches_played": 3, "trend": "neutral"},
    {"id": 16, "rank": 16, "name": "Katie Morey", "skill_level": "3.5 Intermediate", "total_games": 24, "matches_played": 2, "trend": "neutral"},
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
            # Import HTTP helper
            from api.supabase_http import table

            # Filter out admin from player lists
            # Order by total_games descending with NULLS LAST (so 0-game players rank at bottom)
            admin_email = os.environ.get('ADMIN_EMAIL', 'khamel@khamel.com')
            result = table('players').select('*').eq('is_active', True).neq('email', admin_email).order('total_games', desc=True, nulls='last').execute()

            if result.data:
                players = result.data
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
