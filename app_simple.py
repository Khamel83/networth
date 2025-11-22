#!/usr/bin/env python3
"""
NET WORTH - Beautiful Simple Tennis Ladder
Clean Canva-like design with simple login (tennis123 for everyone)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import json
from datetime import datetime, date
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_db():
    conn = sqlite3.connect('/home/ubuntu/dev/networth/networth_tennis.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize with player authentication and match tables"""
    conn = get_db()
    cursor = conn.cursor()

    # Add password to players table
    try:
        cursor.execute('ALTER TABLE players ADD COLUMN password TEXT DEFAULT "tennis123"')
    except:
        pass  # Column might already exist

    # Create match reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            player1_set1 INTEGER DEFAULT 0,
            player1_set2 INTEGER DEFAULT 0,
            player2_set1 INTEGER DEFAULT 0,
            player2_set2 INTEGER DEFAULT 0,
            player1_total INTEGER DEFAULT 0,
            player2_total INTEGER DEFAULT 0,
            match_date DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'confirmed',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
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
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM players WHERE email = ? AND is_active = 1', (email,))
        player = cursor.fetchone()
        conn.close()

        if player and password == 'tennis123':
            session['player_id'] = player['id']
            session['player_name'] = player['name']
            flash(f'Welcome back, {player["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email not found or incorrect password. Use: tennis123', 'error')

    return render_template('login_simple.html')

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

    # Get current rank
    cursor.execute('''
        SELECT rank() over (order by total_score desc) as rank
        FROM players
        WHERE id = ? AND is_active = 1
    ''', (player_id,))
    rank_result = cursor.fetchone()
    player_rank = rank_result['rank'] if rank_result else None

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

    # Get current ladder (top 20)
    cursor.execute('''
        SELECT rank() over (order by total_score desc) as rank,
               name, total_score, skill_level
        FROM players
        WHERE is_active = 1
        ORDER BY total_score DESC, name ASC
        LIMIT 20
    ''')
    ladder = cursor.fetchall()

    # Get potential opponents
    cursor.execute('''
        SELECT id, name, skill_level, total_score
        FROM players
        WHERE id != ? AND is_active = 1
        ORDER BY name ASC
    ''', (player_id,))
    opponents = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html',
                         player=player,
                         player_rank=player_rank,
                         matches=matches,
                         ladder=ladder,
                         opponents=opponents)

@app.route('/report_match', methods=['POST'])
def report_match():
    if 'player_id' not in session:
        return redirect(url_for('login'))

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

    # Determine who is player1 and player2 based on who won
    if player1_total >= player2_total:
        p1_id = session['player_id']
        p2_id = opponent_id
    else:
        p1_id = opponent_id
        p2_id = session['player_id']
        # Swap scores
        player1_total, player2_total = player2_total, player1_total
        player1_set1, player2_set1 = player2_set1, player1_set1
        player1_set2, player2_set2 = player2_set2, player1_set2

    # Insert match report
    cursor.execute('''
        INSERT INTO match_reports
        (player1_id, player2_id,
         player1_set1, player1_set2, player2_set1, player2_set2,
         player1_total, player2_total, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p1_id, p2_id,
        player1_set1, player1_set2, player2_set1, player2_set2,
        player1_total, player2_total, notes
    ))

    # Update winner's score
    cursor.execute('''
        UPDATE players
        SET total_score = total_score + ?
        WHERE id = ?
    ''', (player1_total, p1_id))

    conn.commit()
    conn.close()

    flash('Match score reported and ladder updated!', 'success')
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
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)