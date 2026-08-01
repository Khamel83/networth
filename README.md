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
- 1st @ 12pm PT: read-only pairing health check
- 15th @ 9am PT: mid-month pending-match reminder

Daily safety net (`.github/workflows/daily-health-check.yml`):
- read-only endpoint checks
- public-response privacy checks
- GitHub step summary only; no email alert path

## Reliability and Email Safety

- `EMAIL_DELIVERY_MODE=disabled` is the safe default. `dry_run` reports targets without provider calls; `live` is explicit operator-controlled mode.
- Signup welcome and password-reset mail also require `PUBLIC_TRANSACTIONAL_EMAILS=enabled`; leave it unset while delivery is frozen.
- Protected automation actions require `Authorization: Bearer CRON_SECRET`.
- Scheduled messages are claimed in `email_delivery_log` before provider submission and use stable batch idempotency keys.
- `accepted` means Resend accepted the request, not that every inbox has delivered it. `unknown` and `failed` batches are repairable only through reconciliation with the original idempotency key.
- A provider timeout or post-provider audit failure produces a reconciliation state instead of a false send failure.
- `email_log` is legacy-only during the reviewed migration; `email_delivery_log` is canonical.
- Public `/api/players` is leaderboard-only. `/api/pairings` requires a cron secret or verified admin session.
- Workflows never replay a send to verify deployment; deployment checks use safe GET/OPTIONS requests only.
- Pairings generation has preflight checks, lock semantics, and strict postchecks.
- Pairings generation now uses a general-graph maximum-weight solver for dynamic rosters through 100 players, so avoidable repeat pairs are eliminated without a size-based greedy fallback.
- Pairing quality uses a deterministic uncertainty-aware rating rebuilt from valid two-set match history; no new player data is required.
- `reconcile_month` endpoint exists for safe month reconciliation (`POST /api/system`).
- Reliability tracking tables:
  - `automation_runs`
  - `automation_events`
  - `email_delivery_log`
  - `issue_reports`

Migration:
- `migrations/02_reliability_automation.sql`
- `migrations/04_email_automation_hardening.sql` (run only after the documented read-only schema inventory)
- `migrations/04_match_history_integrity.sql` (run after resolving any existing duplicate pair/period match rows)

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
- `api/ratings.py`
- `api/matching.py`

## Required Configuration

Vercel env vars:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `RESEND_API_KEY`
- `EMAIL_DELIVERY_MODE` = `disabled` (safe default; use `dry_run` for target counts; `live` only after explicit approval)
- `ADMIN_EMAIL`
- `CRON_SECRET`
- `SITE_URL` = `https://www.networthtennis.com`

GitHub Actions secrets:
- `SITE_URL` = `https://www.networthtennis.com`
- `CRON_SECRET` (must exactly match Vercel)

## Operational Endpoints

- `GET /api/system` -> service/database health
- `GET /api/email` -> email system status
- `GET /api/players` -> public leaderboard fields only
- `GET /api/pairings` -> pairing details; cron/admin authorization required
- `POST /api/email` with `action: reconcile_email_delivery` -> protected delivery repair using the original batch key
- `POST /api/system` with `{"action":"reconcile_month","dry_run":true}` (auth required)

## Pairing Rules (Current)

- Primary objective: no repeat pairings when a fresh full pairing is possible.
- The solver first maximizes the number of assignments, then fresh pairings, then rating similarity, while never using a hard-blocked edge.
- Repeats are only allowed as last resort when constraints make a fresh full pairing impossible.
- New players start neutral with high uncertainty; returning players retain history but regain uncertainty after inactivity.

## Local Dev

```bash
python3 serve.py
```
