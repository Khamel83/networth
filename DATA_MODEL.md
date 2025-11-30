# NET WORTH Data Model Documentation

This document describes the TOML-based data model used for the NET WORTH tennis ladder system.

## Overview

The NET WORTH system uses TOML files stored in the `data/` directory to manage all ladder information. This approach eliminates the need for a live database and allows for version-controlled, static deployment.

## File Structure

```
data/
├── league.toml          # League configuration
├── courts.toml          # Tennis court information
├── players.toml         # Player roster and preferences
├── matches.toml         # Historical match results
├── ladder_snapshot.toml # Generated ladder rankings
└── pairings.toml       # Generated weekly pairings
```

## Data Files

### `league.toml`

League-wide configuration and settings.

```toml
[league]
name = "NET WORTH"
city = "Los Angeles"
timezone = "America/Los_Angeles"

[schedule]
matching_frequency = "weekly"            # enum: daily|weekly|manual
matching_run_day = "sunday"             # if weekly; used by Python script logic
matching_run_hour = 17                  # 24h local time; script can interpret

[email]
from_address = "matches@networthtennis.com"
# Placeholders for future integration: SMTP / API, etc.
```

### `courts.toml`

Authoritative list of tennis courts used by the ladder.

```toml
[[courts]]
id = "vermont_canyon"
name = "Vermont Canyon"
city = "Los Angeles"
notes = "Well-maintained courts with great lighting"
google_maps_url = "https://maps.google.com/..."

[[courts]]
id = "griffith_riverside"
name = "Griffith Park - Riverside"
city = "Los Angeles"
notes = "Scenic riverside courts with mountain views"
google_maps_url = "https://maps.google.com/..."
```

**Fields:**
- `id`: Unique identifier (used in pairings)
- `name`: Display name for the court
- `city`: City/location
- `notes`: Additional information
- `google_maps_url`: Direct link to Google Maps

### `players.toml`

Canonical player list with ladder-relevant information.

```toml
[[players]]
id = "ashley_x"
name = "Ashley X"
email = "ashley@example.com"
active = true
initial_rating = 1500
preferred_courts = ["vermont_canyon", "griffith_riverside"]
current_rating = 1520
matches_played = 12
wins = 9
losses = 3
created_at = "2025-03-01T10:00:00Z"
updated_at = "2025-03-15T14:30:00Z"

[players.availability]
mon_morning = true
mon_afternoon = false
mon_evening = true
tue_morning = true
tue_afternoon = false
tue_evening = true
# ... continue for all days and time blocks
```

**Fields:**
- `id`: Unique player identifier
- `name`: Display name
- `email`: Contact email (private, not exposed publicly)
- `active`: Boolean, whether player is currently active
- `initial_rating`: Starting ELO rating
- `preferred_courts`: List of court IDs from `courts.toml`
- `current_rating`: Current ladder rating
- `matches_played`: Total matches in system
- `wins`: Total wins
- `losses`: Total losses
- `availability`: Weekly availability grid

**Availability Time Blocks:**
- `{day}_morning`: 6AM - 12PM
- `{day}_afternoon`: 12PM - 6PM
- `{day}_evening`: 6PM - 10PM

Days: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`

### `matches.toml`

Historical match results used for ladder calculations.

```toml
[[matches]]
id = "2025-03-01-ashley_x-sarah_y"
date = "2025-03-01"
player1_id = "ashley_x"
player2_id = "sarah_y"
court_id = "vermont_canyon"
scoreline = "6-4 4-6 7-6"
winner_id = "ashley_x"
had_fun_player1 = true
had_fun_player2 = false
source = "import"
```

**Fields:**
- `id`: Unique match identifier
- `date`: Match date (YYYY-MM-DD format)
- `player1_id`: First player's ID
- `player2_id`: Second player's ID
- `court_id`: Court ID from `courts.toml`
- `scoreline`: Tennis score notation (e.g., "6-4 4-6 7-6")
- `winner_id`: Winner's player ID
- `had_fun_player1`: Boolean, player enjoyment feedback
- `had_fun_player2`: Boolean, player enjoyment feedback
- `source`: Source of match data ("import", "email", "manual")

### `ladder_snapshot.toml`

Generated ladder rankings (output from `recompute_ladder.py`).

```toml
[metadata]
generated_at = "2025-03-02T01:00:00Z"
total_players = 16

[[ladder]]
rank = 1
player_id = "ashley_x"
player_name = "Ashley X"
rating = 1590
matches_played = 12
wins = 9
losses = 3
last_match_date = "2025-03-01"
```

**Metadata Fields:**
- `generated_at`: ISO 8601 timestamp of ladder computation
- `total_players`: Number of active players

**Ladder Entry Fields:**
- `rank`: Current ladder position
- `player_id`: Player's unique ID
- `player_name`: Player's display name
- `rating`: Current ELO rating
- `matches_played`: Total matches played
- `wins`: Total wins
- `losses`: Total losses
- `last_match_date`: Most recent match date

### `pairings.toml`

Generated weekly match suggestions (output from `generate_pairings.py`).

```toml
[metadata]
generated_at = "2025-03-02T01:00:00Z"
week_of = "2025-03-03"
total_pairings = 8

[[pairings]]
week_of = "2025-03-03"
player1_id = "ashley_x"
player2_id = "sarah_y"
suggested_court_id = "vermont_canyon"
suggested_time_block = "mon_evening"
status = "pending"
rating_diff = 15
last_played = "2025-02-01"
```

**Metadata Fields:**
- `generated_at`: ISO 8601 timestamp of pairing generation
- `week_of`: Start of week (YYYY-MM-DD)
- `total_pairings`: Number of suggested pairings

**Pairing Entry Fields:**
- `week_of`: Week for this pairing
- `player1_id`: First player's ID
- `player2_id`: Second player's ID
- `suggested_court_id`: Recommended court
- `suggested_time_block`: Best available time slot
- `status`: "pending", "accepted", "rejected", "no_match_available"
- `rating_diff`: Difference in player ratings
- `last_played`: When these players last played each other (optional)

## Data Processing Pipeline

### Scripts

1. **`scripts/bootstrap_from_sqlite.py`**
   - Converts existing SQLite database to TOML format
   - One-time migration script

2. **`scripts/recompute_ladder.py`**
   - Generates `ladder_snapshot.toml` from `players.toml` + `matches.toml`
   - Implements ELO rating system
   - Ranks players by rating, breaks ties with matches played

3. **`scripts/generate_pairings.py`**
   - Generates `pairings.toml` from all data files
   - Uses rating proximity, availability, and recent match history
   - Avoids rematches within 28 days

4. **`scripts/export_static_json.py`**
   - Converts TOML data to JSON for frontend consumption
   - Outputs to `public/` directory

### GitHub Actions

The `.github/workflows/networth_static_pipeline.yml` workflow:
- Runs weekly on Mondays 1:00 UTC (Sunday 6:00 PM LA time)
- Also runs on manual triggers or pushes to data files
- Executes: `recompute_ladder.py` → `generate_pairings.py` → `export_static_json.py`
- Commits changes back to repository

## Static JSON Export

For frontend consumption, TOML files are converted to JSON in the `public/` directory:

- `ladder.json` - Current ladder rankings
- `pairings.json` - Weekly suggested matches
- `players.json` - Public player information (limited)
- `courts.json` - Court information
- `league.json` - League configuration

## Integration with secrets-vault

The system can integrate with `https://github.com/Khamel83/secrets-vault` for:

- Email configuration for match notifications
- API keys for external services
- Database credentials if needed for hybrid deployments

Secrets are accessed via GitHub Actions environment variables or runtime configuration.