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

            if not verify_admin(email):
                self._send_error(403, "Admin access required")
                return

            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            action = params.get('action', ['players'])[0]

            if action == 'players':
                # Get all players
                result = table('players').select('*').order('rank').execute()
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
                # Get current month's pairings with player details
                today = date.today()
                period = today.strftime('%B %Y')

                result = table('match_assignments')\
                    .select('*')\
                    .eq('period_label', period)\
                    .execute()

                # Get all players to enrich pairings
                players_result = table('players').select('id, name, email, phone').execute()
                players_map = {p['id']: p for p in players_result.data}

                # Enrich pairings with player info
                enriched_pairings = []
                for pairing in result.data:
                    p1 = players_map.get(pairing.get('player1_id'), {})
                    p2 = players_map.get(pairing.get('player2_id'), {})
                    enriched_pairings.append({
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
                        'period_label': pairing.get('period_label')
                    })

                self._send_success({
                    'period': period,
                    'pairings': enriched_pairings
                })

            elif action == 'player':
                # Get single player details
                player_id = params.get('id', [None])[0]
                if not player_id:
                    self._send_error(400, "Player ID required")
                    return

                result = table('players').select('*').eq('id', player_id).single().execute()
                if not result.data:
                    self._send_error(404, "Player not found")
                    return

                player_data = result.data[0] if isinstance(result.data, list) else result.data
                self._send_success({'player': player_data})

            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Admin actions: update player, pause/activate, etc."""
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

            if not verify_admin(email):
                self._send_error(403, "Admin access required")
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action')
            player_id = data.get('player_id')

            if not player_id:
                self._send_error(400, "player_id required")
                return

            # Verify player exists
            player = table('players').select('id, name, email').eq('id', player_id).single().execute()
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
                table('players').update({'is_active': False}).eq('id', player_id).execute()
                self._send_success({
                    'message': f"Player {player_data.get('name')} rejected",
                    'rejected': True
                })
                return

            elif action == 'update_payment':
                # Toggle payment status
                has_paid = data.get('has_paid', False)
                table('players').update({'has_paid': has_paid}).eq('id', player_id).execute()
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
                table('players').update({'total_games': int(total_games)}).eq('id', player_id).execute()
                self._send_success({
                    'message': f"Games updated for {player_data.get('name')}",
                    'total_games': int(total_games)
                })
                return

            else:
                self._send_error(400, f"Unknown action: {action}")
                return

            if updates:
                table('players').update(updates).eq('id', player_id).execute()

            # Return updated player
            updated = table('players').select('*').eq('id', player_id).single().execute()
            updated_data = updated.data[0] if isinstance(updated.data, list) else updated.data

            self._send_success({
                'message': f"Player updated ({action})",
                'player': updated_data
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
