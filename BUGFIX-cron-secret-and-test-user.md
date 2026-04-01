# BUGFIX: CRON_SECRET Mismatch + Test User + Auth Test Bug

## Problem Summary

Three related issues preventing reliable email automation on the 1st of every month.

---

## Issue 1: CRON_SECRET Mismatch (CRITICAL — blocks all emails)

**Symptom:** Every scheduled email run fails with `HTTP 401: Unauthorized`

**Root Cause:** `CRON_SECRET` is set in GitHub Actions secrets, but the value in Vercel Environment Variables does NOT match. These are two separate systems — updating GitHub does NOT update Vercel.

**Fix:** Sync the value manually.

### Steps (2 minutes):
1. Go to https://github.com/Khamel83/networth/settings/secrets/actions
2. Copy the value of `CRON_SECRET`
3. Go to https://vercel.com → networth project → Settings → Environment Variables
4. Find `CRON_SECRET` — if it exists, click edit and paste the value
5. If it doesn't exist, create it with the same value
6. Environment: select Production (and Preview if prompted)
7. Save → Redeploy (Vercel usually auto-redeploys, but trigger one to be safe)

### Verify it worked:
After redeploy, go to GitHub Actions → biweekly-emails.yml → Run workflow → `health_check`
It should pass auth test now.

---

## Issue 2: Auth Test Was a False Positive (FIXED in code)

**Symptom:** Workflow says "✓ CRON_SECRET auth verified" then immediately fails with 401.

**Root Cause:** The auth verification step sends `action: "test_auth_check"`, but that action was NOT in the `PROTECTED_ACTIONS` list. So the endpoint never checked the CRON_SECRET — it just returned 400 (invalid action), which the workflow interpreted as "auth passed."

**Fix:** Added `test_auth_check` to `PROTECTED_ACTIONS` in `api/email.py`. Now it actually validates the secret before proceeding.

---

## Issue 3: Test User "Probe Test" Created in Production DB

**Symptom:** A fake player "Probe Test" (probe-test@test.invalid) was created in the players table, active, eligible for pairing.

**Root Cause:** A previous coding agent session likely tested the join endpoint against production, creating a real player record.

**Fix (two layers):**
1. **Signup validation** (`api/join.py`): Rejects `.invalid`, `.test`, `.example` TLDs and common test email patterns
2. **Pairing guard** (`api/pairings.py`): Skips players with test-looking email domains before generating pairings

**Still needed:** Deactivate the record in Supabase (Table Editor → players → Probe Test → is_active = false). Requires service role key or dashboard access.

---

## Changes in this PR

| File | Change |
|------|--------|
| `api/email.py` | Added `test_auth_check` to PROTECTED_ACTIONS so auth verification actually works |
| `api/join.py` | Added test/fake email rejection at signup |
| `api/pairings.py` | Added test email exclusion in pairing logic |

## What YOU need to do

1. **Sync CRON_SECRET** to Vercel (steps above) — this is the only manual step
2. **Deactivate "Probe Test"** in Supabase dashboard

That's it. Once CRON_SECRET is synced, tomorrow's 9am PT pairing run will work.
