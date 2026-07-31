"""Vercel Serverless Function: safe monthly pairing orchestration.

The rating and general-graph solver live in pure modules.  This file keeps the
HTTP boundary responsible for authentication, Supabase reads/writes, validation,
and the existing post-validation email path.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, date

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
from api.reliability import preflight, try_start_run, append_event, update_run
from api.matching import build_pairing_plan
init_sentry()


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


def _period_month(period_label):
    """Return the pairing period's month, falling back to the current month."""
    if period_label:
        try:
            return datetime.strptime(period_label.strip(), '%B %Y').month
        except (AttributeError, ValueError):
            pass
    return datetime.now().month


def generate_pairings(players, blocked_pairs, all_assignments, all_matches, period_label=None):
    """Generate a safe plan from a complete roster/history snapshot.

    The public return shape stays compatible with the existing handler/tests,
    while the actual work is delegated to the general-graph solver.  Admin
    flex is resolved before the solver so Natalie/Ashley remain the normal
    solution to an odd roster.
    """
    available_players = [player for player in players if is_player_available(player)]
    if len(available_players) < 2:
        return [], available_players, set()

    skipped = []
    if len(available_players) % 2 == 1:
        natalie = next(
            (p for p in available_players if p.get('email', '').lower() == 'nmcoffen@gmail.com'),
            None,
        )
        ashley = next(
            (p for p in available_players if p.get('email', '').lower() == 'ashleybrooke.kaufman@gmail.com'),
            None,
        )
        is_odd_month = _period_month(period_label) % 2 == 1
        removed_player = None
        if is_odd_month:
            removed_player = ashley or natalie
        else:
            removed_player = natalie or ashley
        if removed_player is None:
            removed_player = sorted(
                available_players,
                key=lambda p: (p.get('rank') or 999, str(p.get('id'))),
            )[-1]
        available_players.remove(removed_player)
        skipped.append(removed_player)

    plan = build_pairing_plan(
        available_players,
        assignment_history=all_assignments,
        canonical_matches=all_matches,
        hard_blocks=blocked_pairs,
        period_label=period_label,
        as_of=period_label,
    )
    skipped.extend(plan['unpaired'])
    return plan['pairings'], skipped, set(plan['forced_repeats'])


def _load_all_rows(table, table_name, columns, order_column, page_size=500):
    """Load a complete Supabase result in bounded PostgREST pages."""
    rows = []
    offset = 0
    while True:
        query = table(table_name).select(columns)
        if order_column:
            query = query.order(order_column, desc=True)
        range_method = getattr(query, 'range', None)
        if callable(range_method):
            response = range_method(offset, offset + page_size - 1).execute()
        else:
            # Compatibility with small test doubles and older local clients.
            response = query.execute()
        if response.error:
            return response
        page = response.data or []
        rows.extend(page)
        if not callable(range_method) or len(page) < page_size:
            break
        offset += page_size

    response.data = rows
    return response


def _load_all_match_scores(table, page_size=500):
    """Load the complete two-set score history in bounded pages."""
    columns = (
        'id, player1_id, player2_id, set1_p1, set1_p2, set2_p1, set2_p2, '
        'player1_games, player2_games, period_label, match_date, status, '
        'is_forfeit, created_at'
    )
    return _load_all_rows(table, 'matches', columns, 'created_at', page_size)


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

            action = data.get('action', 'generate')
            if action == 'clear_period':
                period_label = data.get('period_label')
                if not period_label:
                    self._send_error(400, 'period_label required for clear_period')
                    return
                # Clear FK references and run lock before deleting assignments
                table('email_log').delete().eq('period_label', period_label).execute()
                table('automation_runs').delete().eq('action', 'generate_pairings').eq('period_label', period_label).execute()
                del_resp = table('match_assignments').delete().eq('period_label', period_label).execute()
                if del_resp.error:
                    self._send_error(500, f"Delete failed: {del_resp.error}")
                    return
                self._send_success({"deleted": len(del_resp.data), "period": period_label})
                return

            dry_run = data.get('dry_run', False)
            period_label = data.get('period_label', datetime.now().strftime('%B %Y'))
            period_type = data.get('period_type', 'month')
            self._run_period = period_label

            run_id, lock_error = try_start_run('generate_pairings', period_label, {
                'source': 'api/pairings',
                'period_type': period_type,
            })
            self._run_id = run_id
            if lock_error and not dry_run:
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
                .select('id, name, email, phone, skill_level, rank, is_active, unavailable_until, membership_tier, avail_weekday_early, avail_weekday_day, avail_weekday_late, avail_weekend_early, avail_weekend_day, avail_weekend_late, available_morning, available_afternoon, available_evening')\
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

            # 2. Get every hard-block feedback row (from "would not play again")
            blocked_resp = _load_all_rows(
                table,
                'match_feedback',
                'from_player_id, about_player_id, would_play_again',
                'created_at',
            )
            if blocked_resp.error:
                self._send_error(500, f"Failed to load blocked pairs: {blocked_resp.error}")
                return
            blocked_pairs = []
            for b in blocked_resp.data:
                if b.get('would_play_again', True) is not False:
                    continue
                blocked_pairs.append({
                    'player_a': min(b['from_player_id'], b['about_player_id']),
                    'player_b': max(b['from_player_id'], b['about_player_id'])
                })

            # 3. Get the complete assignment history for repeat detection.
            # NOTE: match_assignments uses 'assigned_at', not 'created_at'.
            history_resp = _load_all_rows(
                table,
                'match_assignments',
                'player1_id, player2_id, period_label, assigned_at',
                'assigned_at',
            )
            if history_resp.error:
                # Hard stop — never generate pairings without knowing full pairing history
                self._send_error(500, f"Failed to load match history: {history_resp.error}")
                return
            all_assignments = history_resp.data

            # 4. Get the complete two-set score history for deterministic rating
            # rebuilds and repeat detection. Pagination removes the old 500-row
            # ceiling without loading an unbounded response at once.
            all_matches_resp = _load_all_match_scores(table)
            if all_matches_resp.error:
                self._send_error(500, f"Failed to load match scores: {all_matches_resp.error}")
                return
            all_matches = all_matches_resp.data

            # 5. Generate pairings using exhaustion-first algorithm
            pairings, skipped, forced_repeats = generate_pairings(
                players, blocked_pairs, all_assignments, all_matches,
                period_label=period_label
            )

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
            # Skipped in dry_run mode — preview doesn't write anything
            if not dry_run:
                existing_resp = table('match_assignments').select('id').eq('period_label', period_label).execute()
                if existing_resp.error:
                    self._send_error(500, f"Failed to check existing assignments: {existing_resp.error}")
                    return
                if existing_resp.data:
                    self._send_error(409, f"Pairings for {period_label} already exist ({len(existing_resp.data)} assignments) — aborting to prevent duplicates")
                    return

            # Step 6d: In dry_run mode, return pairings for human review without saving or emailing
            if dry_run:
                preview = []
                for p in pairings:
                    key = frozenset([p['player1']['id'], p['player2']['id']])
                    preview.append({
                        'player1': p['player1']['name'],
                        'player2': p['player2']['name'],
                        'forced_repeat': key in forced_repeats,
                    })
                self._send_success({
                    'dry_run': True,
                    'period': period_label,
                    'pairings': preview,
                    'skipped': [pl['name'] for pl in skipped],
                    'forced_repeat_count': len(forced_repeats),
                    'total': len(preview),
                })
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

            append_event(self._run_id, 'postcheck', 'info', 'Pairings run completed', {
                'pairings_created': len(assignments),
                'emails_sent': emails_sent,
                'rating_model': 'elo-two-set-v1',
            })
            update_run(self._run_id, 'succeeded', summary={
                'period': period_label,
                'pairings_created': len(assignments),
                'emails_sent': emails_sent,
                'rating_model': 'elo-two-set-v1',
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
                    'player1_rating': p['player1'].get('rating'),
                    'player1_uncertainty': p['player1'].get('uncertainty'),
                    'player1_valid_results': p['player1'].get('valid_results'),
                    'player2': p['player2']['name'],
                    'player2_email': p['player2']['email'],
                    'player2_availability': p['player2_availability'],
                    'player2_rating': p['player2'].get('rating'),
                    'player2_uncertainty': p['player2'].get('uncertainty'),
                    'player2_valid_results': p['player2'].get('valid_results'),
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
