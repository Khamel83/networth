"""
Vercel Serverless Function: Player Profile API

Self-service profile management including:
- 6-slot availability (weekday/weekend × early/day/late)
- Sit-out toggle with email confirmation
- Tier upgrade (Social Butterfly → Player)
- Favorite players
- Phone number

Updated for Ashley's Christmas 2025 feedback.
Uses password-based auth (no Supabase Auth).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, date, timedelta
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


def get_next_month_first():
    """Get the first day of next month"""
    today = date.today()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def get_current_month_label():
    """Get current month label (e.g., 'January 2025')"""
    return datetime.now().strftime('%B %Y')


def get_next_month_label():
    """Get next month label"""
    next_month = get_next_month_first()
    return next_month.strftime('%B %Y')


def get_player_matches(player_id):
    """Get match history for a player"""
    from api.supabase_http import table

    try:
        # Fetch matches and players separately, then join in Python
        matches_response = table('matches').select('*')\
            .or_(f'(player1_id.eq.{player_id},player2_id.eq.{player_id})')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()

        # Get all unique player IDs from matches
        player_ids = set()
        for m in matches_response.data:
            if m.get('player1_id'):
                player_ids.add(m['player1_id'])
            if m.get('player2_id'):
                player_ids.add(m['player2_id'])

        # Fetch player names
        players_map = {}
        if player_ids:
            players_response = table('players').select('id, name').in_('id', list(player_ids)).execute()
            players_map = {p['id']: p for p in players_response.data}

        matches = []
        for m in matches_response.data:
            is_player1 = m['player1_id'] == player_id
            opponent_id = m['player2_id'] if is_player1 else m['player1_id']
            opponent = players_map.get(opponent_id, {})

            # Format score
            if m.get('set1_p1') is not None:
                if is_player1:
                    score = f"{m['set1_p1']}-{m['set1_p2']}, {m['set2_p1']}-{m['set2_p2']}"
                    if m.get('set3_p1') is not None:
                        score += f", {m['set3_p1']}-{m['set3_p2']}"
                else:
                    score = f"{m['set1_p2']}-{m['set1_p1']}, {m['set2_p2']}-{m['set2_p1']}"
                    if m.get('set3_p1') is not None:
                        score += f", {m['set3_p2']}-{m['set3_p1']}"
            else:
                my_games = m['player1_games'] if is_player1 else m['player2_games']
                their_games = m['player2_games'] if is_player1 else m['player1_games']
                score = f"{my_games}-{their_games}"

            matches.append({
                'period_label': m.get('period_label', ''),
                'opponent_name': opponent.get('name', 'Unknown'),
                'score': score
            })

        return matches
    except Exception as e:
        print(f"Error getting player matches: {e}")
        return []


def send_sitout_email(player_email, player_name, period_label):
    """Send sit-out confirmation email"""
    try:
        from api.email import get_sitout_confirmation_email_html, send_email
        html = get_sitout_confirmation_email_html(player_name, period_label)
        send_email(player_email, f"You're sitting out {period_label}", html)
    except Exception as e:
        print(f"Failed to send sit-out email: {e}")


def send_rejoin_email(player_email, player_name, eligible_month):
    """Send rejoin confirmation email"""
    try:
        from api.email import get_rejoin_confirmation_email_html, send_email
        html = get_rejoin_confirmation_email_html(player_name, eligible_month)
        send_email(player_email, f"Welcome back! You're in for {eligible_month}", html)
    except Exception as e:
        print(f"Failed to send rejoin email: {e}")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get player profile - supports both own profile and viewing others"""
        try:
            from api.supabase_http import table

            # Parse query parameters for viewing other profiles
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            profile_id = query_params.get('id', [None])[0]

            # Get email from Authorization header (password-based auth)
            # Format: "Bearer {email}" or custom header
            auth_header = self.headers.get('Authorization', '')
            email = None

            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                # In password-based auth, we might receive email directly or use token
                # For simplicity, check if it looks like an email
                if '@' in token_or_email:
                    email = token_or_email.lower()
                else:
                    # Token-based: would need token lookup, for now require email
                    self._send_error(401, "Please provide your email in Authorization header")
                    return

            # Also check for custom header with email
            if not email:
                email = self.headers.get('X-Player-Email', '').lower()

            if not email:
                self._send_error(401, "Authentication required")
                return

            # If viewing another player's profile
            if profile_id:
                result = table('players').select('*').eq('id', profile_id).single().execute()
                if not result.data:
                    self._send_error(404, "Player not found")
                    return
                player_data = result.data[0] if isinstance(result.data, list) else result.data
                self._send_success({"player": self._format_public_profile(player_data)})
                return

            # Get own profile
            player = get_player_by_email(email)

            if not player:
                self._send_error(404, "Player profile not found")
                return

            self._send_success({"profile": self._format_own_profile(player)})

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Update player profile settings"""
        try:
            from api.supabase_http import table

            # Get email from Authorization header
            auth_header = self.headers.get('Authorization', '')
            email = None

            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                if '@' in token_or_email:
                    email = token_or_email.lower()
                else:
                    self._send_error(401, "Please provide your email in Authorization header")
                    return

            if not email:
                email = self.headers.get('X-Player-Email', '').lower()

            if not email:
                self._send_error(401, "Authentication required")
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'update')

            # Get current player
            player = get_player_by_email(email)

            if not player:
                # If not found by email, try by player_id from request (for email change scenarios)
                player_id = data.get('player_id')
                if player_id:
                    result = table('players').select('*').eq('id', player_id).single().execute()
                    if result.data:
                        player = result.data[0] if isinstance(result.data, list) else result.data

            if not player:
                self._send_error(404, "Player profile not found")
                return

            player_id = player['id']
            player_name = player.get('name', '')
            player_email = player.get('email', '')
            current_tier = player.get('membership_tier', 'player')
            updates = {}

            if action == 'update':
                # Update 6-slot availability
                if 'availability' in data:
                    avail = data['availability']
                    # New 6-slot system
                    if 'weekday_early' in avail:
                        updates['avail_weekday_early'] = bool(avail['weekday_early'])
                    if 'weekday_day' in avail:
                        updates['avail_weekday_day'] = bool(avail['weekday_day'])
                    if 'weekday_late' in avail:
                        updates['avail_weekday_late'] = bool(avail['weekday_late'])
                    if 'weekend_early' in avail:
                        updates['avail_weekend_early'] = bool(avail['weekend_early'])
                    if 'weekend_day' in avail:
                        updates['avail_weekend_day'] = bool(avail['weekend_day'])
                    if 'weekend_late' in avail:
                        updates['avail_weekend_late'] = bool(avail['weekend_late'])

                    # Legacy 3-slot system (for backward compatibility)
                    if 'morning' in avail:
                        updates['available_morning'] = bool(avail['morning'])
                    if 'afternoon' in avail:
                        updates['available_afternoon'] = bool(avail['afternoon'])
                    if 'evening' in avail:
                        updates['available_evening'] = bool(avail['evening'])

                # Update name
                if 'name' in data:
                    if data['name'] and data['name'].strip():
                        updates['name'] = data['name'].strip()

                # Update phone number
                if 'phone' in data:
                    updates['phone'] = data['phone'] if data['phone'] else None

                # Update favorite players
                if 'favorite_players' in data:
                    updates['favorite_players'] = data['favorite_players'] if data['favorite_players'] else None

            elif action == 'pause' or action == 'sit_out':
                # Sit out - set indefinite pause (no auto-reinstate)
                # Using a far future date to indicate indefinite pause
                updates['unavailable_until'] = str(date(2099, 12, 31))

                # Send confirmation email
                send_sitout_email(player_email, player_name, get_current_month_label())

            elif action == 'unpause' or action == 'rejoin':
                # Remove pause, become available immediately
                updates['unavailable_until'] = None

                # Determine eligible month
                # If before match generation (assume 1st of month), can play this month
                # Otherwise, next month
                today = date.today()
                if today.day <= 5:  # First 5 days of month
                    eligible_month = get_current_month_label()
                else:
                    eligible_month = get_next_month_label()

                # Send confirmation email
                send_rejoin_email(player_email, player_name, eligible_month)

            elif action == 'upgrade_tier':
                # Social Butterfly → Player upgrade
                if current_tier == 'social_butterfly':
                    updates['membership_tier'] = 'player'

                    # Require availability before completing upgrade
                    if 'availability' in data:
                        avail = data['availability']
                        updates['avail_weekday_early'] = bool(avail.get('weekday_early', False))
                        updates['avail_weekday_day'] = bool(avail.get('weekday_day', False))
                        updates['avail_weekday_late'] = bool(avail.get('weekday_late', False))
                        updates['avail_weekend_early'] = bool(avail.get('weekend_early', False))
                        updates['avail_weekend_day'] = bool(avail.get('weekend_day', False))
                        updates['avail_weekend_late'] = bool(avail.get('weekend_late', False))
                else:
                    self._send_error(400, "Already a Player tier member")
                    return

            elif action == 'downgrade_tier':
                # Player → Social Butterfly downgrade (rare but allowed)
                if current_tier == 'player':
                    updates['membership_tier'] = 'social_butterfly'
                    # Clear availability since they won't be matched
                    updates['avail_weekday_early'] = False
                    updates['avail_weekday_day'] = False
                    updates['avail_weekday_late'] = False
                    updates['avail_weekend_early'] = False
                    updates['avail_weekend_day'] = False
                    updates['avail_weekend_late'] = False
                else:
                    self._send_error(400, "Already a Social Butterfly tier member")
                    return

            else:
                self._send_error(400, f"Unknown action: {action}")
                return

            if updates:
                table('players').update(updates).eq('id', player_id).execute()

            # Return updated profile
            updated_result = table('players').select('*').eq('id', player_id).single().execute()
            updated = updated_result.data[0] if isinstance(updated_result.data, list) else updated_result.data

            self._send_success({
                "message": "Profile updated",
                "profile": self._format_own_profile(updated)
            })

        except Exception as e:
            self._send_error(500, str(e))

    def _format_own_profile(self, p):
        """Format player data for own profile view (full access)"""
        # Check pause status
        unavailable_until = p.get('unavailable_until')
        is_paused = False
        if unavailable_until:
            if isinstance(unavailable_until, str):
                try:
                    pause_date = date.fromisoformat(unavailable_until.split('T')[0])
                    is_paused = pause_date > date.today()
                except ValueError:
                    is_paused = False
            else:
                is_paused = unavailable_until > date.today()

        return {
            "id": p.get('id'),
            "name": p.get('name'),
            "email": p.get('email'),
            "phone": p.get('phone'),
            "membership_tier": p.get('membership_tier', 'player'),
            "skill_level": p.get('skill_level'),
            "total_games": p.get('total_games', 0),
            "matches_played": p.get('matches_played', 0),
            "rank": p.get('rank'),
            "rms_score": p.get('rms_score'),
            "rms_band": p.get('rms_band'),
            "avatar_url": p.get('avatar_url'),
            "favorite_players": p.get('favorite_players'),
            "availability": {
                # 6-slot system
                "weekday_early": p.get('avail_weekday_early', False),
                "weekday_day": p.get('avail_weekday_day', False),
                "weekday_late": p.get('avail_weekday_late', False),
                "weekend_early": p.get('avail_weekend_early', False),
                "weekend_day": p.get('avail_weekend_day', False),
                "weekend_late": p.get('avail_weekend_late', False),
                # Legacy 3-slot system
                "morning": p.get('available_morning', False),
                "afternoon": p.get('available_afternoon', False),
                "evening": p.get('available_evening', False),
            },
            "is_paused": is_paused,
            "unavailable_until": str(unavailable_until) if unavailable_until else None,
            "is_admin": p.get('is_admin', False),
        }

    def _format_public_profile(self, p):
        """Format player data for public profile view (members can see contact info)"""
        player_id = p.get('id')
        matches = get_player_matches(player_id) if player_id else []

        return {
            "id": p.get('id'),
            "name": p.get('name'),
            "email": p.get('email'),
            "phone": p.get('phone'),
            "membership_tier": p.get('membership_tier', 'player'),
            "total_games": p.get('total_games', 0),
            "matches_played": p.get('matches_played', 0),
            "rank": p.get('rank'),
            "rms_band": p.get('rms_band'),
            "avatar_url": p.get('avatar_url'),
            "favorite_players": p.get('favorite_players'),
            "availability": {
                # 6-slot system (public can see when to coordinate)
                "weekday_early": p.get('avail_weekday_early', False),
                "weekday_day": p.get('avail_weekday_day', False),
                "weekday_late": p.get('avail_weekday_late', False),
                "weekend_early": p.get('avail_weekend_early', False),
                "weekend_day": p.get('avail_weekend_day', False),
                "weekend_late": p.get('avail_weekend_late', False),
            },
            # Also include flat fields for JS compatibility
            "avail_weekday_early": p.get('avail_weekday_early', False),
            "avail_weekday_day": p.get('avail_weekday_day', False),
            "avail_weekday_late": p.get('avail_weekday_late', False),
            "avail_weekend_early": p.get('avail_weekend_early', False),
            "avail_weekend_day": p.get('avail_weekend_day', False),
            "avail_weekend_late": p.get('avail_weekend_late', False),
            # Match history
            "matches": matches,
        }

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
