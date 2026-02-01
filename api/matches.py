"""
Vercel Serverless Function: Matches API
Handles match reporting and history with Supabase REST API.

Match reporting flow:
1. Player enters set scores (e.g., 6-4, 3-6, 6-2)
2. Player answers "Would you play again?" (for silent blocking)
3. System calculates games won for each player
4. Updates player total_games for ranking
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone


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
            from api.supabase_http import table
            from urllib.parse import parse_qs, urlparse

            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            action = params.get('action', ['history'])[0]

            if action == 'outstanding':
                # Get pending matches for the authenticated player
                return self._get_outstanding_matches()

            # Default: return match history (completed matches)
            response = table('matches').select('*').execute()
            matches = response.data
            source = "supabase"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "matches": matches,
                "source": source
            }).encode())

    def _get_outstanding_matches(self):
        """Get pending match assignments for the authenticated player"""
        try:
            from api.supabase_http import table
            from urllib.parse import parse_qs, urlparse

            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            # Get player email from auth header
            auth_header = self.headers.get('Authorization', '')
            player_email = None
            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                if '@' in token_or_email:
                    player_email = token_or_email.lower()

            if not player_email:
                player_email = params.get('player_email', [''])[0].lower()

            if not player_email:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "Authentication required"
                }).encode())
                return

            # Get player by email
            player_result = table('players').select('id, name, email').eq('email', player_email).single().execute()
            if not player_result.data:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "Player not found"
                }).encode())
                return

            player = player_result.data[0] if isinstance(player_result.data, list) else player_result.data
            player_id = player['id']

            # Get all pending match assignments for this player (as player1 OR player2)
            assignments_result = table('match_assignments')\
                .select('*')\
                .or_(f'player1_id.eq.{player_id},player2_id.eq.{player_id}')\
                .eq('status', 'pending')\
                .execute()

            # Get all players for enrichment
            players_result = table('players').select('id, name, email, phone, skill_level').execute()
            players_map = {p['id']: p for p in players_result.data}

            # Enrich assignments with opponent info
            outstanding = []
            for assignment in assignments_result.data:
                p1_id = assignment.get('player1_id')
                p2_id = assignment.get('player2_id')

                # Determine which is the opponent
                if player_id == p1_id:
                    opponent_id = p2_id
                else:
                    opponent_id = p1_id

                opponent = players_map.get(opponent_id, {})

                # Get opponent availability for display
                opponent_avail = []
                if opponent.get('avail_weekday_early'):
                    opponent_avail.append('Weekday mornings')
                if opponent.get('avail_weekday_day'):
                    opponent_avail.append('Weekday afternoons')
                if opponent.get('avail_weekday_late'):
                    opponent_avail.append('Weekday evenings')
                if opponent.get('avail_weekend_early'):
                    opponent_avail.append('Weekend mornings')
                if opponent.get('avail_weekend_day'):
                    opponent_avail.append('Weekend afternoons')
                if opponent.get('avail_weekend_late'):
                    opponent_avail.append('Weekend evenings')

                outstanding.append({
                    'id': assignment.get('id'),
                    'period_label': assignment.get('period_label'),
                    'opponent_id': opponent.get('id'),
                    'opponent_name': opponent.get('name', 'Unknown'),
                    'opponent_email': opponent.get('email', ''),
                    'opponent_phone': opponent.get('phone', ''),
                    'opponent_availability': ', '.join(opponent_avail) if opponent_avail else 'Not specified',
                    'status': assignment.get('status', 'pending')
                })

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "matches": outstanding,
                "count": len(outstanding)
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
        """
        Report a match result with feedback.

        Expected payload:
        {
            "assignment_id": 123,           # Optional: links to match_assignments
            "player1_id": 1,                # Reporter
            "player2_id": 2,                # Opponent
            "set1_p1": 6, "set1_p2": 4,     # Set 1 score
            "set2_p1": 6, "set2_p2": 3,     # Set 2 score
            "set3_p1": null, "set3_p2": null,  # Optional Set 3
            "court": "Vermont Canyon",
            "would_play_again": true        # Feedback (silent blocking if false)
        }
        """
        try:
            from api.supabase_http import table

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            # Calculate total games from set scores
            set1_p1 = int(data.get('set1_p1', 0))
            set1_p2 = int(data.get('set1_p2', 0))
            set2_p1 = int(data.get('set2_p1', 0))
            set2_p2 = int(data.get('set2_p2', 0))
            set3_p1 = int(data.get('set3_p1') or 0)
            set3_p2 = int(data.get('set3_p2') or 0)

            player1_games = set1_p1 + set2_p1 + set3_p1
            player2_games = set1_p2 + set2_p2 + set3_p2

            match_data = {
                "player1_id": data['player1_id'],
                "player2_id": data['player2_id'],
                "set1_p1": set1_p1,
                "set1_p2": set1_p2,
                "set2_p1": set2_p1,
                "set2_p2": set2_p2,
                "set3_p1": set3_p1 if set3_p1 > 0 else None,
                "set3_p2": set3_p2 if set3_p2 > 0 else None,
                "player1_games": player1_games,
                "player2_games": player2_games,
                "period_type": data.get('period_type', 'month'),
                "period_label": data.get('period_label', datetime.now().strftime('%B %Y')),
                "court": data.get('court'),
                "match_date": data.get('match_date'),
                "is_forfeit": data.get('is_forfeit', False)
            }

            # Insert match
            response = table('matches').insert(match_data).execute()
            match = response.data[0] if response.data else None

            # Update match assignment status if provided
            assignment_id = data.get('assignment_id')
            if assignment_id:
                table('match_assignments').update({
                    'status': 'completed',
                    'match_id': match['id'] if match else None
                }).eq('id', assignment_id).execute()

            # Record feedback (would_play_again)
            if 'would_play_again' in data and match:
                feedback_data = {
                    "from_player_id": data['player1_id'],
                    "about_player_id": data['player2_id'],
                    "match_id": match['id'],
                    "would_play_again": data['would_play_again']
                }
                table('match_feedback').insert(feedback_data).execute()

            # NOTE: Player totals are updated automatically by database trigger
            # (update_player_games function in supabase-final-setup.sql)
            # No manual update needed here - trigger handles it atomically

            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "match": match,
                "games_added": {
                    "player1": player1_games,
                    "player2": player2_games
                }
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

    def _send_demo_response(self, data):
        """Send response when database not available (demo mode)"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": True,
            "message": "Match recorded (demo mode)",
            "match": data
        }).encode())
