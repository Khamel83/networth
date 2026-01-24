# CLAUDE.md - NET WORTH Tennis

## Project Overview

Women's tennis ladder for East Side LA. Monthly pairings, games-won ranking system.

**Live**: networthtennis.com
**Stack**: Vercel (static + Python functions) + Supabase + Resend

---

## Quick Reference

### To change colors/copy/branding:
- Website CSS: Variables at top of each `public/*.html` file
- Email templates: `api/email.py` (all 7 templates with inline styles)

### To add a player:
Players self-register via join page → immediately active → can log in right away

### To test emails:
- Emails only send if `RESEND_API_KEY` is set in Vercel
- Check status: `GET /api/email` returns "ready" or "not_configured"

### Key files:
- `api/pairings.py` - Matching algorithm (skill-based), sends match emails
- `api/email.py` - Resend API sender + 7 email templates
- `api/join.py` - Player registration (handles re-registration of inactive accounts)
- `api/admin.py` - Admin dashboard API (approve/reject/pause players, payment tracking)
- `api/auth.py` - Magic link authentication via Supabase Auth
- `api/profile.py` - Profile viewing and updates (includes auto-save for availability)
- `.github/workflows/biweekly-emails.yml` - Scheduled email automation

---

## Admin Dashboard (`/admin`)

### Features:
- **Stats row**: Pending, Players, Social, Active, Paused, Matches counts
- **Current Pairings**: Shows this month's matches with player names, emails, phones, status
- **Pending Approval**: New signups awaiting Venmo verification
- **All Members**: Searchable table with Paid checkbox, tier badge, status
- **Generate Pairings**: Manual trigger for monthly pairing generation

### Payment Tracking:
- `has_paid` boolean in database
- Checkbox in admin table auto-saves on click
- Admin-only (no effect on matching - tracking only)

### Admin Actions:
- `GET /api/admin?action=players` - List all players with has_paid
- `GET /api/admin?action=pairings` - Current month pairings with player details
- `POST /api/admin` with `action: update_payment` - Toggle payment status

---

## Architecture

```
User visits site
    → Vercel serves static HTML from /public
    → JS fetches from /api/* endpoints
    → API reads/writes to Supabase
    → Resend API sends emails (via api/email.py)

Authentication Flow
    → User enters email on /login
    → API sends magic link via Supabase Auth
    → User clicks link → redirected to /dashboard with token in URL hash
    → JS extracts token, verifies with API, stores in localStorage
    → Subsequent requests use Bearer token

Automated Emails (GitHub Actions)
    → 27th of month: Availability check (Players only, not Social Butterflies)
    → Last day of month: Final availability reminder (Players only)
    → 1st of month: Generate pairings + send match emails (Players only)
    → 15th of month: Mid-month reminder for pending matches
```

---

## Email System

**Provider:** Resend (replaced Gmail SMTP for better deliverability)
**Sender:** `Net Worth Tennis <noreply@networthtennis.com>`
**Reply-To:** `ashleybrooke.kaufman@gmail.com`
**Env var:** `RESEND_API_KEY`

### Why Resend over Gmail SMTP:
- Emails don't go to spam (verified domain)
- No rate limiting issues
- Better deliverability tracking
- Free tier: 3,000 emails/month (we use ~100)

### 7 Email Templates (in api/email.py)

| Email | Trigger | Subject | Notes |
|-------|---------|---------|-------|
| Welcome | Signup via `/join` | Welcome to Net Worth Tennis! | Shows $35 or $45 based on tier |
| Match Assignment | Pairing generation | {Player1}, meet {Player2} - You're matched for {Month}! | Players only |
| Availability Check | Cron (27th) | Quick check: are you playing next month? | Players only |
| Final Reminder | Cron (last day) | Last call: update your playing status | Players only |
| Mid-Month Reminder | Cron (15th) | Friendly reminder to play your {Month} match | |
| Sit-Out Confirmation | Player pauses | You're sitting out {Month} | |
| Rejoin Confirmation | Player rejoins | Welcome back! You're in for {Month} | |

---

## Database Schema

```
players
  - id, email, name, phone, skill_level
  - rank, total_games, matches_played
  - is_active (true for new signups, no approval needed)
  - unavailable_until (pause feature)
  - avail_weekday_early/day/late, avail_weekend_early/day/late
  - favorite_players, avatar_url
  - membership_tier (player | social_butterfly)
  - has_paid (boolean, for admin payment tracking)

matches
  - player1_id, player2_id
  - player1_games, player2_games (set scores)
  - period_label ("January 2025")

match_assignments
  - player1_id, player2_id, period_label
  - status (pending/accepted/completed)

match_feedback
  - would_play_again (for silent blocking)
```

---

## Authentication Patterns

### Magic Link Flow
1. User enters email → POST `/api/auth` with `action: 'magic_link'`
2. API checks player exists in DB, sends magic link via Supabase Auth
3. User clicks email link → redirected to `/dashboard#access_token=...`
4. JS extracts token from hash, calls `/api/auth` with `action: 'verify'`
5. API validates token, returns player data
6. JS stores in localStorage: `networth_token`, `networth_player`

### Critical Lessons Learned:
- **Email case sensitivity:** Always `.lower()` emails before storing/comparing
- **No reload after auth:** Don't use `window.location.reload()` after setting localStorage - set variables directly and update UI
- **Rate limiting:** Supabase limits OTP requests to 1 per 30 seconds - show friendly message
- **Cold start timeouts:** Vercel functions need `maxDuration: 30` in vercel.json for Supabase calls

---

## API Response Consistency (CRITICAL)

### The Pattern That Broke Things:
```python
# BAD - Different key names in different contexts
def _format_own_profile(self, p):
    return {"availability": {"weekday_early": ...}}  # No prefix

def _format_public_profile(self, p):
    return {"availability": {"avail_weekday_early": ...}}  # With prefix
```

### The Fix:
```python
# GOOD - Return both formats for JS compatibility
def _format_public_profile(self, p):
    return {
        "availability": {"weekday_early": ...},  # Nested
        "avail_weekday_early": ...,  # Also flat
    }
```

### Rule: When the same data is returned in multiple API endpoints, use IDENTICAL key names.

---

## UX Best Practices Implemented

### Auto-Save Pattern
For frequently-toggled settings (like availability checkboxes):
```javascript
// Attach change listeners that auto-save
checkbox.addEventListener('change', async () => {
    await saveToAPI();
    showSavedIndicator();  // Brief "Saved!" flash
});
```

### Why This Matters:
- Users don't have to remember to click Save
- Changes sync immediately to other viewers
- Visual feedback confirms the action worked

### Where Auto-Save is Used:
- `dashboard.html`: Availability checkboxes auto-save with "Saved!" indicator

---

## Environment Variables

### Vercel Dashboard:
| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `RESEND_API_KEY` | Resend API key (replaced SMTP_PASSWORD) |
| `SITE_URL` | `https://networthtennis.com` |
| `ADMIN_EMAIL` | Admin notification email |
| `CRON_SECRET` | Secret for GitHub Actions auth |

### GitHub Repo Secrets:
- `SITE_URL`, `CRON_SECRET`

---

## Vercel Configuration

### vercel.json
```json
{
  "functions": {
    "api/*.py": {
      "runtime": "@vercel/python@4.3.1",
      "maxDuration": 30  // Extended for Supabase cold starts
    }
  }
}
```

### Hobby plan limit: 12 serverless functions max

Current count: 11 (1 slot available)
```
api/admin.py      api/auth.py       api/email.py      api/health.py
api/join.py       api/matches.py    api/migrate.py    api/pairings.py
api/players.py    api/profile.py    api/upload.py
```

---

## Common Pitfalls & How to Avoid Them

### 1. File Name Confusion
- `profiles.html` = Players directory (grid of all players)
- `profile.html` = Individual player profile (single player view)
- **Always verify which file you're editing before making changes**

### 2. Magic Link Redirect Loops
**Symptom:** User clicks magic link, ends up back at login
**Cause:** `window.location.reload()` before localStorage write completes
**Fix:** Set variables directly, update UI without reload

### 3. "Failed to Fetch" on Login
**Symptom:** Network error when requesting magic link
**Causes:**
- Vercel cold start timeout (default 10s, Supabase needs more)
- User clicking multiple times triggers rate limit
**Fix:**
- Set `maxDuration: 30` in vercel.json
- Add 30s client-side timeout with AbortController
- Show friendly rate limit message

### 4. Emails Going to Spam
**Cause:** Gmail SMTP has poor deliverability
**Fix:** Switch to Resend with verified domain

### 5. Availability Not Syncing
**Cause:** API returning different key formats for public vs own profile
**Fix:** Return data in consistent format across all endpoints

### 6. Silent Failures
**Cause:** Catching exceptions without proper error messages
**Fix:** Always return meaningful error messages, log to console

---

## Abstractable Patterns for Future Projects

### 1. Magic Link Auth Template
```
/login → email input → POST /api/auth (magic_link) → email sent
Click link → /dashboard#access_token=... → JS extracts, verifies → localStorage
```

### 2. Auto-Save Form Fields
```javascript
element.addEventListener('change', async () => {
    await fetch('/api/update', { method: 'POST', body: data });
    showBriefIndicator('Saved!');
});
```

### 3. Consistent API Response Format
```python
def _send_success(self, data):
    return {"success": True, **data}

def _send_error(self, status, message):
    return {"success": False, "error": message}
```

### 4. Profile View Permissions
```python
# Own profile: full data
if viewing_self:
    return full_profile_data()

# Other's profile: filtered data (but include contact for members)
return filtered_profile_data()
```

### 5. Graceful Auth Handling
```javascript
if (response.status === 401) {
    localStorage.clear();
    window.location.href = '/login';
    return;
}
```

---

## Do Not

- Store passwords (we use magic links)
- Add complex features without asking (keep it simple for the players)
- Change the ranking formula (games won, period)
- Add new API endpoints without checking count first (12 max)
- Use DELETE operations on players table (RLS blocks them)
- Use `window.location.reload()` after setting localStorage
- Return different key formats for the same data in different endpoints
- Catch exceptions without logging or returning error messages
- Assume Gmail SMTP will deliver emails reliably

---

## Recent Changes Log

### January 2026
- Switched from Gmail SMTP to Resend for email delivery
- Fixed magic link redirect loop (removed reload, set variables directly)
- Added email and phone display on player profile pages
- Fixed availability key mismatch between API response formats
- Added auto-save for availability checkboxes with visual feedback
- Extended Vercel function timeout to 30s for cold starts
- Added rate limit handling for Supabase OTP requests
- Updated "Favorite Players" to "Favorite Pro Players" with better placeholder
- **Admin: Current Pairings view** - Shows who is matched with whom (names, emails, phones)
- **Admin: Payment tracking** - Added `has_paid` checkbox column in members table
- **Email filtering** - Reminder emails (27th, last day) now only go to Players, not Social Butterflies
- **Welcome email** - Now shows correct tier price ($35 Player / $45 Social Butterfly)
