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


# Real player data fallback - NET WORTH Tennis East Side LA (games-won system)
SAMPLE_PLAYERS = [
    {"id": 1, "rank": 1, "name": "Kim Ndombe", "skill_level": "4.5 Advanced+", "total_games": 51, "matches_played": 5, "trend": "up", "profile_picture": "https://i.pravatar.cc/150?img=1", "neighborhood": "Silver Lake", "instagram_handle": "kimndombe", "fun_fact": "Favorite player: Serena Williams"},
    {"id": 2, "rank": 2, "name": "Natalie Coffen", "skill_level": "4.5 Advanced+", "total_games": 50, "matches_played": 6, "trend": "up", "profile_picture": "https://i.pravatar.cc/150?img=5", "neighborhood": "Echo Park", "instagram_handle": "natalietennis", "fun_fact": "Favorite match: 2019 Wimbledon Final"},
    {"id": 3, "rank": 3, "name": "Sara Chrisman", "skill_level": "4.5 Advanced+", "total_games": 49, "matches_played": 5, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=9", "neighborhood": "Los Feliz", "instagram_handle": "sarachrisman", "fun_fact": "Favorite player: Naomi Osaka"},
    {"id": 4, "rank": 4, "name": "Arianna Hairston", "skill_level": "4.5 Advanced+", "total_games": 48, "matches_played": 4, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=16", "neighborhood": "Highland Park", "instagram_handle": "ariannatennis", "fun_fact": "Favorite player: Coco Gauff"},
    {"id": 5, "rank": 5, "name": "Alik Apelian", "skill_level": "4.5 Advanced+", "total_games": 45, "matches_played": 5, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=20", "neighborhood": "Atwater Village", "instagram_handle": "alikapelian", "fun_fact": "Favorite match: 2023 Australian Open Final"},
    {"id": 6, "rank": 6, "name": "Hannah Shin", "skill_level": "4.5 Advanced+", "total_games": 45, "matches_played": 4, "trend": "up", "profile_picture": "https://i.pravatar.cc/150?img=25", "neighborhood": "Eagle Rock", "instagram_handle": "hannahshintennis", "fun_fact": "Favorite player: Venus Williams"},
    {"id": 7, "rank": 7, "name": "Hanna Pavlova", "skill_level": "4.0 Advanced", "total_games": 41, "matches_played": 6, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=28", "neighborhood": "Downtown LA", "instagram_handle": "hannapavlova", "fun_fact": "Favorite player: Maria Sharapova"},
    {"id": 8, "rank": 8, "name": "Maddy Whitby", "skill_level": "4.0 Advanced", "total_games": 38, "matches_played": 5, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=32", "neighborhood": "Burbank", "instagram_handle": "maddywhitby", "fun_fact": "Favorite match: 2012 Wimbledon Final"},
    {"id": 9, "rank": 9, "name": "Allison Dunne", "skill_level": "4.0 Advanced", "total_games": 37, "matches_played": 4, "trend": "up", "profile_picture": "https://i.pravatar.cc/150?img=36", "neighborhood": "Pasadena", "instagram_handle": "allisondunne", "fun_fact": "Favorite player: Iga Świątek"},
    {"id": 10, "rank": 10, "name": "Ashley Brooke Kaufman", "skill_level": "3.5+ Intermediate", "total_games": 33, "matches_played": 7, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=40", "neighborhood": "Glendale", "instagram_handle": "ashleybrookekaufman", "fun_fact": "Favorite player: Billie Jean King"},
    {"id": 11, "rank": 11, "name": "Kaitlin Kelly", "skill_level": "3.5+ Intermediate", "total_games": 32, "matches_played": 4, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=44", "neighborhood": "West Hollywood", "instagram_handle": "kaitlintennis", "fun_fact": "Favorite match: 2017 US Open Final"},
    {"id": 12, "rank": 12, "name": "Page Eaton", "skill_level": "3.5+ Intermediate", "total_games": 30, "matches_played": 4, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=47", "neighborhood": "Mid City", "instagram_handle": "pageeaton", "fun_fact": "Favorite player: Simona Halep"},
    {"id": 13, "rank": 13, "name": "Sarah Yun", "skill_level": "3.5+ Intermediate", "total_games": 29, "matches_played": 3, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=48", "neighborhood": "Koreatown", "instagram_handle": "sarahyuntennis", "fun_fact": "Favorite player: Madison Keys"},
    {"id": 14, "rank": 14, "name": "Camille Tsalik", "skill_level": "3.5+ Intermediate", "total_games": 29, "matches_played": 3, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=49", "neighborhood": "Culver City", "instagram_handle": "camilletsalik", "fun_fact": "Favorite player: Elena Rybakina"},
    {"id": 15, "rank": 15, "name": "Laurie Berger", "skill_level": "3.5+ Intermediate", "total_games": 26, "matches_played": 3, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=10", "neighborhood": "Venice", "instagram_handle": "laurieberger", "fun_fact": "Favorite match: 2008 Wimbledon Final"},
    {"id": 16, "rank": 16, "name": "Katie Morey", "skill_level": "3.5 Intermediate", "total_games": 24, "matches_played": 2, "trend": "neutral", "profile_picture": "https://i.pravatar.cc/150?img=15", "neighborhood": "Santa Monica", "instagram_handle": "katiemorey", "fun_fact": "Favorite player: Aryna Sabalenka"},
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
