"""
Vercel Serverless Function: Diagnostic Tool

Checks a player's match assignment status and pairing eligibility.
Useful for debugging "I don't see my match" issues.

Usage: GET /api/diagnose?email=leebrunatti@gmail.com

Requires admin access.
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime, date
from urllib.parse import parse_qs, urlparse


def get_player_by_email(email):
    """Get player from database by email"""
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


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Diagnose player's match status"""
        try:
            from api.supabase_http import table

            # Get admin email from Authorization header
            auth_header = self.headers.get('Authorization', '')
            admin_email = None
            if auth_header.startswith('Bearer '):
                token_or_email = auth_header.replace('Bearer ', '')
                if '@' in token_or_email:
                    admin_email = token_or_email.lower()

            if not admin_email:
                admin_email = self.headers.get('X-Player-Email', '').lower()

            if not verify_admin(admin_email):
                self._send_error(403, "Admin access required")
                return

            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            target_email = params.get('email', [None])[0]

            if not target_email:
                self._send_error(400, "Email parameter required")
                return

            # Get player info
            player = get_player_by_email(target_email)
            if not player:
                self._send_success({
                    'found': False,
                    'message': f'Player {target_email} not found in database'
                })
                return

            player_id = player.get('id')
            player_name = player.get('name')

            # Check eligibility for pairing
            is_active = player.get('is_active', True)
            membership_tier = player.get('membership_tier', 'player')
            unavailable_until = player.get('unavailable_until')

            is_paused = False
            if unavailable_until:
                if isinstance(unavailable_until, str):
                    try:
                        pause_date = date.fromisoformat(unavailable_until.split('T')[0])
                        is_paused = pause_date > date.today()
                    except ValueError:
                        pass

            # Get current month's pairings
            current_month = datetime.now().strftime('%B %Y')
            pairings_result = table('match_assignments')\
                .select('*')\
                .eq('period_label', current_month)\
                .execute()

            # Find if player is in any pairing
            my_pairing = None
            for p in pairings_result.data:
                if p.get('player1_id') == player_id or p.get('player2_id') == player_id:
                    my_pairing = p
                    break

            # Get opponent info if paired
            opponent_name = None
            opponent_email = None
            if my_pairing:
                opponent_id = my_pairing.get('player2_id') if my_pairing.get('player1_id') == player_id else my_pairing.get('player1_id')
                opponent = table('players').select('name, email').eq('id', opponent_id).single().execute()
                if opponent.data:
                    opp = opponent.data[0] if isinstance(opponent.data, list) else opponent.data
                    opponent_name = opp.get('name')
                    opponent_email = opp.get('email')

            # Check for completed matches
            matches_result = table('matches')\
                .select('*')\
                .eq('period_label', current_month)\
                .execute()

            my_match = None
            for m in matches_result.data:
                if m.get('player1_id') == player_id or m.get('player2_id') == player_id:
                    my_match = m
                    break

            # Build diagnostic report
            report = {
                'found': True,
                'player_id': player_id,
                'player_name': player_name,
                'email': target_email,
                'is_active': is_active,
                'membership_tier': membership_tier,
                'is_paused': is_paused,
                'unavailable_until': str(unavailable_until) if unavailable_until else None,
                'current_month': current_month,
                'has_match_assignment': my_pairing is not None,
                'assignment_status': my_pairing.get('status') if my_pairing else None,
                'opponent': opponent_name,
                'opponent_email': opponent_email,
                'has_completed_match': my_match is not None,
                'eligible_for_pairing': is_active and membership_tier == 'player' and not is_paused,
            }

            # Add recommendations
            recommendations = []
            if not is_active:
                recommendations.append("Player is marked inactive - contact admin to activate")
            if membership_tier == 'social_butterfly':
                recommendations.append("Player is Social Butterfly tier - not included in match pairings")
            if is_paused:
                recommendations.append(f"Player is paused until {unavailable_until}")
            if not report['eligible_for_pairing']:
                recommendations.append("Player is NOT eligible for pairing - see reasons above")
            if my_pairing and my_pairing.get('status') == 'completed':
                recommendations.append("Match already completed - check match history")
            if not my_pairing and not my_match and report['eligible_for_pairing']:
                recommendations.append("Player is eligible but has no match assignment - pairings may not have been generated")

            report['recommendations'] = recommendations

            self._send_success(report)

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
