#!/usr/bin/env python3
"""
NET WORTH - Complete Tennis Management System
One-shot final implementation with all features
"""

import sqlite3
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
import random
import os
from typing import List, Dict, Tuple, Optional

class NetWorthTennisSystem:
    """Complete tennis management system for East Side Women's Ladder"""

    def __init__(self, db_path: str = '/home/ubuntu/dev/networth/networth_tennis.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize complete database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced players table
        cursor.execute('''
            ALTER TABLE players ADD COLUMN preferred_courts TEXT DEFAULT '[]'
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN availability TEXT DEFAULT '{"weekdays": false, "weekends": false, "flexible": false}'
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN match_frequency TEXT DEFAULT 'weekly'
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN last_opponent_date DATE DEFAULT NULL
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN preferred_match_times TEXT DEFAULT '{"morning": false, "afternoon": false, "evening": false}'
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN is_looking_for_match BOOLEAN DEFAULT TRUE
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN win_rate REAL DEFAULT 0.0
        ''')
        cursor.execute('''
            ALTER TABLE players ADD COLUMN matches_played INTEGER DEFAULT 0
        ''')

        # Courts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                neighborhood TEXT,
                surface TEXT DEFAULT 'Hard',
                lighting BOOLEAN DEFAULT FALSE,
                parking TEXT DEFAULT 'Street',
                notes TEXT,
                rating DECIMAL(3,2) DEFAULT 4.0,
                active BOOLEAN DEFAULT TRUE,
                busy_times TEXT DEFAULT '{"mornings": 0.3, "afternoons": 0.5, "evenings": 0.8}'
            )
        ''')

        # Match suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_suggestions (
                id TEXT PRIMARY KEY,
                player1_id TEXT,
                player2_id TEXT,
                suggestion_score REAL,
                suggested_date DATE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id)
            )
        ''')

        # Enhanced match reports
        cursor.execute('''
            ALTER TABLE match_reports ADD COLUMN court_id TEXT
        ''')
        cursor.execute('''
            ALTER TABLE match_reports ADD COLUMN match_time TIME DEFAULT '09:00'
        ''')
        cursor.execute('''
            ALTER TABLE match_reports ADD COLUMN duration_minutes INTEGER DEFAULT 90
        ''')
        cursor.execute('''
            ALTER TABLE match_reports ADD COLUMN weather TEXT DEFAULT 'Good'
        ''')

        # Insert East Side courts data
        courts = [
            {
                'id': 'vermont_canyon',
                'name': 'Vermont Canyon Courts',
                'address': 'Vermont Canyon, Los Angeles, CA',
                'neighborhood': 'Los Feliz',
                'surface': 'Hard',
                'lighting': True,
                'parking': 'Street + Lot',
                'notes': 'Well-maintained, great lighting for evening matches',
                'rating': 4.5
            },
            {
                'id': 'griffith_riverside',
                'name': 'Griffith Park - Riverside',
                'address': 'Riverside Dr, Los Angeles, CA',
                'neighborhood': 'Griffith Park',
                'surface': 'Hard',
                'lighting': False,
                'parking': 'Free Lot',
                'notes': 'Scenic location, multiple courts available',
                'rating': 4.2
            },
            {
                'id': 'griffith_merrygoround',
                'name': 'Griffith Park - Merry-Go-Round',
                'address': 'Griffith Park Dr, Los Angeles, CA',
                'neighborhood': 'Griffith Park',
                'surface': 'Hard',
                'lighting': True,
                'parking': 'Free Lot',
                'notes': 'Popular with ladder players, good conditions',
                'rating': 4.3
            },
            {
                'id': 'echo_park',
                'name': 'Echo Park Courts',
                'address': 'Echo Park Ave, Los Angeles, CA',
                'neighborhood': 'Echo Park',
                'surface': 'Hard',
                'lighting': False,
                'parking': 'Street',
                'notes': 'Newly resurfaced courts, convenient location',
                'rating': 4.0
            },
            {
                'id': 'hermon_park',
                'name': 'Hermon Park',
                'address': 'Hermon Ave, Los Angeles, CA',
                'neighborhood': 'Hermon',
                'surface': 'Hard',
                'lighting': False,
                'parking': 'Free Lot',
                'notes': 'Quiet courts, ideal for focused matches',
                'rating': 3.8
            },
            {
                'id': 'eagle_rock',
                'name': 'Eagle Rock Courts',
                'address': 'Colorado Blvd, Los Angeles, CA',
                'neighborhood': 'Eagle Rock',
                'surface': 'Hard',
                'lighting': True,
                'parking': 'Street + Lot',
                'notes': 'Community favorite, excellent maintenance',
                'rating': 4.4
            },
            {
                'id': 'cheviot_hills',
                'name': 'Cheviot Hills Recreation Center',
                'address': 'Cheviot Hills Dr, Los Angeles, CA',
                'neighborhood': 'Cheviot Hills',
                'surface': 'Hard',
                'lighting': False,
                'parking': 'Free Lot',
                'notes': 'Multiple courts, family-friendly environment',
                'rating': 4.1
            },
            {
                'id': 'poinsettia',
                'name': 'Poinsettia Park',
                'address': 'Poinsettia St, Los Angeles, CA',
                'neighborhood': 'Hollywood',
                'surface': 'Hard',
                'lighting': False,
                'parking': 'Street',
                'notes': 'Small park, intimate court setting',
                'rating': 3.7
            }
        ]

        for court in courts:
            cursor.execute('''
                INSERT OR IGNORE INTO courts (id, name, address, neighborhood, surface, lighting, parking, notes, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (court['id'], court['name'], court['address'], court['neighborhood'],
                  court['surface'], court['lighting'], court['parking'], court['notes'], court['rating']))

        conn.commit()
        conn.close()
        print("✅ Database initialized with complete schema")

    def get_skill_level_numeric(self, skill_str: str) -> float:
        """Convert skill level string to numeric value"""
        skill_map = {
            '2.5-3.0 (Beginner-Intermediate)': 2.75,
            '3.0-3.5 (Intermediate)': 3.25,
            '3.5-4.0 (Intermediate-Advanced)': 3.75,
            '4.0+ (Advanced)': 4.25
        }
        return skill_map.get(skill_str, 3.5)

    def calculate_match_score(self, player1: Dict, player2: Dict) -> float:
        """Calculate match compatibility score (0-1)"""
        score = 0.0

        # Skill compatibility (40% weight)
        skill_diff = abs(self.get_skill_level_numeric(player1['skill']) -
                        self.get_skill_level_numeric(player2['skill']))
        if skill_diff <= 0.5:
            score += 0.4
        elif skill_diff <= 1.0:
            score += 0.2

        # Availability compatibility (25% weight)
        avail1 = json.loads(player1.get('availability', '{}'))
        avail2 = json.loads(player2.get('availability', '{}'))

        if avail1.get('flexible') or avail2.get('flexible'):
            score += 0.25
        elif avail1.get('weekdays') and avail2.get('weekdays'):
            score += 0.15
        elif avail1.get('weekends') and avail2.get('weekends'):
            score += 0.15

        # Court preference compatibility (20% weight)
        courts1 = json.loads(player1.get('preferred_courts', '[]'))
        courts2 = json.loads(player2.get('preferred_courts', '[]'))

        if courts1 and courts2:
            common_courts = set(courts1) & set(courts2)
            if common_courts:
                score += 0.2 * (len(common_courts) / min(len(courts1), len(courts2)))

        # Avoid recent opponents (15% weight)
        if player1.get('last_opponent_date'):
            days_since = (date.today() - player1['last_opponent_date']).days
            if days_since > 30:
                score += 0.15
            elif days_since > 14:
                score += 0.08

        return min(score, 1.0)

    def find_best_matches(self, player_id: str, limit: int = 3) -> List[Dict]:
        """Find best match suggestions for a player"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get player info
        cursor.execute('SELECT * FROM players WHERE id = ? AND is_active = 1', (player_id,))
        player = cursor.fetchone()
        if not player:
            conn.close()
            return []

        player_dict = {
            'id': player[0],
            'name': player[1],
            'email': player[2],
            'skill': player[5],
            'availability': player.get('availability', '{}'),
            'preferred_courts': player.get('preferred_courts', '[]'),
            'last_opponent_date': player.get('last_opponent_date')
        }

        # Get all other active players
        cursor.execute('SELECT * FROM players WHERE id != ? AND is_active = 1 AND is_looking_for_match = 1',
                      (player_id,))
        all_players = cursor.fetchall()

        matches = []
        for p in all_players:
            other_dict = {
                'id': p[0],
                'name': p[1],
                'email': p[2],
                'skill': p[5],
                'availability': p.get('availability', '{}'),
                'preferred_courts': p.get('preferred_courts', '[]')
            }

            # Calculate match score
            match_score = self.calculate_match_score(player_dict, other_dict)

            if match_score > 0.6:  # Good match threshold
                matches.append({
                    'player': other_dict,
                    'score': match_score
                })

        # Sort by score and limit
        matches.sort(key=lambda x: x['score'], reverse=True)
        conn.close()

        return matches[:limit]

    def generate_weekly_suggestions(self) -> List[Dict]:
        """Generate match suggestions for all active players"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, email FROM players WHERE is_active = 1 AND is_looking_for_match = 1')
        all_players = cursor.fetchall()

        suggestions = []
        for player_id, player_name, player_email in all_players:
            matches = self.find_best_matches(player_id)

            if matches:
                # Create suggestion record
                suggestion_id = f"sug_{player_id}_{datetime.now().strftime('%Y%m%d')}"

                for match in matches:
                    cursor.execute('''
                        INSERT OR REPLACE INTO match_suggestions
                        (id, player1_id, player2_id, suggestion_score, suggested_date, status, expires_at)
                        VALUES (?, ?, ?, ?, CURRENT_DATE, 'pending', datetime('now', '+7 days'))
                    ''', (f"{suggestion_id}_{match['player']['id']}", player_id, match['player']['id'],
                          match['score']))

                    suggestions.append({
                        'player_email': player_email,
                        'player_name': player_name,
                        'suggested_opponent': match['player'],
                        'match_score': match['score']
                    })

        conn.commit()
        conn.close()
        return suggestions

    def update_player_rankings(self):
        """Update ladder rankings based on match results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all confirmed matches
        cursor.execute('''
            SELECT player1_id, player2_id, player1_total, player2_total, status
            FROM match_reports
            WHERE status = 'confirmed'
            ORDER BY created_at DESC
        ''')

        matches = cursor.fetchall()

        # Reset scores to base starting values based on skill level
        cursor.execute('''
            UPDATE players
            SET total_score = CASE
                WHEN skill = '4.0+ (Advanced)' THEN 50
                WHEN skill = '3.5-4.0 (Intermediate-Advanced)' THEN 40
                WHEN skill = '3.0-3.5 (Intermediate)' THEN 30
                WHEN skill = '2.5-3.0 (Beginner-Intermediate)' THEN 20
                ELSE 25
            END
        ''')

        # Add points from confirmed matches
        for player1_id, player2_id, player1_total, player2_total, status in matches:
            if player1_total > player2_total:
                cursor.execute('UPDATE players SET total_score = total_score + ? WHERE id = ?',
                            (player1_total, player1_id))
            elif player2_total > player1_total:
                cursor.execute('UPDATE players SET total_score = total_score + ? WHERE id = ?',
                            (player2_total, player2_id))

        # Update rankings
        cursor.execute('''
            UPDATE players SET ladder_rank = (
                SELECT COUNT(*) + 1
                FROM players p2
                WHERE p2.total_score > players.total_score
                AND p2.is_active = 1
            )
        ''')

        # Update win rates and match counts
        cursor.execute('''
            UPDATE players
            SET matches_played = (
                SELECT COUNT(*)
                FROM match_reports mr
                WHERE (mr.player1_id = players.id OR mr.player2_id = players.id)
                AND mr.status = 'confirmed'
            )
        ''')

        cursor.execute('''
            UPDATE players
            SET win_rate = (
                SELECT CASE
                    WHEN COUNT(*) > 0 THEN
                        CAST(SUM(CASE
                            WHEN (player1_id = players.id AND player1_total > player2_total) OR
                                 (player2_id = players.id AND player2_total > player1_total) THEN 1
                            ELSE 0
                        END) AS FLOAT) / COUNT(*)
                    ELSE 0
                END
                FROM match_reports mr
                WHERE (mr.player1_id = players.id OR mr.player2_id = players.id)
                AND mr.status = 'confirmed'
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Player rankings updated")

    def get_ladder_rankings(self, limit: int = 20) -> List[Dict]:
        """Get current ladder rankings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                rank() OVER (ORDER BY total_score DESC) as rank,
                id, name, email, skill_level, total_score, matches_played, win_rate
            FROM players
            WHERE is_active = 1
            ORDER BY total_score DESC
            LIMIT ?
        ''', (limit,))

        rankings = []
        for row in cursor.fetchall():
            rankings.append({
                'rank': row[0],
                'id': row[1],
                'name': row[2],
                'email': row[3],
                'skill': row[4],
                'score': row[5],
                'matches_played': row[6],
                'win_rate': f"{row[7]*100:.1f}%" if row[7] else "N/A"
            })

        conn.close()
        return rankings

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email using Gmail SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = 'networthtennis@gmail.com'
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()

            # You'll need to set up app password for Gmail
            server.login('networthtennis@gmail.com', 'YOUR_APP_PASSWORD')

            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Email failed: {str(e)}")
            return False

    def send_weekly_match_suggestions(self):
        """Send weekly match suggestion emails to all players"""
        suggestions = self.generate_weekly_suggestions()

        for suggestion in suggestions:
            if suggestion['match_score'] > 0.7:  # Only send for high-quality matches
                subject = f"🎾 NET WORTH: Tennis Match with {suggestion['suggested_opponent']['name']}"

                body = f"""
Hi {suggestion['player_name']},

Great news! We found a perfect tennis match for you:

🎾 **Opponent**: {suggestion['suggested_opponent']['name']}
📧 **Email**: {suggestion['suggested_opponent']['email']}
⭐ **Match Quality**: {suggestion['match_score']*100:.0f}% compatible

**Why this match?**
✅ Similar skill level
✅ Compatible schedules
✅ Great court preferences overlap

**Next Steps:**
1. Email {suggestion['suggested_opponent']['name']} to schedule
2. Pick one of your preferred East Side courts
3. Play and report your score!

Your ladder position improves with every win. Let's get on court!

Best regards,
NET WORTH Tennis Ladder
East Side Women's Tennis Community

---
Reply "UNSUBSCRIBE" to stop match suggestions
                """

                self.send_email(suggestion['player_email'], subject, body)

        print(f"✅ Sent {len(suggestions)} match suggestion emails")

    def send_match_reminders(self):
        """Send reminders for upcoming matches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get matches scheduled for tomorrow
        tomorrow = date.today() + timedelta(days=1)
        cursor.execute('''
            SELECT mr.*, p1.name as player1_name, p1.email as player1_email,
                   p2.name as player2_name, p2.email as player2_email,
                   c.name as court_name
            FROM match_reports mr
            JOIN players p1 ON mr.player1_id = p1.id
            JOIN players p2 ON mr.player2_id = p2.id
            LEFT JOIN courts c ON mr.court_id = c.id
            WHERE mr.match_date = ? AND mr.status = 'confirmed'
        ''', (tomorrow,))

        matches = cursor.fetchall()

        for match in matches:
            subject = f"🎾 Reminder: Tennis Match Tomorrow - {match['player1_name']} vs {match['player2_name']}"

            body = f"""
Hi {match['player1_name']},

This is your reminder for tomorrow's tennis match:

🎾 **Opponent**: {match['player2_name']}
📍 **Court**: {match['court_name'] or 'TBD'}
⏰ **Time**: {match.get('match_time', 'Morning')}

Don't forget:
- Water bottle
- Tennis racket
- Proper shoes
- Positive attitude!

Weather looks great for tennis tomorrow. Have an amazing match!

After playing, report your score at: www.networthtennis.com

Best regards,
NET WORTH Tennis Ladder
            """

            self.send_email(match['player1_email'], subject, body)
            self.send_email(match['player2_email'], subject.replace(match['player1_name'], match['player2_name']),
                           body.replace(match['player1_name'], match['player2_name']).replace(match['player2_name'], match['player1_name']))

        conn.close()
        print(f"✅ Sent {len(matches) * 2} match reminder emails")

    def run_complete_system(self):
        """Run all automated processes"""
        print("🚀 Starting NET WORTH Complete System...")

        # Update rankings
        self.update_player_rankings()

        # Send weekly match suggestions
        self.send_weekly_match_suggestions()

        # Send match reminders
        self.send_match_reminders()

        print("✅ Complete system run finished!")

# Main execution
if __name__ == "__main__":
    system = NetWorthTennisSystem()
    system.run_complete_system()