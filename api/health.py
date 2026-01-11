"""
Vercel Serverless Function: Health Check
Simple health endpoint for monitoring
Uses Supabase REST API (no Python supabase client).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db_status = "not_configured"
        supabase_available = False

        try:
            from api.supabase_http import table

            if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_ANON_KEY'):
                supabase_available = True
                try:
                    table('players').select('id').limit(1).execute()
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
