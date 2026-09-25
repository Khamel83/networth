"""
Vercel Serverless Function: Admin API
Full player management for league administrators.

Endpoints:
- GET: List all players, pairings, or single player details
- POST: Update any player's info, pause/activate players

Only accessible to users with is_admin=true in the database.
Uses password-based auth (no Supabase Auth).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
init_sentry()


def get_player_by_email(email):
    """Get player from database by email (password-based auth)"""
    from api.supabase_http import table

    if not email:
        return None

    try:
        result = table('players').select('*').eq('email', email.lower()).single().execute()
        if result.data:
            return result.data[0] if isinstance(result.data, list) else result.data
    except Exception:
        pass
    return None


def verify_admin(email):
    """Check if the user is an admin"""
    if not email:
        return False
    try:
        player = get_player_by_email(email)
        return player and player.get('is_admin', False)
    except Exception:
        return False


def get_next_month_first():
    """Get the first day of next month"""
    today = date.today()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def _pair_key(a, b):
    return tuple(sorted((str(a), str(b))))


def _match_view(m):
    """Admin-facing summary of a stored match row."""
    return {
        'id': m.get('id'),
        'player1_id': m.get('player1_id'),
        'player2_id': m.get('player2_id'),
        'set1_p1': m.get('set1_p1'), 'set1_p2': m.get('set1_p2'),
        'set2_p1': m.get('set2_p1'), 'set2_p2': m.get('set2_p2'),
        'player1_games': m.get('player1_games'),
        'player2_games': m.get('player2_games'),
        'is_forfeit': bool(m.get('is_forfeit')),
        'period_label': m.get('period_label'),
    }


def _games_credit(m):
    """Games the update_player_games() trigger credited for a match row."""
    if not m:
        return 0, 0
    if m.get('is_forfeit'):
        return 6, 0
    return int(m.get('player1_games') or 0), int(m.get('player2_games') or 0)


def build_period_data(period):
    """Pairings, recorded scores, and extra matches for one period label.

    Returns (data, error). Every query is checked so a failed read is never
    shown to admins as "no matches".
    """
    from api.supabase_http import table

    assignments = table('match_assignments').select('*').eq('period_label', period).execute()
    if assignments.error:
        return None, f"Failed to fetch pairings: {assignments.error}"
    matches = table('matches').select('*').eq('period_label', period).execute()
    if matches.error:
        return None, f"Failed to fetch matches: {matches.error}"
    players = table('players').select('id, name, email, phone').execute()
    if players.error:
        return None, f"Failed to fetch player details: {players.error}"

    players_map = {p['id']: p for p in players.data}
    matches_by_id = {m.get('id'): m for m in matches.data}
    matches_by_pair = {_pair_key(m.get('player1_id'), m.get('player2_id')): m for m in matches.data}
    used_match_ids = set()

    pairings = []
    for pairing in assignments.data:
        p1 = players_map.get(pairing.get('player1_id'), {})
        p2 = players_map.get(pairing.get('player2_id'), {})
        match = matches_by_id.get(pairing.get('match_id')) or matches_by_pair.get(
            _pair_key(pairing.get('player1_id'), pairing.get('player2_id'))
        )
        if match:
            used_match_ids.add(match.get('id'))
        pairings.append({
            'id': pairing.get('id'),
            'player1_id': pairing.get('player1_id'),
            'player1_name': p1.get('name', 'Unknown'),
            'player1_email': p1.get('email', ''),
            'player1_phone': p1.get('phone', ''),
            'player2_id': pairing.get('player2_id'),
            'player2_name': p2.get('name', 'Unknown'),
            'player2_email': p2.get('email', ''),
            'player2_phone': p2.get('phone', ''),
            'status': pairing.get('status', 'pending'),
            'period_label': pairing.get('period_label'),
            'match': _match_view(match) if match else None,
        })

    extra_matches = []
    for m in matches.data:
        if m.get('id') in used_match_ids:
            continue
        view = _match_view(m)
        view['player1_name'] = players_map.get(m.get('player1_id'), {}).get('name', 'Unknown')
        view['player2_name'] = players_map.get(m.get('player2_id'), {}).get('name', 'Unknown')
        extra_matches.append(view)

    return {'period': period, 'pairings': pairings, 'extra_matches': extra_matches}, None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get admin data: players list, pairings, or single player"""
        try:
            from api.supabase_http import table
            from api.auth import verify_session

            token = self.headers.get('Authorization', '').replace('Bearer ', '').strip()
            email = verify_session(token)
            if not email:
                self._send_error(401, "Invalid or expired session")
                return

            if not verify_admin(email):
                self._send_error(403, "Admin access required")
                return

            # Explicit column list — never return password fields
            ADMIN_COLUMNS = (
                'id,name,email,phone,skill_level,rank,total_games,matches_played,'
                'trend,is_active,is_admin,membership_tier,has_paid,avatar_url,'
                'unavailable_until,avail_weekday_early,avail_weekday_day,avail_weekday_late,'
                'avail_weekend_early,avail_weekend_day,avail_weekend_late,rms_score,rms_band'
            )

            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            action = params.get('action', ['players'])[0]

            if action == 'players':
                result = table('players').select(ADMIN_COLUMNS).order('rank').execute()
                if result.error:
                    self._send_error(500, f"Failed to fetch players: {result.error}")
                    return
                players = []
                for p in result.data:
                    unavailable_until = p.get('unavailable_until')
                    is_paused = False
                    if unavailable_until:
                        if isinstance(unavailable_until, str):
                            pause_date = date.fromisoformat(unavailable_until.split('T')[0])
                        else:
                            pause_date = unavailable_until
                        is_paused = pause_date > date.today()

                    players.append({
                        'id': p.get('id'),
                        'name': p.get('name'),
                        'email': p.get('email'),
                        'phone': p.get('phone'),
                        'skill_level': p.get('skill_level'),
                        'rank': p.get('rank'),
                        'total_games': p.get('total_games', 0),
                        'matches_played': p.get('matches_played', 0),
                        'is_active': p.get('is_active', True),
                        'is_admin': p.get('is_admin', False),
                        'is_paused': is_paused,
                        'unavailable_until': str(unavailable_until) if unavailable_until else None,
                        'membership_tier': p.get('membership_tier', 'player'),
                        'has_paid': p.get('has_paid', False),
                        'available_morning': p.get('available_morning', True),
                        'available_afternoon': p.get('available_afternoon', True),
                        'available_evening': p.get('available_evening', True),
                        'avail_weekday_early': p.get('avail_weekday_early', False),
                        'avail_weekday_day': p.get('avail_weekday_day', False),
                        'avail_weekday_late': p.get('avail_weekday_late', False),
                        'avail_weekend_early': p.get('avail_weekend_early', False),
                        'avail_weekend_day': p.get('avail_weekend_day', False),
                        'avail_weekend_late': p.get('avail_weekend_late', False),
                    })

                self._send_success({'players': players})

            elif action == 'pairings':
                # Pairings with recorded scores for a period
                # Supports optional 'period' query param (e.g., "January 2026")
                # Default: current month
                period = params.get('period', [date.today().strftime('%B %Y')])[0]
                period_data, error = build_period_data(period)
                if error:
                    self._send_error(500, error)
                    return
                self._send_success(period_data)

            elif action == 'report':
                # Monthly report: results, unreported matches, standings, unpaid members
                period = params.get('period', [date.today().strftime('%B %Y')])[0]
                period_data, error = build_period_data(period)
                if error:
                    self._send_error(500, error)
                    return
                roster_columns = 'id,name,email,total_games,matches_played,is_active,membership_tier,has_paid'
                roster = table('players').select(roster_columns + ',reported_paid,reported_paid_at')\
                    .eq('is_active', True).order('total_games', desc=True, nulls='last').execute()
                reported_paid_tracked = not roster.error
                if roster.error:
                    # migrations/05_reported_paid.sql not applied yet: report without it
                    print(f"Report roster without reported_paid: {roster.error}")
                    roster = table('players').select(roster_columns)\
                        .eq('is_active', True).order('total_games', desc=True, nulls='last').execute()
                if roster.error:
                    self._send_error(500, f"Failed to fetch roster: {roster.error}")
                    return
                pairings = period_data['pairings']
                reported = [p for p in pairings if p['match']]

                # Games won in the selected month, from that month's match rows
                month_games = {}
                names = {}
                for p in pairings:
                    names[p['player1_id']] = p['player1_name']
                    names[p['player2_id']] = p['player2_name']
                month_matches = [p['match'] for p in reported] + period_data['extra_matches']
                for m in period_data['extra_matches']:
                    names[m['player1_id']] = m['player1_name']
                    names[m['player2_id']] = m['player2_name']
                for m in month_matches:
                    g1, g2 = _games_credit(m)
                    for pid, games in ((m['player1_id'], g1), (m['player2_id'], g2)):
                        entry = month_games.setdefault(pid, {'games': 0, 'matches': 0})
                        entry['games'] += games
                        entry['matches'] += 1
                month_ranked = sorted(month_games.items(), key=lambda kv: (-kv[1]['games'], names.get(kv[0]) or ''))
                standings = [
                    {'rank': i + 1, 'name': names.get(pid, 'Unknown'),
                     'total_games': v['games'], 'matches_played': v['matches']}
                    for i, (pid, v) in enumerate(month_ranked)
                ]
                # Cumulative season standings as of today (not historical)
                season_standings = [
                    {'rank': i + 1, 'name': p.get('name'), 'total_games': p.get('total_games') or 0,
                     'matches_played': p.get('matches_played') or 0}
                    for i, p in enumerate(r for r in roster.data if r.get('membership_tier') == 'player')
                ]
                unpaid = [
                    {'name': p.get('name'), 'email': p.get('email'),
                     'membership_tier': p.get('membership_tier'),
                     'reported_paid': bool(p.get('reported_paid')) if reported_paid_tracked else None,
                     'reported_paid_at': p.get('reported_paid_at')}
                    for p in roster.data
                    if not p.get('has_paid') and p.get('membership_tier') != 'admin'
                ]
                self._send_success({
                    **period_data,
                    'summary': {
                        'pairings': len(pairings),
                        'reported': len(reported),
                        'unreported': len(pairings) - len(reported),
                        'extra_matches': len(period_data['extra_matches']),
                        'active_members': len(roster.data),
                        'unpaid_members': len(unpaid),
                        'unpaid_says_paid': sum(1 for p in unpaid if p['reported_paid']),
                    },
                    'unreported': [p for p in pairings if not p['match']],
                    'standings': standings,
                    'season_standings': season_standings,
                    'reported_paid_tracked': reported_paid_tracked,
                    'unpaid': unpaid,
                })

            elif action == 'player':
                # Get single player details
                player_id = params.get('id', [None])[0]
                if not player_id:
                    self._send_error(400, "Player ID required")
                    return

                result = table('players').select(ADMIN_COLUMNS).eq('id', player_id).single().execute()
                if result.error:
                    self._send_error(500, f"Failed to fetch player: {result.error}")
                    return
                if not result.data:
                    self._send_error(404, "Player not found")
                    return

                player_data = result.data[0] if isinstance(result.data, list) else result.data
                self._send_success({'player': player_data})

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            print(f"Admin error: {e}")
            self._send_error(500, "An unexpected error occurred")

    def do_POST(self):
        """Admin actions: update player, pause/activate, etc."""
        try:
            from api.supabase_http import table

            from api.auth import verify_session
            token = self.headers.get('Authorization', '').replace('Bearer ', '').strip()
            email = verify_session(token)
            if not email:
                self._send_error(401, "Invalid or expired session")
                return

            if not verify_admin(email):
                self._send_error(403, "Admin access required")
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action')
            player_id = data.get('player_id')

            if action == 'record_score':
                return self._record_score(data)
            if action == 'update_score':
                return self._update_score(data)

            if not player_id:
                self._send_error(400, "player_id required")
                return

            # Verify player exists
            player = table('players').select('id, name, email').eq('id', player_id).single().execute()
            if player.error:
                self._send_error(500, f"Failed to fetch player for verification: {player.error}")
                return
            if not player.data:
                self._send_error(404, "Player not found")
                return

            player_data = player.data[0] if isinstance(player.data, list) else player.data
            updates = {}

            if action == 'update':
                # Update player fields
                allowed_fields = ['name', 'email', 'phone', 'skill_level', 'is_active', 'membership_tier']
                for field in allowed_fields:
                    if field in data:
                        updates[field] = data[field]

                # Handle availability (new format)
                avail_fields = [
                    'avail_weekday_early', 'avail_weekday_day', 'avail_weekday_late',
                    'avail_weekend_early', 'avail_weekend_day', 'avail_weekend_late'
                ]
                for field in avail_fields:
                    if field in data:
                        updates[field] = bool(data[field])

                # Handle legacy availability format
                if 'availability' in data:
                    avail = data['availability']
                    if 'morning' in avail:
                        updates['available_morning'] = bool(avail['morning'])
                    if 'afternoon' in avail:
                        updates['available_afternoon'] = bool(avail['afternoon'])
                    if 'evening' in avail:
                        updates['available_evening'] = bool(avail['evening'])

            elif action == 'pause':
                # Pause player for rest of month
                updates['unavailable_until'] = str(get_next_month_first())

            elif action == 'unpause':
                # Remove pause
                updates['unavailable_until'] = None

            elif action == 'activate' or action == 'approve':
                # Approve/activate player (after Venmo verification)
                updates['is_active'] = True

            elif action == 'deactivate':
                # Deactivate player (soft delete)
                updates['is_active'] = False

            elif action == 'reject':
                # Reject player signup - deactivate (RLS blocks deletes)
                reject_result = table('players').update({'is_active': False}).eq('id', player_id).execute()
                if reject_result.error:
                    self._send_error(500, f"Failed to reject player: {reject_result.error}")
                    return
                self._send_success({
                    'message': f"Player {player_data.get('name')} rejected",
                    'rejected': True
                })
                return

            elif action == 'update_payment':
                # Toggle payment status
                has_paid = data.get('has_paid', False)
                payment_result = table('players').update({'has_paid': has_paid}).eq('id', player_id).execute()
                if payment_result.error:
                    self._send_error(500, f"Failed to update payment status: {payment_result.error}")
                    return
                self._send_success({
                    'message': f"Payment status updated for {player_data.get('name')}",
                    'has_paid': has_paid
                })
                return

            elif action == 'update_games':
                # Admin fix for total_games (e.g., correcting doubled scores)
                total_games = data.get('total_games')
                if total_games is None:
                    self._send_error(400, "total_games required")
                    return
                games_result = table('players').update({'total_games': int(total_games)}).eq('id', player_id).execute()
                if games_result.error:
                    self._send_error(500, f"Failed to update games count: {games_result.error}")
                    return
                self._send_success({
                    'message': f"Games updated for {player_data.get('name')}",
                    'total_games': int(total_games)
                })
                return

            else:
                self._send_error(400, f"Unknown action: {action}")
                return

            if updates:
                update_result = table('players').update(updates).eq('id', player_id).execute()
                if update_result.error:
                    self._send_error(500, f"Failed to apply player updates: {update_result.error}")
                    return

            # Return updated player
            updated = table('players').select('*').eq('id', player_id).single().execute()
            if updated.error:
                self._send_error(500, f"Failed to fetch updated player: {updated.error}")
                return
            updated_data = updated.data[0] if isinstance(updated.data, list) else updated.data

            self._send_success({
                'message': f"Player updated ({action})",
                'player': updated_data
            })

        except Exception as e:
            print(f"Admin error: {e}")
            self._send_error(500, "An unexpected error occurred")

    def _record_score(self, data):
        """Admin records a score for any two players (assigned or extra match)."""
        from api.supabase_http import table
        from api.matches import (
            calculate_two_set_games, parse_admin_set_scores, is_duplicate_match_error,
            find_assignment, close_assignment, recover_duplicate,
        )

        player1_id = data.get('player1_id')
        player2_id = data.get('player2_id')
        period = (data.get('period_label') or '').strip() or date.today().strftime('%B %Y')
        if not player1_id or not player2_id or str(player1_id) == str(player2_id):
            self._send_error(400, "Choose two different players")
            return
        scores, error = parse_admin_set_scores(data)
        if error:
            self._send_error(400, error)
            return

        # Resolve and validate the pairing before writing anything
        assignment, error = find_assignment(table, player1_id, player2_id, period, data.get('assignment_id'))
        if error:
            self._send_error(400, error)
            return

        player1_games, player2_games = calculate_two_set_games(
            scores['set1_p1'], scores['set1_p2'], scores['set2_p1'], scores['set2_p2']
        )
        match_data = {
            'player1_id': player1_id,
            'player2_id': player2_id,
            **scores,
            'player1_games': player1_games,
            'player2_games': player2_games,
            'period_type': 'month',
            'period_label': period,
            'is_forfeit': False,
        }
        # Insert fires update_player_games(), which adds both players' games
        inserted = table('matches').insert(match_data).execute()
        if inserted.error:
            print(f"Admin record_score insert failed: {inserted.error}")
            if is_duplicate_match_error(inserted.error):
                # Finish closing the pairing if an earlier attempt stopped half way
                closed = recover_duplicate(table, player1_id, player2_id, period, assignment)
                self._send_error(409, "A score for these two players is already recorded for this month"
                                 + (" (pairing now marked completed)" if closed else "") + ". Use Edit to change it.")
            else:
                self._send_error(500, "Failed to save the score")
            return
        if len(inserted.data or []) != 1:
            print(f"Admin record_score insert returned {len(inserted.data or [])} rows")
            self._send_error(500, "Failed to save the score")
            return
        match = inserted.data[0]

        # Close out the pairing so the players stop seeing it as pending
        if assignment:
            close_error = close_assignment(table, assignment['id'], match.get('id'))
            if close_error:
                print(f"Admin score saved but pairing not closed: {close_error}")
                self._send_error(500, "Score saved, but the pairing wasn't marked completed. Save again to finish.")
                return

        self._send_success({'message': 'Score recorded', 'match': _match_view(match)})

    def _update_score(self, data):
        """Admin corrects an existing score and adjusts both players' totals.

        The games trigger only runs on INSERT, so totals are adjusted here.
        Supabase REST has no multi-statement transaction, so every write is
        conditional on the value it read (optimistic locking) and earlier
        writes are rolled back if a later one fails. A concurrent edit gets a
        409 instead of a double-applied or partial adjustment.
        """
        from api.supabase_http import table
        from api.matches import calculate_two_set_games, parse_admin_set_scores

        match_id = data.get('match_id')
        if not match_id:
            self._send_error(400, "match_id required")
            return
        scores, error = parse_admin_set_scores(data)
        if error:
            self._send_error(400, error)
            return

        # Preferred path: one database transaction (migrations/06_admin_update_match_score.sql)
        from api.supabase_http import rpc, is_missing_function_error
        atomic = rpc('admin_update_match_score', {
            'p_match_id': match_id,
            'p_set1_p1': scores['set1_p1'], 'p_set1_p2': scores['set1_p2'],
            'p_set2_p1': scores['set2_p1'], 'p_set2_p2': scores['set2_p2'],
        })
        if not atomic.error:
            if len(atomic.data or []) != 1:
                self._send_error(500, "Failed to update match")
                return
            self._send_success({'message': 'Score updated', 'match': _match_view(atomic.data[0])})
            return
        if not is_missing_function_error(atomic.error):
            print(f"admin_update_match_score failed: {atomic.error}")
            if 'P0002' in str(atomic.error) or 'match not found' in str(atomic.error):
                self._send_error(404, "Match not found")
            else:
                self._send_error(500, "Failed to update match; nothing was changed")
            return
        print("admin_update_match_score not installed; using guarded REST fallback")

        existing = table('matches').select('*').eq('id', match_id).execute()
        if existing.error:
            self._send_error(500, f"Failed to fetch match: {existing.error}")
            return
        if not existing.data:
            self._send_error(404, "Match not found")
            return
        old = existing.data[0]

        player1_games, player2_games = calculate_two_set_games(
            scores['set1_p1'], scores['set1_p2'], scores['set2_p1'], scores['set2_p2']
        )
        new = {**scores, 'player1_games': player1_games, 'player2_games': player2_games, 'is_forfeit': False}
        old_fields = {k: old.get(k) for k in new}

        old_p1, old_p2 = _games_credit(old)
        deltas = [(old['player1_id'], player1_games - old_p1), (old['player2_id'], player2_games - old_p2)]

        # 1. Apply the player total changes, each conditional on the total we read
        applied = []

        def rollback_totals():
            for pid, before, after in reversed(applied):
                undone = table('players').update({'total_games': before})\
                    .eq('id', pid).eq('total_games', after).returning().execute()
                if undone.error or len(undone.data or []) != 1:
                    # Never silent: surface exactly what needs a manual fix
                    print(f"ROLLBACK FAILED: player {pid} total_games should be {before}, "
                          f"was set to {after} (match {match_id} unchanged)")

        for pid, delta in deltas:
            if not delta:
                continue
            current = table('players').select('id,total_games').eq('id', pid).execute()
            if current.error or not current.data:
                rollback_totals()
                self._send_error(500, "Failed to read player totals; nothing was changed")
                return
            before = int(current.data[0].get('total_games') or 0)
            after = max(before + delta, 0)
            adjusted = table('players').update({'total_games': after}).eq('id', pid).eq('total_games', before).returning().execute()
            if adjusted.error or len(adjusted.data or []) != 1:
                rollback_totals()
                self._send_error(409, "Player totals changed while saving; nothing was changed. Please try again.")
                return
            applied.append((pid, before, after))

        # 2. Update the match only if nobody else edited it since we read it
        update = table('matches').update(new).eq('id', match_id)
        for key, value in old_fields.items():
            if value is not None:
                update = update.eq(key, value)
        updated = update.returning().execute()
        if updated.error or len(updated.data or []) != 1:
            rollback_totals()
            if updated.error:
                self._send_error(500, "Failed to update match; nothing was changed")
            else:
                self._send_error(409, "This score was changed by someone else; nothing was changed. Reload and try again.")
            return

        self._send_success({'message': 'Score updated', 'match': _match_view({**old, **new})})

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
