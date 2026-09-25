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
| 2nd of month, 10am PT | Last month's report emailed to Natalie + Ashley | GitHub Actions (`monthly-report.yml`) |
| Daily | Read-only health check; fails if current-month pairings are missing after the 1st | GitHub Actions |
| Daily, 9am PT | Watchdog (Vercel, independent of GitHub) emails the owner if any job didn't run or any email failed; all-clear on the 3rd | Vercel Cron |
| Every 5 days | Supabase keep-alive ping (free tier pauses after 7 idle days) | GitHub Actions |
| On player signup / re-join | Notice emailed to Natalie + Ashley; welcome email to the player only if `PUBLIC_TRANSACTIONAL_EMAILS=enabled` | Automatic |
| On match score submitted | Games added to both players, pairing marked complete | Automatic (database triggers) |

---

## Admin Dashboard Operations

**Location:** `https://www.networthtennis.com/admin`

Signups are active immediately; there is no approval step. Natalie and Ashley get an email for each signup.

### Mark Someone Paid

1. Check Venmo
2. In **All Members**, tick the **Paid** box (saves instantly)
3. The monthly report's "Not marked paid" list shows "Says paid" for anyone who ticked "I paid" when joining

### Enter or Fix a Score

1. In **Pairings & Scores**, pick the month
2. Click **Enter score** on the pairing (or **+ Record a match** for an extra match)
3. For an existing score, click **Edit**; both players' game totals are corrected automatically
4. Admins may record a match that ended early or a forfeit as-is (0–7 per set)

### Pause a Player

1. Find the player in **All Members**, click **Edit**
2. Click **Pause**; they won't be matched until unpaused

### Edit Player Info

1. Find the player, click **Edit**
2. Update name, email, phone, membership tier, or availability
3. Click **Save Changes**

### Remove / Restore a Player

1. Find the player, click **Remove** (soft delete: RLS blocks real deletes)
2. They disappear from rankings, the directory, pairings, and emails
3. To undo: open **Removed Members** (collapsed at the bottom) and click **Restore**
4. If a removed person signs up again with the same email, their account is reactivated

### Monthly Report

- **Monthly Report** section: pick a month, then **Download CSV** or **Print**
- The same report is emailed to Natalie + Ashley on the 2nd for the previous month

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

To resend a monthly report: **Actions > Monthly League Report > Run workflow**, optionally entering a month like `August 2026`. This sends real email to Natalie and Ashley; a month that already went out is not sent twice.

### Read-only API checks (safe, no emails sent)
```bash
curl https://www.networthtennis.com/api/system
curl https://www.networthtennis.com/api/email
curl https://www.networthtennis.com/api/pairings
```

---

## If You Get a Watchdog Email

The email says what's wrong in plain words. It repeats daily until fixed.
- "... never ran": open GitHub > Actions, find the workflow, check it is enabled, and run it manually (see Manual Triggers above).
- "did not finish cleanly" / emails "unknown" or "failed": run the same workflow again; if it fails, the run log in Actions says why.
- "no pairings this month": run **Tennis League Emails > generate_pairings** manually.
- No all-clear on the 3rd: the watchdog itself isn't running; check Vercel > Project > Settings > Cron Jobs and that `ADMIN_EMAIL` and `CRON_SECRET` are set.

## Maintenance Checklist

Small league, light touch. Nothing here is monthly.

**Once a year (pick a date, e.g. January):**
- Renew the domain (`networthtennis.com`) at the registrar; set auto-renew if possible
- Confirm the Resend domain is still verified (Resend > Domains) and the API key works (`GET /api/email` shows `ready`)
- Glance at GitHub > Actions: the daily health check and "Tennis League Emails" runs should be green
- Export `players` and `matches` to CSV from Supabase (Table Editor > Export) and store it somewhere private
- Rotate `CRON_SECRET` if anyone who had it has left (update Vercel and GitHub together)

**If the repo sits untouched for ~2 months:** GitHub turns off scheduled workflows on public repositories after 60 days without activity. The watchdog emails you the next morning when a job doesn't run; fix it with Actions tab > pick the workflow > **Enable workflow**, then run it manually.

**Keep the repository public.** Making it private (tried September 2026) moves the workflows onto GitHub's paid minutes; on this account every job then failed instantly without starting. The code holds no secrets (those live in Vercel and GitHub settings).

**When membership renews each year:** clear the Paid boxes in the admin page (or ask a developer to reset `has_paid` for everyone).

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

**Check 2: Is delivery switched on?**
The same `GET /api/email` response shows `delivery_mode`. It must be `live` to send. `disabled` and `dry_run` never contact Resend (by design). Welcome and password-reset emails also need `PUBLIC_TRANSACTIONAL_EMAILS=enabled`.

**Check 3: Are GitHub Actions running?**
If scheduled runs stopped entirely, GitHub may have disabled them after 60 days of repo inactivity: Actions tab > pick the workflow > **Enable workflow**.
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
| Monthly report / signup notice recipients | Change `ORGANIZER_EMAILS` in `api/email.py` (developer) |
| Domain renewal | Account owner |
| Player disputes | League admins (Ashley/Natalie) |

---

## Environment Variables Reference

These are set in Vercel and should NOT be changed unless necessary:

| Variable | Purpose | Where to Find |
|----------|---------|---------------|
| `SUPABASE_URL` | Database connection | Supabase > Settings > API |
| `SUPABASE_ANON_KEY` | Public key (deny-all RLS) | Supabase > Settings > API |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side database access | Supabase > Settings > API |
| `EMAIL_DELIVERY_MODE` | `live` to send email | Set by the owner |
| `PUBLIC_TRANSACTIONAL_EMAILS` | `enabled` for welcome/reset mail | Set by the owner |
| `RESEND_API_KEY` | Email sending | Resend dashboard |
| `SITE_URL` | Link generation | `https://www.networthtennis.com` |
| `CRON_SECRET` | Protect scheduled endpoints | Must match GitHub + Vercel |

---

## Backups

### Database Backups

What Supabase backs up depends on the plan; check Supabase > Database > Backups. Do not rely on it alone.

The old weekly GitHub backup job was removed in September 2026: it never saved anything, and in this public repository it would have published member emails and phone numbers if it had worked.

To export data (do this at least yearly):
1. Supabase dashboard > Table Editor
2. Select table (`players`, `matches`, `match_assignments`)
3. Click **Export** > CSV and keep it somewhere private (not in this repo)

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
