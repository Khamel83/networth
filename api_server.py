#!/usr/bin/env python3
"""
Simple API server for NET WORTH Tennis Ladder
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs

class NetWorthAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/ladder':
            self.send_cors_headers()
            self.send_response(200)
            self.end_headers()

            try:
                # Get ladder data from database
                conn = sqlite3.connect('/home/ubuntu/dev/networth/networth_tennis.db')
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT name, total_score, skill_level
                    FROM players
                    WHERE is_active = 1
                    ORDER BY total_score DESC, name ASC
                """)

                players = []
                for i, (name, score, skill) in enumerate(cursor.fetchall(), 1):
                    players.append({
                        'rank': i,
                        'name': name,
                        'total_score': score,
                        'skill_level': skill
                    })

                conn.close()

                response = json.dumps(players, indent=2)
                self.wfile.write(response.encode())

            except Exception as e:
                error_response = json.dumps({'error': str(e)})
                self.wfile.write(error_response.encode())

        elif parsed_path.path == '/':
            # Serve the main HTML file
            self.send_cors_headers()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            try:
                with open('/home/ubuntu/dev/networth/index.html', 'r') as f:
                    content = f.read()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.wfile.write(b'<h1>NET WORTH Tennis Ladder</h1><p>Loading...</p>')

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_cors_headers()
        self.send_response(200)
        self.end_headers()

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == '__main__':
    # Ensure we have the database and data
    os.system('cd /home/ubuntu/dev/networth && python3 networth_safe.py --setup 2>/dev/null')

    server = HTTPServer(('localhost', 8080), NetWorthAPI)
    print('NET WORTH API server running on port 8080...')
    server.serve_forever()