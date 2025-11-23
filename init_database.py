#!/usr/bin/env python3
"""
Initialize NET WORTH Tennis Ladder Database (SQLite)
Creates database with schema and sample player data for testing
"""

import sqlite3
import uuid
from datetime import datetime
import os

def initialize_sqlite(db_path='networth_tennis.db'):
    """Initialize SQLite database with schema only (for production)"""

    print(f"📁 Database not found. Creating: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating tables...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            skill_level REAL NOT NULL,
            is_active INTEGER DEFAULT 1,
            total_score INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_reports (
            id TEXT PRIMARY KEY,
            winner_id TEXT NOT NULL,
            loser_id TEXT NOT NULL,
            winner_sets INTEGER NOT NULL,
            loser_sets INTEGER NOT NULL,
            winner_games INTEGER,
            loser_games INTEGER,
            match_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_by TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (winner_id) REFERENCES players(id),
            FOREIGN KEY (loser_id) REFERENCES players(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_history (
            id TEXT PRIMARY KEY,
            winner_id TEXT NOT NULL,
            loser_id TEXT NOT NULL,
            winner_sets INTEGER NOT NULL,
            loser_sets INTEGER NOT NULL,
            winner_games INTEGER,
            loser_games INTEGER,
            match_date TEXT NOT NULL,
            confirmed_by TEXT,
            created_at TEXT,
            FOREIGN KEY (winner_id) REFERENCES players(id),
            FOREIGN KEY (loser_id) REFERENCES players(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_matches (
            id TEXT PRIMARY KEY,
            player_id TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            matches_played INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, month, year)
        )
    ''')

    conn.commit()

    # Add admin player if no players exist
    cursor.execute("SELECT COUNT(*) FROM players")
    if cursor.fetchone()[0] == 0:
        print("Adding admin player...")
        cursor.execute('''
            INSERT INTO players (id, name, email, skill_level, is_active, total_score, wins, losses, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            'Admin User',
            'admin@networthtennis.com',
            4.0,
            1200,
            0,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        print("✅ Admin player added")

    conn.commit()
    conn.close()
    print("✅ Database tables created successfully")

def init_database(db_path='networth_tennis.db', force=False):
    """Initialize database with schema and sample data"""

    print("=" * 60)
    print("NET WORTH Tennis Ladder - Database Initialization")
    print("=" * 60)
    print()

    # Check if database already exists
    if os.path.exists(db_path):
        if not force:
            print(f"⚠️  Database '{db_path}' already exists.")
            print("   Use --force to overwrite or delete the file manually.")
            return
        os.remove(db_path)
        print(f"✓ Removed existing database")

    print(f"Creating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating tables...")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            skill_level REAL NOT NULL,
            is_active INTEGER DEFAULT 1,
            total_score INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            reporter_id TEXT NOT NULL,
            player1_set1 INTEGER NOT NULL,
            player1_set2 INTEGER NOT NULL,
            player1_set3 INTEGER DEFAULT 0,
            player2_set1 INTEGER NOT NULL,
            player2_set2 INTEGER NOT NULL,
            player2_set3 INTEGER DEFAULT 0,
            player1_total INTEGER NOT NULL,
            player2_total INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            confirmed_by TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (player1_id) REFERENCES players(id),
            FOREIGN KEY (player2_id) REFERENCES players(id),
            FOREIGN KEY (reporter_id) REFERENCES players(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_id TEXT NOT NULL,
            loser_id TEXT NOT NULL,
            match_date TEXT NOT NULL,
            winner_score INTEGER NOT NULL,
            loser_score INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (winner_id) REFERENCES players(id),
            FOREIGN KEY (loser_id) REFERENCES players(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            month TEXT NOT NULL,
            matches_played INTEGER DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, month)
        )
    ''')

    print("✓ Tables created")

    # Insert sample players
    print("\nAdding sample players...")

    sample_players = [
        # Admin player (matches@networthtennis.com)
        {
            'id': str(uuid.uuid4()),
            'name': 'Admin Player',
            'email': 'admin@networthtennis.com',
            'skill_level': 4.5,
            'total_score': 1200,
            'wins': 8,
            'losses': 2
        },
        # Test players with varying skill levels
        {
            'id': str(uuid.uuid4()),
            'name': 'John Smith',
            'email': 'john.smith@example.com',
            'skill_level': 4.0,
            'total_score': 1450,
            'wins': 15,
            'losses': 3
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@example.com',
            'skill_level': 4.5,
            'total_score': 1350,
            'wins': 12,
            'losses': 5
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Mike Williams',
            'email': 'mike.williams@example.com',
            'skill_level': 3.5,
            'total_score': 1250,
            'wins': 10,
            'losses': 7
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Emily Davis',
            'email': 'emily.davis@example.com',
            'skill_level': 4.0,
            'total_score': 1180,
            'wins': 7,
            'losses': 8
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'David Brown',
            'email': 'david.brown@example.com',
            'skill_level': 3.0,
            'total_score': 1100,
            'wins': 6,
            'losses': 10
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Lisa Martinez',
            'email': 'lisa.martinez@example.com',
            'skill_level': 3.5,
            'total_score': 1050,
            'wins': 5,
            'losses': 9
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Tom Anderson',
            'email': 'tom.anderson@example.com',
            'skill_level': 4.0,
            'total_score': 980,
            'wins': 4,
            'losses': 11
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Jennifer Taylor',
            'email': 'jennifer.taylor@example.com',
            'skill_level': 3.0,
            'total_score': 920,
            'wins': 3,
            'losses': 12
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Chris Wilson',
            'email': 'chris.wilson@example.com',
            'skill_level': 2.5,
            'total_score': 850,
            'wins': 2,
            'losses': 14
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Amy Thomas',
            'email': 'amy.thomas@example.com',
            'skill_level': 3.5,
            'total_score': 800,
            'wins': 1,
            'losses': 15
        }
    ]

    now = datetime.now().isoformat()

    for player in sample_players:
        cursor.execute('''
            INSERT INTO players (id, name, email, skill_level, is_active, total_score, wins, losses, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ''', (
            player['id'],
            player['name'],
            player['email'],
            player['skill_level'],
            player['total_score'],
            player['wins'],
            player['losses'],
            now,
            now
        ))
        print(f"  ✓ Added {player['name']} ({player['email']}) - Rank score: {player['total_score']}")

    conn.commit()

    # Verify data
    cursor.execute('SELECT COUNT(*) as count FROM players')
    player_count = cursor.fetchone()[0]

    cursor.execute('SELECT name, email, total_score FROM players ORDER BY total_score DESC LIMIT 1')
    top_player = cursor.fetchone()

    conn.close()

    print()
    print("=" * 60)
    print("✓ Database initialized successfully!")
    print("=" * 60)
    print()
    print(f"📊 Players added: {player_count}")
    print(f"🏆 Top player: {top_player[0]} ({top_player[2]} pts)")
    print(f"📁 Database file: {os.path.abspath(db_path)}")
    print()
    print("Default login credentials:")
    print("  Email: admin@networthtennis.com")
    print("  Password: tennis123")
    print()
    print("Test with:")
    print("  python3 production_server.py")
    print("  Then visit: http://localhost:5000")
    print()

if __name__ == '__main__':
    import sys

    # Parse arguments
    force = '--force' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--force']
    db_path = args[0] if args else 'networth_tennis.db'

    try:
        init_database(db_path, force=force)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
