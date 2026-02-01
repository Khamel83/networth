"""
Vercel Serverless Function: Pending Matches API

Returns ALL pending match assignments (status != 'completed').
This allows players to enter scores for any unplayed match, regardless of month.
"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get all pending match assignments"""
        try:
            from api.supabase_http import table
            from api.pairings import get_availability_text

            # Get ALL match assignments
            response = table('match_assignments').select('*').execute()

            # Filter out completed matches
            pending_assignments = [m for m in response.data if m.get('status') != 'completed']

            if pending_assignments:
                # Get player IDs to look up player details
                player_ids = set()
                for p in pending_assignments:
                    player_ids.add(p.get('player1_id'))
                    player_ids.add(p.get('player2_id'))

                # Get all relevant players
                players_result = table('players').select('*').execute()
                players_map = {pl['id']: pl for pl in players_result.data if pl['id'] in player_ids}

                pairings_with_availability = []
                for p in pending_assignments:
                    p1 = players_map.get(p.get('player1_id'), {})
                    p2 = players_map.get(p.get('player2_id'), {})
                    p['player1'] = p1
                    p['player2'] = p2
                    p['player1_availability'] = get_availability_text(p1)
                    p['player2_availability'] = get_availability_text(p2)
                    pairings_with_availability.append(p)

                self._send_success({
                    'pairings': pairings_with_availability,
                    'count': len(pending_assignments)
                })
            else:
                self._send_success({
                    'pairings': [],
                    'count': 0
                })

        except Exception as e:
            self._send_error(500, str(e))

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
