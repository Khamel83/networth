# Clone and Customize Guide

Want to create your own tennis league (e.g., "West Side Tennis League")? This guide covers everything you need.

## Prerequisites

You'll need accounts on these free services:

| Service | Purpose | Time to Setup |
|---------|---------|---------------|
| [GitHub](https://github.com) | Host your code | 2 min |
| [Vercel](https://vercel.com) | Host your website | 2 min (sign up with GitHub) |
| [Supabase](https://supabase.com) | Database + Auth | 3 min |
| Gmail account | Send emails | Have one ready |

## Quick Start (30 minutes)

### Step 1: Fork the Repository

1. Go to the original repo on GitHub
2. Click **Fork** (top right)
3. Name it something like `westside-tennis`

### Step 2: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **New Project**
3. Choose a name (e.g., `westside-tennis`)
4. Set a strong database password (save this!)
5. Select region closest to your players
6. Wait 2 minutes for setup

**Copy these values** (Settings > API):
- Project URL: `https://xxxxx.supabase.co`
- `anon` public key: `eyJhbGc...` (long string)

### Step 3: Set Up Database

1. In Supabase, go to **SQL Editor**
2. Click **New Query**
3. Open `supabase-final-setup.sql` from your fork
4. **EDIT THESE LINES** before running:

```sql
-- Line 34: Change league name
INSERT INTO league_settings (league_name, ...)
VALUES ('YOUR LEAGUE NAME HERE', ...);
```

5. Run the entire script

### Step 4: Set Up Gmail App Password

See [GMAIL_SETUP.md](./GMAIL_SETUP.md) for detailed instructions.

You'll get a 16-character password like: `abcd efgh ijkl mnop`

### Step 5: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **Add New > Project**
3. Import your forked repository
4. Add environment variables:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SMTP_PASSWORD` | Gmail app password (no spaces) |
| `SITE_URL` | `https://your-project.vercel.app` (update after deploy) |
| `ADMIN_EMAIL` | Your admin email |

5. Click **Deploy**

### Step 6: Configure GitHub Actions

1. In your GitHub repo, go to **Settings > Secrets > Actions**
2. Add these secrets:
   - `SITE_URL` = your Vercel URL (e.g., `https://westside-tennis.vercel.app`)

---

## Customization Checklist

### Required Changes (Must Do)

These values are hardcoded and MUST be changed:

#### 1. `lib/config.py` - Main branding

```python
# Line 17-19: Change these
LEAGUE_NAME = "WEST SIDE"  # Your league name
LEAGUE_TAGLINE = "West LA Women's Tennis"  # Your tagline
SITE_URL = "https://your-domain.com"  # Your domain

# Line 97-106: Change court list
APPROVED_COURTS = [
    "Your Court 1",
    "Your Court 2",
    # ...
]
```

#### 2. `api/email.py` - Email sender

```python
# Line 17-18: Change these
SMTP_USER = 'your-league-email@gmail.com'
SENDER_NAME = 'West Side Tennis'
```

#### 3. `api/pairings.py` - Admin accounts

```python
# Line 181: Change admin emails for "flex" logic
return email in ['admin1@gmail.com', 'admin2@gmail.com']

# Line 237: Change or remove Ashley-specific logic
```

#### 4. `content/landing.json` - Homepage content

```json
{
  "hero": {
    "subtitle": "YOUR LOCATION",
    "title": "Your League Name"
  },
  "membership": {
    "description": "...Venmo @YOUR_HANDLE..."
  },
  "footer": {
    "contactEmail": "your@email.com"
  }
}
```

#### 5. `content/emails.json` - Email templates

Update all references to "Net Worth" with your league name.

#### 6. HTML Files - Venmo and pricing

In `public/index.html` and `public/join.html`, search and replace:
- `@NCOFFEN` → Your Venmo handle
- `$35` → Your player price
- `$45` → Your social butterfly price
- `networthtennis.com` → Your domain

### Optional Changes

#### Colors (`lib/config.py`)

```python
COLORS = {
    'gold': '#YOUR_HEX',  # Primary accent
    'lime': '#YOUR_HEX',  # Secondary accent
    # ...
}
```

#### Skill Levels (`lib/config.py`)

```python
SKILL_LEVELS = [
    ('5.0', '5.0 Tournament'),
    ('4.5', '4.5 Advanced+'),
    # Customize as needed
]
```

---

## File Reference

| File | What to Change |
|------|----------------|
| `lib/config.py` | League name, tagline, colors, courts, skill levels |
| `api/email.py` | Gmail account, sender name, hardcoded links |
| `api/pairings.py` | Admin email addresses |
| `content/landing.json` | Homepage text, Venmo handle, contact email |
| `content/emails.json` | Email templates |
| `public/index.html` | Venmo handle, prices (search for `@NCOFFEN`, `$35`) |
| `public/join.html` | Venmo handle, prices, membership text |
| `supabase-final-setup.sql` | League name in database |

---

## Testing Your Setup

### 1. Test the website
- Visit your Vercel URL
- Homepage should load with your branding

### 2. Test registration
- Click "Join Now"
- Submit a test registration
- Check Supabase > Table Editor > players

### 3. Test emails
- Visit `/api/email` - should return `{"status": "ready"}`
- Test welcome email by approving a player in admin dashboard

### 4. Test admin dashboard
- Create an admin user in Supabase:
  ```sql
  UPDATE players SET is_admin = true WHERE email = 'your@email.com';
  ```
- Log in and access `/admin.html`

---

## Troubleshooting

### "SMTP_PASSWORD not configured"
- Check Vercel environment variables
- Make sure there are no spaces in the password

### "Supabase connection failed"
- Verify SUPABASE_URL and SUPABASE_ANON_KEY are correct
- Check Supabase project is not paused (free tier pauses after 7 days inactivity)

### Emails not sending
- Verify Gmail app password is correct
- Check that 2FA is enabled on the Gmail account
- Make sure the Gmail account hasn't hit daily limits (100/day for free)

### GitHub Actions not running
- Check that SITE_URL secret is set in repo settings
- Verify the workflow file exists at `.github/workflows/biweekly-emails.yml`

---

## Architecture Notes

### Vercel Function Limit

**Vercel Hobby plan: 12 serverless functions max**

Current count: 11 (after cleanup)

```
api/admin.py    api/auth.py     api/email.py    api/health.py
api/join.py     api/matches.py  api/migrate.py  api/pairings.py
api/players.py  api/profile.py  api/upload.py
```

Adding new `.py` files to `/api/` will count against this limit.

### Database Notes

- The `players` table has NO DELETE policy (by design)
- Use `is_active = false` instead of deleting players
- Admin operations use UPDATE, not DELETE

### Email Schedule

GitHub Actions runs these automatically:
- **27th**: Availability check
- **Last day of month**: Final reminder
- **1st**: Generate pairings + send match emails
- **15th**: Mid-month reminder

---

## Support

If you're stuck:
1. Check [RUNBOOK.md](./RUNBOOK.md) for common operations
2. Review error messages in Vercel Functions logs
3. Check Supabase logs for database errors
