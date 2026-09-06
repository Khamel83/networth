# Operations Runbook

This document covers routine operations and what to do when things go wrong. Designed for the league to run independently without a developer.

---

## What Runs Automatically (Autopilot)

These processes run without any human intervention:

| Schedule | What Happens | System |
|----------|--------------|--------|
| 27th of month, 9am PT | Availability check emails sent | GitHub Actions |
| Last day of month, 9am PT | Final reminder emails sent | GitHub Actions |
| 1st of month, 9am PT | Pairings generated + match emails sent | GitHub Actions |
| 1st of month, 1pm PDT / noon PST | Read-only post-generation pairing check | GitHub Actions |
| 15th of month, 9am PT | Mid-month reminder emails sent | GitHub Actions |
| Daily, from the 2nd of each month | Read-only watchdog fails if current-month pairings are missing | GitHub Actions |
| On player signup | Welcome email sent | Automatic |
| On match score submitted | Rankings recalculated | Automatic |

---

## Admin Dashboard Operations

**Location:** `https://www.networthtennis.com/admin`

### Approve New Players

1. Log in with an admin account
2. New signups appear in "Pending Approvals"
3. Verify they paid via Venmo
4. Click **Approve** to activate them

### Pause a Player

1. Find the player in the list
2. Click **Pause**
3. They won't be matched until unpaused

### Edit Player Info

1. Find the player
2. Click **Edit**
3. Update name, email, phone, or membership tier
4. Click **Save**

### Reject/Remove a Player

1. Find the player
2. Click **Reject** or **Deactivate**
3. Note: This doesn't delete them, just marks them inactive

---

## Manual Triggers (Use Only If Needed)

If automation ever fails, trigger workflows manually from GitHub Actions.

### Via GitHub Actions (Recommended)

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Tennis League Emails** workflow
4. Click **Run workflow**
5. Select the action:
   - `monthly_availability` - Send availability check
   - `final_availability` - Send final reminder
   - `generate_pairings` - Generate pairings + send match emails
   - `mid_month_reminder` - Send mid-month reminder
6. Click **Run workflow**

### Read-only API checks (safe, no emails sent)
```bash
curl https://www.networthtennis.com/api/system
curl https://www.networthtennis.com/api/email
curl https://www.networthtennis.com/api/pairings
```

---

## Annual Tasks

### Domain Renewal

**When:** Before your domain expires (check your registrar)

**How:**
1. Log into your domain registrar (GoDaddy, Namecheap, etc.)
2. Renew the domain

**Set a calendar reminder** for 30 days before expiration.

### Review Resend API Key Access
**When:** Annually or when team access changes
**How:** Rotate `RESEND_API_KEY` in Vercel and confirm `GET /api/email` is still `ready`

---

## Troubleshooting

### Emails Not Sending

**Check 1: Is the email system configured?**
```
Visit: https://www.networthtennis.com/api/email
Expected: {"status": "ready"}
```

If it says "not_configured", `RESEND_API_KEY` is missing in Vercel.
1. Go to Vercel dashboard > Your project > Settings > Environment Variables
2. Check that `RESEND_API_KEY` exists and has a value

**Check 3: Are GitHub Actions running?**
1. Go to GitHub repo > Actions tab
2. Check if recent workflow runs succeeded
3. If failing, check the error messages

### Website Not Loading

**Check 1: Is Vercel up?**
- Visit [vercel.com/status](https://www.vercel-status.com/)

**Check 2: Is the domain configured?**
- Try visiting the `.vercel.app` URL directly
- If that works but custom domain doesn't, check DNS settings

**Check 3: Are environment variables set?**
- Vercel dashboard > Settings > Environment Variables
- Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`

### Database Issues

**"Supabase connection failed"**

1. Log into [supabase.com](https://supabase.com)
2. Check your project status
3. If paused (free tier pauses after 7 days inactivity):
   - Click **Restore** to wake it up
   - Takes 1-2 minutes

**Check database is working:**
```
Visit: https://www.networthtennis.com/api/system
Expected: {"status": "healthy"}
```

### Players Can't Log In

- Verify the player email exists in `players`
- Ask player to use password reset flow (`/reset-password`)
- Confirm password reset email delivery via Resend dashboard if needed

---

## Emergency Contacts

| Issue | Who to Contact |
|-------|----------------|
| Website down | Developer (Khamel) |
| Database issues | Developer |
| Resend key/access issues | Account owner (Ashley) |
| Domain renewal | Account owner |
| Player disputes | League admins (Ashley/Natalie) |

---

## Environment Variables Reference

These are set in Vercel and should NOT be changed unless necessary:

| Variable | Purpose | Where to Find |
|----------|---------|---------------|
| `SUPABASE_URL` | Database connection | Supabase > Settings > API |
| `SUPABASE_ANON_KEY` | Database auth | Supabase > Settings > API |
| `RESEND_API_KEY` | Email sending | Resend dashboard |
| `SITE_URL` | Link generation | `https://www.networthtennis.com` |
| `CRON_SECRET` | Protect scheduled endpoints | Must match GitHub + Vercel |

---

## Backups

### Database Backups

Supabase automatically backs up your database daily (free tier: 7 days retention).

To manually export data:
1. Supabase dashboard > Table Editor
2. Select table (e.g., `players`)
3. Click **Export** > CSV

### Code Backups

Your code is stored in GitHub. As long as you don't delete the repository, your code is safe.

---

## Scaling Notes

The current setup supports:
- Up to ~100 players comfortably
- Resend free-tier limits depend on plan
- Unlimited website traffic (Vercel handles scaling)

If you grow beyond 100 players:
- Consider higher Resend plan for larger volume
- Consider Supabase Pro plan for more database capacity
- Contact a developer for assistance

---

## Reliability-Specific Recovery

### Reconcile month state (safe repair path)
Use when you suspect assignment status drift or month consistency issues.

Authenticated POST:
```bash
curl -X POST https://www.networthtennis.com/api/system \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <CRON_SECRET>" \
  -d '{"action":"reconcile_month","dry_run":true}'
```

Then run with `dry_run:false` only if dry run looks correct.

### Critical Secrets Checklist

These must exist and be consistent:
- Vercel: `CRON_SECRET`, `SITE_URL=https://www.networthtennis.com`
- GitHub Actions: `CRON_SECRET`, `SITE_URL=https://www.networthtennis.com`

If secrets mismatch, scheduled jobs will fail by design.

### Pairing repeat policy (operator expectation)

- The monthly pairing engine prioritizes non-repeat pairings.
- It uses the general-graph maximum-weight solver, not a size-based greedy fallback; the supported target is 2–100 players.
- If repeat pairs appear, treat that as a bug and investigate immediately (do not assume expected behavior).
