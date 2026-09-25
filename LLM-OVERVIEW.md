# LLM Overview — networth
*Updated: 2026-09-25 (manual refresh after the September 2026 feature + maintenance pass)*

## What This Is
East Side LA women's tennis ladder (~50 members): monthly pairings, automated reminder emails, games-won ranking, admin dashboard. Live at https://www.networthtennis.com.

## Current State
*Status: 🟢 active, low-maintenance*

- Monthly automation green: pairings on the 1st, reminders on the 27th / last day / 15th, daily read-only health check, Supabase keep-alive.
- September 2026 additions: crystal-ball logo; admin score entry/editing (atomic DB function); monthly report page + email to Natalie/Ashley on the 2nd; signup notice email to Natalie/Ashley; Venmo pay step with optional "I paid" checkbox; Removed Members list.
- Migrations 05-07 applied in production.
- Independent daily watchdog on Vercel Cron emails the owner on any missed job or unconfirmed email.
- Known operational risk: the repo is public, so GitHub disables scheduled workflows after 60 days without activity. See RUNBOOK.md > Maintenance Checklist.

## Architecture
- Vercel static site (`public/`) + Python serverless functions (`api/`, 10 of the 12 Hobby slots).
- Supabase Postgres via a small REST client (`api/supabase_http.py`); triggers keep game totals and close pairings.
- Resend for email, gated by `EMAIL_DELIVERY_MODE`; scheduled sends go through the `email_delivery_log` ledger.
- GitHub Actions: `biweekly-emails.yml`, `monthly-report.yml`, `daily-health-check.yml`, `keep-alive.yml`, `tests.yml`.

## Key Commands
- `python3 serve.py` (local site)
- `python3 -m pytest -q` (179 tests)

## Dependencies
- **Runs on:** Vercel (Hobby), Supabase (free tier), GitHub Actions
- **Calls out to:** Supabase REST, Resend, Sentry (optional)
- **Env vars required:** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`, `EMAIL_DELIVERY_MODE`, `PUBLIC_TRANSACTIONAL_EMAILS`, `ADMIN_EMAIL`, `CRON_SECRET`, `SITE_URL`, `SENTRY_DSN` (optional)

## Critical Rules
- Read `CLAUDE.md` first: email-safety and pairings-reliability invariants are non-negotiable.
- Never commit member data or secrets; the repository is public.

## Gotchas
- `players` has no hard deletes (RLS); removal = `is_active=false`.
- Score edits require `migrations/06`; there is intentionally no non-atomic fallback.
