#!/usr/bin/env python3
"""
Simple pairings generation script that doesn't use tomlkit for compatibility.
"""

import sys
import os
from pathlib import Path
import argparse
import itertools
from datetime import datetime

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: Python 3.11+ required for tomllib, or install tomli: pip install tomli")
        sys.exit(1)

def simple_dump(data, filepath):
    """Simple TOML dump that handles None values."""
    cleaned_data = {}
    for key, value in data.items():
        if value is not None:
            cleaned_data[key] = value
    with open(filepath, 'w') as f:
        for key, value in cleaned_data.items():
            f.write(f"{key} = {repr(value)}\n")

class PairingGenerator:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.RATING_TOLERANCE = 200  # Max rating difference for pairings
        self.RECENT_MATCH_DAYS = 28  # Days to avoid rematches

    def load_players(self):
        """Load player data from players.toml."""
        players_file = self.data_dir / 'players.toml'
        if not players_file.exists():
            return []

        with open(players_file, 'rb') as f:
            data = tomllib.load(f)

        return data.get('players', [])

    def load_matches(self):
        """Load match data from matches.toml."""
        matches_file = self.data_dir / 'matches.toml'
        if not matches_file.exists():
            return []

        with open(matches_file, 'rb') as f:
            data = tomllib.load(f)

        return data.get('matches', [])

    def get_recent_matches(self, player1_id, player2_id):
        """Get recent matches between two players."""
        matches = self.load_matches()
        recent = []
        cutoff_date = datetime.now() - timedelta(days=self.RECENT_MATCH_DAYS)

        for match in matches:
            if match.get('date') and datetime.fromisoformat(match['date']) >= cutoff_date:
                if ((match['player1_id'] == player1_id and match['player2_id'] == player2_id) or
                    (match['player1_id'] == player2_id and match['player2_id'] == player1_id)):
                    recent.append(match)
                    break  # Only need one recent match

        return recent

    def calculate_pairing_score(self, player1, player2):
        """Calculate compatibility score for two players."""
        rating_diff = abs(player1['rating'] - player2['rating'])
        rating_score = max(0, 100 - rating_diff)  # 100 points for same rating, down to 0 for big diff

        # Prefer active players
        activity_score = 50 if player1.get('active') else 0
        activity_score += 50 if player2.get('active') else 0

        return rating_score + activity_score

    def generate_pairings(self):
        """Generate weekly pairings based on player data."""
        players = self.load_players()
        matches = self.load_matches()

        # Filter active players
        active_players = [p for p in players if p.get('active', True)]

        pairings = []
        used_players = set()

        # Generate all possible pairings
        for player1, player2 in itertools.combinations(active_players, 2):
            if player1['id'] in used_players or player2['id'] in used_players:
                continue  # Player already paired

            # Check rating compatibility
            rating_diff = abs(player1['rating'] - player2['rating'])
            if rating_diff > self.RATING_TOLERANCE:
                continue  # Too different skill levels

            # Check for recent matches
            recent_matches = self.get_recent_matches(player1['id'], player2['id'])
            if recent_matches:
                continue  # They played recently

            # Calculate compatibility score
            score = self.calculate_pairing_score(player1, player2)

            # Find compatible court
            court1_prefs = player1.get('preferred_courts', [])
            court2_prefs = player2.get('preferred_courts', [])
            common_courts = list(set(court1_prefs) & set(court2_prefs))
            selected_court = common_courts[0] if common_courts else court1_prefs[0]

            # Find compatible time slot
            p1_avail = player1.get('availability', {})
            p2_avail = player2.get('availability', {})
            common_times = [
                time for time in ['mon_evening', 'tue_evening', 'wed_evening', 'thu_evening',
                             'fri_evening', 'sat_evening', 'sun_evening']
                if p1_avail.get(time, False) and p2_avail.get(time, False)
            ]

            selected_time = common_times[0] if common_times else 'flexible'

            pairings.append({
                'player1_id': player1['id'],
                'player2_id': player2['id'],
                'score': score,
                'suggested_court_id': selected_court,
                'suggested_time_block': selected_time,
                'status': 'pending'
            })

            used_players.add(player1['id'])
            used_players.add(player2['id'])

        return pairings

    def save_pairings(self, pairings):
        """Save pairings to TOML file."""
        output_file = self.data_dir / 'pairings.toml'

        # Get current week
        current_week = datetime.now()
        monday = current_week - timedelta(days=current_week.weekday())
        week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)

        pairings_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat() + 'Z',
                'week_of': week_start.strftime('%Y-%m-%d'),
                'total_pairings': len(pairings)
            },
            'pairings': pairings
        }

        simple_dump(pairings_data, output_file)
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate weekly pairings from TOML data')
    parser.add_argument('--data-dir', default='data', help='Data directory containing TOML files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Path setup
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    try:
        generator = PairingGenerator(data_dir)
        pairings = generator.generate_pairings()

        if args.verbose:
            print(f"Generated {len(pairings)} potential pairings")

        output_file = generator.save_pairings(pairings)
        if args.verbose:
            print(f"Generated {output_file}")

    except Exception as e:
        print(f"Error generating pairings: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()