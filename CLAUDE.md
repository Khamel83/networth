# CLAUDE.md - NET WORTH Tennis

## Project Overview

Women's tennis ladder for East Side LA. Monthly pairings, games-won ranking system.

**Live**: networthtennis.com
**Stack**: Vercel (static + Python functions) + Supabase + Resend

## Quick Reference

### To change colors/copy/branding:
- Email content: `api/config.py`
- Website CSS: Variables at top of each `public/*.html` file

### To add a player:
Add row to `players` table in Supabase

### To test emails locally:
Set `EMAIL_ENABLED=false` in Vercel env vars - emails get logged but not sent

### Key files:
- `api/pairings.py` - Matching algorithm (skill-based)
- `api/email.py` - All email templates
- `api/config.py` - Centralized config
- `.github/workflows/biweekly-emails.yml` - Scheduled emails

## Architecture

```
User visits site
    → Vercel serves static HTML from /public
    → JS fetches from /api/* endpoints
    → API reads/writes to Supabase
    → Resend sends emails

GitHub Actions (1st + 15th of month)
    → Calls /api/cron/monthly to generate pairings
    → Calls /api/email to send notifications
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
- `RESEND_API_KEY`
- `SITE_URL` = https://networthtennis.com
- `EMAIL_FROM` = NET WORTH Tennis <noreply@networthtennis.com>
- `ADMIN_EMAIL` = where join requests go
- `EMAIL_ENABLED` = true/false kill switch
- `CRON_SECRET` = for GitHub Actions auth

Set in GitHub repo secrets:
- `SITE_URL`, `CRON_SECRET`

## Fallback Mode

If Supabase/Vercel are down, `public/fallback.html` is a pure static page with:
- Current ladder (manually updated)
- mailto: links for score reporting
- No JS dependencies

## Do Not

- Store passwords (we use magic links)
- Add complex features without asking (keep it simple for the players)
- Change the ranking formula (games won, period)
