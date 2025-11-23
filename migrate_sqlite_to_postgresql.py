#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
Run this script to transfer all data from networth_tennis.db to PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime

# Configuration
SQLITE_DB = os.environ.get('SQLITE_DB_PATH', 'networth_tennis.db')
POSTGRES_URL = os.environ.get('DATABASE_URL')  # Railway sets this automatically

if not POSTGRES_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Railway should set this automatically when you add PostgreSQL")
    sys.exit(1)

def connect_sqlite():
    """Connect to SQLite database"""
    if not os.path.exists(SQLITE_DB):
        print(f"ERROR: SQLite database not found at {SQLITE_DB}")
        sys.exit(1)

    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def connect_postgresql():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        return conn
    except Exception as e:
        print(f"ERROR connecting to PostgreSQL: {e}")
        sys.exit(1)

def migrate_players(sqlite_conn, pg_conn):
    """Migrate players table"""
    print("Migrating players...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all players from SQLite
    sqlite_cursor.execute('''
        SELECT id, name, email, skill_level, is_active, total_score, wins, losses, created_at
        FROM players
        ORDER BY created_at
    ''')

    players = sqlite_cursor.fetchall()

    if not players:
        print("  No players to migrate")
        return

    # Insert into PostgreSQL
    player_data = []
    for player in players:
        player_data.append((
            player['id'],
            player['name'],
            player['email'],
            player['skill_level'],
            bool(player['is_active']),
            player['total_score'],
            player['wins'],
            player['losses'],
            player['created_at'] if player['created_at'] else datetime.now()
        ))

    execute_values(
        pg_cursor,
        '''
        INSERT INTO players (id, name, email, skill_level, is_active, total_score, wins, losses, created_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            skill_level = EXCLUDED.skill_level,
            is_active = EXCLUDED.is_active,
            total_score = EXCLUDED.total_score,
            wins = EXCLUDED.wins,
            losses = EXCLUDED.losses
        ''',
        player_data
    )

    pg_conn.commit()
    print(f"  ✓ Migrated {len(players)} players")

def migrate_match_reports(sqlite_conn, pg_conn):
    """Migrate match reports"""
    print("Migrating match reports...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all match reports from SQLite
    sqlite_cursor.execute('''
        SELECT
            player1_id, player2_id, reporter_id,
            player1_set1, player1_set2,
            player2_set1, player2_set2,
            player1_total, player2_total,
            match_date, status, notes, confirmed_by, created_at
        FROM match_reports
        ORDER BY created_at
    ''')

    reports = sqlite_cursor.fetchall()

    if not reports:
        print("  No match reports to migrate")
        return

    # Insert into PostgreSQL
    report_data = []
    for report in reports:
        report_data.append((
            report['player1_id'],
            report['player2_id'],
            report['reporter_id'],
            report['player1_set1'] or 0,
            report['player1_set2'] or 0,
            0,  # player1_set3 (doesn't exist in old schema)
            report['player2_set1'] or 0,
            report['player2_set2'] or 0,
            0,  # player2_set3
            report['player1_total'] or 0,
            report['player2_total'] or 0,
            report['match_date'],
            report['status'] or 'pending',
            report['notes'],
            report['confirmed_by'],
            report['created_at'] if report['created_at'] else datetime.now()
        ))

    execute_values(
        pg_cursor,
        '''
        INSERT INTO match_reports
        (player1_id, player2_id, reporter_id, player1_set1, player1_set2, player1_set3,
         player2_set1, player2_set2, player2_set3, player1_total, player2_total,
         match_date, status, notes, confirmed_by, created_at)
        VALUES %s
        ''',
        report_data
    )

    pg_conn.commit()
    print(f"  ✓ Migrated {len(reports)} match reports")

def verify_migration(sqlite_conn, pg_conn):
    """Verify the migration was successful"""
    print("\nVerifying migration...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Check player counts
    sqlite_cursor.execute('SELECT COUNT(*) FROM players')
    sqlite_player_count = sqlite_cursor.fetchone()[0]

    pg_cursor.execute('SELECT COUNT(*) FROM players')
    pg_player_count = pg_cursor.fetchone()[0]

    print(f"  Players: SQLite={sqlite_player_count}, PostgreSQL={pg_player_count}", end="")
    if sqlite_player_count == pg_player_count:
        print(" ✓")
    else:
        print(" ✗ MISMATCH!")

    # Check match report counts
    sqlite_cursor.execute('SELECT COUNT(*) FROM match_reports')
    sqlite_report_count = sqlite_cursor.fetchone()[0]

    pg_cursor.execute('SELECT COUNT(*) FROM match_reports')
    pg_report_count = pg_cursor.fetchone()[0]

    print(f"  Match Reports: SQLite={sqlite_report_count}, PostgreSQL={pg_report_count}", end="")
    if sqlite_report_count == pg_report_count:
        print(" ✓")
    else:
        print(" ✗ MISMATCH!")

    # Check a sample player
    sqlite_cursor.execute('SELECT name, email, total_score FROM players ORDER BY total_score DESC LIMIT 1')
    sqlite_top = sqlite_cursor.fetchone()

    pg_cursor.execute('SELECT name, email, total_score FROM players ORDER BY total_score DESC LIMIT 1')
    pg_top = pg_cursor.fetchone()

    print(f"  Top Player: {sqlite_top[0]} ({sqlite_top[2]} pts) ", end="")
    if sqlite_top[0] == pg_top[0] and sqlite_top[2] == pg_top[2]:
        print("✓")
    else:
        print("✗ MISMATCH!")

def main():
    """Main migration function"""
    print("=" * 60)
    print("NET WORTH Tennis Ladder - SQLite to PostgreSQL Migration")
    print("=" * 60)
    print()

    # Connect to both databases
    print("Connecting to databases...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgresql()
    print("  ✓ Connected to both databases")
    print()

    try:
        # Run migrations
        migrate_players(sqlite_conn, pg_conn)
        migrate_match_reports(sqlite_conn, pg_conn)

        # Verify
        verify_migration(sqlite_conn, pg_conn)

        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Update DATABASE_PATH environment variable to use PostgreSQL")
        print("2. Restart your Railway service")
        print("3. Test the application")
        print("4. Keep SQLite backup for safety")

    except Exception as e:
        print(f"\n✗ ERROR during migration: {e}")
        print("Rolling back PostgreSQL changes...")
        pg_conn.rollback()
        sys.exit(1)

    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    main()
