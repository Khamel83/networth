#!/usr/bin/env python3
"""
Recompute ladder rankings from players.toml and matches.toml data.
Implements a simple ELO-based rating system.
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime, timedelta
import itertools

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: Python 3.11+ required for tomllib, or install tomli: pip install tomli")
        sys.exit(1)

try:
    import tomli_w
except ImportError:
    try:
        import tomlkit as tomli_w
    except ImportError:
        print("Error: Please install tomli_w: pip install tomli_w")
        sys.exit(1)

class LadderComputer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.K_FACTOR = 32

    def load_players(self):
        """Load player data from players.toml."""
        players_file = self.data_dir / 'players.toml'
        if not players_file.exists():
            raise FileNotFoundError(f"Players file not found: {players_file}")

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

    def parse_scoreline(self, scoreline):
        """Parse a scoreline like '6-4 4-6 7-6' to determine winner."""
        try:
            sets = scoreline.split()
            p1_sets = 0
            p2_sets = 0
            for set_score in sets:
                p1, p2 = map(int, set_score.split('-'))
                if p1 > p2:
                    p1_sets += 1
                else:
                    p2_sets += 1
            return 1 if p1_sets > p2_sets else 2
        except:
            return 1

    def compute_elo_change(self, rating1, rating2, player1_won):
        """Compute ELO rating change for a match."""
        expected_score1 = 1 / (1 + 10 ** ((rating2 - rating1) / 400))
        actual_score1 = 1 if player1_won else 0

        change1 = self.K_FACTOR * (actual_score1 - expected_score1)
        change2 = -change1

        return int(round(change1)), int(round(change2))

    def compute_ladder(self):
        """Compute ladder standings from players and matches."""
        players = self.load_players()
        matches = self.load_matches()

        # Initialize player data
        player_data = {}
        for player in players:
            if player.get('active', True):
                player_data[player['id']] = {
                    'id': player['id'],
                    'name': player['name'],
                    'email': player['email'],
                    'rating': player.get('current_rating', player.get('initial_rating', 1500)),
                    'matches_played': player.get('matches_played', 0),
                    'wins': player.get('wins', 0),
                    'losses': player.get('losses', 0),
                    'last_match_date': None
                }

        # Process matches chronologically
        sorted_matches = sorted(matches, key=lambda m: m.get('date', ''))
        for match in sorted_matches:
            p1_id = match['player1_id']
            p2_id = match['player2_id']

            # Skip if players not found
            if p1_id not in player_data or p2_id not in player_data:
                continue

            # Update match counts
            player_data[p1_id]['matches_played'] += 1
            player_data[p2_id]['matches_played'] += 1

            # Determine winner
            if match.get('winner_id'):
                winner_id = match['winner_id']
            else:
                winner_id = self.parse_scoreline(match.get('scoreline', '6-4'))
                winner_id = p1_id if winner_id == 1 else p2_id

            # Update wins/losses
            if p1_id == winner_id:
                player_data[p1_id]['wins'] += 1
                player_data[p2_id]['losses'] += 1
            else:
                player_data[p1_id]['losses'] += 1
                player_data[p2_id]['wins'] += 1

            # Compute ELO changes
            p1_rating = player_data[p1_id]['rating']
            p2_rating = player_data[p2_id]['rating']
            player1_won = (p1_id == winner_id)

            change1, change2 = self.compute_elo_change(p1_rating, p2_rating, player1_won)

            player_data[p1_id]['rating'] += change1
            player_data[p2_id]['rating'] += change2

            # Update last match date
            match_date = match.get('date', '')
            if match_date:
                player_data[p1_id]['last_match_date'] = match_date
                player_data[p2_id]['last_match_date'] = match_date

        # Sort players by rating (descending), then by matches played, then by name
        ranked_players = sorted(
            player_data.values(),
            key=lambda p: (-p['rating'], -p['matches_played'], p['name'])
        )

        # Add rankings
        for i, player in enumerate(ranked_players, 1):
            player['rank'] = i

        return ranked_players

    def save_ladder(self, ladder):
        """Save ladder rankings to ladder_snapshot.toml."""
        output_file = self.data_dir / 'ladder_snapshot.toml'

        ladder_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat() + 'Z',
                'total_players': len(ladder)
            },
            'ladder': []
        }

        for player in ladder:
            ladder_entry = {
                'rank': player['rank'],
                'player_id': player['id'],
                'player_name': player['name'],
                'rating': player['rating'],
                'matches_played': player['matches_played'],
                'wins': player['wins'],
                'losses': player['losses'],
                'last_match_date': player['last_match_date']
            }
            ladder_data['ladder'].append(ladder_entry)

        with open(output_file, 'wb') as f:
            tomli_w.dump(ladder_data, f)

        return output_file

def main():
    parser = argparse.ArgumentParser(description='Recompute ladder rankings from TOML data')
    parser.add_argument('--data-dir', default='data', help='Data directory containing TOML files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Path setup
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    try:
        computer = LadderComputer(data_dir)
        ladder = computer.compute_ladder()

        if args.verbose:
            print(f"Ladder recomputed successfully!")
            print(f"Generated {len(ladder)} player rankings")

        output_file = computer.save_ladder(ladder)
        if args.verbose:
            print(f"Generated {output_file}")

        # Create final summary with top 5 players
        if args.verbose and ladder:
            print("\nTop 5 players:")
            for player in ladder[:5]:
                print(f"  {player['rank']}. {player['player_name']} - Rating: {player['rating']} ({player['wins']}-{player['losses']})")

    except Exception as e:
        print(f"Error computing ladder: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()