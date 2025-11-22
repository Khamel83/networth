#!/usr/bin/env python3
"""
NET WORTH API for Vercel Serverless Functions
"""

from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
def get_db():
    # Check if database file exists, create basic one if not
    db_path = '/tmp/networth_tennis.db'
    if not os.path.exists(db_path):
        # Create basic database with sample players
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create players table
        cursor.execute('''
            CREATE TABLE players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                skill_level TEXT,
                total_score INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert some sample players
        players = [
            ('kim_1', 'Kim Ndombe', 'kimberly@ndombe.com', '4.0+ (Advanced)', 51),
            ('natalie_2', 'Natalie Coffen', 'nmcoffen@gmail.com', '4.0+ (Advanced)', 50),
            ('sara_3', 'Sara Chrisman', 'Sara.Chrisman@gmail.com', '4.0+ (Advanced)', 49),
            ('arianna_4', 'Arianna Hairston', 'ariannahairston@gmail.com', '4.0+ (Advanced)', 48),
            ('hannah_5', 'Hannah Shin', 'hannah.shin4@gmail.com', '4.0+ (Advanced)', 45),
            ('alik_6', 'Alik Apelian', 'aapelian@gmail.com', '4.0+ (Advanced)', 45)
        ]

        for player in players:
            cursor.execute('''
                INSERT INTO players (id, name, email, skill_level, total_score)
                VALUES (?, ?, ?, ?, ?)
            ''', player)

        conn.commit()
        conn.close()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        # Debug log
        print(f"Login attempt: {email}")

        # Password check
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

        # Get rank
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

        player_dict = {
            'id': player['id'],
            'name': player['name'],
            'email': player['email'],
            'skill_level': player['skill_level'],
            'total_score': player['total_score'],
            'current_rank': current_rank,
            'total_players': total_players,
            'matches_played': 0
        }

        conn.close()

        return jsonify({
            'success': True,
            'message': f'Welcome back, {player["name"]}! 🎾',
            'player': player_dict,
            'recent_matches': []
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}'
        }), 500

@app.route('/ladder', methods=['GET'])
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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'NET WORTH API is running!',
        'timestamp': datetime.now().isoformat()
    })

# Export the app for Vercel
app = app