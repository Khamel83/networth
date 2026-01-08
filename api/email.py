"""
Vercel Serverless Function: Email Notifications
Email sending is currently DISABLED.
All notification features rely on the admin dashboard instead.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime


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


def send_email(to_email, subject, html_content, reply_to=None):
    """
    Email sending is disabled.
    Returns success but does not actually send.
    Admins check the dashboard for notifications.
    """
    return {
        'success': True,
        'blocked': True,
        'message': 'Email notifications disabled - check admin dashboard'
    }


# Stub functions for email templates (kept for future use)
def get_pairing_email_html(player1_name, player2_name, opponent_email, period_label,
                           player_availability="", opponent_availability=""):
    return "<p>Pairing notification</p>"


def get_welcome_email_html(player_name, membership_tier):
    return "<p>Welcome to Net Worth Tennis!</p>"


def get_sitout_confirmation_email_html(player_name, period_label):
    return "<p>You are sitting out this month.</p>"


def get_rejoin_confirmation_email_html(player_name, eligible_month):
    return "<p>Welcome back!</p>"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Return email system status"""
        self._send_success({
            "status": "disabled",
            "message": "Email notifications are disabled. Admins check dashboard for pending actions."
        })

    def do_POST(self):
        """Handle email requests (all disabled)"""
        self._send_success({
            "status": "disabled",
            "message": "Email notifications are disabled. Check admin dashboard instead.",
            "emails_sent": 0
        })

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
