#!/usr/bin/env python3
"""
NET WORTH Production API Server
Flask backend for tennis ladder with login, score reporting, and dynamic rankings
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app)

# Environment configuration
DB_PATH = os.environ.get('DATABASE_PATH', 'networth_tennis.db')
FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')  # For CORS

# Simple password (in production, use proper auth)
DEFAULT_PASSWORD = os.environ.get('PLAYER_PASSWORD', 'tennis123')

def get_db():
    """Get database connection with relative path"""
    db_path = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(os.path.dirname(__file__), DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM players')
        player_count = cursor.fetchone()['count']
        conn.close()

        return jsonify({
            'success': True,
            'message': 'NET WORTH API is running!',
            'timestamp': datetime.now().isoformat(),
            'players': player_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Player login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        # Simple password check
        if password != DEFAULT_PASSWORD:
            return jsonify({
                'success': False,
                'message': f'Use "{DEFAULT_PASSWORD}" for all players'
            }), 401

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM players
            WHERE LOWER(email) = LOWER(?) AND is_active = 1
        ''', (email,))

        player = cursor.fetchone()

        if not player:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Email not found. Email matches@networthtennis.com to join!'
            }), 404

        # Get current rank
        cursor.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM players
            WHERE total_score > ? AND is_active = 1
        ''', (player['total_score'],))

        rank_result = cursor.fetchone()
        current_rank = rank_result['rank'] if rank_result else 1

        # Get total players
        cursor.execute('SELECT COUNT(*) as total FROM players WHERE is_active = 1')
        total_players = cursor.fetchone()['total']

        # Get recent matches
        cursor.execute('''
            SELECT * FROM match_reports
            WHERE (player1_id = ? OR player2_id = ?)
            AND status = 'confirmed'
            ORDER BY match_date DESC
            LIMIT 5
        ''', (player['id'], player['id']))

        recent_matches = []
        for match in cursor.fetchall():
            recent_matches.append({
                'date': match['match_date'],
                'player1_total': match['player1_total'],
                'player2_total': match['player2_total']
            })

        conn.close()

        return jsonify({
            'success': True,
            'message': f'Welcome back, {player["name"]}! 🎾',
            'player': {
                'id': player['id'],
                'name': player['name'],
                'email': player['email'],
                'skill_level': player['skill_level'],
                'total_score': player['total_score'],
                'current_rank': current_rank,
                'total_players': total_players,
                'wins': player['wins'],
                'losses': player['losses']
            },
            'recent_matches': recent_matches
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}'
        }), 500

@app.route('/api/ladder', methods=['GET'])
def get_ladder():
    """Get full ladder rankings"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id, name, skill_level, total_score, wins, losses,
                ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank
            FROM players
            WHERE is_active = 1
            ORDER BY total_score DESC
        ''')

        ladder = []
        for row in cursor.fetchall():
            ladder.append({
                'rank': row['rank'],
                'name': row['name'],
                'skill_level': row['skill_level'],
                'total_score': row['total_score'],
                'wins': row['wins'],
                'losses': row['losses']
            })

        conn.close()

        return jsonify({
            'success': True,
            'ladder': ladder,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        })

    except Exception as e:
        print(f"Ladder error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/report-score', methods=['POST'])
def report_score():
    """Report match score"""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        opponent_name = data.get('opponent_name')
        player_set1 = int(data.get('player_set1', 0))
        player_set2 = int(data.get('player_set2', 0))
        opponent_set1 = int(data.get('opponent_set1', 0))
        opponent_set2 = int(data.get('opponent_set2', 0))
        match_date = data.get('match_date', datetime.now().strftime('%Y-%m-%d'))

        conn = get_db()
        cursor = conn.cursor()

        # Find opponent by name
        cursor.execute('SELECT id FROM players WHERE name = ? AND is_active = 1', (opponent_name,))
        opponent = cursor.fetchone()

        if not opponent:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Player "{opponent_name}" not found'
            }), 404

        opponent_id = opponent['id']

        # Calculate totals
        player_total = player_set1 + player_set2
        opponent_total = opponent_set1 + opponent_set2

        # Insert match report
        cursor.execute('''
            INSERT INTO match_reports
            (player1_id, player2_id, reporter_id, player1_set1, player1_set2,
             player2_set1, player2_set2, player1_total, player2_total, match_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (player_id, opponent_id, player_id, player_set1, player_set2,
              opponent_set1, opponent_set2, player_total, opponent_total, match_date))

        report_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Score reported! Waiting for opponent confirmation.',
            'report_id': report_id
        })

    except Exception as e:
        print(f"Score report error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all active players for dropdowns"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, skill_level
            FROM players
            WHERE is_active = 1
            ORDER BY name
        ''')

        players = []
        for row in cursor.fetchall():
            players.append({
                'id': row['id'],
                'name': row['name'],
                'skill_level': row['skill_level']
            })

        conn.close()

        return jsonify({
            'success': True,
            'players': players
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Serve static files (for development)
@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    print(f"🎾 NET WORTH Tennis Ladder API")
    print(f"🚀 Starting server on port {port}...")
    print(f"📊 Health check: http://localhost:{port}/api/health")
    print(f"📊 Database: {DB_PATH}")

    app.run(host='0.0.0.0', port=port, debug=debug)
