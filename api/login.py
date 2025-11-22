#!/usr/bin/env python3
"""
NET WORTH Login API
Simple, working login system for tennis ladder
"""

from flask import Flask, request, jsonify, make_response
import sqlite3
import json
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Enable CORS for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def get_db():
    conn = sqlite3.connect('/home/ubuntu/dev/networth/networth_tennis.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        # Simple password check
        if password != 'tennis123':
            return jsonify({
                'success': False,
                'message': 'Invalid password. Hint: Use "tennis123" for all players'
            }), 401

        # Check if player exists
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM players
            WHERE email = ? AND is_active = 1
        ''', (email,))

        player = cursor.fetchone()

        if not player:
            return jsonify({
                'success': False,
                'message': 'Email not found. Contact matches@networthtennis.com to join!'
            }), 404

        # Get player's recent matches
        cursor.execute('''
            SELECT mr.*, p1.name as opponent_name
            FROM match_reports mr
            LEFT JOIN players p1 ON
                (mr.player1_id = p1.id AND mr.player2_id = ?) OR
                (mr.player2_id = p1.id AND mr.player1_id = ?)
            WHERE (mr.player1_id = ? OR mr.player2_id = ?)
            ORDER BY mr.created_at DESC
            LIMIT 5
        ''', (player['id'], player['id'], player['id'], player['id']))

        recent_matches = cursor.fetchall()

        # Get current rank
        cursor.execute('''
            SELECT rank() OVER (ORDER BY total_score DESC) as current_rank
            FROM players
            WHERE id = ? AND is_active = 1
        ''', (player['id'],))

        rank_result = cursor.fetchone()
        current_rank = rank_result['current_rank'] if rank_result else None

        # Get total players for context
        cursor.execute('SELECT COUNT(*) as total FROM players WHERE is_active = 1')
        total_players = cursor.fetchone()['total']

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
                'matches_played': len(recent_matches)
            },
            'recent_matches': [dict(match) for match in recent_matches if match['opponent_name']]
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login error. Please try again.'
        }), 500

@app.route('/api/ladder', methods=['GET'])
def get_ladder():
    """Get current ladder rankings"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                rank() OVER (ORDER BY total_score DESC) as rank,
                id, name, skill_level, total_score,
                (SELECT COUNT(*) FROM match_reports mr
                 WHERE (mr.player1_id = players.id OR mr.player2_id = players.id)
                 AND mr.status = 'confirmed') as matches_played
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
                'total_score': row['total_score'],
                'matches_played': row['matches_played']
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
            'message': 'Error loading ladder'
        }), 500

@app.route('/api/courts', methods=['GET'])
def get_courts():
    """Get court information"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check if courts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='courts'")
        if not cursor.fetchone():
            # Return default court list if table doesn't exist yet
            default_courts = [
                {
                    'id': 'vermont_canyon',
                    'name': 'Vermont Canyon Courts',
                    'neighborhood': 'Los Feliz',
                    'lighting': True,
                    'parking': 'Street + Lot',
                    'rating': 4.5,
                    'notes': 'Well-maintained, great lighting for evening matches'
                },
                {
                    'id': 'griffith_riverside',
                    'name': 'Griffith Park - Riverside',
                    'neighborhood': 'Griffith Park',
                    'lighting': False,
                    'parking': 'Free Lot',
                    'rating': 4.2,
                    'notes': 'Scenic location, multiple courts available'
                },
                {
                    'id': 'echo_park',
                    'name': 'Echo Park Courts',
                    'neighborhood': 'Echo Park',
                    'lighting': False,
                    'parking': 'Street',
                    'rating': 4.0,
                    'notes': 'Newly resurfaced courts, convenient location'
                }
            ]
            return jsonify({
                'success': True,
                'courts': default_courts
            })

        cursor.execute('SELECT * FROM courts WHERE active = 1 ORDER BY rating DESC')
        courts = []

        for row in cursor.fetchall():
            courts.append({
                'id': row['id'],
                'name': row['name'],
                'neighborhood': row['neighborhood'],
                'lighting': bool(row['lighting']),
                'parking': row['parking'],
                'rating': float(row['rating']),
                'notes': row['notes']
            })

        conn.close()

        return jsonify({
            'success': True,
            'courts': courts
        })

    except Exception as e:
        print(f"Courts error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error loading courts'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'NET WORTH API is running!',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 NET WORTH Login API starting...")
    print("📊 Visit http://localhost:5001/api/health to check status")
    app.run(host='0.0.0.0', port=5001, debug=True)