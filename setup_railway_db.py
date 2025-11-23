#!/usr/bin/env python3
"""
Railway database setup script
Creates the database file in the Railway volume at /app/data/
"""

import os
import sys
from datetime import datetime

def setup_railway_database():
    """Setup database for Railway deployment"""

    # Railway volume path
    db_dir = '/app/data'
    db_path = os.path.join(db_dir, 'networth_tennis.db')

    print(f"🚀 Railway Database Setup")
    print(f"📁 Database directory: {db_dir}")
    print(f"📄 Database file: {db_path}")

    # Ensure data directory exists
    os.makedirs(db_dir, exist_ok=True)
    print(f"✓ Data directory ready")

    # Check if database already exists
    if os.path.exists(db_path):
        print(f"✓ Database already exists at {db_path}")
        return True

    try:
        # Import and run database initialization
        import init_database

        print(f"🔧 Creating database at {db_path}...")
        init_database.initialize_sqlite(db_path)

        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"✅ Database created successfully!")
            print(f"📊 Database size: {size} bytes")

            # Verify database has data
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            print(f"👥 Players created: {player_count}")
            conn.close()

            return True
        else:
            print(f"❌ Database file was not created")
            return False

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = setup_railway_database()
    sys.exit(0 if success else 1)