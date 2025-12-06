"""
Vercel Serverless Function: Health Check
Simple health endpoint for monitoring
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone


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
    def do_GET(self):
        db_status = "not_configured"
        supabase_available = False

        try:
            supabase = get_supabase_client()
            if supabase:
                supabase_available = True
                try:
                    supabase.table('players').select('id').limit(1).execute()
                    db_status = "connected"
                except Exception:
                    db_status = "error"
        except Exception:
            db_status = "init_error"

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "healthy",
            "service": "networth-tennis",
            "version": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "supabase_configured": bool(os.environ.get('SUPABASE_URL')),
                "supabase_available": supabase_available,
                "status": db_status
            },
            "environment": os.environ.get('VERCEL_ENV', 'development')
        }).encode())
