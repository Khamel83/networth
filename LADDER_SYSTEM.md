# NET WORTH Tennis Ladder System

## Overview

A women's tennis ladder for East Side LA. One match per month, ranked by total games won.

## Scoring System

### Match Format
- **Two sets** (no third set)
- **Ranking based on total games won**, not match wins
- **Tiebreaker at 6-6**: Play until someone wins by 2 (7-5, 8-6, etc.) or record as 6-6 draw
- **Max 14 games possible per match** (7-5, 7-5)

### Score Recording Examples
```
Ashley vs Kim: 6-3, 3-6
  Ashley: 9 games
  Kim: 9 games

Sara vs Natalie: 6-4, 6-2
  Sara: 12 games
  Natalie: 6 games

Hanna vs Maddy: 7-6, 4-6
  Hanna: 11 games
  Maddy: 12 games
```

### Forfeits
- Forfeit without playing: Opponent gets 6 points, you get 0
- Reschedule encouraged even after month ends

---

## Data Collection Philosophy

**Principle: Collect the minimum data to make the best matches possible.**

### Tier 1: Required After Every Match (3 items)

| Data | Format | Purpose |
|------|--------|---------|
| **Set 1 Score** | `6-3` | Calculate games won |
| **Set 2 Score** | `4-6` | Calculate games won |
| **Would play again?** | Yes/No (1 click) | Silent block on "No" |

That's it. Two scores + one click.

### Tier 2: Optional Profile (one-time)

| Data | Purpose |
|------|---------|
| Top 3 preferred courts | Suggest meeting locations |
| General availability | Morning/Afternoon/Evening per day |
| Match frequency preference | Weekly / Biweekly / Monthly |

### Tier 3: Derived (no user input)

| Insight | How It's Calculated |
|---------|---------------------|
| True skill level | Games won patterns over time |
| Reliability | Forfeit rate, matches completed |
| Compatibility | "Would play again" network |
| Preferred times | When matches actually occur |

---

## Matching Algorithm

```
MATCH_SCORE = 0

# Skill similarity (40% weight)
IF similar games-won average: +40 points
IF past matches were close: +10 bonus

# Compatibility (35% weight)
IF both said "would play again": +35 points
IF never played before: +5 variety bonus

# Logistics (15% weight)
IF overlapping court preferences: +15 points

# Activity (10% weight)
IF both active this season: +10 points

# HARD BLOCKS
IF either said "would NOT play again": NEVER PAIR (silent)
IF 3+ forfeits this season: -50 points
```

### Silent Block System
- When a player says "No" to "would play again?", they are never paired with that person again
- No notification to either player
- Only admin can see block data
- Blocks are one-directional (A blocks B, but B might not block A)

---

## Approved Courts

1. Vermont Canyon (Griffith Park)
2. Griffith Park - Riverside Dr
3. Griffith Park - Merry-Go-Round
4. Echo Park
5. Hermon Park
6. Eagle Rock
7. Cheviot Hills
8. Poinsettia Park

---

## Monthly Process

1. **Start of month**: Admin sends pairings
2. **During month**: Players coordinate and play
3. **After match**: Both players report score + feedback
4. **End of month**: Rankings update automatically

---

## Multi-League Support

For other cities/groups:

### Option A: Hosted by NET WORTH (easiest)
- Same Supabase, add `league_id` column
- Admin sees all leagues
- Each league has own subdomain or path
- Free for them, you manage infrastructure

### Option B: Self-Hosted
- They fork the repo
- They create own Supabase project
- They deploy to own Vercel
- Completely independent

**Current setup supports Option A with minimal changes** (add league_id to tables).

---

## Database Schema Summary

### Tables

```
players
  - id, email, name, phone
  - skill_level, rank, total_games, matches_played
  - is_active, is_admin
  - preferred_match_frequency, max_travel_minutes

player_availability
  - player_id, day_of_week, time_slot, is_available

player_court_preferences
  - player_id, court_name, preference_level (1-5)

matches
  - player1_id, player2_id
  - set1_p1, set1_p2, set2_p1, set2_p2 (individual set scores)
  - player1_games, player2_games (totals)
  - month, court, match_date
  - status (reported/confirmed)

match_feedback
  - match_id, from_player_id, about_player_id
  - would_play_again (BOOLEAN) -- the key field
  - private_note (admin only)
```

### Automatic Triggers
- When match inserted → Update both players' total_games
- When match inserted → Recalculate all rankings

---

## Internal Metrics (Admin Only)

| Metric | What It Shows |
|--------|---------------|
| Forfeit rate | Who's unreliable |
| Block count | Who has issues |
| Response time | Who's engaged |
| Match completion rate | League health |

---

## Tech Stack

- **Frontend**: Static HTML/CSS/JS (Vercel)
- **Backend**: Vercel Serverless Functions (Python)
- **Database**: Supabase (PostgreSQL)
- **Auth**: Demo mode (shared password) or Supabase Auth

---

## Files

```
/public/           - Static HTML pages
/api/              - Serverless functions
  auth.py          - Login
  players.py       - Get players list
  matches.py       - Get/post matches
supabase-final-setup.sql - Complete database setup
```
