"""
Vercel Serverless Function: Player Profile API
Self-service updates for availability and preferences.

Endpoints:
- GET: Fetch current profile (requires auth)
- POST: Update profile settings (requires auth)

Players can update:
- Time-of-day availability (morning/afternoon/evening)
- Pause for current month (unavailable_until)
- Phone number (optional, for text coordination)
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date, timedelta
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


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Get current player profile"""
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

            # Get player profile
            player = supabase.table('players').select('*').eq('email', user.email).single().execute()

            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            # Build availability status
            p = player.data
            availability = {
                'morning': p.get('available_morning', True),
                'afternoon': p.get('available_afternoon', True),
                'evening': p.get('available_evening', True),
            }

            unavailable_until = p.get('unavailable_until')
            is_paused = False
            if unavailable_until:
                if isinstance(unavailable_until, str):
                    pause_date = date.fromisoformat(unavailable_until.split('T')[0])
                else:
                    pause_date = unavailable_until
                is_paused = pause_date > date.today()

            self._send_success({
                "profile": {
                    "id": p.get('id'),
                    "name": p.get('name'),
                    "email": p.get('email'),
                    "phone": p.get('phone'),
                    "skill_level": p.get('skill_level'),
                    "total_games": p.get('total_games', 0),
                    "matches_played": p.get('matches_played', 0),
                    "rank": p.get('rank'),
                    "availability": availability,
                    "is_paused": is_paused,
                    "unavailable_until": str(unavailable_until) if unavailable_until else None,
                }
            })

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

            # Get current player
            player = supabase.table('players').select('id, name').eq('email', user.email).single().execute()
            if not player.data:
                self._send_error(404, "Player profile not found")
                return

            player_id = player.data['id']
            updates = {}

            if action == 'update':
                # Update time-of-day availability
                if 'availability' in data:
                    avail = data['availability']
                    if 'morning' in avail:
                        updates['available_morning'] = bool(avail['morning'])
                    if 'afternoon' in avail:
                        updates['available_afternoon'] = bool(avail['afternoon'])
                    if 'evening' in avail:
                        updates['available_evening'] = bool(avail['evening'])

                # Update phone number
                if 'phone' in data:
                    updates['phone'] = data['phone'] if data['phone'] else None

            elif action == 'pause':
                # Pause for rest of this month (auto-available next month)
                updates['unavailable_until'] = str(get_next_month_first())

            elif action == 'unpause':
                # Remove pause, become available immediately
                updates['unavailable_until'] = None

            else:
                self._send_error(400, f"Unknown action: {action}")
                return

            if updates:
                supabase.table('players').update(updates).eq('id', player_id).execute()

            # Return updated profile
            updated = supabase.table('players').select('*').eq('id', player_id).single().execute()
            p = updated.data

            availability = {
                'morning': p.get('available_morning', True),
                'afternoon': p.get('available_afternoon', True),
                'evening': p.get('available_evening', True),
            }

            unavailable_until = p.get('unavailable_until')
            is_paused = False
            if unavailable_until:
                if isinstance(unavailable_until, str):
                    pause_date = date.fromisoformat(unavailable_until.split('T')[0])
                else:
                    pause_date = unavailable_until
                is_paused = pause_date > date.today()

            self._send_success({
                "message": "Profile updated",
                "profile": {
                    "name": p.get('name'),
                    "phone": p.get('phone'),
                    "availability": availability,
                    "is_paused": is_paused,
                    "unavailable_until": str(unavailable_until) if unavailable_until else None,
                }
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
