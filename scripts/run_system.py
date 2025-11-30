#!/usr/bin/env python3
"""
Complete NET WORTH system runner - import, process, export.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the complete NET WORTH static system pipeline."""
    print("🎾 Running NET WORTH Static System Pipeline...")

    try:
        # 1. Import from CSV (if exists)
        if Path("Net Worth ladder 2025 - Net Worth.csv").exists():
            print("📥 Importing from CSV...")
            result = subprocess.run([
                "python3", "scripts/import_simple_csv.py",
                "Net Worth ladder 2025 - Net Worth.csv"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ CSV import successful")
            else:
                print("❌ CSV import failed")
                print(result.stdout)
        else:
            print("📊 No CSV file found, using existing TOML data")

        # 2. Recompute ladder
        print("\n📈 Recomputing ladder rankings...")
        result = subprocess.run([
            "python3", "scripts/recompute_ladder.py", "--verbose"
            ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ladder recomputed successfully")
        else:
            print("❌ Ladder recomputation failed")
            print(result.stdout)

        # 3. Generate pairings
        print("\n🤝 Generating weekly pairings...")
        result = subprocess.run([
            "python3", "scripts/generate_pairings_simple.py", "--verbose"
            ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Pairings generated successfully")
        else:
            print("❌ Pairings generation failed")
            print(result.stdout)

        # 4. Export static JSON
        print("\n📄 Exporting static JSON for frontend...")
        result = subprocess.run([
            "python3", "scripts/export_static_json.py", "--verbose"
            ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Static JSON export successful")
        else:
            print("❌ JSON export failed")
            print(result.stdout)

        # 5. Summary
        print("\n🎉 NET WORTH Static System Pipeline Complete!")
        print("=" * 50)
        print("📁 Files Created/Updated:")

        # Check key files
        files_to_check = [
            "data/players.toml",
            "data/ladder_snapshot.toml",
            "data/pairings.toml",
            "public/ladder.json",
            "public/pairings.json",
            "public/players.json",
            "public/courts.json",
            "public/league.json"
        ]

        for file_path in files_to_check:
            if Path(file_path).exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (missing)")

        print("\n📋 Next Steps:")
        print("1. git add data/ public/")
        print("2. git commit -m '🎾 Setup NET WORTH static system with 42 players'")
        print("3. git push origin master")
        print("4. Deploy to Vercel and test networthtennis.com")
        print("5. GitHub Actions will handle weekly updates automatically!")

        return 0

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())