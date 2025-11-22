#!/usr/bin/env python3
"""
ASHLEY KAFMAN'S ENHANCED TENNIS MATCHER
Email-based system with feedback and availability updates
"""

import sqlite3
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date, timedelta
import os
import secrets
import re
from urllib.parse import quote

class EnhancedTennisMatcher:
    def __init__(self, db_path="tennis_simple.db"):
        self.db_path = db_path
        self.init_db()
        self.club_name = "Ashley's Tennis Matching"
        self.web_url = "https://ashleytennis.com"  # Ashley will update this

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
                match_type TEXT NOT NULL,
                match_date DATE NOT NULL,
                location TEXT,
                status TEXT DEFAULT 'pending',  -- pending, confirmed_both, cancelled, completed
                confirmation_emails_sent INTEGER DEFAULT 0,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id)
            )
        """)

        # Match feedback table - SIMPLE feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_feedback (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                played BOOLEAN,
                skill_match INTEGER,  -- 1-5 scale, NULL if didn't play
                enjoyment INTEGER,     -- 1-5 scale, NULL if didn't play
                would_play_again BOOLEAN,
                feedback_text TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id),
                FOREIGN KEY (player_id) REFERENCES players (id)
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
        conn.row_factory = sqlite3.Row

        # Get all active players who haven't been matched recently
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
                    AND status != 'cancelled'
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
                suggested_time = "6:00 PM"  # Simple default

                cursor.execute("""
                    INSERT INTO matches (id, player1_id, player2_id, match_type, match_date, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (match_id, player1["id"], player2["id"], "singles", match_date, midpoint_zip))

                matches.append({
                    "id": match_id,
                    "player1": player1,
                    "player2": player2,
                    "date": match_date,
                    "location": midpoint_zip,
                    "suggested_time": suggested_time
                })

        conn.commit()
        conn.close()
        return matches

    def send_match_notifications(self, matches):
        """Send ultra-simple match notifications with confirmation links"""
        for match in matches:
            p1, p2 = match["player1"], match["player2"]

            # Create confirmation links
            yes_link_p1 = f"{self.web_url}/confirm/{match['id']}/yes/{p1['id']}"
            no_link_p1 = f"{self.web_url}/confirm/{match['id']}/no/{p1['id']}"
            yes_link_p2 = f"{self.web_url}/confirm/{match['id']}/yes/{p2['id']}"
            no_link_p2 = f"{self.web_url}/confirm/{match['id']}/no/{p2['id']}"

            # Create pretty email
            message1 = f"""🎾 TENNIS MATCH FOUND! {self.club_name}

Hi {p1['name']},

Great news! You've been matched with {p2['name']} for tennis.

📊 MATCH DETAILS:
• Opponent: {p2['name']} (Skill: {p2['skill_level']})
• Suggested Time: {match['suggested_time']}
• Location: {match['location']}

🎯 NEXT STEPS:
Can you play at this time?
[YES, I can play]({yes_link_p1})
[NO, I can't play]({no_link_p1})

Once you confirm, I'll share {p2['name']}'s contact details.

Questions? Reply to this email.

Have fun on the court! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

            message2 = f"""🎾 TENNIS MATCH FOUND! {self.club_name}

Hi {p2['name']},

Great news! You've been matched with {p1['name']} for tennis.

📊 MATCH DETAILS:
• Opponent: {p1['name']} (Skill: {p1['skill_level']})
• Suggested Time: {match['suggested_time']}
• Location: {match['location']}

🎯 NEXT STEPS:
Can you play at this time?
[YES, I can play]({yes_link_p2})
[NO, I can't play]({no_link_p2})

Once you confirm, I'll share {p1['name']}'s contact details.

Questions? Reply to this email.

Have fun on the court! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

            # Send emails
            self.send_email(p1["email"], f"🎾 Tennis Match with {p2['name']}", message1)
            self.send_email(p2["email"], f"🎾 Tennis Match with {p1['name']}", message2)

    def confirm_match(self, match_id, player_id, confirmed):
        """Handle match confirmation via email link"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get match details
        cursor.execute("""
            SELECT player1_id, player2_id, status, confirmation_emails_sent
            FROM matches WHERE id = ?
        """, (match_id,))
        match = cursor.fetchone()

        if not match:
            return False

        # Update match status
        if confirmed:
            if match['status'] == 'pending':
                # First confirmation
                if match['player1_id'] == player_id:
                    cursor.execute("UPDATE matches SET status = 'confirmed_p1' WHERE id = ?", (match_id,))
                else:
                    cursor.execute("UPDATE matches SET status = 'confirmed_p2' WHERE id = ?", (match_id,))
            elif match['status'] == 'confirmed_p1' and match['player2_id'] == player_id:
                # Second confirmation - match is confirmed!
                cursor.execute("UPDATE matches SET status = 'confirmed_both' WHERE id = ?", (match_id,))
                # Send contact info emails
                self.send_confirmed_match_emails(match_id)
            elif match['status'] == 'confirmed_p2' and match['player1_id'] == player_id:
                # Second confirmation - match is confirmed!
                cursor.execute("UPDATE matches SET status = 'confirmed_both' WHERE id = ?", (match_id,))
                # Send contact info emails
                self.send_confirmed_match_emails(match_id)
        else:
            # Player declined - cancel match
            cursor.execute("UPDATE matches SET status = 'cancelled' WHERE id = ?", (match_id,))

        conn.commit()
        conn.close()
        return True

    def send_confirmed_match_emails(self, match_id):
        """Send contact info emails for confirmed matches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row

        # Get match details
        cursor.execute("""
            SELECT m.*, p1.name as p1_name, p1.email as p1_email, p1.phone as p1_phone,
                   p2.name as p2_name, p2.email as p2_email, p2.phone as p2_phone
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id
            JOIN players p2 ON m.player2_id = p2.id
            WHERE m.id = ?
        """, (match_id,))

        match = cursor.fetchone()
        if not match:
            return

        # Send to player 1
        message1 = f"""✅ TENNIS MATCH CONFIRMED! {self.club_name}

Hi {match['p1_name']},

Great news! {match['p2_name']} also confirmed. Your match is on! 🎾

📊 MATCH DETAILS:
• Opponent: {match['p2_name']} (Skill: from their profile)
• Date: {match['match_date']}
• Location: {match['location']}

📞 CONTACT INFORMATION:
• Phone: {match['p2_phone']}
• Email: {match['p2_email']}

💬 GET STARTED:
Contact {match['p2_name']} to coordinate exact time and court location.
Suggested message: "Hi {match['p2_name']}! I'm your tennis match from {self.club_name}. When works for you?"

3 days from now, I'll ask how your match went to improve future matches.

Have a great game! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

        # Send to player 2
        message2 = f"""✅ TENNIS MATCH CONFIRMED! {self.club_name}

Hi {match['p2_name']},

Great news! {match['p1_name']} also confirmed. Your match is on! 🎾

📊 MATCH DETAILS:
• Opponent: {match['p1_name']} (Skill: from their profile)
• Date: {match['match_date']}
• Location: {match['location']}

📞 CONTACT INFORMATION:
• Phone: {match['p1_phone']}
• Email: {match['p1_email']}

💬 GET STARTED:
Contact {match['p1_name']} to coordinate exact time and court location.
Suggested message: "Hi {match['p1_name']}! I'm your tennis match from {self.club_name}. When works for you?"

3 days from now, I'll ask how your match went to improve future matches.

Have a great game! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

        # Send emails
        self.send_email(match['p1_email'], f"✅ Tennis Match Confirmed with {match['p2_name']}", message1)
        self.send_email(match['p2_email'], f"✅ Tennis Match Confirmed with {match['p1_name']}", message2)

        conn.close()

    def send_feedback_request(self, match_id):
        """Send feedback request 3 days after match"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row

        # Get match details
        cursor.execute("""
            SELECT m.*, p1.name as p1_name, p1.email as p1_email,
                   p2.name as p2_name, p2.email as p2_email,
                   p1.id as p1_id, p2.id as p2_id
            FROM matches m
            JOIN players p1 ON m.player1_id = p1.id
            JOIN players p2 ON m.player2_id = p2.id
            WHERE m.id = ? AND m.status = 'confirmed_both'
        """, (match_id,))

        match = cursor.fetchone()
        if not match:
            return

        # Check if feedback already given
        cursor.execute("""
            SELECT player_id FROM match_feedback
            WHERE match_id = ?
        """, (match_id,))
        existing_feedback = [row['player_id'] for row in cursor.fetchall()]

        # Send to player 1 if no feedback yet
        if match['p1_id'] not in existing_feedback:
            message1 = f"""🎾 How was your match? {self.club_name}

Hi {match['p1_name']},

Hope you had a great match with {match['p2_name']}! 🎾

I'd love to hear how it went - your feedback helps me make better matches for everyone.

Just reply to this email and tell me:
✅ Did you play the match?
✅ How was the skill level match? (Too easy / Just right / Too hard)
✅ Did you enjoy playing with {match['p2_name']}?
✅ Would you play with them again?

Example reply:
"Yes we played! Skill was perfect, had fun, would play again. Played at Beverly Hills courts."

Your feedback helps improve matching for everyone - just hit reply!

Thanks for being part of {self.club_name}! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

            self.send_email(match['p1_email'], f"🎾 How was your match with {match['p2_name']}?", message1)

        # Send to player 2 if no feedback yet
        if match['p2_id'] not in existing_feedback:
            message2 = f"""🎾 How was your match? {self.club_name}

Hi {match['p2_name']},

Hope you had a great match with {match['p1_name']}! 🎾

I'd love to hear how it went - your feedback helps me make better matches for everyone.

Just reply to this email and tell me:
✅ Did you play the match?
✅ How was the skill level match? (Too easy / Just right / Too hard)
✅ Did you enjoy playing with {match['p1_name']}?
✅ Would you play with them again?

Example reply:
"Yes we played! Skill was perfect, had fun, would play again. Played at Beverly Hills courts."

Your feedback helps improve matching for everyone - just hit reply!

Thanks for being part of {self.club_name}! 🎾

---
Ashley Kaufman
{self.club_name}
            """.strip()

            self.send_email(match['p2_email'], f"🎾 How was your match with {match['p1_name']}?", message2)

        conn.close()

    def process_email_feedback(self, from_email, subject, message_text):
        """Process feedback from email replies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find player by email
        cursor.execute("SELECT id, name FROM players WHERE email = ?", (from_email,))
        player = cursor.fetchone()

        if not player:
            return {"error": "Player not found"}

        # Simple feedback parsing
        message_lower = message_text.lower()

        played = any(word in message_lower for word in ["played", "play", "yes we played", "we played"])

        skill_match = 3  # Default
        if "too easy" in message_lower or "much easier" in message_lower:
            skill_match = 1
        elif "too hard" in message_lower or "much harder" in message_lower:
            skill_match = 5
        elif "just right" in message_lower or "perfect" in message_lower or "good match" in message_lower:
            skill_match = 4
        elif "perfect" in message_lower:
            skill_match = 5

        enjoyment = 3  # Default
        if "had fun" in message_lower or "enjoyed" in message_lower or "great" in message_lower:
            enjoyment = 5
        elif "fun" in message_lower:
            enjoyment = 4
        elif "boring" in message_lower or "not fun" in message_lower:
            enjoyment = 2

        would_play_again = any(word in message_lower for word in ["would play again", "play again", "yes again", "would again"])

        # Find most recent match for this player
        cursor.execute("""
            SELECT id FROM matches
            WHERE (player1_id = ? OR player2_id = ?)
            AND status = 'confirmed_both'
            ORDER BY created DESC
            LIMIT 1
        """, (player['id'], player['id']))

        recent_match = cursor.fetchone()

        if recent_match:
            feedback_id = secrets.token_urlsafe(8)
            cursor.execute("""
                INSERT INTO match_feedback
                (id, match_id, player_id, played, skill_match, enjoyment, would_play_again, feedback_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id, recent_match['id'], player['id'], played, skill_match, enjoyment, would_play_again, message_text
            ))

        conn.commit()
        conn.close()

        return {"success": True, "player": player['name']}

    def update_preferences_from_email(self, from_email, message_text):
        """Update player preferences from email reply"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find player by email
        cursor.execute("SELECT id, name FROM players WHERE email = ?", (from_email,))
        player = cursor.fetchone()

        if not player:
            return {"error": "Player not found"}

        # Parse preferences from email
        message_lower = message_text.lower()

        # Parse days
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        preferred_days = [day for day in days if day in message_lower]

        # Parse times
        times = ["morning", "afternoon", "evening"]
        preferred_times = [time for time in times if time in message_lower]

        # Update preferences
        cursor.execute("""
            UPDATE players
            SET preferred_days = ?, preferred_times = ?
            WHERE id = ?
        """, (
            json.dumps(preferred_days if preferred_days else ["monday", "wednesday", "saturday"]),
            json.dumps(preferred_times if preferred_times else ["evening"]),
            player['id']
        ))

        conn.commit()
        conn.close()

        return {"success": True, "player": player['name'], "updated_days": preferred_days, "updated_times": preferred_times}

    def send_email(self, to_email, subject, message):
        """Send email using Gmail SMTP (free)"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = os.getenv('GMAIL_EMAIL', f"tennis@{self.web_url.replace('https://', '').replace('http://', '')}")
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

    def send_follow_up_emails(self):
        """Send follow-up emails 3 days after matches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row

        # Find matches that were confirmed 3 days ago
        cursor.execute("""
            SELECT id FROM matches
            WHERE status = 'confirmed_both'
            AND date('now') = date(match_date, '+3 days')
        """)

        match_ids = [row['id'] for row in cursor.fetchall()]

        for match_id in match_ids:
            self.send_feedback_request(match_id)
            print(f"📧 Sent follow-up for match {match_id}")

        conn.close()

# CLI Interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Tennis Matcher for Ashley Kaufman')
    parser.add_argument('--run-matching', action='store_true', help='Run daily matching')
    parser.add_argument('--send-followups', action='store_true', help='Send follow-up emails')
    parser.add_argument('--confirm-match', nargs=3, metavar=('MATCH_ID', 'PLAYER_ID', 'CONFIRMED'), help='Confirm match')
    parser.add_argument('--process-email', nargs=3, metavar=('EMAIL', 'SUBJECT', 'MESSAGE_FILE'), help='Process email feedback')

    args = parser.parse_args()

    matcher = EnhancedTennisMatcher()

    if args.run_matching:
        matches = matcher.run_daily_matching()
        print(f"✅ Processed {len(matches)} matches")

    elif args.send_followups:
        matcher.send_follow_up_emails()
        print("✅ Follow-up emails sent")

    elif args.confirm_match:
        match_id, player_id, confirmed = args.confirm_match
        result = matcher.confirm_match(match_id, player_id, confirmed.lower() == 'true')
        print(f"✅ Match confirmation: {result}")

    elif args.process_email:
        email, subject, message_file = args.process_email
        try:
            with open(message_file, 'r') as f:
                message = f.read()
            result = matcher.process_email_feedback(email, subject, message)
            print(f"✅ Processed email from {result.get('player', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error processing email: {e}")

    else:
        print("🎾 Enhanced Tennis Matcher")
        print("Use --help for commands")
        print("\nAshley's quick start:")
        print("1. python simple_matcher_enhanced.py --run-matching")
        print("2. python simple_matcher_enhanced.py --send-followups")

if __name__ == "__main__":
    main()