"""
Vercel Serverless Function: Pairing Algorithm (RMS-Based)

Generates monthly match pairings based on:
1. RMS (Rolling Match Score) - Average total games won in last 3 matches
2. Performance bands: developing (≤6), competitive (6.1-9), strong (9.1-12), dominant (>12)
3. New players paired together when possible
4. Anti-staleness: avoid same matchup within 3 months
5. Admin flex: remove Ashley/Natalie if odd count
6. Only matches Players (not Social Butterflies)

Updated for Ashley's Christmas 2025 feedback.
Uses Supabase REST API (no Python supabase client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, date
import random


def calculate_rms(player_id, matches):
    """
    Calculate Rolling Match Score (RMS) for a player.
    RMS = Average total games won in last 3 completed matches.

    Args:
        player_id: The player's ID
        matches: List of recent matches from database

    Returns:
        float or None if player has no matches
    """
    player_matches = []

    for m in matches:
        if m['player1_id'] == player_id:
            games_won = (m.get('set1_p1', 0) or 0) + (m.get('set2_p1', 0) or 0)
            player_matches.append(games_won)
        elif m['player2_id'] == player_id:
            games_won = (m.get('set1_p2', 0) or 0) + (m.get('set2_p2', 0) or 0)
            player_matches.append(games_won)

        # Only consider last 3 matches
        if len(player_matches) >= 3:
            break

    if not player_matches:
        return None

    return sum(player_matches) / len(player_matches)


def get_performance_band(rms):
    """
    Get performance band based on RMS score.

    Bands:
    - developing: ≤6 games average
    - competitive: 6.1-9 games average
    - strong: 9.1-12 games average
    - dominant: >12 games average
    - new: No RMS (new player)

    Returns:
        tuple: (band_name, band_order) where band_order is used for sorting
    """
    if rms is None:
        return ('new', 0)  # New players get matched together
    if rms <= 6:
        return ('developing', 1)
    elif rms <= 9:
        return ('competitive', 2)
    elif rms <= 12:
        return ('strong', 3)
    else:
        return ('dominant', 4)


def get_availability_text(player):
    """Build human-readable availability string using 6-slot system"""
    # New 6-slot system
    weekday_early = player.get('avail_weekday_early', False)
    weekday_day = player.get('avail_weekday_day', False)
    weekday_late = player.get('avail_weekday_late', False)
    weekend_early = player.get('avail_weekend_early', False)
    weekend_day = player.get('avail_weekend_day', False)
    weekend_late = player.get('avail_weekend_late', False)

    has_new_slots = any([
        weekday_early, weekday_day, weekday_late,
        weekend_early, weekend_day, weekend_late
    ])

    # Fallback to old 3-slot system
    if not has_new_slots:
        morning = player.get('available_morning', False)
        afternoon = player.get('available_afternoon', False)
        evening = player.get('available_evening', False)

        if morning and afternoon and evening:
            return "Any time"
        if not morning and not afternoon and not evening:
            return ""

        times = []
        if morning:
            times.append("Mornings")
        if afternoon:
            times.append("Afternoons")
        if evening:
            times.append("Evenings")
        return ", ".join(times)

    # Build from 6-slot system
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


def is_player_available(player):
    """Check if player is currently available for matching"""
    if not player.get('is_active', True):
        return False

    # Exclude admin from matching
    admin_email = os.environ.get('ADMIN_EMAIL', 'khamel@khamel.com')
    if player.get('email') == admin_email:
        return False

    # Social Butterflies are never included in matching
    if player.get('membership_tier') == 'social_butterfly':
        return False

    unavailable_until = player.get('unavailable_until')
    if unavailable_until:
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


def is_admin_flex(player):
    """Check if player is an admin flex (can be removed if odd count)"""
    email = player.get('email', '').lower()
    return email in ['nmcoffen@gmail.com', 'ashleybrooke.kaufman@gmail.com']


def generate_pairings(players, blocked_pairs, recent_matches, all_matches):
    """
    Generate optimal pairings using RMS-based matching.

    Algorithm:
    1. Calculate RMS for each player
    2. Group players by performance band
    3. Within each band, pair randomly
    4. New players are paired together when possible
    5. Avoid same matchup within 3 months
    6. Handle odd player by removing admin flex or floating to adjacent band

    Args:
        players: List of eligible players
        blocked_pairs: List of blocked pairs (wouldn't play again)
        recent_matches: Recent match assignments (for anti-staleness)
        all_matches: All matches with scores (for RMS calculation)

    Returns:
        tuple: (pairings, skipped)
    """
    # Filter to only available players
    available_players = [p for p in players if is_player_available(p)]

    if len(available_players) < 2:
        return [], available_players

    # Calculate RMS for each player and add to player dict
    for player in available_players:
        rms = calculate_rms(player['id'], all_matches)
        player['rms'] = rms
        band, band_order = get_performance_band(rms)
        player['band'] = band
        player['band_order'] = band_order

    # Convert blocked pairs to a set for O(1) lookup
    blocked_set = set()
    for bp in blocked_pairs:
        blocked_set.add((bp['player_a'], bp['player_b']))
        blocked_set.add((bp['player_b'], bp['player_a']))

    # Build recent matchup set (last 3 months - anti-staleness)
    recent_matchups = set()
    for m in recent_matches:
        key = tuple(sorted([m['player1_id'], m['player2_id']]))
        recent_matchups.add(key)

    # Handle odd number of players - remove admin flex with alternating rotation
    # Ashley sits out on odd months (Jan, Mar, May, Jul, Sep, Nov)
    # Natalie sits out on even months (Feb, Apr, Jun, Aug, Oct, Dec)
    if len(available_players) % 2 == 1:
        # Find admin flex players
        natalie = next((p for p in available_players if p.get('email', '').lower() == 'nmcoffen@gmail.com'), None)
        ashley = next((p for p in available_players if p.get('email', '').lower() == 'ashleybrooke.kaufman@gmail.com'), None)

        # Determine whose turn it is to sit out based on the month
        current_month = datetime.now().month
        is_odd_month = current_month % 2 == 1  # Jan=1, Mar=3, etc.

        removed_player = None
        if is_odd_month:
            # Ashley sits out first (odd months)
            if ashley:
                available_players.remove(ashley)
                removed_player = ashley
            elif natalie:
                # Fallback to Natalie if Ashley not available
                available_players.remove(natalie)
                removed_player = natalie
        else:
            # Natalie sits out (even months)
            if natalie:
                available_players.remove(natalie)
                removed_player = natalie
            elif ashley:
                # Fallback to Ashley if Natalie not available
                available_players.remove(ashley)
                removed_player = ashley

        if not removed_player:
            # No admin flex available, remove lowest ranked player
            available_players.sort(key=lambda p: (p.get('rank', 999), p.get('band_order', 0)))
            removed_player = available_players.pop()

        skipped = [removed_player] if removed_player else []
    else:
        skipped = []

    # Group players by band
    bands = {}
    for player in available_players:
        band = player['band']
        if band not in bands:
            bands[band] = []
        bands[band].append(player)

    # Shuffle within each band for randomness
    for band_players in bands.values():
        random.shuffle(band_players)

    pairings = []
    unpaired = []

    # Process bands in order: new players first, then developing, competitive, strong, dominant
    band_order = ['new', 'developing', 'competitive', 'strong', 'dominant']

    for band_name in band_order:
        if band_name not in bands:
            continue

        band_players = bands[band_name]

        while len(band_players) >= 2:
            player1 = band_players.pop(0)

            # Find best match in this band
            best_match_idx = None
            best_score = -999

            for i, player2 in enumerate(band_players):
                # Check if blocked
                if (player1['id'], player2['id']) in blocked_set:
                    continue

                # Calculate match score
                score = 100  # Base score for same-band match

                # Anti-staleness: penalty for recent matchup
                pair_key = tuple(sorted([player1['id'], player2['id']]))
                if pair_key in recent_matchups:
                    score -= 50  # Big penalty for recent matchup

                # RMS similarity bonus (closer RMS = better match)
                if player1['rms'] is not None and player2['rms'] is not None:
                    rms_diff = abs(player1['rms'] - player2['rms'])
                    score += max(0, 20 - rms_diff * 3)

                if score > best_score:
                    best_score = score
                    best_match_idx = i

            if best_match_idx is not None:
                player2 = band_players.pop(best_match_idx)
                pairings.append({
                    'player1': player1,
                    'player2': player2,
                    'player1_availability': get_availability_text(player1),
                    'player2_availability': get_availability_text(player2),
                    'score': best_score,
                    'band': band_name
                })
            else:
                # No valid match in this band, add to unpaired
                unpaired.append(player1)

        # Any remaining unpaired in this band
        unpaired.extend(band_players)

    # Try to pair any unpaired players across bands
    while len(unpaired) >= 2:
        player1 = unpaired.pop(0)
        best_match_idx = None
        best_score = -999

        for i, player2 in enumerate(unpaired):
            if (player1['id'], player2['id']) in blocked_set:
                continue

            score = 50  # Lower score for cross-band match

            # Band proximity bonus
            band_diff = abs(player1['band_order'] - player2['band_order'])
            score += max(0, 30 - band_diff * 10)

            # Anti-staleness
            pair_key = tuple(sorted([player1['id'], player2['id']]))
            if pair_key in recent_matchups:
                score -= 30

            if score > best_score:
                best_score = score
                best_match_idx = i

        if best_match_idx is not None:
            player2 = unpaired.pop(best_match_idx)
            pairings.append({
                'player1': player1,
                'player2': player2,
                'player1_availability': get_availability_text(player1),
                'player2_availability': get_availability_text(player2),
                'score': best_score,
                'band': f"cross-band ({player1['band']} + {player2['band']})"
            })
        else:
            skipped.append(player1)

    # Any remaining unpaired
    skipped.extend(unpaired)

    return pairings, skipped


def update_player_rms(player_id, matches):
    """Update a player's RMS score and band in the database"""
    from api.supabase_http import table

    rms = calculate_rms(player_id, matches)
    band, _ = get_performance_band(rms)

    table('players').update({
        'rms_score': rms,
        'rms_band': band
    }).eq('id', player_id).execute()

    return rms, band


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
            from api.supabase_http import table

            current_month = datetime.now().strftime('%B %Y')

            # Get match assignments (without complex joins for simplicity)
            response = table('match_assignments')\
                .select('*')\
                .eq('period_label', current_month)\
                .execute()

            if response.data:
                # Get player IDs to look up player details
                player_ids = set()
                for p in response.data:
                    player_ids.add(p.get('player1_id'))
                    player_ids.add(p.get('player2_id'))

                # Get all relevant players
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
                    'count': 0,
                    'demo': True
                })

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Generate new pairings for current or specified month"""
        try:
            from api.supabase_http import table

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            period_label = data.get('period_label', datetime.now().strftime('%B %Y'))
            period_type = data.get('period_type', 'month')

            # 1. Get all active Players (exclude Social Butterflies and admin)
            admin_email = os.environ.get('ADMIN_EMAIL', 'khamel@khamel.com')
            players_resp = table('players')\
                .select('id, name, email, skill_level, rank, is_active, unavailable_until, membership_tier, rms_score, rms_band, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening')\
                .eq('is_active', True)\
                .neq('membership_tier', 'social_butterfly')\
                .neq('email', admin_email)\
                .execute()
            players = players_resp.data

            # 2. Get blocked pairs (from "would not play again" feedback)
            blocked_resp = table('match_feedback')\
                .select('from_player_id, about_player_id')\
                .eq('would_play_again', False)\
                .execute()
            blocked_pairs = []
            for b in blocked_resp.data:
                blocked_pairs.append({
                    'player_a': min(b['from_player_id'], b['about_player_id']),
                    'player_b': max(b['from_player_id'], b['about_player_id'])
                })

            # 3. Get recent match assignments (last 3 months for anti-staleness)
            recent_resp = table('match_assignments')\
                .select('player1_id, player2_id')\
                .order('created_at', desc=True)\
                .limit(200)\
                .execute()
            recent_matches = recent_resp.data

            # 4. Get all matches with scores (for RMS calculation)
            all_matches_resp = table('matches')\
                .select('player1_id, player2_id, set1_p1, set1_p2, set2_p1, set2_p2')\
                .order('created_at', desc=True)\
                .limit(500)\
                .execute()
            all_matches = all_matches_resp.data

            # 5. Generate pairings with new RMS algorithm
            pairings, skipped = generate_pairings(players, blocked_pairs, recent_matches, all_matches)

            # 6. Save to match_assignments
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
                table('match_assignments').insert(assignments).execute()

            # 7. Send match assignment emails
            emails_sent = 0
            email_errors = []
            try:
                import time
                from api.email import send_email, get_match_assignment_email_html
                for i, p in enumerate(pairings):
                    # Rate limit: Resend allows 2 req/sec, add delay between emails
                    if i > 0:
                        time.sleep(0.6)
                    p1 = p['player1']
                    p2 = p['player2']
                    html = get_match_assignment_email_html(
                        p1['name'],
                        p2['name'],
                        period_label,
                        p['player1_availability'],
                        p['player2_availability'],
                        p1.get('phone', ''),
                        p2.get('phone', '')
                    )
                    subject = f"{p1['name']}, meet {p2['name']} - You're matched for {period_label}!"
                    # Set reply-to to both players so Ashley isn't included in replies
                    reply_to = [p1['email'], p2['email']]
                    result = send_email(
                        [p1['email'], p2['email']],
                        subject,
                        html,
                        reply_to=reply_to
                    )
                    if result.get('success'):
                        emails_sent += 1
                    else:
                        email_errors.append(f"{p1['name']} & {p2['name']}: {result.get('error')}")
            except Exception as e:
                email_errors.append(f"Email system error: {str(e)}")

            # 8. Update RMS scores for all players
            for player in players:
                update_player_rms(player['id'], all_matches)

            self._send_success({
                'period': period_label,
                'pairings_created': len(assignments),
                'emails_sent': emails_sent,
                'email_errors': email_errors if email_errors else None,
                'players_available': len([p for p in players if is_player_available(p)]),
                'players_unavailable': len([p for p in players if not is_player_available(p)]),
                'players_skipped': [{'name': s['name'], 'reason': 'admin_flex' if is_admin_flex(s) else 'odd_count'} for s in skipped],
                'pairings': [{
                    'player1': p['player1']['name'],
                    'player1_email': p['player1']['email'],
                    'player1_availability': p['player1_availability'],
                    'player1_rms': p['player1'].get('rms'),
                    'player1_band': p['player1'].get('band'),
                    'player2': p['player2']['name'],
                    'player2_email': p['player2']['email'],
                    'player2_availability': p['player2_availability'],
                    'player2_rms': p['player2'].get('rms'),
                    'player2_band': p['player2'].get('band'),
                    'match_score': p['score'],
                    'match_band': p['band']
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
