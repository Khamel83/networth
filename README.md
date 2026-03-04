# NET WORTH Tennis Ladder

East Side LA women's tennis ladder with monthly pairings, automated reminders, and games-won ranking.

## Live

- `https://www.networthtennis.com` (canonical)
- `https://networthtennis.com` redirects to `www`

## Autopilot Model

This system is designed to run without monthly manual intervention.

Automated schedule (`.github/workflows/biweekly-emails.yml`):
- 27th @ 9am PT: availability reminder
- Last day @ 9am PT: final reminder
- 1st @ 9am PT: generate pairings + send match emails
- 1st @ 12pm PT: health-check/self-heal backup
- 15th @ 9am PT: mid-month pending-match reminder

Daily safety net (`.github/workflows/daily-health-check.yml`):
- endpoint checks
- template compile check
- failure alert path

## Reliability Hardening (March 2026)

- Protected automation actions now require `CRON_SECRET`.
- Scheduled actions fail closed on delivery/validation errors (no silent success).
- Pairings generation has preflight checks, lock semantics, and strict postchecks.
- `reconcile_month` endpoint exists for safe month reconciliation (`POST /api/system`).
- Reliability tracking tables:
  - `automation_runs`
  - `automation_events`
  - `email_delivery_log`

Migration:
- `migrations/02_reliability_automation.sql`

## Tech Stack

- Frontend: static HTML/CSS/JS on Vercel
- Backend: Python serverless functions on Vercel
- Database: Supabase (PostgreSQL)
- Auth: password-based login + reset token flow
- Email: Resend (`hello@networthtennis.com`)

## Current API Layout

`api/admin.py`, `api/auth.py`, `api/email.py`, `api/join.py`, `api/matches.py`, `api/pairings.py`, `api/players.py`, `api/profile.py`, `api/system.py`, `api/upload.py`

Utility modules:
- `api/supabase_http.py`
- `api/reliability.py`
- `api/sentry_init.py`

## Required Configuration

Vercel env vars:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `RESEND_API_KEY`
- `ADMIN_EMAIL`
- `CRON_SECRET`
- `SITE_URL` = `https://www.networthtennis.com`

GitHub Actions secrets:
- `SITE_URL` = `https://www.networthtennis.com`
- `CRON_SECRET` (must exactly match Vercel)

## Operational Endpoints

- `GET /api/system` -> service/database health
- `GET /api/email` -> email system status
- `GET /api/pairings` -> current month pairings
- `POST /api/system` with `{"action":"reconcile_month","dry_run":true}` (auth required)

## Local Dev

```bash
python3 serve.py
```
