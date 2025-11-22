#!/usr/bin/env python3
"""
Ashley's Tennis Ladder Data Import
NET WORTH - Women's LA East Side Tennis Ladder
"""

import sqlite3
import re
from typing import List, Dict, Optional

# Ashley's current tennis ladder players with all data
ASHLEY_PLAYERS = [
    {"name": "Kim Ndombe", "email": "kimberly@ndombe.com", "phone": "603-264-2486", "total_score": 51, "march": 8, "april": 9, "may": 12, "june": 10, "july": 12},
    {"name": "Natalie Coffen", "email": "nmcoffen@gmail.com", "phone": "310-849-6750", "total_score": 50, "march": 12, "april": 4, "may": 2, "july": 12, "august": 8, "september": 12},
    {"name": "Sara Chrisman", "email": "Sara.Chrisman@gmail.com", "phone": "541-398-2012", "total_score": 49, "may": 12, "june": 12, "july": 12, "august": 12},
    {"name": "Arianna Hairston", "email": "ariannahairston@gmail.com", "phone": "484-832-9906", "total_score": 48, "march": 12, "april": 12, "may": 12, "july": 12},
    {"name": "Alik Apelian", "email": "aapelian@gmail.com", "phone": "978-397-1645", "total_score": 45, "march": 7, "april": 12, "may": 12, "june": 11, "july": 3},
    {"name": "Hannah Shin", "email": "hannah.shin4@gmail.com", "phone": "949-861-1329", "total_score": 45, "march": 12, "april": 9, "may": 12, "october": 12},
    {"name": "Hanna Pavlova", "email": "sayhellotohanna@gmail.com", "phone": "347-549-6748", "total_score": 41, "march": 2, "april": 9, "may": 2, "june": 4, "july": 12, "august": 12},
    {"name": "Maddy Whitby", "email": "Madeline.whitby@gmail.com", "phone": "818-859-0282", "total_score": 38, "march": 2, "april": 6, "may": 8, "july": 10, "august": 12},
    {"name": "Allison Dunne", "email": "Allison.n.dunne@gmail.com", "phone": "414-698-6455", "total_score": 37, "march": 12, "april": 12, "may": 1, "june": 12},
    {"name": "Ashley Brooke Kaufman", "email": "Ashleybrooke.kaufman@gmail.com", "phone": "630-453-3430", "total_score": 33, "march": 0, "april": 1, "may": 1, "june": 5, "july": 9, "august": 5, "september": 12},
    {"name": "Kaitlin Kelly", "email": "kaitlinmariekelly@gmail.com", "phone": "213-308-7605", "total_score": 32, "april": 12, "may": 6, "june": 12, "august": 2},
    {"name": "Page Eaton", "email": "Pagek.eaton@gmail.com", "phone": "206-228-5082", "total_score": 30, "march": 12, "april": 12, "may": 5, "june": 1},
    {"name": "Sarah Yun", "email": "BySarahYun@gmail.com", "phone": "213-249-3893", "total_score": 29, "april": 7, "june": 10, "july": 12},
    {"name": "Laurie Berger", "email": "Laurenjaneberger@gmail.com", "phone": "510-333-4308", "total_score": 26, "march": 14, "may": 6, "september": 6},
    {"name": "Katie Morey", "email": "Katelinmorey@gmail.com", "phone": "620-513-6067", "total_score": 24, "june": 12, "july": 12},
    {"name": "Carlyn Hudson", "email": "hudson.carlyn@gmail.com", "phone": "830-305-1378", "total_score": 22, "april": 12, "may": 10},
    {"name": "Seena Chokshi", "email": "Skchokshi@gmail.com", "phone": "909-996-7643", "total_score": 21, "may": 8, "june": 10, "august": 3},
    {"name": "Carolina Ciappa", "email": "carolciappa@gmail.com", "phone": "415-531-6798", "total_score": 20, "march": 9, "april": 11},
    {"name": "Camille Tsalik", "email": "camille.tsalik@gmail.com", "phone": "310-993-2670", "total_score": 20, "june": 12, "july": 8},
    {"name": "Lola Miranda", "email": "ichheisselola@yahoo.com", "phone": "714-234-0006", "total_score": 19, "july": 12, "september": 7},
    {"name": "Hannah Crichton", "email": "hannah.crichton@gmail.com", "phone": "206-229-0294", "total_score": 15, "march": 12, "april": 3},
    {"name": "Nicole Malick", "email": "ngmalick@gmail.com", "phone": "", "total_score": 12, "march": 3, "august": 9},
    {"name": "Sandy Arango", "email": "sandyarango@gmail.com", "phone": "415-225-3331", "total_score": 12, "september": 12},
    {"name": "Shandel Love", "email": "Shandellove@yahoo.com", "phone": "213-842-3345", "total_score": 12, "september": 12},
    {"name": "Erica Gleason", "email": "Erica.e.gleason@gmail.com", "phone": "562-485-8277", "total_score": 11, "september": 11},
    {"name": "Nikki Bohnett", "email": "NikkiBohnett@gmail.com", "phone": "562-277-3976", "total_score": 8, "june": 0, "july": 4, "august": 3, "september": 1},
    {"name": "Carmela Garcia Lammers", "email": "carmela.garcialammers@gmail.com", "phone": "605-690-9500", "total_score": 3, "june": 3},
    {"name": "Isa Quiros", "email": "Isabella.quiros@gmail.com", "phone": "954-805-7657", "total_score": 2, "may": 2, "july": 0},
    {"name": "Alyssa Jeong Perry", "email": "Alyssa.j.perry@gmail.com", "phone": "415-937-3825", "total_score": 1, "march": 0, "april": 1, "may": 0},
    {"name": "Katie Hathaway", "email": "Katiehathaway18@gmail.com", "phone": "310-795-9990", "total_score": 5, "september": 5}
]

# Players without scores - need to be contacted
INACTIVE_PLAYERS = [
    {"name": "Maryam Marzara", "email": "MarzaraM@gmail.com", "phone": "949-413-4831", "total_score": 4, "march": 4},
    {"name": "Jardine Hammond", "email": "Jardineh@gmail.com", "phone": "760-576-9645", "total_score": 0},
    {"name": "Hannah Fard", "email": "hannahrnasseri@gmail.com", "phone": "310-729-1553", "total_score": 0},
    {"name": "Anisha Vasandani", "email": "anishavasandani@gmail.com", "phone": "626-802-0840", "total_score": 0},
    {"name": "Alex Moreno", "email": "asmorenohere@icloud.com", "phone": "203-505-8904", "total_score": 0},
    {"name": "Ellen Fehr", "email": "ellenfehr@gmail.com", "phone": "323-327-6093", "total_score": 0},
    {"name": "Alicia Harris", "email": "Aliciaharris4@gmail.com", "phone": "310-913-5858", "total_score": 0},
    {"name": "Stacy Kim", "email": "stacyk321@outlook.com", "phone": "213-327-6093", "total_score": 0},
    {"name": "Maddie Dunkelberg", "email": "dunkelbee@gmail.com", "phone": "541-647-0688", "total_score": 0},
    {"name": "Christina Catherine Martinez", "email": "christinacatherine@gmail.com", "phone": "562-972-5848", "total_score": 0}
]

# LA East Side court recommendations
COURT_RECOMMENDATIONS = [
    "Vermont Canyon",
    "Griffith Park - Riverside",
    "Griffith Park - Merry-Go-Round",
    "Echo Park",
    "Hermon Park",
    "Eagle Rock",
    "Cheviot Hills",
    "Poinsettia Park"
]

def import_ashley_data(db_path: str = "tennis_match.db") -> bool:
    """Import Ashley's ladder data into the tennis match system."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                skill_level TEXT DEFAULT 'Intermediate',
                location TEXT DEFAULT 'LA East Side',
                availability TEXT DEFAULT 'Flexible',
                total_score INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                joined_date DATE DEFAULT CURRENT_DATE,
                last_matched DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER,
                player2_id INTEGER,
                month TEXT,
                year INTEGER,
                player1_games INTEGER,
                player2_games INTEGER,
                played_date DATE,
                FOREIGN KEY (player1_id) REFERENCES players (id),
                FOREIGN KEY (player2_id) REFERENCES players (id)
            )
        ''')

        # Import active players
        for player in ASHLEY_PLAYERS:
            cursor.execute('''
                INSERT OR REPLACE INTO players
                (name, email, phone, total_score, active, skill_level)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (
                player["name"],
                player["email"],
                player["phone"],
                player["total_score"],
                estimate_skill_level(player["total_score"])
            ))

        # Import inactive players
        for player in INACTIVE_PLAYERS:
            cursor.execute('''
                INSERT OR REPLACE INTO players
                (name, email, phone, total_score, active, skill_level)
                VALUES (?, ?, ?, ?, 0, ?)
            ''', (
                player["name"],
                player["email"],
                player["phone"],
                player["total_score"],
                estimate_skill_level(player["total_score"])
            ))

        conn.commit()
        conn.close()

        print(f"✅ Successfully imported {len(ASHLEY_PLAYERS)} active players")
        print(f"✅ Successfully imported {len(INACTIVE_PLAYERS)} inactive players")
        print(f"✅ Total players in system: {len(ASHLEY_PLAYERS) + len(INACTIVE_PLAYERS)}")

        return True

    except Exception as e:
        print(f"❌ Error importing Ashley's data: {e}")
        return False

def estimate_skill_level(total_score: int) -> str:
    """Estimate skill level based on total score."""
    if total_score >= 45:
        return "Advanced (4.0+)"
    elif total_score >= 30:
        return "Intermediate-Advanced (3.5-4.0)"
    elif total_score >= 15:
        return "Intermediate (3.0-3.5)"
    else:
        return "Beginner-Intermediate (2.5-3.0)"

def print_ladder_rankings(db_path: str = "tennis_match.db"):
    """Print current ladder rankings."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT name, email, phone, total_score, skill_level, active
        FROM players
        ORDER BY total_score DESC, name ASC
    ''')

    players = cursor.fetchall()

    print("\n🎾 NET WORTH - LA East Side Tennis Ladder Rankings")
    print("=" * 80)

    rank = 1
    active_count = 0
    for name, email, phone, score, skill, active in players:
        if active:
            active_count += 1
            print(f"{rank:2d}. {name:<25} | {score:2d} pts | {skill}")
            rank += 1

    print(f"\n📊 Total Active Players: {active_count}")
    print(f"🏆 This Month: Pairings sent via email")
    print(f"🎯 Focus: LA East Side courts only")

    conn.close()

if __name__ == "__main__":
    if import_ashley_data():
        print_ladder_rankings()
    else:
        print("❌ Failed to import data")