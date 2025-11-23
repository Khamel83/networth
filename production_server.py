#!/usr/bin/env python3
"""
NET WORTH Production Server - Full Platform
Complete web application with player and admin features
"""

from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
import sqlite3
import json
import os
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

# PostgreSQL support (optional)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

app = Flask(__name__, template_folder='templates')
CORS(app)

# Fix for gunicorn - create app object
def create_app():
    return app

# For gunicorn compatibility
application = app

# Session configuration
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Environment configuration
DATABASE_URL = os.environ.get('DATABASE_URL')  # PostgreSQL URL from Railway
DB_PATH = os.environ.get('DATABASE_PATH', '/app/data/networth_tennis.db')  # Railway volume
DEFAULT_PASSWORD = os.environ.get('PLAYER_PASSWORD', 'tennis123')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@networthtennis.com')

# Detect database type
USE_POSTGRES = DATABASE_URL and DATABASE_URL.startswith('postgres') and POSTGRES_AVAILABLE

def get_db():
    """
    Get database connection - supports both SQLite and PostgreSQL
    Returns connection with dict-like row access
    """
    if USE_POSTGRES:
        # PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    else:
        # SQLite connection
        db_path = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(os.path.dirname(__file__), DB_PATH)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def db_param():
    """Return the correct parameter placeholder for the current database"""
    return '%s' if USE_POSTGRES else '?'

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'player_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'player_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        if not session.get('is_admin', False):
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_player_by_id(player_id):
    """Get player data by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE id = ? AND is_active = 1', (player_id,))
    player = cursor.fetchone()
    conn.close()
    return dict(player) if player else None

def get_player_rank(player_id, total_score):
    """Get player's current rank"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) + 1 as rank
        FROM players
        WHERE total_score > ? AND is_active = 1
    ''', (total_score,))
    rank = cursor.fetchone()['rank']
    conn.close()
    return rank

# ============================================================================
# PUBLIC ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve public ladder page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (HTML, CSS, etc.)"""
    # Allow serving HTML files
    if filename.endswith('.html'):
        return send_from_directory('.', filename)
    return send_from_directory('.', filename)

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET'])
def login_page():
    """Show login form"""
    if 'player_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login"""
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Please enter both email and password.', 'danger')
        return redirect(url_for('login_page'))

    # Check password
    if password != DEFAULT_PASSWORD:
        flash('Incorrect password.', 'danger')
        return render_template('login.html', email=email)

    # Ensure database exists
    if not ensure_database_exists():
        flash('Database setup failed. Please try again.', 'danger')
        return render_template('login.html', email=email)

    # Find player
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM players
        WHERE LOWER(email) = LOWER(?) AND is_active = 1
    ''', (email,))
    player = cursor.fetchone()
    conn.close()

    if not player:
        flash('Email not found. Contact matches@networthtennis.com to join!', 'danger')
        return render_template('login.html', email=email)

    # Set session
    session.permanent = True
    session['player_id'] = player['id']
    session['player_name'] = player['name']
    session['player_email'] = player['email']

    # Check if admin
    session['is_admin'] = (email.lower() == ADMIN_EMAIL.lower())

    flash(f'Welcome back, {player["name"]}! 🎾', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ============================================================================
# PLAYER ROUTES
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Player dashboard"""
    player_id = session['player_id']
    player = get_player_by_id(player_id)

    if not player:
        session.clear()
        flash('Player not found.', 'danger')
        return redirect(url_for('login_page'))

    # Get rank
    rank = get_player_rank(player_id, player['total_score'])

    # Get total players
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM players WHERE is_active = 1')
    total_players = cursor.fetchone()['total']

    # Get recent matches
    cursor.execute('''
        SELECT
            mr.*,
            p1.name as player1_name,
            p2.name as player2_name
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        WHERE (mr.player1_id = ? OR mr.player2_id = ?)
        AND mr.status = 'confirmed'
        ORDER BY mr.match_date DESC
        LIMIT 5
    ''', (player_id, player_id))

    recent_matches = [dict(row) for row in cursor.fetchall()]

    # Get pending matches
    cursor.execute('''
        SELECT
            mr.*,
            p1.name as player1_name,
            p2.name as player2_name
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        WHERE (mr.player1_id = ? OR mr.player2_id = ?)
        AND mr.status = 'pending'
        ORDER BY mr.created_at DESC
        LIMIT 5
    ''', (player_id, player_id))

    pending_matches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Calculate win rate
    total_matches = player['wins'] + player['losses']
    win_rate = (player['wins'] / total_matches * 100) if total_matches > 0 else 0

    return render_template('dashboard.html',
                         player=player,
                         rank=rank,
                         total_players=total_players,
                         win_rate=win_rate,
                         recent_matches=recent_matches,
                         pending_matches=pending_matches)

@app.route('/report-score', methods=['GET'])
@login_required
def report_score_page():
    """Show score reporting form"""
    # Get all players for dropdown
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, skill_level
        FROM players
        WHERE is_active = 1 AND id != ?
        ORDER BY name
    ''', (session['player_id'],))
    players = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('report_score.html', players=players)

@app.route('/report-score', methods=['POST'])
@login_required
def report_score():
    """Handle score report submission"""
    try:
        player_id = session['player_id']
        opponent_id = request.form.get('opponent_id')
        match_date = request.form.get('match_date')

        # Get set scores
        player_set1 = int(request.form.get('player_set1', 0))
        player_set2 = int(request.form.get('player_set2', 0))
        player_set3 = int(request.form.get('player_set3', 0) or 0)

        opponent_set1 = int(request.form.get('opponent_set1', 0))
        opponent_set2 = int(request.form.get('opponent_set2', 0))
        opponent_set3 = int(request.form.get('opponent_set3', 0) or 0)

        notes = request.form.get('notes', '')

        # Validation
        if not opponent_id or not match_date:
            flash('Please select an opponent and match date.', 'danger')
            return redirect(url_for('report_score_page'))

        # Validate scores
        if player_set1 == 0 and opponent_set1 == 0:
            flash('Please enter valid set scores.', 'danger')
            return redirect(url_for('report_score_page'))

        # Calculate totals
        player_total = player_set1 + player_set2 + player_set3
        opponent_total = opponent_set1 + opponent_set2 + opponent_set3

        # Insert match report
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO match_reports
            (player1_id, player2_id, reporter_id, player1_set1, player1_set2,
             player2_set1, player2_set2, player1_total, player2_total,
             match_date, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (player_id, opponent_id, player_id, player_set1, player_set2,
              opponent_set1, opponent_set2, player_total, opponent_total,
              match_date, notes, datetime.now()))

        conn.commit()
        conn.close()

        flash('Score reported successfully! Pending admin review.', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error reporting score: {str(e)}', 'danger')
        return redirect(url_for('report_score_page'))

@app.route('/history')
@login_required
def match_history():
    """Show match history for logged-in player"""
    player_id = session['player_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            mr.*,
            p1.name as player1_name,
            p2.name as player2_name,
            CASE
                WHEN mr.player1_id = ? THEN p2.name
                ELSE p1.name
            END as opponent_name,
            CASE
                WHEN mr.player1_id = ? THEN
                    CASE WHEN mr.player1_total > mr.player2_total THEN 'W' ELSE 'L' END
                ELSE
                    CASE WHEN mr.player2_total > mr.player1_total THEN 'W' ELSE 'L' END
            END as result
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        WHERE (mr.player1_id = ? OR mr.player2_id = ?)
        ORDER BY mr.match_date DESC, mr.created_at DESC
    ''', (player_id, player_id, player_id, player_id))

    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('history.html', matches=matches)

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    conn = get_db()
    cursor = conn.cursor()

    # Get stats
    cursor.execute('SELECT COUNT(*) as count FROM players WHERE is_active = 1')
    total_players = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM players WHERE is_active = 0')
    inactive_players = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM match_reports WHERE status = "pending"')
    pending_scores = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM match_reports WHERE status = "confirmed"')
    confirmed_matches = cursor.fetchone()['count']

    # Get recent activity
    cursor.execute('''
        SELECT
            mr.created_at,
            p1.name as player1_name,
            p2.name as player2_name,
            mr.status
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        ORDER BY mr.created_at DESC
        LIMIT 10
    ''')
    recent_activity = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template('admin_dashboard.html',
                         total_players=total_players,
                         inactive_players=inactive_players,
                         pending_scores=pending_scores,
                         confirmed_matches=confirmed_matches,
                         recent_activity=recent_activity)

@app.route('/admin/players')
@admin_required
def admin_players():
    """Manage players"""
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'active')

    conn = get_db()
    cursor = conn.cursor()

    if search:
        cursor.execute('''
            SELECT *,
                ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank
            FROM players
            WHERE (name LIKE ? OR email LIKE ?)
            AND is_active = ?
            ORDER BY total_score DESC
        ''', (f'%{search}%', f'%{search}%', 1 if status_filter == 'active' else 0))
    else:
        cursor.execute('''
            SELECT *,
                ROW_NUMBER() OVER (ORDER BY total_score DESC) as rank
            FROM players
            WHERE is_active = ?
            ORDER BY total_score DESC
        ''', (1 if status_filter == 'active' else 0,))

    players = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('admin_players.html',
                         players=players,
                         search=search,
                         status_filter=status_filter)

@app.route('/admin/players/add', methods=['GET', 'POST'])
@admin_required
def admin_add_player():
    """Add new player"""
    if request.method == 'GET':
        return render_template('admin_add_player.html')

    # Handle POST
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').lower().strip()
    skill_level = float(request.form.get('skill_level', 3.5))

    if not name or not email:
        flash('Name and email are required.', 'danger')
        return render_template('admin_add_player.html', name=name, email=email)

    # Check if email exists
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM players WHERE LOWER(email) = ?', (email,))
    if cursor.fetchone():
        flash('Email already exists.', 'danger')
        conn.close()
        return render_template('admin_add_player.html', name=name, email=email)

    # Create player
    player_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO players
        (id, name, email, skill_level, is_active, total_score, wins, losses, created_at)
        VALUES (?, ?, ?, ?, 1, 1000, 0, 0, ?)
    ''', (player_id, name, email, skill_level, datetime.now()))

    conn.commit()
    conn.close()

    flash(f'Player {name} added successfully!', 'success')
    return redirect(url_for('admin_players'))

@app.route('/admin/players/edit/<player_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_player(player_id):
    """Edit player"""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        player = cursor.fetchone()
        conn.close()

        if not player:
            flash('Player not found.', 'danger')
            return redirect(url_for('admin_players'))

        return render_template('admin_edit_player.html', player=dict(player))

    # Handle POST
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').lower().strip()
    skill_level = float(request.form.get('skill_level', 3.5))
    is_active = request.form.get('is_active') == '1'

    cursor.execute('''
        UPDATE players
        SET name = ?, email = ?, skill_level = ?, is_active = ?
        WHERE id = ?
    ''', (name, email, skill_level, is_active, player_id))

    conn.commit()
    conn.close()

    flash('Player updated successfully!', 'success')
    return redirect(url_for('admin_players'))

@app.route('/admin/scores')
@admin_required
def admin_scores():
    """Review pending scores"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            mr.*,
            p1.name as player1_name,
            p2.name as player2_name,
            reporter.name as reporter_name
        FROM match_reports mr
        JOIN players p1 ON mr.player1_id = p1.id
        JOIN players p2 ON mr.player2_id = p2.id
        JOIN players reporter ON mr.reporter_id = reporter.id
        WHERE mr.status = 'pending'
        ORDER BY mr.created_at DESC
    ''')

    pending_scores = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('admin_scores.html', pending_scores=pending_scores)

@app.route('/admin/scores/approve/<int:report_id>', methods=['POST'])
@admin_required
def admin_approve_score(report_id):
    """Approve a score report"""
    conn = get_db()
    cursor = conn.cursor()

    # Get the match report
    cursor.execute('SELECT * FROM match_reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()

    if not report:
        flash('Match report not found.', 'danger')
        conn.close()
        return redirect(url_for('admin_scores'))

    # Determine winner and loser
    if report['player1_total'] > report['player2_total']:
        winner_id = report['player1_id']
        loser_id = report['player2_id']
    else:
        winner_id = report['player2_id']
        loser_id = report['player1_id']

    # Update player stats
    cursor.execute('UPDATE players SET wins = wins + 1, total_score = total_score + 100 WHERE id = ?', (winner_id,))
    cursor.execute('UPDATE players SET losses = losses + 1, total_score = total_score - 50 WHERE id = ?', (loser_id,))

    # Mark report as confirmed
    cursor.execute('UPDATE match_reports SET status = "confirmed", confirmed_by = ? WHERE id = ?',
                   (session['player_id'], report_id))

    conn.commit()
    conn.close()

    flash('Score approved and ladder updated!', 'success')
    return redirect(url_for('admin_scores'))

@app.route('/admin/scores/reject/<int:report_id>', methods=['POST'])
@admin_required
def admin_reject_score(report_id):
    """Reject a score report"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('UPDATE match_reports SET status = "rejected" WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()

    flash('Score rejected.', 'info')
    return redirect(url_for('admin_scores'))

# ============================================================================
# API ROUTES (for backward compatibility)
# ============================================================================

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

@app.route('/api/ladder', methods=['GET'])
def api_get_ladder():
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

        ladder = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'ladder': ladder,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/players', methods=['GET'])
def api_get_players():
    """Get all active players"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, skill_level
            FROM players
            WHERE is_active = 1
            ORDER BY name
        ''')

        players = [dict(row) for row in cursor.fetchall()]
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

def ensure_database_exists():
    """Create database if it doesn't exist (lazy initialization)"""
    if not USE_POSTGRES and not os.path.exists(DB_PATH):
        try:
            import init_database
            init_database.initialize_sqlite(DB_PATH)
            return True
        except Exception as e:
            print(f"❌ Database creation failed: {e}")
            return False
    return True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    print(f"🎾 NET WORTH Tennis Ladder")
    print(f"🚀 Starting server on port {port}...")

    if USE_POSTGRES:
        print(f"📊 Database: PostgreSQL (Railway)")
        print(f"🔗 Connection: {DATABASE_URL[:50]}...")
    else:
        print(f"📊 Database: SQLite")
        print(f"📁 Path: {DB_PATH}")

    print(f"🔐 Admin: {ADMIN_EMAIL}")

    app.run(host='0.0.0.0', port=port, debug=debug)
