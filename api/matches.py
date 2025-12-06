"""
Vercel Serverless Function: Matches API
Handles match reporting and history with Supabase
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

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

    def do_GET(self):
        try:
            if supabase:
                response = supabase.table('matches').select('*, winner:players!winner_id(*), loser:players!loser_id(*)').order('played_at', desc=True).limit(20).execute()
                matches = response.data
            else:
                # Sample match data
                matches = [
                    {
                        "id": 1,
                        "winner": {"name": "Kim Ndombe"},
                        "loser": {"name": "Sarah Kaplan"},
                        "winner_score": "6-4, 6-3",
                        "loser_score": "4-6, 3-6",
                        "played_at": "2024-12-01T14:00:00Z",
                        "court": "Vermont Canyon"
                    },
                    {
                        "id": 2,
                        "winner": {"name": "Sarah Kaplan"},
                        "loser": {"name": "Jessica Chen"},
                        "winner_score": "7-5, 6-4",
                        "loser_score": "5-7, 4-6",
                        "played_at": "2024-11-28T10:00:00Z",
                        "court": "Griffith Park"
                    },
                    {
                        "id": 3,
                        "winner": {"name": "Jessica Chen"},
                        "loser": {"name": "Maria Rodriguez"},
                        "winner_score": "6-2, 6-4",
                        "loser_score": "2-6, 4-6",
                        "played_at": "2024-11-25T16:00:00Z",
                        "court": "Echo Park"
                    },
                ]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "matches": matches,
                "source": "supabase" if supabase else "sample"
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

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            # Validate required fields
            required = ['winner_id', 'loser_id', 'winner_score', 'loser_score']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            if supabase:
                # Insert match
                match_data = {
                    "winner_id": data['winner_id'],
                    "loser_id": data['loser_id'],
                    "winner_score": data['winner_score'],
                    "loser_score": data['loser_score'],
                    "court": data.get('court', 'Unknown'),
                    "played_at": data.get('played_at', datetime.utcnow().isoformat())
                }
                response = supabase.table('matches').insert(match_data).execute()

                # Update player rankings
                # Winner gains points, loser loses points
                winner = supabase.table('players').select('*').eq('id', data['winner_id']).single().execute()
                loser = supabase.table('players').select('*').eq('id', data['loser_id']).single().execute()

                if winner.data and loser.data:
                    # Simple ELO-like point system
                    points_transfer = 3  # Base points for a win

                    supabase.table('players').update({
                        "points": winner.data['points'] + points_transfer,
                        "wins": winner.data['wins'] + 1,
                        "trend": "up"
                    }).eq('id', data['winner_id']).execute()

                    supabase.table('players').update({
                        "points": max(0, loser.data['points'] - 1),
                        "losses": loser.data['losses'] + 1,
                        "trend": "down"
                    }).eq('id', data['loser_id']).execute()

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

        except ValueError as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
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
