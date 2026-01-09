# CLAUDE.md - NET WORTH Tennis

## Project Overview

Women's tennis ladder for East Side LA. Monthly pairings, games-won ranking system.

**Live**: networthtennis.com
**Stack**: Vercel (static + Python functions) + Supabase + Gmail SMTP

## Quick Reference

### To change colors/copy/branding:
- Website CSS: Variables at top of each `public/*.html` file
- Email templates: `api/email.py` (all 7 templates with inline styles)

### To add a player:
Players self-register via join page → admin approves via dashboard → player is active

### To test emails:
- Emails only send if `SMTP_PASSWORD` is set in Vercel
- Check status: `GET /api/email` returns "ready" or "not_configured"

### Key files:
- `api/pairings.py` - Matching algorithm (skill-based), sends match emails
- `api/email.py` - Gmail SMTP sender + 7 email templates
- `api/join.py` - Player registration (handles re-registration of inactive accounts)
- `api/admin.py` - Admin dashboard API (approve/reject/pause players)
- `.github/workflows/biweekly-emails.yml` - Scheduled email automation

## Architecture

```
User visits site
    → Vercel serves static HTML from /public
    → JS fetches from /api/* endpoints
    → API reads/writes to Supabase
    → Gmail SMTP sends emails (via api/email.py)

Automated Emails (GitHub Actions)
    → 27th of month: Availability check to all active players
    → Last day of month: Final availability reminder
    → 1st of month: Generate pairings + send match emails
    → 15th of month: Mid-month reminder for pending matches
```

## Email System

**Sender:** Ashley's Gmail (`ashleybrooke.kaufman@gmail.com`)
**Method:** Gmail SMTP with app password
**Env var:** `SMTP_PASSWORD` (Gmail app password, 16 chars)

### 7 Email Templates (in api/email.py)

| Email | Trigger | Subject |
|-------|---------|---------|
| Welcome | Signup via `/join` | Welcome to Net Worth Tennis! |
| Match Assignment | Pairing generation | {Player1}, meet {Player2} - You're matched for {Month}! |
| Availability Check | Cron (27th) | Quick check: are you playing next month? |
| Final Reminder | Cron (last day) | Last call: update your playing status |
| Mid-Month Reminder | Cron (15th) | Friendly reminder to play your {Month} match |
| Sit-Out Confirmation | Player pauses | You're sitting out {Month} |
| Rejoin Confirmation | Player rejoins | Welcome back! You're in for {Month} |

## Database Schema

```
players
  - id, email, name, skill_level
  - rank, total_games, matches_played
  - is_active (false until admin approves)
  - unavailable_until (pause feature)
  - avail_weekday_early/day/late, avail_weekend_early/day/late

matches
  - player1_id, player2_id
  - player1_games, player2_games (set scores)
  - period_label ("January 2025")

match_assignments
  - player1_id, player2_id, period_label
  - status (pending/accepted/completed)

match_feedback
  - would_play_again (for silent blocking)
```

## RLS Policies (IMPORTANT)

The `players` table has NO DELETE policy. Delete operations fail silently.

**Allowed operations:**
- SELECT (all)
- UPDATE (all)
- INSERT (all)

**NOT allowed:**
- DELETE (no policy exists)

This is why `api/join.py` uses UPDATE for re-registrations instead of delete+insert.

## Environment Variables

### Vercel Dashboard:
| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SMTP_PASSWORD` | Gmail app password (16 chars, from Ashley's account) |
| `SITE_URL` | `https://networthtennis.com` |
| `ADMIN_EMAIL` | Admin notification email |
| `CRON_SECRET` | Secret for GitHub Actions auth |

### GitHub Repo Secrets:
- `SITE_URL`, `CRON_SECRET`

## Vercel Limits (CRITICAL)

**Hobby plan limit: 12 serverless functions max**

Current count: 11 (1 slot available)
```
api/admin.py      api/auth.py       api/email.py      api/health.py
api/join.py       api/matches.py    api/migrate.py    api/pairings.py
api/players.py    api/profile.py    api/upload.py
```

**DO NOT add new .py files to api/ folder without checking count first.**

## Common Operations

### Via Admin Dashboard (frontend):
- Approve new players
- Pause/unpause players
- View all players and their status

### Via Supabase (rare, admin only):
```sql
-- Manually recalculate rankings
SELECT recalculate_rankings();

-- See pending matches
SELECT * FROM match_assignments WHERE status = 'pending' AND period_label = 'January 2025';
```

## Do Not

- Store passwords (we use magic links)
- Add complex features without asking (keep it simple for the players)
- Change the ranking formula (games won, period)
- Add new API endpoints without checking count first (12 max)
- Use DELETE operations on players table (RLS blocks them)
