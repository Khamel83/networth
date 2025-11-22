#!/usr/bin/env python3
"""
ULTRA-SIMPLE TENNIS MATCHER
The world's simplest way to get people playing tennis

No dashboards. No profiles. No chatting.
Just matches. Straight to your phone/email.
"""

import sqlite3
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date, timedelta
import os
import secrets

class SimpleTennisMatcher:
    def __init__(self, db_path="tennis_simple.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create the simplest possible database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row

        # Players table - ONLY what we need
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                skill_level REAL NOT NULL,
                location_zip TEXT NOT NULL,
                preferred_days TEXT,  -- JSON array
                preferred_times TEXT, -- JSON array
                last_match_date DATE,
                is_active BOOLEAN DEFAULT 1,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Matches table - JUST the matches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                player1_id TEXT NOT NULL,
                player2_id TEXT NOT NULL,
                match_date DATE NOT NULL,
                location TEXT,
                status TEXT DEFAULT 'pending',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id)
            )
        """)

        conn.commit()
        conn.close()

    def add_player(self, name, email, phone="", skill_level=3.0,
                   location_zip="90210", preferred_days=None, preferred_times=None):
        """Add a new player - simple as possible"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        player_id = secrets.token_urlsafe(8)

        cursor.execute("""
            INSERT INTO players (id, name, email, phone, skill_level, location_zip,
                               preferred_days, preferred_times)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, name, email, phone, skill_level, location_zip,
            json.dumps(preferred_days or ["monday", "wednesday", "saturday"]),
            json.dumps(preferred_times or ["evening"])
        ))

        conn.commit()
        conn.close()
        return player_id

    def find_matches(self, max_distance_miles=15, skill_gap_max=1.0):
        """Find the best matches - PURELY algorithmic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all active players
        cursor.execute("""
            SELECT id, name, email, phone, skill_level, location_zip,
                   preferred_days, preferred_times, last_match_date
            FROM players
            WHERE is_active = 1
            AND (last_match_date IS NULL OR last_match_date < date('now', '-7 days'))
            ORDER BY created DESC
        """)

        players = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            players.append(dict(zip(columns, row)))
        matches = []

        for i, player1 in enumerate(players):
            for player2 in players[i+1:]:
                # Skip if they played recently
                cursor.execute("""
                    SELECT id FROM matches
                    WHERE ((player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?))
                    AND match_date >= date('now', '-14 days')
                """, (player1["id"], player2["id"], player2["id"], player1["id"]))

                if cursor.fetchone():
                    continue

                # Simple compatibility checks
                skill_gap = abs(player1["skill_level"] - player2["skill_level"])
                if skill_gap > skill_gap_max:
                    continue

                # Simple zip code distance (rough estimate)
                zip_distance = abs(int(player1["location_zip"][:3]) - int(player2["location_zip"][:3])) * 5
                if zip_distance > max_distance_miles:
                    continue

                # Check day/time compatibility
                try:
                    days1 = json.loads(player1["preferred_days"])
                    days2 = json.loads(player2["preferred_days"])
                    times1 = json.loads(player1["preferred_times"])
                    times2 = json.loads(player2["preferred_times"])
                except (json.JSONDecodeError, TypeError):
                    # Fallback to default days/times if JSON parsing fails
                    days1 = ["monday", "wednesday", "saturday"]
                    days2 = ["monday", "wednesday", "saturday"]
                    times1 = ["evening"]
                    times2 = ["evening"]

                if not (set(days1) & set(days2)) or not (set(times1) & set(times2)):
                    continue

                # Create the match
                match_id = secrets.token_urlsafe(8)
                match_date = date.today() + timedelta(days=1)

                # Find midpoint location (simplified)
                midpoint_zip = player1["location_zip"] if zip_distance < 10 else "Central LA"

                cursor.execute("""
                    INSERT INTO matches (id, player1_id, player2_id, match_date, location, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (match_id, player1["id"], player2["id"], match_date, midpoint_zip))

                matches.append({
                    "id": match_id,
                    "player1": player1,
                    "player2": player2,
                    "date": match_date,
                    "location": midpoint_zip
                })

        conn.commit()
        conn.close()
        return matches

    def send_match_notifications(self, matches, use_email=True, use_sms=False):
        """Send ultra-simple match notifications"""
        for match in matches:
            p1, p2 = match["player1"], match["player2"]

            message = f"""
🎾 TENNIS MATCH FOUND!

You've been matched with {p2['name']}!

📞 Contact: {p2['phone'] if p2['phone'] else p2['email']}
⭐ Skill Level: {p2['skill_level']}
📍 Location: {match['location']}
📅 Suggested: {match['date']}

Reply to this email if you need help finding a court or have questions.

Game on! 🎾
"""

            if use_email and p1["email"]:
                self.send_email(p1["email"], f"🎾 Tennis Match with {p2['name']}", message)

            if use_sms and p1["phone"]:
                self.send_sms(p1["phone"], message)

            # Send the same to player 2
            message = message.replace(p2['name'], p1['name']).replace(str(p2['skill_level']), str(p1['skill_level']))
            message = message.replace(p2['phone'] if p2['phone'] else p2['email'], p1['phone'] if p1['phone'] else p1['email'])

            if use_email and p2["email"]:
                self.send_email(p2["email"], f"🎾 Tennis Match with {p1['name']}", message)

            if use_sms and p2["phone"]:
                self.send_sms(p2["phone"], message)

    def send_email(self, to_email, subject, message):
        """Send email using Gmail SMTP (free)"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = os.getenv('GMAIL_EMAIL', 'tennis-match@example.com')
            msg['To'] = to_email

            # Use Gmail's free SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()

            # Use app password for Gmail
            gmail_password = os.getenv('GMAIL_PASSWORD')
            if gmail_password:
                server.login(msg['From'], gmail_password)
                server.send_message(msg)
                print(f"Email sent to {to_email}")

            server.quit()
        except Exception as e:
            print(f"Email failed to {to_email}: {e}")

    def send_sms(self, phone_number, message):
        """Send SMS using free Twilio trial or email-to-SMS gateway"""
        # Email-to-SMS gateway (works for most carriers)
        carriers = {
            'verizon': 'vtext.com',
            'att': 'txt.att.net',
            'tmobile': 'tmomail.net',
            'sprint': 'messaging.sprintpcs.com'
        }

        # For now, just log it - real SMS would require Twilio or similar
        print(f"SMS to {phone_number}: {message}")

    def run_daily_matching(self):
        """The entire daily process - ONE function call"""
        print(f"🎾 Starting daily tennis matching - {datetime.now()}")

        matches = self.find_matches()
        print(f"🎾 Found {len(matches)} potential matches")

        if matches:
            self.send_match_notifications(matches)
            print(f"🎾 Sent notifications for {len(matches)} matches")

            # Update last match dates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for match in matches:
                cursor.execute("""
                    UPDATE players SET last_match_date = date('now')
                    WHERE id = ? OR id = ?
                """, (match["player1"]["id"], match["player2"]["id"]))
            conn.commit()
            conn.close()

        print(f"🎾 Daily matching complete - {datetime.now()}")
        return matches

# CLI Interface for easy management
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Ultra-Simple Tennis Matcher')
    parser.add_argument('--add-player', nargs='+', metavar='PLAYER_INFO',
                       help='Add a new player: "Name Email Phone Skill Zip Times"')
    parser.add_argument('--run-matching', action='store_true', help='Run daily matching')
    parser.add_argument('--list-players', action='store_true', help='List all players')
    parser.add_argument('--export', help='Export data to CSV file')
    parser.add_argument('--import-data', help='Import players from file (CSV/Excel)')
    parser.add_argument('--ashley-import', help='Ashley: Import any file format automatically')

    args = parser.parse_args()

    matcher = SimpleTennisMatcher()

    if args.add_player:
        # Handle flexible player addition
        player_data = args.add_player
        if len(player_data) == 1:
            # Single string with commas
            parts = [p.strip() for p in player_data[0].split(',')]
        else:
            parts = player_data

        # Default values
        name = parts[0] if len(parts) > 0 else "Unknown"
        email = parts[1] if len(parts) > 1 else ""
        phone = parts[2] if len(parts) > 2 else ""
        skill = float(parts[3]) if len(parts) > 3 else 3.5
        zip_code = parts[4] if len(parts) > 4 else "90210"
        times = parts[5].split(',') if len(parts) > 5 else ["evening"]

        player_id = matcher.add_player(
            name=name, email=email, phone=phone,
            skill_level=skill, location_zip=zip_code,
            preferred_times=times
        )
        print(f"✅ Added player: {name} (ID: {player_id})")

    elif args.run_matching:
        matches = matcher.run_daily_matching()
        print(f"✅ Processed {len(matches)} matches")

    elif args.list_players:
        conn = sqlite3.connect(matcher.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players ORDER BY created DESC")
        players = cursor.fetchall()

        print("\n🎾 TENNIS PLAYERS:")
        print("-" * 80)
        for player in players:
            print(f"{player[1]} | {player[2]} | Skill: {player[4]} | Zip: {player[5]}")
        conn.close()

    elif args.export:
        import csv
        conn = sqlite3.connect(matcher.db_path)

        with open(args.export, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Name', 'Email', 'Phone', 'Skill', 'Zip', 'Created'])

            cursor = conn.cursor()
            cursor.execute("SELECT name, email, phone, skill_level, location_zip, created FROM players")
            for row in cursor:
                writer.writerow(row)

        conn.close()
        print(f"✅ Exported data to {args.export}")

    elif args.import_data:
        # Basic CSV import
        try:
            import pandas as pd
            df = pd.read_csv(args.import_data)

            imported = 0
            for _, row in df.iterrows():
                try:
                    matcher.add_player(
                        name=str(row.get('name', 'Unknown')),
                        email=str(row.get('email', '')),
                        phone=str(row.get('phone', '')),
                        skill_level=float(row.get('skill_level', 3.5)),
                        location_zip=str(row.get('zip_code', '90210')),
                        preferred_days=['monday', 'wednesday', 'saturday'],
                        preferred_times=['evening']
                    )
                    imported += 1
                except Exception as e:
                    print(f"Error importing row: {e}")

            print(f"✅ Imported {imported} players from {args.import_data}")
        except Exception as e:
            print(f"❌ Import failed: {e}")

    elif args.ashley_import:
        # Use Ashley's advanced import system
        try:
            from data_import import AshleyDataImporter
            importer = AshleyDataImporter()
            result = importer.import_csv_file(args.ashley_import)

            print(f"\n✅ Ashley's Import Complete!")
            print(f"📊 Total rows: {result.get('total_rows', 0)}")
            print(f"✅ Successfully imported: {result.get('imported', 0)}")

            if result.get('errors'):
                print(f"\n⚠️ Some rows had errors:")
                for error in result['errors'][:5]:
                    print(f"   {error}")

        except ImportError:
            print("❌ Ashley's import system not available. Please ensure data_import.py exists.")
        except Exception as e:
            print(f"❌ Import failed: {e}")

    else:
        print("🎾 Ultra-Simple Tennis Matcher")
        print("Use --help for commands")
        print("\nAshley's quick start:")
        print("1. python simple_matcher.py --ashley-import players.csv")
        print("2. python simple_matcher.py --run-matching")
        print("3. python simple_matcher.py --list-players")

if __name__ == "__main__":
    main()