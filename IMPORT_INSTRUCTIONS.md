# NET WORTH Player Import Instructions

## 📥 Import Your 2025 Player Roster

You have `Net Worth ladder 2025 - Net Worth.csv` which contains the complete player roster for the NET WORTH tennis ladder.

## 🎯 What This File Contains

Based on the filename, this CSV likely contains:
- Complete list of all 80+ players in the NET WORTH system
- Player contact information (names, emails)
- Skill levels and rankings
- Match history and statistics

## 📋 Next Steps

### Option 1: Automated CSV Import (Recommended)

```bash
# 1. Place your CSV file in the repository root
cp "/Users/khamel83/Downloads/Net Worth ladder 2025 - Net Worth.csv" ./networth_players_2025.csv

# 2. Run the existing import script with TOML output
python3 scripts/import_players.py networth_players_2025.csv --toml-output

# 3. This will create/update data/players.toml with all your players
# 4. Then run the pipeline to update ladder rankings
python3 scripts/recompute_ladder.py --verbose
python3 scripts/generate_pairings.py --verbose
python3 scripts/export_static_json.py --verbose
```

### Option 2: Manual TOML Creation

If the CSV import doesn't work perfectly, you can manually create `data/players.toml`:

```bash
# 1. Edit the players file
nano data/players.toml

# 2. Add all 80+ players using this format for each:
[[players]]
id = "player_unique_id"
name = "Player Full Name"
email = "player@email.com"
active = true  # Set to false for inactive players
initial_rating = 1500  # Starting ELO rating
preferred_courts = ["vermont_canyon", "griffith_riverside"]

[players.availability]
mon_morning = false
mon_afternoon = false
mon_evening = true
# ... continue for all days/time blocks

# 3. Save and run pipeline
python3 scripts/recompute_ladder.py
python3 scripts/generate_pairings.py
python3 scripts/export_static_json.py
```

## 🔄 After Import: Update Everything

```bash
# 1. Recompute ladder with all players
python3 scripts/recompute_ladder.py --verbose

# 2. Generate new pairings based on full roster
python3 scripts/generate_pairings.py --verbose

# 3. Export static JSON for website
python3 scripts/export_static_json.py --verbose

# 4. Commit all changes
git add .
git commit -m "🎾 Import complete 2025 player roster

- Added 80+ players from Net Worth ladder 2025
- Updated ladder rankings for full roster
- Generated pairings for all active players
- Exported static JSON for frontend

🤖 Generated with Claude Code"

git push origin master
```

## 🏗️ What This Accomplishes

- **Complete Player Roster**: All 80+ players from your 2025 ladder
- **Accurate Rankings**: Ladder computed from full player base
- **Smart Pairings**: Weekly matches based on availability and skill level
- **Static Website**: Frontend shows complete rankings without database
- **Git Version Control**: All player data tracked in repository

## 🔍 Expected Results

After import, the website will show:
- Full ladder with all ranked players
- Player statistics (wins, losses, match history)
- Weekly pairings for all active players
- Historical data preservation

## ⚠️ Important Notes

1. **Active Status**: Only mark players as `active = true` if they're currently participating
2. **Email Privacy**: Emails are in TOML but filtered out for public JSON display
3. **Skill Levels**: Convert to numerical ratings (1500 baseline + adjustments)
4. **Availability**: Critical for automatic pairings - set realistic schedules

## 🎉 Success Criteria

You'll know the import worked when:
- `data/players.toml` contains 80+ players
- `ladder.json` shows complete rankings
- Website displays full ladder (no "loading" messages)
- GitHub Actions can process all players without errors

---

**Ready to proceed?**

1. Copy your CSV to the repository
2. Run the import command above
3. Commit and push to update the live site

The NET WORTH static system is designed to handle any number of players and will automatically scale to support your complete 2025 roster!