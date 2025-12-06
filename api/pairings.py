"""
Vercel Serverless Function: Pairing Algorithm
Generates monthly match pairings based on:
1. Skill level similarity (PRIMARY - the main matching criterion)
2. Blocked pairs exclusion (would_play_again=false)
3. Variety (prefer players who haven't played each other recently)
4. Respects unavailable_until for players taking a break

SIMPLIFIED: No court constraints, no availability matching.
Email will include each player's time preferences for them to coordinate.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, date
import random


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


def skill_to_numeric(skill_level):
    """Convert skill level string to numeric for comparison"""
    if not skill_level:
        return 3.0
    if '4.5' in skill_level:
        return 4.5
    elif '4.0' in skill_level:
        return 4.0
    elif '3.5+' in skill_level:
        return 3.75
    elif '3.5' in skill_level:
        return 3.5
    elif '3.0' in skill_level:
        return 3.0
    else:
        return 2.5


def get_availability_text(player):
    """Build human-readable availability string for emails"""
    morning = player.get('available_morning', True)
    afternoon = player.get('available_afternoon', True)
    evening = player.get('available_evening', True)

    if morning and afternoon and evening:
        return "Any time"
    if not morning and not afternoon and not evening:
        return "No times specified"

    times = []
    if morning:
        times.append("Mornings")
    if afternoon:
        times.append("Afternoons")
    if evening:
        times.append("Evenings")
    return ", ".join(times)


def is_player_available(player):
    """Check if player is currently available for matching"""
    if not player.get('is_active', True):
        return False

    unavailable_until = player.get('unavailable_until')
    if unavailable_until:
        # Handle both string and date formats
        if isinstance(unavailable_until, str):
            try:
                unavailable_date = datetime.fromisoformat(unavailable_until.replace('Z', '+00:00')).date()
            except ValueError:
                unavailable_date = datetime.strptime(unavailable_until, '%Y-%m-%d').date()
        else:
            unavailable_date = unavailable_until

        if unavailable_date > date.today():
            return False

    return True


def generate_pairings(players, blocked_pairs, recent_matches):
    """
    Generate optimal pairings for all active players.
    SIMPLIFIED: Skill-based matching only. No court/time constraints.

    Returns list of pairing dicts with player info and availability text.
    """
    # Filter to only available players
    available_players = [p for p in players if is_player_available(p)]

    # Convert blocked pairs to a set for O(1) lookup
    blocked_set = set()
    for bp in blocked_pairs:
        blocked_set.add((bp['player_a'], bp['player_b']))
        blocked_set.add((bp['player_b'], bp['player_a']))

    # Convert recent matches to count dict
    recent_count = {}
    for m in recent_matches:
        key = tuple(sorted([m['player1_id'], m['player2_id']]))
        recent_count[key] = recent_count.get(key, 0) + 1

    # Sort players by skill level for better matching
    sorted_players = sorted(
        available_players,
        key=lambda p: skill_to_numeric(p.get('skill_level', '3.0')),
        reverse=True
    )

    pairings = []
    unpaired = list(sorted_players)
    skipped = []  # Players who couldn't be matched (all options blocked)

    while len(unpaired) >= 2:
        player1 = unpaired.pop(0)

        # Find best match for player1
        best_match = None
        best_score = -999

        for i, player2 in enumerate(unpaired):
            # Check if blocked
            if (player1['id'], player2['id']) in blocked_set:
                continue

            # Calculate match score - SKILL IS PRIMARY
            score = 0

            # Skill similarity (max 50 points, lose points for difference)
            skill_diff = abs(
                skill_to_numeric(player1.get('skill_level', '3.0')) -
                skill_to_numeric(player2.get('skill_level', '3.0'))
            )
            score += 50 - (skill_diff * 25)  # Increased weight on skill

            # Variety bonus (haven't played recently)
            pair_key = tuple(sorted([player1['id'], player2['id']]))
            times_played = recent_count.get(pair_key, 0)
            if times_played == 0:
                score += 15  # Never played = bonus
            else:
                score -= times_played * 5  # Played recently = penalty

            if score > best_score:
                best_score = score
                best_match = (i, player2)

        if best_match:
            idx, player2 = best_match
            pairings.append({
                'player1': player1,
                'player2': player2,
                'player1_availability': get_availability_text(player1),
                'player2_availability': get_availability_text(player2),
                'score': best_score
            })
            unpaired.pop(idx)
        else:
            # No valid match found (all blocked), add to skipped list
            skipped.append(player1)

    # If odd number of players, last one gets skipped
    if unpaired:
        skipped.extend(unpaired)

    return pairings, skipped


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get current month's pairings"""
        try:
            supabase = get_supabase_client()
            current_month = datetime.now().strftime('%B %Y')

            if supabase:
                # Get existing pairings for this month with player details
                response = supabase.table('match_assignments')\
                    .select('*, player1:players!player1_id(id, name, email, available_morning, available_afternoon, available_evening), player2:players!player2_id(id, name, email, available_morning, available_afternoon, available_evening)')\
                    .eq('period_label', current_month)\
                    .execute()

                # Add availability text to response
                pairings_with_availability = []
                for p in response.data:
                    p['player1_availability'] = get_availability_text(p.get('player1', {}))
                    p['player2_availability'] = get_availability_text(p.get('player2', {}))
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
                    'count': 0,
                    'demo': True
                })

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Generate new pairings for current or specified month"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            period_label = data.get('period_label', datetime.now().strftime('%B %Y'))
            period_type = data.get('period_type', 'month')

            supabase = get_supabase_client()

            if not supabase:
                self._send_error(503, "Database not configured")
                return

            # 1. Get all active players (including new availability fields)
            players_resp = supabase.table('players')\
                .select('id, name, email, skill_level, rank, is_active, unavailable_until, available_morning, available_afternoon, available_evening')\
                .eq('is_active', True)\
                .eq('is_admin', False)\
                .execute()
            players = players_resp.data

            # 2. Get blocked pairs (from "would not play again" feedback)
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

            # 3. Get recent matches (last 3 months for variety)
            recent_resp = supabase.table('matches')\
                .select('player1_id, player2_id')\
                .order('created_at', desc=True)\
                .limit(200)\
                .execute()
            recent_matches = recent_resp.data

            # 4. Generate pairings (now returns tuple: pairings, skipped)
            pairings, skipped = generate_pairings(players, blocked_pairs, recent_matches)

            # 5. Save to match_assignments
            assignments = []
            for p in pairings:
                assignment = {
                    'player1_id': p['player1']['id'],
                    'player2_id': p['player2']['id'],
                    'period_type': period_type,
                    'period_label': period_label,
                    'status': 'pending'
                }
                assignments.append(assignment)

            if assignments:
                supabase.table('match_assignments').insert(assignments).execute()

            self._send_success({
                'period': period_label,
                'pairings_created': len(assignments),
                'players_available': len([p for p in players if is_player_available(p)]),
                'players_unavailable': len([p for p in players if not is_player_available(p)]),
                'players_skipped': [s['name'] for s in skipped],
                'pairings': [{
                    'player1': p['player1']['name'],
                    'player1_email': p['player1']['email'],
                    'player1_availability': p['player1_availability'],
                    'player2': p['player2']['name'],
                    'player2_email': p['player2']['email'],
                    'player2_availability': p['player2_availability'],
                    'match_score': p['score']
                } for p in pairings]
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
