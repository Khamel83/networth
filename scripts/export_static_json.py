#!/usr/bin/env python3
"""
Export TOML data files to static JSON for frontend consumption.
This script converts TOML data to JSON format that can be served by Vercel.
"""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: Python 3.11+ required for tomllib, or install tomli: pip install tomli")
        sys.exit(1)

class StaticExporter:
    def __init__(self, data_dir, output_dir):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)

    def load_toml_file(self, filename):
        """Load a TOML file and return data."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, 'rb') as f:
            return tomllib.load(f)

    def export_ladder(self):
        """Export ladder data to JSON."""
        ladder_data = self.load_toml_file('ladder_snapshot.toml')
        if not ladder_data:
            return None

        ladder_export = {
            'metadata': ladder_data.get('metadata', {}),
            'last_updated': ladder_data.get('metadata', {}).get('generated_at'),
            'ladder': ladder_data.get('ladder', [])
        }

        output_file = self.output_dir / 'ladder.json'
        with open(output_file, 'w') as f:
            json.dump(ladder_export, f, indent=2)

        return output_file

    def export_pairings(self):
        """Export pairings data to JSON."""
        pairings_data = self.load_toml_file('pairings.toml')
        if not pairings_data:
            return None

        # Filter only active matches
        active_pairings = [p for p in pairings_data.get('pairings', [])
                           if p.get('player2_id') and p.get('status') == 'pending']

        pairings_export = {
            'metadata': pairings_data.get('metadata', {}),
            'active_match_count': len(active_pairings),
            'pairings': active_pairings
        }

        output_file = self.output_dir / 'pairings.json'
        with open(output_file, 'w') as f:
            json.dump(pairings_export, f, indent=2)

        return output_file

    def export_players(self):
        """Export players data to JSON (public information only)."""
        players_data = self.load_toml_file('players.toml')
        if not players_data:
            return None

        # Only include active players and limited public information
        players_export = {
            'metadata': {
                'generated_at': datetime.now().isoformat() + 'Z',
                'total_players': len(players_data.get('players', []))
            },
            'players': []
        }

        for player in players_data.get('players', []):
            if player.get('active', True):
                public_player = {
                    'id': player['id'],
                    'name': player['name'],
                    'rating': player.get('current_rating', player.get('initial_rating', 1500)),
                    'matches_played': player.get('matches_played', 0),
                    'wins': player.get('wins', 0),
                    'losses': player.get('losses', 0)
                }
                players_export['players'].append(public_player)

        output_file = self.output_dir / 'players.json'
        with open(output_file, 'w') as f:
            json.dump(players_export, f, indent=2)

        return output_file

    def export_courts(self):
        """Export courts data to JSON."""
        courts_data = self.load_toml_file('courts.toml')
        if not courts_data:
            return None

        courts_export = {
            'metadata': {
                'generated_at': datetime.now().isoformat() + 'Z',
                'total_courts': len(courts_data.get('courts', []))
            },
            'courts': courts_data.get('courts', [])
        }

        output_file = self.output_dir / 'courts.json'
        with open(output_file, 'w') as f:
            json.dump(courts_export, f, indent=2)

        return output_file

    def export_league(self):
        """Export league information to JSON."""
        league_data = self.load_toml_file('league.toml')
        if not league_data:
            return None

        # Public league information only
        league_export = {
            'metadata': {
                'generated_at': datetime.now().isoformat() + 'Z'
            },
            'league': {
                'name': league_data.get('league', {}).get('name', 'NET WORTH'),
                'city': league_data.get('league', {}).get('city', 'Los Angeles')
            }
        }

        output_file = self.output_dir / 'league.json'
        with open(output_file, 'w') as f:
            json.dump(league_export, f, indent=2)

        return output_file

    def export_all(self):
        """Export all data to JSON files."""
        exports = []

        ladder_file = self.export_ladder()
        if ladder_file:
            exports.append(ladder_file)
            print(f"✅ Ladder exported: {ladder_file}")

        pairings_file = self.export_pairings()
        if pairings_file:
            exports.append(pairings_file)
            print(f"✅ Pairings exported: {pairings_file}")

        players_file = self.export_players()
        if players_file:
            exports.append(players_file)
            print(f"✅ Players exported: {players_file}")

        courts_file = self.export_courts()
        if courts_file:
            exports.append(courts_file)
            print(f"✅ Courts exported: {courts_file}")

        league_file = self.export_league()
        if league_file:
            exports.append(league_file)
            print(f"✅ League exported: {league_file}")

        return exports

def main():
    parser = argparse.ArgumentParser(description='Export TOML data to static JSON files')
    parser.add_argument('--data-dir', default='data', help='Data directory containing TOML files')
    parser.add_argument('--output-dir', default='public', help='Output directory for JSON files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Path setup
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        sys.exit(1)

    try:
        exporter = StaticExporter(data_dir, output_dir)
        exports = exporter.export_all()

        if args.verbose:
            print(f"Static JSON export completed successfully!")
            print(f"Files exported: {len(exports)}")

        return 0

    except Exception as e:
        print(f"Error exporting static JSON: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()