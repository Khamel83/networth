"""
Vercel Cron Job: Monthly Pairing Generation
Runs on 1st of each month at 9am PT
Generates pairings and sends notification emails
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


def get_supabase_client():
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_ANON_KEY')
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Called by Vercel Cron on 1st of each month.
        1. Generate pairings based on skill, blocked pairs, availability
        2. Send pairing notification emails to all players
        """
        try:
            # Verify this is a cron request (Vercel sets this header)
            auth_header = self.headers.get('Authorization')
            cron_secret = os.environ.get('CRON_SECRET')

            # In production, verify the request is from Vercel cron
            # if cron_secret and auth_header != f'Bearer {cron_secret}':
            #     self._send_error(401, 'Unauthorized')
            #     return

            period_label = datetime.now().strftime('%B %Y')
            supabase = get_supabase_client()

            if not supabase:
                self._send_error(503, 'Database not configured')
                return

            # Import the pairing logic
            from api.pairings import generate_pairings, skill_to_numeric

            # 1. Get all active players with availability
            players_resp = supabase.table('players')\
                .select('id, name, email, skill_level, rank')\
                .eq('is_active', True)\
                .eq('is_admin', False)\
                .execute()
            players = players_resp.data

            # 2. Get availability preferences
            availability_resp = supabase.table('player_availability')\
                .select('player_id, day_of_week, time_slot, is_available')\
                .eq('is_available', True)\
                .execute()

            # Build availability lookup
            availability = {}
            for a in availability_resp.data:
                pid = a['player_id']
                if pid not in availability:
                    availability[pid] = []
                availability[pid].append({
                    'day': a['day_of_week'],
                    'time': a['time_slot']
                })

            # 3. Get blocked pairs
            blocked_resp = supabase.table('match_feedback')\
                .select('from_player_id, about_player_id')\
                .eq('would_play_again', False)\
                .execute()
            blocked_pairs = []
            for b in blocked_resp.data:
                blocked_pairs.append({
                    'player_a': min(b['from_player_id'], b['about_player_id']),
                    'player_b': max(b['from_player_id'], b['about_player_id'])
                })

            # 4. Get recent matches for variety
            recent_resp = supabase.table('matches')\
                .select('player1_id, player2_id')\
                .order('created_at', desc=True)\
                .limit(200)\
                .execute()

            # 5. Generate pairings
            pairings = generate_pairings(players, blocked_pairs, recent_resp.data)

            # 6. Find overlapping availability for each pair
            assignments = []
            for p in pairings:
                p1_avail = availability.get(p['player1']['id'], [])
                p2_avail = availability.get(p['player2']['id'], [])

                # Find overlapping times
                suggested_times = []
                for a1 in p1_avail:
                    for a2 in p2_avail:
                        if a1['day'] == a2['day'] and a1['time'] == a2['time']:
                            suggested_times.append({
                                'day': a1['day'],
                                'time': a1['time']
                            })

                assignment = {
                    'player1_id': p['player1']['id'],
                    'player2_id': p['player2']['id'],
                    'period_type': 'month',
                    'period_label': period_label,
                    'status': 'pending',
                    'notes': json.dumps({'suggested_times': suggested_times[:3]}) if suggested_times else None
                }
                assignments.append(assignment)

            # 7. Save assignments to database
            if assignments:
                supabase.table('match_assignments').insert(assignments).execute()

            # 8. Send pairing emails
            # Import email sending function
            from api.email import send_email, get_pairing_email_html

            sent_count = 0
            for assignment in assignments:
                # Get player details
                p1 = next((p for p in players if p['id'] == assignment['player1_id']), None)
                p2 = next((p for p in players if p['id'] == assignment['player2_id']), None)

                if p1 and p2:
                    # Email to player 1
                    html1 = get_pairing_email_html(p1['name'], p2['name'], p2['email'], period_label)
                    result1 = send_email(p1['email'], f'🎾 Your {period_label} Tennis Match', html1)
                    if result1.get('success'):
                        sent_count += 1

                    # Email to player 2
                    html2 = get_pairing_email_html(p2['name'], p1['name'], p1['email'], period_label)
                    result2 = send_email(p2['email'], f'🎾 Your {period_label} Tennis Match', html2)
                    if result2.get('success'):
                        sent_count += 1

            self._send_success({
                'period': period_label,
                'pairings_created': len(assignments),
                'emails_sent': sent_count,
                'players': len(players)
            })

        except Exception as e:
            self._send_error(500, str(e))

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, **data}).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode())
