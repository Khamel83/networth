#!/usr/bin/env python3
"""
NET WORTH Tennis - Local Development Server
Serves the static site and API routes for local testing
"""
import http.server
import socketserver
import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 7654
DIRECTORY = "public"

# Sample data for local testing
SAMPLE_PLAYERS = [
    {"id": 1, "rank": 1, "name": "Kim Ndombe", "skill_level": "4.0+ Advanced", "points": 51, "wins": 8, "losses": 1, "trend": "neutral"},
    {"id": 2, "rank": 2, "name": "Sarah Kaplan", "skill_level": "4.0 Advanced", "points": 47, "wins": 7, "losses": 2, "trend": "up"},
    {"id": 3, "rank": 3, "name": "Jessica Chen", "skill_level": "3.5-4.0 Int-Adv", "points": 43, "wins": 6, "losses": 2, "trend": "up"},
    {"id": 4, "rank": 4, "name": "Maria Rodriguez", "skill_level": "4.0 Advanced", "points": 41, "wins": 6, "losses": 3, "trend": "down"},
    {"id": 5, "rank": 5, "name": "Emily Watson", "skill_level": "3.5 Intermediate+", "points": 38, "wins": 5, "losses": 3, "trend": "neutral"},
    {"id": 6, "rank": 6, "name": "Lisa Park", "skill_level": "3.5-4.0 Int-Adv", "points": 35, "wins": 5, "losses": 4, "trend": "up"},
    {"id": 7, "rank": 7, "name": "Anna Thompson", "skill_level": "3.5 Intermediate+", "points": 32, "wins": 4, "losses": 4, "trend": "neutral"},
    {"id": 8, "rank": 8, "name": "Rachel Kim", "skill_level": "3.0-3.5 Intermediate", "points": 28, "wins": 4, "losses": 5, "trend": "down"},
    {"id": 9, "rank": 9, "name": "Diana Lee", "skill_level": "3.5 Intermediate+", "points": 25, "wins": 3, "losses": 5, "trend": "up"},
    {"id": 10, "rank": 10, "name": "Michelle Brown", "skill_level": "3.0-3.5 Intermediate", "points": 22, "wins": 3, "losses": 6, "trend": "neutral"},
]

SAMPLE_MATCHES = [
    {"id": 1, "winner": {"name": "Kim Ndombe"}, "loser": {"name": "Sarah Kaplan"}, "winner_score": "6-4, 6-3", "loser_score": "4-6, 3-6", "played_at": "2024-12-01T14:00:00Z", "court": "Vermont Canyon"},
    {"id": 2, "winner": {"name": "Sarah Kaplan"}, "loser": {"name": "Jessica Chen"}, "winner_score": "7-5, 6-4", "loser_score": "5-7, 4-6", "played_at": "2024-11-28T10:00:00Z", "court": "Griffith Park"},
    {"id": 3, "winner": {"name": "Jessica Chen"}, "loser": {"name": "Maria Rodriguez"}, "winner_score": "6-2, 6-4", "loser_score": "2-6, 4-6", "played_at": "2024-11-25T16:00:00Z", "court": "Echo Park"},
]


class NetWorthHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API routes
        if path.startswith('/api/'):
            self.handle_api(path, 'GET')
            return

        # SPA routes - serve index.html for non-file paths
        if not '.' in path.split('/')[-1] and path != '/':
            # Check if there's an HTML file for this route
            html_path = Path(DIRECTORY) / f"{path.strip('/')}.html"
            if html_path.exists():
                self.path = f"/{path.strip('/')}.html"
            else:
                self.path = '/index.html'

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            self.handle_api(parsed.path, 'POST')
            return
        self.send_error(405, "Method Not Allowed")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def handle_api(self, path, method):
        if path == '/api/players':
            self.send_json({"success": True, "players": SAMPLE_PLAYERS, "source": "local"})

        elif path == '/api/matches':
            if method == 'GET':
                self.send_json({"success": True, "matches": SAMPLE_MATCHES, "source": "local"})
            elif method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body) if body else {}
                self.send_json({"success": True, "message": "Match recorded (demo mode)", "match": data}, 201)

        elif path == '/api/auth':
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body) if body else {}

                email = data.get('email', '')
                password = data.get('password', '')

                # Demo login - accept any email with password 'tennis123'
                if password == 'tennis123':
                    # Find or create player
                    player = next((p for p in SAMPLE_PLAYERS if email.split('@')[0].lower() in p['name'].lower()), None)
                    if not player:
                        player = {"id": 99, "name": email.split('@')[0].title(), "email": email, "rank": 99, "points": 0, "wins": 0, "losses": 0, "is_admin": email == "admin@networthtennis.com"}

                    self.send_json({
                        "success": True,
                        "token": "demo-token-12345",
                        "player": player
                    })
                else:
                    self.send_json({"success": False, "error": "Invalid credentials"}, 401)
            else:
                self.send_error(405)

        elif path == '/api/health':
            from datetime import datetime
            self.send_json({
                "status": "healthy",
                "service": "networth-tennis",
                "version": "2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "database": {"status": "local-demo"},
                "environment": "development"
            })

        else:
            self.send_json({"success": False, "error": "Not found"}, 404)


def main():
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    with socketserver.TCPServer(("", PORT), NetWorthHandler) as httpd:
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ██╗███████╗████████╗    ██╗    ██╗ ██████╗ ██████╗  ║
║   ████╗  ██║██╔════╝╚══██╔══╝    ██║    ██║██╔═══██╗██╔══██╗ ║
║   ██╔██╗ ██║█████╗     ██║       ██║ █╗ ██║██║   ██║██████╔╝ ║
║   ██║╚██╗██║██╔══╝     ██║       ██║███╗██║██║   ██║██╔══██╗ ║
║   ██║ ╚████║███████╗   ██║       ╚███╔███╔╝╚██████╔╝██║  ██║ ║
║   ╚═╝  ╚═══╝╚══════╝   ╚═╝        ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝ ║
║                                                               ║
║   East Side Tennis Ladder - Development Server                ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║   Local:     http://localhost:{PORT}                            ║
║   Network:   http://0.0.0.0:{PORT}                              ║
║   Health:    http://localhost:{PORT}/api/health                 ║
║                                                               ║
║   Demo Login: any email + password 'tennis123'                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    main()
