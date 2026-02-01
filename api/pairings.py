"""
Vercel Serverless Function: Pairings API - GET only for now

Returns current month's pairings.
POST (pairing generation) temporarily disabled.
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime


def get_availability_text(player):
    """Build human-readable availability string"""
    weekday_early = player.get('avail_weekday_early', False)
    weekday_day = player.get('avail_weekday_day', False)
    weekday_late = player.get('avail_weekday_late', False)
    weekend_early = player.get('avail_weekend_early', False)
    weekend_day = player.get('avail_weekend_day', False)
    weekend_late = player.get('avail_weekend_late', False)

    weekday_times = []
    if weekday_early:
        weekday_times.append("before 9am")
    if weekday_day:
        weekday_times.append("9-5")
    if weekday_late:
        weekday_times.append("after 5pm")

    weekend_times = []
    if weekend_early:
        weekend_times.append("before 9am")
    if weekend_day:
        weekend_times.append("9-5")
    if weekend_late:
        weekend_times.append("after 5pm")

    parts = []
    if weekday_times:
        parts.append(f"Weekdays: {', '.join(weekday_times)}")
    if weekend_times:
        parts.append(f"Weekends: {', '.join(weekend_times)}")

    return " | ".join(parts) if parts else ""


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get current month's pairings"""
        try:
            from api.supabase_http import table

            current_month = datetime.now().strftime('%B %Y')

            response = table('match_assignments')\
                .select('*')\
                .eq('period_label', current_month)\
                .execute()

            if response.data:
                player_ids = set()
                for p in response.data:
                    player_ids.add(p.get('player1_id'))
                    player_ids.add(p.get('player2_id'))

                players_result = table('players').select('*').execute()
                players_map = {pl['id']: pl for pl in players_result.data if pl['id'] in player_ids}

                pairings_with_availability = []
                for p in response.data:
                    p1 = players_map.get(p.get('player1_id'), {})
                    p2 = players_map.get(p.get('player2_id'), {})
                    p['player1'] = p1
                    p['player2'] = p2
                    p['player1_availability'] = get_availability_text(p1)
                    p['player2_availability'] = get_availability_text(p2)
                    pairings_with_availability.append(p)

                self._send_success({
                    'period': current_month,
                    'pairings': pairings_with_availability,
                    'count': len(response.data)
                })
            else:
                self._send_success({
                    'period': current_month,
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
