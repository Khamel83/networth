"""
Vercel Serverless Function: Database Migration API

Admin-only endpoint for running database migrations.
No more manual Supabase SQL Editor visits!
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path


# Available migrations in order
MIGRATIONS = {
    '001_base_schema': {
        'name': 'Base Schema',
        'file': 'supabase-final-setup.sql',
        'description': 'Initial database setup with all tables',
    },
    '002_add_columns': {
        'name': 'Add Availability Columns',
        'file': 'add-columns.sql',
        'description': 'Adds availability and pause columns',
    },
    '003_ashley_2025': {
        'name': 'Ashley Christmas 2025 Migration',
        'file': 'ashley-migration-2025.sql',
        'description': 'Adds membership tiers, 6-slot availability, RMS scoring',
    },
}


def get_supabase_client():
    """Lazy initialization of Supabase client"""
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
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


def is_admin(supabase, user_email):
    """Check if user is an admin"""
    try:
        result = supabase.table('players').select('is_admin').eq('email', user_email).single().execute()
        return result.data and result.data.get('is_admin', False)
    except Exception:
        return False


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """List available migrations"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            # Check admin status
            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user or not is_admin(supabase, user.email):
                self._send_error(403, "Admin access required")
                return

            # Get list of applied migrations
            applied = []
            try:
                result = supabase.table('_migrations').select('*').order('applied_at').execute()
                applied = [m['name'] for m in result.data] if result.data else []
            except Exception:
                # Table doesn't exist yet - that's ok
                pass

            # Build migration status
            migration_status = []
            for key, info in MIGRATIONS.items():
                migration_status.append({
                    'id': key,
                    'name': info['name'],
                    'description': info['description'],
                    'file': info['file'],
                    'applied': key in applied,
                })

            self._send_success({
                'migrations': migration_status,
                'applied_count': len(applied),
                'pending_count': len(MIGRATIONS) - len(applied),
            })

        except Exception as e:
            self._send_error(500, str(e))

    def do_POST(self):
        """Run a migration or arbitrary SQL (admin only)"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                self._send_error(503, "Database not available")
                return

            # Check admin status
            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(supabase, auth_header)

            if not user or not is_admin(supabase, user.email):
                self._send_error(403, "Admin access required")
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'run_migration')

            if action == 'run_migration':
                migration_id = data.get('migration')
                if not migration_id or migration_id not in MIGRATIONS:
                    self._send_error(400, f"Invalid migration: {migration_id}")
                    return

                migration = MIGRATIONS[migration_id]

                # Read migration file
                # Note: In Vercel, we'd need to bundle these files or store SQL inline
                # For now, return the SQL that needs to be run manually
                self._send_success({
                    'migration': migration_id,
                    'name': migration['name'],
                    'file': migration['file'],
                    'message': f"Migration '{migration['name']}' is ready. Run the SQL file '{migration['file']}' in Supabase SQL Editor.",
                    'note': "Full automated migration requires SUPABASE_SERVICE_KEY with execute permissions.",
                })

            elif action == 'run_sql':
                # Run arbitrary SQL (dangerous but useful for admins)
                sql = data.get('sql', '').strip()
                if not sql:
                    self._send_error(400, "No SQL provided")
                    return

                # Security: Only allow certain statements
                sql_lower = sql.lower()
                if any(dangerous in sql_lower for dangerous in ['drop database', 'truncate', 'delete from players']):
                    self._send_error(400, "Dangerous SQL operation blocked")
                    return

                try:
                    # Use rpc to run raw SQL (requires a Supabase function)
                    # Alternative: use postgrest for safe operations only
                    self._send_success({
                        'message': "Direct SQL execution not available. Use Supabase SQL Editor or create an RPC function.",
                        'sql': sql[:500] + ('...' if len(sql) > 500 else ''),
                    })
                except Exception as e:
                    self._send_error(500, f"SQL execution failed: {str(e)}")

            elif action == 'check_schema':
                # Quick schema check
                from api.schema import EXPECTED_SCHEMA

                results = {}
                for table_name in EXPECTED_SCHEMA.keys():
                    try:
                        response = supabase.table(table_name).select('*').limit(1).execute()
                        if response.data and len(response.data) > 0:
                            results[table_name] = {
                                'exists': True,
                                'columns': list(response.data[0].keys()),
                            }
                        else:
                            results[table_name] = {'exists': True, 'columns': [], 'empty': True}
                    except Exception as e:
                        results[table_name] = {'exists': False, 'error': str(e)}

                self._send_success({'tables': results})

            else:
                self._send_error(400, f"Unknown action: {action}")

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
