"""
Vercel Serverless Function: Health Check
Simple health endpoint for monitoring
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
    SUPABASE_AVAILABLE = True
except ImportError:
    supabase = None
    SUPABASE_AVAILABLE = False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db_status = "disconnected"

        if supabase:
            try:
                # Quick health check query
                supabase.table('players').select('id').limit(1).execute()
                db_status = "connected"
            except Exception:
                db_status = "error"

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "healthy",
            "service": "networth-tennis",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "supabase_configured": bool(os.environ.get('SUPABASE_URL')),
                "supabase_available": SUPABASE_AVAILABLE,
                "status": db_status
            },
            "environment": os.environ.get('VERCEL_ENV', 'development')
        }).encode())
