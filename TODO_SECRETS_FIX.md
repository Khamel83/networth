# URGENT: CRON_SECRET Fix Required

**Status:** Scheduled automation disabled temporarily. Manual triggers still work.

---

## What Happened

On **March 3, 2026**, commit `6e7ed51` changed auth from "loose" to "strict":

| Before March 3 | After March 3 |
|----------------|---------------|
| CRON_SECRET missing → **auth skipped, worked fine** | CRON_SECRET missing → **500 error, fails** |

Today (March 27) at 9am PT, the monthly availability reminder automation ran and failed because:
- GitHub Actions has `CRON_SECRET` set
- Vercel does **not** have `CRON_SECRET` set
- Auth mismatch → 500 error → failure alert email

---

## What Needs To Be Done (When at Computer)

### Step 1: Copy CRON_SECRET from GitHub
1. Go to: https://github.com/Khamel83/networth/settings/secrets/actions
2. Find `CRON_SECRET`
3. Click to reveal and **copy the value**

### Step 2: Set CRON_SECRET in Vercel
1. Go to: Vercel dashboard → networth project → Settings → Environment Variables
2. Click "Add New" (or edit existing if present)
3. Name: `CRON_SECRET`
4. Value: Paste from GitHub
5. Environment: **Production** (not Preview)
6. Click **Save**

### Step 3: Redeploy Vercel
1. In Vercel dashboard, click **Redeploy**
2. Wait ~2 minutes for deployment to complete

### Step 4: Verify
```bash
curl -s https://www.networthtennis.com/api/email
```
Should return: `{"success": true, "status": "ready", ...}`

### Step 5: Re-enable Scheduled Automation
1. Edit `.github/workflows/biweekly-emails.yml`
2. Uncomment the `schedule:` section (remove `#` from each line)
3. Remove the "SCHEDULE DISABLED" comment block
4. Commit and push

---

## Current Status

| System | Status |
|---------|--------|
| Website | ✅ Running fine |
| API endpoints | ✅ Working |
| Email sending | ✅ Resend configured |
| Scheduled automation | ⏸️ **Disabled temporarily** |
| Manual triggers | ✅ Still work (GitHub Actions → Run workflow) |

---

## Can Use Manual Triggers in Meantime

If you need to send availability reminders or generate pairings manually:

1. Go to GitHub Actions → Tennis League Emails
2. Click "Run workflow"
3. Select action (monthly_availability, generate_pairings, etc.)
4. Click "Run workflow"

---

## Related Files

- `.github/workflows/biweekly-emails.yml` — Automation workflow
- `README.md` — Environment variable docs
- `RUNBOOK.md` — Operations guide

---

**Created:** March 27, 2026
**To delete:** After CRON_SECRET is synced and schedule is re-enabled
