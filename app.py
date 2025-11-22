#!/usr/bin/env python3
"""
NET WORTH - Real Tennis Ladder System
Players can log in, report scores, see dynamic rankings
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import secrets
from datetime import datetime, date
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_db():
    conn = sqlite3.connect('/home/ubuntu/dev/networth/networth_tennis.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_player_tables():
    """Initialize player authentication and scoring tables"""
    conn = get_db()
    cursor = conn.cursor()

    # Add authentication to existing players table
    cursor.execute('''
        ALTER TABLE players ADD COLUMN login_token TEXT DEFAULT NULL
    ''')

    # Create match reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            reporter_id TEXT NOT NULL,
            player1_set1 INTEGER DEFAULT 0,
            player1_set2 INTEGER DEFAULT 0,
            player2_set1 INTEGER DEFAULT 0,
            player2_set2 INTEGER DEFAULT 0,
            player1_total INTEGER DEFAULT 0,
            player2_total INTEGER DEFAULT 0,
            match_date DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            confirmed_by TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id),
            FOREIGN KEY (reporter_id) REFERENCES players (id)
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE email = ? AND is_active = 1', (email,))
        player = cursor.fetchone()
        conn.close()

        if player:
            # Generate login token
            token = secrets.token_urlsafe(32)
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE players SET login_token = ? WHERE id = ?', (token, player['id']))
            conn.commit()
            conn.close()

            # In real system, email token. For now, show token directly.
            flash(f'Your login code is: {token}', 'success')
            return redirect(url_for('token_login'))
        else:
            flash('Email not found in ladder', 'error')

    return render_template('login.html')

@app.route('/token-login', methods=['GET', 'POST'])
def token_login():
    if request.method == 'POST':
        token = request.form['token'].strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM players
            WHERE login_token = ? AND is_active = 1
        ''', (token,))
        player = cursor.fetchone()
        conn.close()

        if player:
            session['player_id'] = player['id']
            session['player_name'] = player['name']
            flash(f'Welcome back, {player["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login code', 'error')

    return render_template('token_login.html')

@app.route('/dashboard')
def dashboard():
    if 'player_id' not in session:
        return redirect(url_for('login'))

    player_id = session['player_id']

    conn = get_db()
    cursor = conn.cursor()

    # Get player info
    cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = cursor.fetchone()

    # Get recent matches
    cursor.execute('''
        SELECT mr.*, p1.name as player1_name, p2.name as player2_name
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        WHERE (mr.player1_id = ? OR mr.player2_id = ?)
        ORDER BY mr.created_at DESC
        LIMIT 5
    ''', (player_id, player_id))
    matches = cursor.fetchall()

    # Get current ladder standings
    cursor.execute('''
        SELECT rank() over (order by total_score desc) as rank,
               name, total_score, skill_level
        FROM players
        WHERE is_active = 1
        ORDER BY total_score DESC, name ASC
        LIMIT 10
    ''')
    ladder = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html', player=player, matches=matches, ladder=ladder)

@app.route('/report-match', methods=['GET', 'POST'])
def report_match():
    if 'player_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        opponent_id = request.form['opponent_id']
        player1_set1 = int(request.form.get('player1_set1', 0))
        player1_set2 = int(request.form.get('player1_set2', 0))
        player2_set1 = int(request.form.get('player2_set1', 0))
        player2_set2 = int(request.form.get('player2_set2', 0))
        notes = request.form.get('notes', '')

        # Calculate totals
        player1_total = player1_set1 + player1_set2
        player2_total = player2_set1 + player2_set2

        conn = get_db()
        cursor = conn.cursor()

        # Insert match report
        cursor.execute('''
            INSERT INTO match_reports
            (player1_id, player2_id, reporter_id,
             player1_set1, player1_set2, player2_set1, player2_set2,
             player1_total, player2_total, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['player_id'], opponent_id, session['player_id'],
            player1_set1, player1_set2, player2_set1, player2_set2,
            player1_total, player2_total, notes
        ))

        conn.commit()
        conn.close()

        flash('Match score reported! Waiting for opponent to confirm.', 'success')
        return redirect(url_for('dashboard'))

    # Get potential opponents
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, skill_level
        FROM players
        WHERE id != ? AND is_active = 1
        ORDER BY name ASC
    ''', (session['player_id'],))
    opponents = cursor.fetchall()
    conn.close()

    return render_template('report_match.html', opponents=opponents)

@app.route('/confirm-match/<int:match_id>')
def confirm_match(match_id):
    if 'player_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Get match details
    cursor.execute('''
        SELECT * FROM match_reports
        WHERE id = ? AND status = 'pending'
    ''', (match_id,))
    match = cursor.fetchone()

    if not match:
        flash('Match not found or already confirmed', 'error')
        return redirect(url_for('dashboard'))

    # Check if this player can confirm
    if match['player1_id'] != session['player_id'] and match['player2_id'] != session['player_id']:
        flash('You cannot confirm this match', 'error')
        return redirect(urlfor('dashboard'))

    # Confirm match and update scores
    cursor.execute('''
        UPDATE match_reports
        SET status = 'confirmed', confirmed_by = ?, match_date = CURRENT_DATE
        WHERE id = ?
    ''', (session['player_id'], match_id))

    # Update player scores
    if match['player1_total'] > match['player2_total']:
        cursor.execute('''
            UPDATE players
            SET total_score = total_score + ?
            WHERE id = ?
        ''', (match['player1_total'], match['player1_id']))
    elif match['player2_total'] > match['player1_total']:
        cursor.execute('''
            UPDATE players
            SET total_score = total_score + ?
            WHERE id = ?
        ''', (match['player2_total'], match['player2_id']))

    conn.commit()
    conn.close()

    flash('Match confirmed and scores updated!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/api/ladder')
def api_ladder():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rank() over (order by total_score desc) as rank,
               name, total_score, skill_level
        FROM players
        WHERE is_active = 1
        ORDER BY total_score DESC, name ASC
    ''')
    ladder = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(ladder)

@app.route('/api/matches')
def api_matches():
    player_id = request.args.get('player_id')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mr.*, p1.name as player1_name, p2.name as player2_name
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        WHERE mr.status = 'confirmed'
        ORDER BY mr.match_date DESC
        LIMIT 20
    ''')
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(matches)

if __name__ == '__main__':
    # Initialize additional tables
    init_player_tables()

    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)