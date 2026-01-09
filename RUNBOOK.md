# Operations Runbook

This document covers routine operations and what to do when things go wrong. Designed for the league to run independently without a developer.

---

## What Runs Automatically

These processes run without any human intervention:

| Schedule | What Happens | System |
|----------|--------------|--------|
| 27th of month, 9am PT | Availability check emails sent | GitHub Actions |
| Last day of month, 9am PT | Final reminder emails sent | GitHub Actions |
| 1st of month, 9am PT | Pairings generated + match emails sent | GitHub Actions |
| 15th of month, 9am PT | Mid-month reminder emails sent | GitHub Actions |
| On player signup | Welcome email sent | Automatic |
| On match score submitted | Rankings recalculated | Automatic |

---

## Admin Dashboard Operations

**Location:** `https://networthtennis.com/admin.html`

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

## Manual Email Triggers

If automated emails don't send, you can trigger them manually:

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

### Via Direct API (Advanced)

```bash
# Check email system status
curl https://networthtennis.com/api/email

# Should return: {"status": "ready"}
```

---

## Annual Tasks

### Domain Renewal

**When:** Before your domain expires (check your registrar)

**How:**
1. Log into your domain registrar (GoDaddy, Namecheap, etc.)
2. Renew the domain

**Set a calendar reminder** for 30 days before expiration.

### Review Gmail App Password

**When:** Annually or if someone with access leaves

**How:** See [GMAIL_SETUP.md](./GMAIL_SETUP.md) for password rotation instructions.

---

## Troubleshooting

### Emails Not Sending

**Check 1: Is the email system configured?**
```
Visit: https://networthtennis.com/api/email
Expected: {"status": "ready"}
```

If it says "not_configured", the Gmail password is missing:
1. Go to Vercel dashboard > Your project > Settings > Environment Variables
2. Check that `SMTP_PASSWORD` exists and has a value
3. If missing, see [GMAIL_SETUP.md](./GMAIL_SETUP.md)

**Check 2: Is Gmail blocking?**
- Gmail may block if you hit daily limits (~100 emails)
- Check the sender's Gmail inbox for bounce notifications
- Wait 24 hours if you hit limits

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
Visit: https://networthtennis.com/api/health
Expected: {"status": "ok"}
```

### Players Can't Log In

**Magic link not arriving:**
- Check spam/junk folder
- Verify their email is correct in database
- Supabase dashboard > Authentication > Users > check status

**Session expired:**
- Have them request a new magic link
- Sessions last 7 days by default

---

## Emergency Contacts

| Issue | Who to Contact |
|-------|----------------|
| Website down | Developer (Khamel) |
| Database issues | Developer |
| Gmail password issues | Account owner (Ashley) |
| Domain renewal | Account owner |
| Player disputes | League admins (Ashley/Natalie) |

---

## Environment Variables Reference

These are set in Vercel and should NOT be changed unless necessary:

| Variable | Purpose | Where to Find |
|----------|---------|---------------|
| `SUPABASE_URL` | Database connection | Supabase > Settings > API |
| `SUPABASE_ANON_KEY` | Database auth | Supabase > Settings > API |
| `SMTP_PASSWORD` | Email sending | Gmail app password |
| `SITE_URL` | Link generation | Your domain |

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
- ~100 emails per day (Gmail limit)
- Unlimited website traffic (Vercel handles scaling)

If you grow beyond 100 players:
- Consider upgrading to a dedicated email service (SendGrid, Mailgun)
- Consider Supabase Pro plan for more database capacity
- Contact a developer for assistance
