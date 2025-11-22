#!/usr/bin/env python3
"""
Simple working NET WORTH API server
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve other static files
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

def get_db():
    conn = sqlite3.connect('/home/ubuntu/dev/networth/networth_tennis.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        # Debug: Log the login attempt
        print(f"Login attempt: {email}")

        # Simple password check
        if password != 'tennis123':
            return jsonify({
                'success': False,
                'message': 'Use "tennis123" for all players'
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

        # Get basic player info
        player_dict = {
            'id': player['id'],
            'name': player['name'],
            'email': player['email'],
            'skill_level': player['skill_level'],
            'total_score': player['total_score'],
            'matches_played': 0  # Will update later
        }

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

        conn.close()

        return jsonify({
            'success': True,
            'message': f'Welcome back, {player["name"]}! 🎾',
            'player': {
                'id': player_dict['id'],
                'name': player_dict['name'],
                'email': player_dict['email'],
                'skill_level': player_dict['skill_level'],
                'total_score': player_dict['total_score'],
                'current_rank': current_rank,
                'total_players': total_players,
                'matches_played': 0
            },
            'recent_matches': []
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}'
        }), 500

@app.route('/api/ladder', methods=['GET'])
def get_ladder():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                rank() OVER (ORDER BY total_score DESC) as rank,
                id, name, skill_level, total_score
            FROM players
            WHERE is_active = 1
            ORDER BY total_score DESC
            LIMIT 20
        ''')

        ladder = []
        for row in cursor.fetchall():
            ladder.append({
                'rank': row['rank'],
                'name': row['name'],
                'skill_level': row['skill_level'],
                'total_score': row['total_score']
            })

        conn.close()

        return jsonify({
            'success': True,
            'ladder': ladder,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        })

    except Exception as e:
        print(f"Ladder error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'NET WORTH API is running!',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting NET WORTH server on port 5000...")
    print("📊 Site: http://localhost:5000")
    print("📊 Health check: http://localhost:5000/api/health")
    app.run(host='0.0.0.0', port=5000, debug=False)