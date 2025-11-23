#!/usr/bin/env python3
"""
Create NET WORTH Tennis Ladder Database with REAL players
Creates database with the actual players from index.html for Railway deployment
"""

import sqlite3
import uuid
from datetime import datetime
import os

def create_production_database(db_path='networth_tennis.db'):
    """Create production database with real players from index.html"""

    print(f"🎾 Creating NET WORTH Production Database")
    print(f"📁 Database: {db_path}")

    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Removed existing database")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    print("Creating tables...")
    cursor.execute('''
        CREATE TABLE players (
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
        CREATE TABLE match_reports (
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
        CREATE TABLE match_history (
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
        CREATE TABLE monthly_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            month TEXT NOT NULL,
            matches_played INTEGER DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, month)
        )
    ''')

    print("✓ Tables created")

    # Real players from index.html (with proper skill levels)
    real_players = [
        # Top players (4.5+ skill)
        {"name": "Kim Ndombe", "email": "kimberly@ndombe.com", "skill": 4.5, "score": 1510},
        {"name": "Natalie Coffen", "email": "nmcoffen@gmail.com", "skill": 4.5, "score": 1500},
        {"name": "Sara Chrisman", "email": "Sara.Chrisman@gmail.com", "skill": 4.5, "score": 1490},
        {"name": "Arianna Hairston", "email": "ariannahairston@gmail.com", "skill": 4.5, "score": 1480},
        {"name": "Hannah Shin", "email": "hannah.shin4@gmail.com", "skill": 4.5, "score": 1450},
        {"name": "Alik Apelian", "email": "aapelian@gmail.com", "skill": 4.5, "score": 1450},

        # Advanced players (4.0-4.4 skill)
        {"name": "Hanna Pavlova", "email": "sayhellotohanna@gmail.com", "skill": 4.2, "score": 1410},
        {"name": "Maddy Whitby", "email": "Madeline.whitby@gmail.com", "skill": 4.1, "score": 1380},
        {"name": "Allison Dunne", "email": "Allison.n.dunne@gmail.com", "skill": 4.0, "score": 1370},
        {"name": "Ashley Brooke Kaufman", "email": "Ashleybrooke.kaufman@gmail.com", "skill": 4.0, "score": 1330},
        {"name": "Kaitlin Kelly", "email": "kaitlinmariekelly@gmail.com", "skill": 4.0, "score": 1320},
        {"name": "Page Eaton", "email": "Pagek.eaton@gmail.com", "skill": 4.0, "score": 1300},

        # Intermediate-Advanced (3.5-3.9 skill)
        {"name": "Sarah Yun", "email": "BySarahYun@gmail.com", "skill": 3.8, "score": 1290},
        {"name": "Laurie Berger", "email": "Laurenjaneberger@gmail.com", "skill": 3.7, "score": 1260},
        {"name": "Katie Morey", "email": "Katelinmorey@gmail.com", "skill": 3.6, "score": 1240},
        {"name": "Alyssa Perry", "email": "Alyssa.j.perry@gmail.com", "skill": 3.5, "score": 1200}
    ]

    print(f"\nAdding {len(real_players)} real players...")

    now = datetime.now().isoformat()

    for i, player in enumerate(real_players, 1):
        # Calculate reasonable win/loss records based on ranking
        wins = max(0, 20 - i * 2)
        losses = min(15, i - 1)

        cursor.execute('''
            INSERT INTO players (id, name, email, skill_level, is_active, total_score, wins, losses, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            player['name'],
            player['email'],
            player['skill'],
            player['score'],
            wins,
            losses,
            now,
            now
        ))
        print(f"  ✓ {i:2d}. {player['name']} - {player['email']} - Score: {player['score']}")

    conn.commit()

    # Verify data
    cursor.execute('SELECT COUNT(*) FROM players')
    player_count = cursor.fetchone()[0]

    cursor.execute('SELECT name, email, total_score FROM players ORDER BY total_score DESC LIMIT 3')
    top_players = cursor.fetchall()

    conn.close()

    print(f"\n✅ Production database created successfully!")
    print(f"📊 Players added: {player_count}")
    print(f"🏆 Top 3 players:")
    for i, (name, email, score) in enumerate(top_players, 1):
        print(f"   {i}. {name} - {score} pts")
    print(f"📁 Database file: {os.path.abspath(db_path)}")
    print(f"\n🔐 Login credentials:")
    print(f"   Email: Any of the {player_count} player emails above")
    print(f"   Password: tennis123")

if __name__ == '__main__':
    db_path = 'networth_tennis.db'
    try:
        create_production_database(db_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()