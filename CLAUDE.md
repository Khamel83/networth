# CLAUDE.md - NET WORTH Tennis

## Project Overview

Women's tennis ladder for East Side LA. Monthly pairings, games-won ranking system.

**Live**: networthtennis.com
**Stack**: Vercel (static + Python functions) + Supabase

## Quick Reference

### To change colors/copy/branding:
- Website CSS: Variables at top of each `public/*.html` file
- Email templates: Configured in Supabase Auth dashboard

### To add a player:
Add row to `players` table in Supabase

### Key files:
- `api/pairings.py` - Matching algorithm (skill-based)
- `api/profile.py` - Player profile management
- `lib/config.py` - Centralized config (in lib/ to avoid Vercel limit)
- `api/migrate.py` - Admin tools (migrations)

## Architecture

```
User visits site
    → Vercel serves static HTML from /public
    → JS fetches from /api/* endpoints
    → API reads/writes to Supabase
    → Supabase Auth handles magic link emails

GitHub Actions (1st + 15th of month)
    → Calls /api/cron/monthly to generate pairings
    → Admin dashboard shows pending notifications
```

## Database Schema

```
players
  - id, email, name, skill_level
  - rank, total_games, matches_played
  - available_morning/afternoon/evening (for scheduling)
  - unavailable_until (pause feature)

matches
  - player1_id, player2_id
  - player1_games, player2_games (set scores)
  - period_label ("December 2024")

match_assignments
  - player1_id, player2_id, period_label
  - status (pending/accepted/completed)

match_feedback
  - would_play_again (for silent blocking)
```

## Common Tasks

### Change a player's availability
```sql
UPDATE players SET unavailable_until = '2025-02-01' WHERE email = 'player@email.com';
```

### See who hasn't played their match
```sql
SELECT * FROM match_assignments WHERE status = 'pending' AND period_label = 'December 2024';
```

### Manually recalculate rankings
```sql
SELECT recalculate_rankings();
```

## Environment Variables

Set in Vercel dashboard:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- `SITE_URL` = https://networthtennis.com
- `ADMIN_EMAIL` = where join requests go
- `CRON_SECRET` = for GitHub Actions auth

Set in GitHub repo secrets:
- `SITE_URL`, `CRON_SECRET`

## Fallback Mode

If Supabase/Vercel are down, `public/fallback.html` is a pure static page with:
- Current ladder (manually updated)
- mailto: links for score reporting
- No JS dependencies

## Vercel Limits (CRITICAL)

**Hobby plan limit: 12 serverless functions max**

Current count: 12 (at limit!)
```
api/admin.py      api/auth.py       api/email.py      api/health.py
api/join.py       api/matches.py    api/migrate.py    api/pairings.py
api/players.py    api/profile.py    api/upload.py     api/cron/monthly.py
```

**INCLUDES api/cron/ subfolder - Vercel counts ALL .py files under api/**

**DO NOT add new .py files to api/ folder without removing one first.**

Config is in `lib/config.py` (not api/) specifically to avoid this limit.

## Do Not

- Store passwords (we use magic links)
- Add complex features without asking (keep it simple for the players)
- Change the ranking formula (games won, period)
- Add new API endpoints without checking count first (12 max)
