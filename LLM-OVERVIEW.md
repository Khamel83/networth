# LLM Overview — networth
*Updated: 2026-05-10 07:35 UTC | Tier: standard | Auto-updated: daily cron*

## What This Is
East Side LA women's tennis ladder with monthly pairings, automated reminders, and games-won ranking.

## Current State
*Status: 🟢 active from local git history*

**Active work:**
- 92bc5f9 chore: bootstrap LLM-OVERVIEW files 2026-05-10
- 0cd652b fix: clear_period clears email_log FK + automation_runs lock before deleting
- 64d5c70 feat: add dry_run mode to pairings API for human preview before sending
- 6f7be7f feat: add clear_period action to pairings API for admin rematch
- 7360903 fix: check matches table for repeat prevention, not just match_assignments
- b6c4ded fix: handle 409 in health-check recovery loop

**Known issues:**
- No known issue found in recent commit subjects or local TODO/BLOCKERS docs.

**Recent changes (7 days):**
- `92bc5f9 chore: bootstrap LLM-OVERVIEW files 2026-05-10`

## Architecture
- Stack marker: Vercel deployment
- Top-level entry: `AGENTS.md`
- Top-level entry: `api/`
- Top-level entry: `BUGFIX-match-history-unknown.md`
- Top-level entry: `BUGFIX-once-and-for-all.md`
- Top-level entry: `CLAUDE.md`
- Top-level entry: `content/`
- Top-level entry: `CONTENT_LOCATIONS.md`
- Top-level entry: `docs/`

## Key Commands
- `git status --short`
- `git log --oneline -5`

## Dependencies
- **Runs on:** Not declared in local repo evidence.
- **Calls out to:** See repo docs and config files.
- **Called by:** Not declared in local repo evidence.
- **Env vars required:** `ADMIN_EMAIL`, `CRON_SECRET`, `SITE_URL`, `SMTP_PASSWORD`, `SUPABASE_ANON_KEY`, `SUPABASE_URL`

## Critical Rules
- Preserve repo-local instructions in `AGENTS.md`, `CLAUDE.md`, or README when present.
- Do not infer behavior from the repository name alone; verify against local docs and source.

## Gotchas
- Generated from local evidence only: git history, top-level structure, README/CLAUDE/AGENTS/docs, and env examples.
