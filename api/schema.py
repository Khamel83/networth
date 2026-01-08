"""
Vercel Serverless Function: Schema Validation API

Checks actual database schema against expected schema.
Use this to verify migrations have been run.
"""
from http.server import BaseHTTPRequestHandler
import json
import os


# Expected columns for each table based on all migrations
EXPECTED_SCHEMA = {
    'players': [
        # Base schema (supabase-final-setup.sql)
        'id', 'email', 'name', 'phone', 'skill_level', 'rank',
        'total_games', 'matches_played', 'trend', 'is_active', 'is_admin',
        'preferred_match_frequency', 'max_travel_minutes', 'notes',
        'created_at', 'updated_at',
        # add-columns.sql
        'available_morning', 'available_afternoon', 'available_evening',
        'unavailable_until',
        # ashley-migration-2025.sql
        'membership_tier', 'avatar_url', 'favorite_players',
        'avail_weekday_early', 'avail_weekday_day', 'avail_weekday_late',
        'avail_weekend_early', 'avail_weekend_day', 'avail_weekend_late',
        'rms_score', 'rms_band',
    ],
    'matches': [
        'id', 'player1_id', 'player2_id', 'player1_games', 'player2_games',
        'set1_p1', 'set1_p2', 'set2_p1', 'set2_p2', 'set3_p1', 'set3_p2',
        'period_type', 'period_label', 'court', 'match_date', 'match_time',
        'is_forfeit', 'reported_by', 'confirmed_by', 'status', 'notes', 'created_at',
    ],
    'match_assignments': [
        'id', 'player1_id', 'player2_id', 'period_type', 'period_label',
        'status', 'declined_by', 'decline_count', 'is_rematch',
        'original_assignment_id', 'assigned_at', 'responded_at',
    ],
    'match_feedback': [
        'id', 'match_id', 'from_player_id', 'about_player_id',
        'would_play_again', 'competitive_match', 'private_note', 'created_at',
    ],
    'league_settings': [
        'id', 'league_name', 'match_frequency', 'sets_per_match',
        'games_per_set', 'tiebreak_enabled', 'created_at',
    ],
}


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


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Check schema - returns what columns exist vs expected"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            results = {}

            for table_name, expected_cols in EXPECTED_SCHEMA.items():
                try:
                    # Query information_schema to get actual columns
                    # This requires the right permissions in Supabase
                    query = f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = '{table_name}'
                    """

                    # Use rpc to run raw SQL (requires function or direct query)
                    # Alternative: just try to select from table and see what columns exist

                    # Simpler approach: try to select * and parse the response
                    response = supabase.table(table_name).select('*').limit(1).execute()

                    if response.data and len(response.data) > 0:
                        existing_cols = list(response.data[0].keys())
                    else:
                        # Table exists but is empty - try to get column names from error
                        # or just mark as "empty, can't determine"
                        existing_cols = []

                    missing = [c for c in expected_cols if c not in existing_cols]
                    extra = [c for c in existing_cols if c not in expected_cols]

                    results[table_name] = {
                        'existing_columns': sorted(existing_cols),
                        'expected_columns': sorted(expected_cols),
                        'missing_columns': sorted(missing),
                        'extra_columns': sorted(extra),
                        'valid': len(missing) == 0,
                        'row_count': len(response.data) if response.data else 0,
                    }

                except Exception as e:
                    results[table_name] = {
                        'error': str(e),
                        'valid': False,
                    }

            all_valid = all(r.get('valid', False) for r in results.values())

            self._send_success({
                'schema_valid': all_valid,
                'tables': results,
                'summary': {
                    'total_tables': len(EXPECTED_SCHEMA),
                    'valid_tables': sum(1 for r in results.values() if r.get('valid', False)),
                    'tables_with_issues': [k for k, v in results.items() if not v.get('valid', False)],
                }
            })

        except Exception as e:
            self._send_error(500, str(e))

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, **data}, indent=2).encode())

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode())
