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

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
from api.reliability import preflight, try_start_run, append_event, update_run
init_sentry()


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

    # Exclude test/fake email addresses
    _email = player.get('email', '').lower()
    _test_tlds = ('.invalid', '.test', '.example', '.localhost', '.onion')
    if any(_email.endswith(t) for t in _test_tlds):
        return False
    if 'test' in _email and '@test.' in _email:
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


def _pair_score(player1, player2):
    """Score pairing quality (higher is better)."""
    score = 100

    # Prefer similar RMS when available
    if player1.get('rms') is not None and player2.get('rms') is not None:
        rms_diff = abs(player1['rms'] - player2['rms'])
        score += max(0, 20 - rms_diff * 3)

    # Prefer same/adjacent bands
    band_diff = abs(player1.get('band_order', 0) - player2.get('band_order', 0))
    score += max(0, 30 - band_diff * 10)

    return score


def _find_best_fresh_pairs(players, blocked_set, all_time_pairs):
    """
    Exact fresh-pair solver for small leagues.

    Finds a maximum-cardinality matching using only non-repeat, non-blocked edges.
    Tiebreak: highest total score.

    Returns:
      (pair_idx_list, unpaired_idx_list) where pair_idx_list is [(i, j), ...]
    """
    n = len(players)
    if n == 0:
        return [], []

    # Keep search bounded to avoid pathological explosion on very large leagues.
    if n > 20:
        return None, None

    neighbors = [[] for _ in range(n)]
    edge_score = {}
    for i in range(n):
        for j in range(i + 1, n):
            p1 = players[i]
            p2 = players[j]
            if (p1['id'], p2['id']) in blocked_set:
                continue
            key = frozenset([p1['id'], p2['id']])
            if key in all_time_pairs:
                continue  # Fresh pass only
            s = _pair_score(p1, p2)
            neighbors[i].append(j)
            neighbors[j].append(i)
            edge_score[(i, j)] = s
            edge_score[(j, i)] = s

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def solve(mask):
        # Returns tuple: (pair_count, score_sum, pairs_tuple, unpaired_tuple)
        if mask == 0:
            return (0, 0, tuple(), tuple())

        # Pick the unpaired player with the fewest available partners in mask
        bits = [idx for idx in range(n) if mask & (1 << idx)]
        best_i = None
        best_degree = 10**9
        for idx in bits:
            deg = 0
            for nb in neighbors[idx]:
                if mask & (1 << nb):
                    deg += 1
            if deg < best_degree:
                best_degree = deg
                best_i = idx

        i = best_i
        best = None

        # Option A: leave i unmatched
        next_mask = mask & ~(1 << i)
        a_cnt, a_score, a_pairs, a_unpaired = solve(next_mask)
        best = (a_cnt, a_score, a_pairs, tuple(sorted((i,) + a_unpaired)))

        # Option B: pair i with each eligible j
        # Highest-score edges first to reduce search churn.
        candidates = [j for j in neighbors[i] if mask & (1 << j)]
        candidates.sort(key=lambda j: edge_score[(i, j)], reverse=True)

        for j in candidates:
            pair_mask = mask & ~(1 << i) & ~(1 << j)
            c_cnt, c_score, c_pairs, c_unpaired = solve(pair_mask)
            c_cnt += 1
            c_score += edge_score[(i, j)]
            c_pairs = tuple(sorted(((min(i, j), max(i, j)),) + c_pairs))
            candidate = (c_cnt, c_score, c_pairs, c_unpaired)

            # Max pairs first, then score.
            if (candidate[0] > best[0]) or (candidate[0] == best[0] and candidate[1] > best[1]):
                best = candidate

        return best

    full_mask = (1 << n) - 1
    pair_count, _score, pairs, unpaired = solve(full_mask)

    # Safety: ensure no duplicates in output
    used = set()
    pair_idx_list = []
    for i, j in pairs:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        pair_idx_list.append((i, j))

    unpaired_idx = [idx for idx in range(n) if idx not in used]
    return pair_idx_list, unpaired_idx


def generate_pairings(players, blocked_pairs, all_assignments, all_matches):
    """
    Generate optimal pairings using exhaustion-first matching.

    Algorithm:
    1. Calculate RMS for each player
    2. Group players by performance band
    3. Pass 1: treat ALL previously-paired players as blocked — pair everyone fresh
    4. Pass 2: for any player who couldn't be paired fresh, allow repeats (oldest first)
    5. Handle odd player by removing admin flex or floating to adjacent band

    Args:
        players: List of eligible players
        blocked_pairs: List of hard-blocked pairs (wouldn't play again)
        all_assignments: ALL historical match assignments (for exhaustion check)
        all_matches: All matches with scores (for RMS calculation)

    Returns:
        tuple: (pairings, skipped, forced_repeats)
            forced_repeats: set of frozenset pair keys that were unavoidable repeats
    """
    # Filter to only available players
    available_players = [p for p in players if is_player_available(p)]

    if len(available_players) < 2:
        return [], available_players, set()

    # Calculate RMS for each player and add to player dict
    for player in available_players:
        rms = calculate_rms(player['id'], all_matches)
        player['rms'] = rms
        band, band_order = get_performance_band(rms)
        player['band'] = band
        player['band_order'] = band_order

    # Convert hard-blocked pairs to a set for O(1) lookup
    blocked_set = set()
    for bp in blocked_pairs:
        blocked_set.add((bp['player_a'], bp['player_b']))
        blocked_set.add((bp['player_b'], bp['player_a']))

    # Build all-time pair history from BOTH assignments AND logged matches.
    # match_assignments covers formal monthly pairings; matches covers extra matches
    # logged via "Log Extra Match" (which don't create assignments). Without both,
    # players who played a pickup game can get formally paired with the same person.
    all_time_pairs = {}
    for m in all_assignments:
        key = frozenset([m['player1_id'], m['player2_id']])
        if key not in all_time_pairs:
            all_time_pairs[key] = m.get('period_label', '')
    for m in all_matches:
        key = frozenset([m['player1_id'], m['player2_id']])
        if key not in all_time_pairs:
            all_time_pairs[key] = m.get('period_label', '')

    # Handle odd number of players - remove admin flex with alternating rotation
    # Ashley sits out on odd months (Jan, Mar, May, Jul, Sep, Nov)
    # Natalie sits out on even months (Feb, Apr, Jun, Aug, Oct, Dec)
    if len(available_players) % 2 == 1:
        natalie = next((p for p in available_players if p.get('email', '').lower() == 'nmcoffen@gmail.com'), None)
        ashley = next((p for p in available_players if p.get('email', '').lower() == 'ashleybrooke.kaufman@gmail.com'), None)

        current_month = datetime.now().month
        is_odd_month = current_month % 2 == 1

        removed_player = None
        if is_odd_month:
            if ashley:
                available_players.remove(ashley)
                removed_player = ashley
            elif natalie:
                available_players.remove(natalie)
                removed_player = natalie
        else:
            if natalie:
                available_players.remove(natalie)
                removed_player = natalie
            elif ashley:
                available_players.remove(ashley)
                removed_player = ashley

        if not removed_player:
            available_players.sort(key=lambda p: (p.get('rank') or 999, p.get('band_order') or 0))
            removed_player = available_players.pop()

        skipped = [removed_player] if removed_player else []
    else:
        skipped = []

    pairings = []
    unpaired = []
    forced_repeats = set()

    # Pass 1: exact fresh matching for small/medium leagues.
    # If a no-repeat full pairing exists, this finds it.
    # Fallback to deterministic greedy if league size is larger than solver bound.
    available_players.sort(key=lambda p: (p.get('rank') or 999, str(p.get('id'))))
    exact_pairs, exact_unpaired = _find_best_fresh_pairs(available_players, blocked_set, all_time_pairs)

    if exact_pairs is not None:
        for i, j in exact_pairs:
            p1 = available_players[i]
            p2 = available_players[j]
            pairings.append({
                'player1': p1,
                'player2': p2,
                'player1_availability': get_availability_text(p1),
                'player2_availability': get_availability_text(p2),
                'score': _pair_score(p1, p2),
                'band': p1['band'] if p1['band'] == p2['band'] else f"cross-band ({p1['band']} + {p2['band']})"
            })
        unpaired = [available_players[idx] for idx in exact_unpaired]
    else:
        # Deterministic fallback (large league): greedy fresh first.
        working = list(available_players)
        while len(working) >= 2:
            player1 = working.pop(0)
            best_idx = None
            best_score = -999
            for i, player2 in enumerate(working):
                if (player1['id'], player2['id']) in blocked_set:
                    continue
                pair_key = frozenset([player1['id'], player2['id']])
                if pair_key in all_time_pairs:
                    continue
                score = _pair_score(player1, player2)
                if score > best_score:
                    best_score = score
                    best_idx = i

            if best_idx is not None:
                player2 = working.pop(best_idx)
                pairings.append({
                    'player1': player1,
                    'player2': player2,
                    'player1_availability': get_availability_text(player1),
                    'player2_availability': get_availability_text(player2),
                    'score': best_score,
                    'band': player1['band'] if player1['band'] == player2['band'] else f"cross-band ({player1['band']} + {player2['band']})"
                })
            else:
                unpaired.append(player1)
        unpaired.extend(working)

    # Pass 2: allow repeats for anyone still unpaired (exhausted all fresh options)
    while len(unpaired) >= 2:
        player1 = unpaired.pop(0)

        best_idx = None
        best_score = -999
        for i, player2 in enumerate(unpaired):
            if (player1['id'], player2['id']) in blocked_set:
                continue
            score = _pair_score(player1, player2)
            pair_key = frozenset([player1['id'], player2['id']])
            if pair_key in all_time_pairs:
                score -= 500  # Huge penalty but not impossible
            if score > best_score:
                best_score = score
                best_idx = i

        if best_idx is not None:
            player2 = unpaired.pop(best_idx)
            pair_key = frozenset([player1['id'], player2['id']])
            if pair_key in all_time_pairs:
                forced_repeats.add(pair_key)
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

    skipped.extend(unpaired)

    return pairings, skipped, forced_repeats


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
        """Get pairings for a given period (defaults to current month)"""
        try:
            from api.supabase_http import table
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            period = params.get('period', [datetime.now().strftime('%B %Y')])[0]

            # Get match assignments (without complex joins for simplicity)
            response = table('match_assignments')\
                .select('*')\
                .eq('period_label', period)\
                .execute()

            if response.data:
                # Get player IDs to look up player details
                player_ids = set()
                for p in response.data:
                    player_ids.add(p.get('player1_id'))
                    player_ids.add(p.get('player2_id'))

                # Get only fields needed by admin/pairings view (avoid leaking sensitive columns)
                players_result = table('players')\
                    .select('id, name, email, phone, skill_level, rank, membership_tier, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening')\
                    .execute()
                players_map = {pl['id']: pl for pl in players_result.data if pl['id'] in player_ids}

                def _public_pairing_player(player):
                    """Return only safe fields required for pairing coordination."""
                    return {
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'email': player.get('email'),
                        'phone': player.get('phone'),
                        'skill_level': player.get('skill_level'),
                        'rank': player.get('rank'),
                        'membership_tier': player.get('membership_tier', 'player'),
                        'avail_weekday_early': player.get('avail_weekday_early', False),
                        'avail_weekday_day': player.get('avail_weekday_day', False),
                        'avail_weekday_late': player.get('avail_weekday_late', False),
                        'avail_weekend_early': player.get('avail_weekend_early', False),
                        'avail_weekend_day': player.get('avail_weekend_day', False),
                        'avail_weekend_late': player.get('avail_weekend_late', False),
                        'available_morning': player.get('available_morning', False),
                        'available_afternoon': player.get('available_afternoon', False),
                        'available_evening': player.get('available_evening', False),
                    }

                pairings_with_availability = []
                for p in response.data:
                    p1 = players_map.get(p.get('player1_id'), {})
                    p2 = players_map.get(p.get('player2_id'), {})
                    p['player1'] = _public_pairing_player(p1)
                    p['player2'] = _public_pairing_player(p2)
                    p['player1_availability'] = get_availability_text(p1)
                    p['player2_availability'] = get_availability_text(p2)
                    pairings_with_availability.append(p)

                self._send_success({
                    'period': period,
                    'pairings': pairings_with_availability,
                    'count': len(response.data)
                })
            else:
                self._send_success({
                    'period': period,
                    'pairings': [],
                    'count': 0
                })

        except Exception as e:
            print(f"Pairings GET error: {e}")
            self._send_error(500, "An unexpected error occurred")

    def do_POST(self):
        """Generate new pairings for current or specified month"""
        self._run_id = None
        self._run_action = 'generate_pairings'
        self._run_period = None
        try:
            from api.supabase_http import table

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            # Auth check: CRON_SECRET required (GitHub Actions or admin dashboard)
            cron_secret = os.environ.get('CRON_SECRET', '')
            if cron_secret:
                auth = self.headers.get('Authorization', '').replace('Bearer ', '')
                if auth != cron_secret:
                    self._send_error(401, 'Unauthorized')
                    return

            period_label = data.get('period_label', datetime.now().strftime('%B %Y'))
            period_type = data.get('period_type', 'month')
            self._run_period = period_label

            run_id, lock_error = try_start_run('generate_pairings', period_label, {
                'source': 'api/pairings',
                'period_type': period_type,
            })
            self._run_id = run_id
            if lock_error:
                self._send_error(409, lock_error)
                return

            ok, preflight_details = preflight(
                required_env=['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'RESEND_API_KEY'],
                check_db=True
            )
            if not ok:
                append_event(self._run_id, 'preflight', 'error', 'Preflight failed', preflight_details)
                self._send_error(500, f"Preflight failed: {preflight_details}")
                return
            append_event(self._run_id, 'preflight', 'info', 'Preflight passed', preflight_details)

            # 1. Get all active Players (exclude Social Butterflies and admin)
            admin_email = os.environ.get('ADMIN_EMAIL', 'khamel@khamel.com')
            players_resp = table('players')\
                .select('id, name, email, phone, skill_level, rank, is_active, unavailable_until, membership_tier, rms_score, rms_band, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening')\
                .eq('is_active', True)\
                .neq('membership_tier', 'social_butterfly')\
                .neq('email', admin_email)\
                .order('rank', nulls='last')\
                .execute()
            if players_resp.error:
                self._send_error(500, f"Failed to load players: {players_resp.error}")
                return
            if not players_resp.data:
                self._send_error(500, "No active players found — cannot generate pairings")
                return
            players = players_resp.data

            # 2. Get blocked pairs (from "would not play again" feedback)
            blocked_resp = table('match_feedback')\
                .select('from_player_id, about_player_id')\
                .eq('would_play_again', False)\
                .execute()
            if blocked_resp.error:
                self._send_error(500, f"Failed to load blocked pairs: {blocked_resp.error}")
                return
            blocked_pairs = []
            for b in blocked_resp.data:
                blocked_pairs.append({
                    'player_a': min(b['from_player_id'], b['about_player_id']),
                    'player_b': max(b['from_player_id'], b['about_player_id'])
                })

            # 3. Get ALL historical match assignments (exhaustion-first algorithm needs full history)
            # NOTE: match_assignments uses 'assigned_at', not 'created_at'
            history_resp = table('match_assignments')\
                .select('player1_id, player2_id, period_label, assigned_at')\
                .order('assigned_at', desc=True)\
                .execute()
            if history_resp.error:
                # Hard stop — never generate pairings without knowing full pairing history
                self._send_error(500, f"Failed to load match history: {history_resp.error}")
                return
            all_assignments = history_resp.data

            # 4. Get all matches with scores (for RMS calculation)
            all_matches_resp = table('matches')\
                .select('player1_id, player2_id, set1_p1, set1_p2, set2_p1, set2_p2')\
                .order('created_at', desc=True)\
                .limit(500)\
                .execute()
            if all_matches_resp.error:
                self._send_error(500, f"Failed to load match scores: {all_matches_resp.error}")
                return
            all_matches = all_matches_resp.data

            # 5. Generate pairings using exhaustion-first algorithm
            pairings, skipped, forced_repeats = generate_pairings(players, blocked_pairs, all_assignments, all_matches)

            # 6. Validation gate — runs before any DB write or email
            # Step 6a: No duplicate players
            seen_players = set()
            for p in pairings:
                for pid in [p['player1']['id'], p['player2']['id']]:
                    if pid in seen_players:
                        self._send_error(500, f"Duplicate player in assignments — aborting before save")
                        return
                    seen_players.add(pid)

            # Step 6b: No avoidable repeats (check both assignments AND logged matches)
            all_time_pairs = {}
            for m in all_assignments:
                key = frozenset([m['player1_id'], m['player2_id']])
                if key not in all_time_pairs:
                    all_time_pairs[key] = m.get('period_label', '')
            for m in all_matches:
                key = frozenset([m['player1_id'], m['player2_id']])
                if key not in all_time_pairs:
                    all_time_pairs[key] = m.get('period_label', '')
            for p in pairings:
                key = frozenset([p['player1']['id'], p['player2']['id']])
                if key in all_time_pairs and key not in forced_repeats:
                    self._send_error(500,
                        f"Avoidable repeat detected: {p['player1']['name']} + {p['player2']['name']} — aborting")
                    return

            # Step 6c: No existing pairings for this period (duplicate-run protection)
            existing_resp = table('match_assignments').select('id').eq('period_label', period_label).execute()
            if existing_resp.error:
                self._send_error(500, f"Failed to check existing assignments: {existing_resp.error}")
                return
            if existing_resp.data:
                self._send_error(409, f"Pairings for {period_label} already exist ({len(existing_resp.data)} assignments) — aborting to prevent duplicates")
                return

            # Step 6d: Build and insert assignments
            assignments = []
            for p in pairings:
                assignments.append({
                    'player1_id': p['player1']['id'],
                    'player2_id': p['player2']['id'],
                    'period_type': period_type,
                    'period_label': period_label,
                    'status': 'pending'
                })

            if not assignments:
                self._send_error(500, "No valid pairings generated")
                return

            insert_resp = table('match_assignments').insert(assignments).execute()
            if insert_resp.error:
                self._send_error(500, f"DB insert failed: {insert_resp.error}")
                return

            # Step 6e: Verify insert by re-querying
            confirm_resp = table('match_assignments').select('id, player1_id, player2_id').eq('period_label', period_label).execute()
            if confirm_resp.error or len(confirm_resp.data) != len(assignments):
                self._send_error(500,
                    f"Insert verification failed: expected {len(assignments)}, found {len(confirm_resp.data) if not confirm_resp.error else confirm_resp.error}")
                return
            # Build lookup map for email tracking: frozenset of player IDs -> assignment ID
            assignment_id_map = {
                frozenset([a['player1_id'], a['player2_id']]): a['id']
                for a in confirm_resp.data
            }

            # 7. Send match assignment emails — only reached after all validation passes
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
                    # Reply-to first player so they can coordinate
                    reply_to = p1['email']
                    result = send_email(
                        [p1['email'], p2['email']],
                        subject,
                        html,
                        reply_to=reply_to
                    )
                    if result.get('success'):
                        emails_sent += 1
                        # Track email ID in match_assignments and universal email_log
                        assignment_id = assignment_id_map.get(frozenset([p1['id'], p2['id']]))
                        if assignment_id:
                            table('match_assignments').update({
                                'match_email_id': result.get('id'),
                            }).eq('id', assignment_id).execute()
                            table('email_log').insert({
                                'action': 'generate_pairings',
                                'to_emails': [p1['email'], p2['email']],
                                'period_label': period_label,
                                'match_id': assignment_id,
                                'resend_email_id': result.get('id'),
                            }).execute()
                    else:
                        email_errors.append(f"{p1['name']} & {p2['name']}: {result.get('error')}")
                        # Continue to attempt all remaining pairings (no break)
            except Exception as e:
                email_errors.append(f"Email system error: {str(e)}")

            if email_errors:
                append_event(self._run_id, 'email_delivery', 'error', 'Match email delivery failed', {
                    'emails_sent': emails_sent,
                    'pairings_created': len(assignments),
                    'errors': email_errors,
                })
                self._send_error(500, f"Email delivery failed: {emails_sent}/{len(assignments)} sent: {email_errors[0]}",
                                 extra={"sent": emails_sent, "failed": len(email_errors), "errors": email_errors})
                return

            if emails_sent != len(assignments):
                append_event(self._run_id, 'postcheck', 'error', 'Postcheck failed: sent count mismatch', {
                    'emails_sent': emails_sent,
                    'pairings_created': len(assignments),
                })
                self._send_error(500, f"Postcheck failed: sent {emails_sent} emails for {len(assignments)} pairings")
                return

            # 8. Update RMS scores for all players
            for player in players:
                update_player_rms(player['id'], all_matches)

            append_event(self._run_id, 'postcheck', 'info', 'Pairings run completed', {
                'pairings_created': len(assignments),
                'emails_sent': emails_sent,
            })
            update_run(self._run_id, 'succeeded', summary={
                'period': period_label,
                'pairings_created': len(assignments),
                'emails_sent': emails_sent,
            })
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
            print(f"Pairings POST error: {e}")
            append_event(self._run_id, 'exception', 'error', 'Unhandled exception', {'error': str(e)})
            self._send_error(500, "An unexpected error occurred")

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": True, **data}
        run_id = getattr(self, '_run_id', None)
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())

    def _send_error(self, status, message, extra=None):
        run_id = getattr(self, '_run_id', None)
        if run_id:
            append_event(run_id, 'error', 'error', message, {
                'status': status,
                'action': getattr(self, '_run_action', None),
                'period': getattr(self, '_run_period', None),
            })
            update_run(run_id, 'failed_terminal', error={
                'status': status,
                'message': message,
            })

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": False, "error": message}
        if extra:
            payload.update(extra)
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())
