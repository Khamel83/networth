# Net Worth Tennis: Email Automation Fix — Once and For All

## The Problem

Emails haven't sent since March 4th. Every automated run since then either failed silently or was a no-op. The root cause is a single env var mismatch, compounded by a broken auth test that masked the real error.

## Root Cause

`CRON_SECRET` in GitHub Actions ≠ `CRON_SECRET` in Vercel Environment Variables.

These are **two separate systems**. Changing one does not change the other. The Vercel deployment reads its own env vars at build time. If the secret doesn't match, every protected endpoint call returns 401.

The auth test in the workflow was also broken — it sent `test_auth_check` as the action, which wasn't in the protected list, so the endpoint never checked the secret at all. It returned 400 (invalid action) and the workflow said "auth passed." False positive for weeks.

## The Fix (One Step)

1. Go to **GitHub** → Khamel83/networth → Settings → Secrets and variables → Actions → `CRON_SECRET` → **copy the value**
2. Go to **Vercel** → networth project → Settings → Environment Variables
3. Find `CRON_SECRET` — if it exists, edit it and paste the value. If not, create it.
4. Make sure it's assigned to **Production** environment.
5. Click **Save**.
6. Trigger a redeploy: Vercel → networth → Deployments → latest → **Redeploy**

## Verify It Worked

1. After redeploy completes (~1 min), go to **GitHub Actions** → biweekly-emails.yml → **Run workflow**
2. Select action: `health_check` → click **Run workflow**
3. If auth test passes → you're good. Cancel the run after the auth check step (pairings don't need to regenerate).
4. If auth test fails (401) → the Vercel env var still doesn't match. Compare the values character by character.

## What Happens Tomorrow

- **9:00 AM PT** — Scheduled run generates April pairings + sends match emails
- **12:00 PM PT** — Health check runs; if pairings are missing, it retries up to 3 times
- If both fail, you get an error notification

## What Was Fixed in Code

| File | Fix |
|------|-----|
| `api/email.py` | `test_auth_check` added to `PROTECTED_ACTIONS` — auth test now actually validates the secret |
| `api/join.py` | Rejects `.invalid`, `.test`, `.example` TLDs and test-looking emails at signup |
| `api/pairings.py` | Skips players with test email domains during pairing generation |

## Outstanding Cleanup

**Deactivate "Probe Test" in the database:**
- Supabase Dashboard → Table Editor → `players` → find "Probe Test" → set `is_active` to false → Save
- This was a fake user created by a previous agent session testing the live join endpoint

## Rules Going Forward

- **Never trigger email workflows manually.** Only scheduled runs.
- **Never test against production endpoints.** Use `.env` local values for testing.
- **GitHub Secrets ≠ Vercel Env Vars.** If a secret is needed by both, set it in both places.
