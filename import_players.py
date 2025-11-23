#!/usr/bin/env python3
"""
Import players from CSV file into NET WORTH Tennis Ladder database

CSV Format:
name,email,skill_level
John Smith,john@example.com,4.0
Sarah Johnson,sarah@example.com,4.5

Optional columns: total_score, wins, losses
"""

import sqlite3
import csv
import uuid
from datetime import datetime
import sys
import os

def import_players_from_csv(csv_file, db_path='networth_tennis.db', skip_duplicates=True):
    """Import players from CSV file"""

    print("=" * 60)
    print("NET WORTH Tennis Ladder - Player Import")
    print("=" * 60)
    print()

    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file '{csv_file}' not found")
        return False

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Error: Database '{db_path}' not found")
        print("   Run 'python3 init_database.py --force' first")
        return False

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read CSV file
    print(f"Reading CSV file: {csv_file}")
    players_to_import = []

    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)

            # Validate headers
            required_headers = {'name', 'email', 'skill_level'}
            headers = set(reader.fieldnames)

            if not required_headers.issubset(headers):
                missing = required_headers - headers
                print(f"❌ Error: CSV missing required columns: {missing}")
                print(f"   Required: name, email, skill_level")
                print(f"   Found: {', '.join(reader.fieldnames)}")
                return False

            # Read players
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    name = row['name'].strip()
                    email = row['email'].strip().lower()
                    skill_level = float(row['skill_level'])

                    # Optional fields
                    total_score = int(row.get('total_score', 1000))
                    wins = int(row.get('wins', 0))
                    losses = int(row.get('losses', 0))

                    # Validate
                    if not name or not email:
                        print(f"⚠️  Warning: Row {row_num} skipped (empty name or email)")
                        continue

                    if skill_level < 2.0 or skill_level > 7.0:
                        print(f"⚠️  Warning: Row {row_num} has invalid skill level {skill_level} (should be 2.0-7.0)")
                        continue

                    if '@' not in email:
                        print(f"⚠️  Warning: Row {row_num} has invalid email: {email}")
                        continue

                    players_to_import.append({
                        'name': name,
                        'email': email,
                        'skill_level': skill_level,
                        'total_score': total_score,
                        'wins': wins,
                        'losses': losses
                    })

                except (ValueError, KeyError) as e:
                    print(f"⚠️  Warning: Row {row_num} skipped ({e})")
                    continue

        print(f"✓ Found {len(players_to_import)} valid players in CSV")

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False

    if not players_to_import:
        print("❌ No valid players to import")
        return False

    print()

    # Import players
    print("Importing players...")
    imported = 0
    skipped = 0
    errors = 0
    now = datetime.now().isoformat()

    for player in players_to_import:
        try:
            # Check if email already exists
            cursor.execute('SELECT id, name FROM players WHERE LOWER(email) = ?', (player['email'],))
            existing = cursor.fetchone()

            if existing:
                if skip_duplicates:
                    print(f"  ⊘ Skipped: {player['name']} ({player['email']}) - email already exists")
                    skipped += 1
                    continue
                else:
                    # Update existing player
                    cursor.execute('''
                        UPDATE players
                        SET name = ?, skill_level = ?, total_score = ?, wins = ?, losses = ?, updated_at = ?
                        WHERE LOWER(email) = ?
                    ''', (player['name'], player['skill_level'], player['total_score'],
                          player['wins'], player['losses'], now, player['email']))
                    print(f"  ↻ Updated: {player['name']} ({player['email']})")
                    imported += 1
            else:
                # Insert new player
                player_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO players
                    (id, name, email, skill_level, is_active, total_score, wins, losses, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                ''', (player_id, player['name'], player['email'], player['skill_level'],
                      player['total_score'], player['wins'], player['losses'], now, now))
                print(f"  ✓ Added: {player['name']} ({player['email']}) - Skill {player['skill_level']}")
                imported += 1

        except Exception as e:
            print(f"  ✗ Error importing {player['name']}: {e}")
            errors += 1

    # Commit changes
    conn.commit()

    # Get final count
    cursor.execute('SELECT COUNT(*) FROM players WHERE is_active = 1')
    total_players = cursor.fetchone()[0]

    conn.close()

    print()
    print("=" * 60)
    print("Import Complete!")
    print("=" * 60)
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total active players in database: {total_players}")
    print()

    return imported > 0


def create_sample_csv(output_file='players_template.csv'):
    """Create a sample CSV template for importing players"""

    print(f"Creating sample CSV template: {output_file}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'skill_level', 'total_score', 'wins', 'losses'])
        writer.writeheader()

        # Sample data
        writer.writerow({
            'name': 'John Smith',
            'email': 'john.smith@example.com',
            'skill_level': 4.0,
            'total_score': 1200,
            'wins': 5,
            'losses': 2
        })
        writer.writerow({
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@example.com',
            'skill_level': 4.5,
            'total_score': 1300,
            'wins': 8,
            'losses': 3
        })
        writer.writerow({
            'name': 'Mike Williams',
            'email': 'mike@example.com',
            'skill_level': 3.5,
            'total_score': 1000,
            'wins': 0,
            'losses': 0
        })

    print(f"✓ Sample CSV created: {output_file}")
    print()
    print("Edit this file with your real player data, then run:")
    print(f"  python3 import_players.py {output_file}")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create template:  python3 import_players.py --template")
        print("  Import players:   python3 import_players.py players.csv")
        print("  Update existing:  python3 import_players.py players.csv --update")
        print()
        print("CSV Format (required columns):")
        print("  name,email,skill_level")
        print()
        print("Optional columns:")
        print("  total_score (default: 1000)")
        print("  wins (default: 0)")
        print("  losses (default: 0)")
        sys.exit(1)

    if sys.argv[1] == '--template':
        create_sample_csv()
    else:
        csv_file = sys.argv[1]
        skip_duplicates = '--update' not in sys.argv

        success = import_players_from_csv(csv_file, skip_duplicates=skip_duplicates)

        if success:
            print("Next steps:")
            print("  1. Test locally: python3 production_server.py")
            print("  2. Visit: http://localhost:5000")
            print("  3. Login with any imported player email + password")
            print()
        else:
            sys.exit(1)
