#!/usr/bin/env python3
"""
NET WORTH - LA East Side Tennis Ladder System
SAFE VERSION - No emails, no texts, just local matching and rankings
"""

import sqlite3
import json
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import random
import hashlib

class NetWorthTennisSafe:
    """NET WORTH Tennis Matching - Safe Version (No Outgoing Communications)"""

    def __init__(self, db_path="networth_tennis.db"):
        self.db_path = db_path
        self.web_url = "https://networthtennis.com"
        self.init_db()

    def init_db(self):
        """Initialize database with Ashley's ladder structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                skill_level TEXT,
                location TEXT DEFAULT 'LA East Side',
                total_score INTEGER DEFAULT 0,
                ladder_rank INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_matched DATE
            )
        """)

        # Monthly matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_matches (
                id TEXT PRIMARY KEY,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                player1_id TEXT NOT NULL,
                player2_id TEXT NOT NULL,
                player1_games INTEGER,
                player2_games INTEGER,
                match_status TEXT DEFAULT 'pending',
                suggested_court TEXT,
                suggested_date DATE,
                UNIQUE(month, year, player1_id, player2_id)
            )
        """)

        # Match history for rankings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_history (
                id TEXT PRIMARY KEY,
                player1_id TEXT NOT NULL,
                player2_id TEXT NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                player1_games INTEGER DEFAULT 0,
                player2_games INTEGER DEFAULT 0,
                played_date DATE,
                match_completed BOOLEAN DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def generate_player_id(self, email: str) -> str:
        """Generate consistent player ID from email"""
        return hashlib.md5(email.encode()).hexdigest()[:8]

    def add_ashley_players(self):
        """Add all of Ashley's players to the system"""
        from ashley_data import ASHLEY_PLAYERS, INACTIVE_PLAYERS

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Add active players
        for i, player in enumerate(ASHLEY_PLAYERS):
            player_id = self.generate_player_id(player["email"])
            cursor.execute("""
                INSERT OR REPLACE INTO players
                (id, name, email, phone, skill_level, total_score, ladder_rank, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                player_id,
                player["name"],
                player["email"],
                player["phone"],
                self.estimate_skill_level(player["total_score"]),
                player["total_score"],
                i + 1  # Current ladder ranking
            ))

        # Add inactive players
        for player in INACTIVE_PLAYERS:
            player_id = self.generate_player_id(player["email"])
            cursor.execute("""
                INSERT OR REPLACE INTO players
                (id, name, email, phone, skill_level, total_score, ladder_rank, is_active)
                VALUES (?, ?, ?, ?, ?, ?, NULL, 0)
            """, (
                player_id,
                player["name"],
                player["email"],
                player["phone"],
                self.estimate_skill_level(player["total_score"]),
                player["total_score"]
            ))

        conn.commit()
        conn.close()

    def estimate_skill_level(self, total_score: int) -> str:
        """Estimate NTRP skill level based on ladder performance"""
        if total_score >= 45:
            return "4.0+ (Advanced)"
        elif total_score >= 30:
            return "3.5-4.0 (Intermediate-Advanced)"
        elif total_score >= 15:
            return "3.0-3.5 (Intermediate)"
        else:
            return "2.5-3.0 (Beginner-Intermediate)"

    def get_active_players(self) -> List[Dict]:
        """Get all active players for matching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email, phone, skill_level, total_score, ladder_rank
            FROM players
            WHERE is_active = 1
            ORDER BY total_score DESC, name ASC
        """)

        players = []
        for row in cursor.fetchall():
            player_id, name, email, phone, skill, score, rank = row
            players.append({
                'id': player_id,
                'name': name,
                'email': email,
                'phone': phone,
                'skill_level': skill,
                'total_score': score,
                'ladder_rank': rank
            })

        conn.close()
        return players

    def get_ladder_rankings(self) -> List[Dict]:
        """Get current ladder rankings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, email, skill_level, total_score, ladder_rank
            FROM players
            WHERE is_active = 1
            ORDER BY total_score DESC, name ASC
        """)

        rankings = []
        for i, (name, email, skill, score, rank) in enumerate(cursor.fetchall(), 1):
            rankings.append({
                'rank': i,
                'name': name,
                'email': email,
                'skill_level': skill,
                'total_score': score,
                'current_rank': rank
            })

        conn.close()
        return rankings

    def generate_monthly_pairings(self, month: str = None, year: int = None) -> List[Dict]:
        """Generate monthly pairings for the ladder"""
        if month is None:
            month = datetime.now().strftime("%B")
        if year is None:
            year = datetime.now().year

        players = self.get_active_players()
        if len(players) < 2:
            return []

        # Sort players by current ranking
        players.sort(key=lambda x: x['total_score'], reverse=True)

        # Create pairings (snake draft style for competitive balance)
        pairings = []
        unpaired = players.copy()

        while len(unpaired) >= 2:
            # Take top and bottom for competitive balance
            player1 = unpaired[0]
            player2 = unpaired[-1]

            # Remove from unpaired list
            unpaired = unpaired[1:-1]

            # Create pairing
            pairing_id = hashlib.md5(f"{player1['id']}{player2['id']}{month}{year}".encode()).hexdigest()[:8]

            # Suggest a court (from Ashley's recommendations)
            courts = [
                "Vermont Canyon", "Griffith Park - Riverside", "Griffith Park - Merry-Go-Round",
                "Echo Park", "Hermon Park", "Eagle Rock", "Cheviot Hills", "Poinsettia Park"
            ]
            suggested_court = random.choice(courts)

            # Suggest date (mid-month)
            import calendar
            last_day = calendar.monthrange(year, datetime.strptime(month, "%B").month)[1]
            suggested_date = f"{year}-{datetime.strptime(month, '%B').month:02d}-{15:02d}"

            pairings.append({
                'id': pairing_id,
                'month': month,
                'year': year,
                'player1': player1,
                'player2': player2,
                'suggested_court': suggested_court,
                'suggested_date': suggested_date,
                'match_status': 'pending'
            })

        # Handle odd player (gets a bye)
        if unpaired:
            unpaired_player = unpaired[0]
            pairings.append({
                'id': 'bye_' + unpaired_player['id'],
                'month': month,
                'year': year,
                'player1': unpaired_player,
                'player2': None,
                'suggested_court': None,
                'suggested_date': None,
                'match_status': 'bye'
            })

        # Save pairings to database
        self.save_pairings(pairings)

        return pairings

    def save_pairings(self, pairings: List[Dict]):
        """Save generated pairings to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for pairing in pairings:
            if pairing['player2']:  # Skip bye pairings
                cursor.execute("""
                    INSERT OR REPLACE INTO monthly_matches
                    (id, month, year, player1_id, player2_id, match_status, suggested_court, suggested_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pairing['id'],
                    pairing['month'],
                    pairing['year'],
                    pairing['player1']['id'],
                    pairing['player2']['id'],
                    pairing['match_status'],
                    pairing['suggested_court'],
                    pairing['suggested_date']
                ))

        conn.commit()
        conn.close()

    def show_monthly_matches(self, month: str = None, year: int = None):
        """Display monthly matches without sending emails"""
        if month is None:
            month = datetime.now().strftime("%B")
        if year is None:
            year = datetime.now().year

        # Generate or retrieve pairings
        pairings = self.generate_monthly_pairings(month, year)

        print(f"\n🎾 NET WORTH - {month} {year} Tennis Ladder Pairings")
        print("=" * 80)
        print(f"🏆 Ladder System: Total Games Won Ranking")
        print(f"📍 Focus: LA East Side Courts")
        print(f"📧 Format: One match per month, coordinate directly with opponent")
        print("=" * 80)

        for i, pairing in enumerate(pairings, 1):
            if pairing['player2']:  # Regular match
                player1 = pairing['player1']
                player2 = pairing['player2']

                print(f"\n{i}. {player1['name']} vs {player2['name']}")
                print(f"   📊 Ranking: #{player1['total_score']} pts vs #{player2['total_score']} pts")
                print(f"   🎯 Skills: {player1['skill_level']} vs {player2['skill_level']}")
                print(f"   📍 Suggested: {pairing['suggested_court']} around {pairing['suggested_date']}")
                print(f"   📱 Contact: {player1['email']} & {player2['email']}")

            else:  # Bye
                player = pairing['player1']
                print(f"\n{i}. {player['name']} - BYE THIS MONTH")
                print(f"   📊 Current ranking: {player['total_score']} points")

        print(f"\n📋 Instructions:")
        print(f"   • Contact your opponent directly to schedule")
        print(f"   • Play 2-set format (total games count toward ranking)")
        print(f"   • Report scores in the system")
        print(f"   • Split court costs, bring fresh balls")

    def show_current_ladder(self):
        """Display current ladder standings"""
        rankings = self.get_ladder_rankings()

        print(f"\n🏆 NET WORTH - LA East Side Tennis Ladder")
        print("=" * 80)
        print(f"📊 Rank by Total Games Won (All-Time)")
        print("=" * 80)

        for player in rankings:
            print(f"{player['rank']:2d}. {player['name']:<25} | {player['total_score']:2d} pts | {player['skill_level']}")

        print(f"\n📈 Active Players: {len(rankings)}")
        print(f"🎯 Next month pairings will be generated automatically")

    def what_would_be_emailed(self, month: str = None, year: int = None) -> List[Dict]:
        """Show what emails would be sent (without actually sending)"""
        if month is None:
            month = datetime.now().strftime("%B")
        if year is None:
            year = datetime.now().year

        pairings = self.generate_monthly_pairings(month, year)

        email_previews = []
        for pairing in pairings:
            if pairing['player2']:  # Regular match
                # Email for player 1
                email_previews.append({
                    'to': pairing['player1']['email'],
                    'to_name': pairing['player1']['name'],
                    'subject': f'🎾 NET WORTH {month} Match: {pairing["player2"]["name"]}',
                    'body': f'''Hi {pairing["player1"]["name"]}!

Your NET WORTH {month} tennis ladder match has been scheduled!

OPPONENT: {pairing["player2"]["name"]}
CONTACT: {pairing["player2"]["email"]} | {pairing["player2"]["phone"]}
SKILL LEVEL: {pairing["player2"]["skill_level"]}
SUGGESTED COURT: {pairing["suggested_court"]}
SUGGESTED DATE: Around {pairing["suggested_date"]}

WHAT TO DO:
• Contact {pairing["player2"]["name"]} directly to schedule
• Play 2-set format (total games won count toward ranking)
• Split court costs and bring fresh balls
• Report your score after the match

Current ladder rankings are available at: {self.web_url}

Game on! 🎾

NET WORTH Tennis
{self.web_url}'''
                })

                # Email for player 2
                email_previews.append({
                    'to': pairing['player2']['email'],
                    'to_name': pairing['player2']['name'],
                    'subject': f'🎾 NET WORTH {month} Match: {pairing["player1"]["name"]}',
                    'body': f'''Hi {pairing["player2"]["name"]}!

Your NET WORTH {month} tennis ladder match has been scheduled!

OPPONENT: {pairing["player1"]["name"]}
CONTACT: {pairing["player1"]["email"]} | {pairing["player1"]["phone"]}
SKILL LEVEL: {pairing["player1"]["skill_level"]}
SUGGESTED COURT: {pairing["suggested_court"]}
SUGGESTED DATE: Around {pairing["suggested_date"]}

WHAT TO DO:
• Contact {pairing["player1"]["name"]} directly to schedule
• Play 2-set format (total games won count toward ranking)
• Split court costs and bring fresh balls
• Report your score after the match

Current ladder rankings are available at: {self.web_url}

Game on! 🎾

NET WORTH Tennis
{self.web_url}'''
                })

            else:  # Bye
                email_previews.append({
                    'to': pairing['player1']['email'],
                    'to_name': pairing['player1']['name'],
                    'subject': f'🎾 NET WORTH {month} - Bye This Month',
                    'body': f'''Hi {pairing["player1"]["name"]}!

You have a bye this month in the NET WORTH tennis ladder.

This means you get a month off - no match required this {month}.

You'll be back in the pairings next month!
Current ladder rankings: {self.web_url}

Enjoy the break! 🎾

NET WORTH Tennis
{self.web_url}'''
                })

        return email_previews

# Command line interface
if __name__ == "__main__":
    import sys

    matcher = NetWorthTennisSafe()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--setup":
            print("🏗️ Setting up NET WORTH with Ashley's players...")
            matcher.add_ashley_players()
            print("✅ Ashley's tennis ladder imported successfully!")

        elif command == "--ladder":
            matcher.show_current_ladder()

        elif command == "--pairings":
            month = sys.argv[2] if len(sys.argv) > 2 else None
            matcher.show_monthly_matches(month)

        elif command == "--preview-emails":
            month = sys.argv[2] if len(sys.argv) > 2 else None
            emails = matcher.what_would_be_emailed(month)

            print(f"\n📧 EMAIL PREVIEW - {month if month else 'This Month'}")
            print("=" * 80)
            print(f"NOTE: These are previews. NO emails will be sent in safe mode.")
            print("=" * 80)

            for i, email in enumerate(emails, 1):
                print(f"\n📧 EMAIL {i}:")
                print(f"   TO: {email['to_name']} <{email['to']}>")
                print(f"   SUBJECT: {email['subject']}")
                print(f"   PREVIEW:")
                print("   " + "\n   ".join(email['body'].split('\n')[:10]) + "...")

        else:
            print("NET WORTH Tennis Ladder - Safe Mode (No Emails)")
            print("Commands:")
            print("  --setup          Import Ashley's players")
            print("  --ladder         Show current ladder rankings")
            print("  --pairings       Show this month's pairings")
            print("  --preview-emails Show what emails would be sent")

    else:
        # Default: show everything
        print("🎾 NET WORTH - LA East Side Tennis Ladder")
        print("=" * 50)

        # Import players if not already done
        try:
            matcher.add_ashley_players()
        except:
            pass

        # Show ladder
        matcher.show_current_ladder()

        # Show this month's pairings
        matcher.show_monthly_matches()