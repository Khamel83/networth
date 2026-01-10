"""
Vercel Serverless Function: Player Profile API

Self-service profile management including:
- 6-slot availability (weekday/weekend × early/day/late)
- Sit-out toggle with email confirmation
- Tier upgrade (Social Butterfly → Player)
- Favorite players
- Phone number

Updated for Ashley's Christmas 2025 feedback.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, date, timedelta
from urllib.parse import parse_qs, urlparse


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


def get_user_from_token(supabase, auth_header):
    """Extract and verify user from Authorization header"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '')
    try:
        user = supabase.auth.get_user(token)
        if user and user.user:
            return user.user
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


def send_sitout_email(supabase, player_email, player_name, period_label):
    """Send sit-out confirmation email"""
    try:
        from api.email import get_sitout_confirmation_email_html, send_email
        html = get_sitout_confirmation_email_html(player_name, period_label)
        send_email(player_email, f"You're sitting out {period_label}", html)
    except Exception as e:
        print(f"Failed to send sit-out email: {e}")


def send_rejoin_email(supabase, player_email, player_name, eligible_month):
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
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            # Parse query parameters for viewing other profiles
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            profile_id = query_params.get('id', [None])[0]

            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user:
                self._send_error(401, "Authentication required")
                return

            # If viewing another player's profile
            if profile_id:
                player = supabase.table('players').select('*').eq('id', profile_id).single().execute()
                if not player.data:
                    self._send_error(404, "Player not found")
                    return
                self._send_success({"player": self._format_public_profile(player.data)})
                return

            # Get own profile (lowercase email to match join.py storage)
            email = user.email.lower() if user.email else ''
            player = supabase.table('players').select('*').eq('email', email).single().execute()

            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            self._send_success({"profile": self._format_own_profile(player.data)})

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Update player profile settings"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user:
                self._send_error(401, "Authentication required")
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'update')

            # Get current player - try by auth email first (lowercase to match join.py storage)
            auth_email = user.email.lower() if user.email else ''
            player = supabase.table('players').select('*').eq('email', auth_email).maybe_single().execute()

            # If not found by email, try by player_id from request (for email change scenarios)
            if not player.data:
                player_id = data.get('player_id')
                if player_id:
                    player = supabase.table('players').select('*').eq('id', player_id).single().execute()
                    # Sync email if found by ID but email doesn't match
                    if player.data and player.data.get('email') != auth_email:
                        supabase.table('players').update({'email': auth_email}).eq('id', player_id).execute()
                        player = supabase.table('players').select('*').eq('id', player_id).single().execute()

            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            player_data = player.data
            player_id = player_data['id']
            player_name = player_data.get('name', '')
            player_email = player_data.get('email', '')
            current_tier = player_data.get('membership_tier', 'player')
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
                send_sitout_email(supabase, player_email, player_name, get_current_month_label())

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
                send_rejoin_email(supabase, player_email, player_name, eligible_month)

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
                supabase.table('players').update(updates).eq('id', player_id).execute()

            # Return updated profile
            updated = supabase.table('players').select('*').eq('id', player_id).single().execute()

            self._send_success({
                "message": "Profile updated",
                "profile": self._format_own_profile(updated.data)
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
                "avail_weekday_early": p.get('avail_weekday_early', False),
                "avail_weekday_day": p.get('avail_weekday_day', False),
                "avail_weekday_late": p.get('avail_weekday_late', False),
                "avail_weekend_early": p.get('avail_weekend_early', False),
                "avail_weekend_day": p.get('avail_weekend_day', False),
                "avail_weekend_late": p.get('avail_weekend_late', False),
            },
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
