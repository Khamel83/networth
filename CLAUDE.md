# CLAUDE.md - NET WORTH Tennis

## Project Overview

Women's tennis ladder for East Side LA. Monthly pairings, games-won ranking system.

**Live**: www.networthtennis.com
**Stack**: Vercel (static + Python functions) + Supabase + Resend

**Email safety invariant:** `EMAIL_DELIVERY_MODE` defaults to `disabled`. No test,
deployment check, workflow, or operator action may use live delivery without a
separate explicit approval.

---

## Quick Reference

### To change colors/copy/branding:
- Website CSS: Variables at top of each `public/*.html` file
- Email templates: `api/email.py` (all 7 templates with inline styles)

### To add a player:
Players self-register via join page → immediately active → can log in right away

### To inspect email delivery without sending:
- `GET /api/email` returns the current `delivery_mode`; disabled and dry-run never contact Resend.
- `GET /api/system` is a health check. The provider connectivity probe is protected by `CRON_SECRET` and is read-only.
- Never use a workflow replay or a test email as deployment verification.
- Unauthenticated signup/reset mail has a second opt-in, `PUBLIC_TRANSACTIONAL_EMAILS=enabled`, in addition to `EMAIL_DELIVERY_MODE=live`.

### Key files:
- `api/pairings.py` - Matching algorithm (exact fresh matching + RMS bands), sends match emails
- `api/email.py` - Resend API sender + 8 email templates (including admin alerts)
- `api/join.py` - Player registration (handles re-registration of inactive accounts)
- `api/admin.py` - Admin dashboard API (approve/reject/pause players, payment tracking)
- `api/auth.py` - Password-based authentication + reset token flow
- `api/profile.py` - Profile viewing and updates (includes auto-save for availability)
- `api/supabase_http.py` - Custom Supabase REST client (lightweight alternative to SDK)
- `api/system.py` - Health check, bug reports, and email connectivity check
- `.github/workflows/biweekly-emails.yml` - Scheduled email automation
- `.github/workflows/daily-health-check.yml` - Daily read-only health check
- `.github/workflows/tests.yml` - CI/CD test runner
- `supabase-final-setup.sql` - Database schema, triggers, and functions

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
    → Resend API sends emails only when EMAIL_DELIVERY_MODE=live (via api/email.py)

Authentication Flow
    → User logs in with email + password on /login
    → API verifies password hash from players table
    → Frontend stores local session token + player object in localStorage
    → Subsequent requests pass `Authorization: Bearer {session token}`

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
- Better deliverability tracking
- Free tier: 3,000 emails/month (we use ~100)

### Rate Limits & Reliability:
- Scheduled bulk sends use Resend's batch endpoint (up to 100 individualized emails per request), with one stable provider idempotency key per batch
- `email_delivery_log` is the canonical message-level ledger with `pending`, `accepted`, `failed`, and `unknown` states
- Every message is claimed before provider submission; provider acceptance and audit persistence are reported separately
- A timeout or incomplete provider response marks the whole batch `unknown`; reconciliation retries the exact same batch key or returns `manual_review_required`
- `send_email()` auto-retries once on `RateLimitError` (429) with 1s sleep
- All scheduled responses include `outcome`, `delivery_summary`, and `reconciliation_required`
- `email_log` is retained only as a legacy migration source until its row counts are verified

### 8 Email Templates (in api/email.py)

| Email | Trigger | Subject | Notes |
|-------|---------|---------|-------|
| Welcome | Signup via `/join` | Welcome to Net Worth Tennis! | Shows $35 or $45 based on tier |
| Match Assignment | Pairing generation | {Player1}, meet {Player2} - You're matched for {Month}! | Players only |
| Availability Check | Cron (27th) | Quick check: are you playing next month? | All Players (active + paused), not Social Butterflies |
| Final Reminder | Cron (last day) | Last call: update your playing status | All Players (active + paused), not Social Butterflies |
| Mid-Month Reminder | Cron (15th) | Friendly reminder to play your {Month} match | |
| Sit-Out Confirmation | Player pauses | You're sitting out {Month} | |
| Rejoin Confirmation | Player rejoins | Welcome back! You're in for {Month} | |
| Admin Alert | Health check failure / Bug report | Net Worth Alert: {subject} | Goes to admin emails |

---

## Database Schema

```
players
  - id, email, name, phone, skill_level
  - rank, total_games, matches_played
  - is_active (true for new signups, no approval needed)
  - is_admin (boolean - league admins like Ashley, Natalie, Khamel)
  - unavailable_until (pause feature)
  - avail_weekday_early/day/late, avail_weekend_early/day/late
  - favorite_players, avatar_url
  - membership_tier (player | social_butterfly | admin)
  - has_paid (boolean, for admin payment tracking)

matches
  - player1_id, player2_id
  - player1_games, player2_games (set scores)
  - period_label ("January 2025")

match_assignments
  - player1_id, player2_id, period_label
  - status (pending/accepted/completed)
  - reminder_sent_at, reminder_email_id (idempotency: skip pairs already reminded)
  - match_email_id (Resend ID of the original match assignment email)

match_feedback
  - would_play_again (for silent blocking)

email_delivery_log (canonical)
  - action, period_label, message_key, recipient_emails[], template
  - delivery_status (pending/accepted/failed/unknown)
  - idempotency_key (shared by one provider batch), provider_id, accepted_at

issue_reports
  - reporter_email, reporter_name, page_path, message, status, timestamps
  - Public issue reports are queued here; they never send an implicit admin email
```

---

## Authentication Patterns

### Password Auth Flow
Players log in with email + password. Password reset via emailed link (`/reset-password?token=...`).

### Critical Lessons Learned:
- **Email case sensitivity:** Always `.lower()` emails before storing/comparing
- **No reload after auth:** Don't use `window.location.reload()` after setting localStorage - set variables directly and update UI
- **Function timeouts:** Vercel Hobby functions max out at 60 seconds; scheduled bulk email work must stay bounded below that limit

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
| `SITE_URL` | `https://www.networthtennis.com` |
| `ADMIN_EMAIL` | Admin notification email |
| `CRON_SECRET` | Secret for GitHub Actions auth |

### GitHub Repo Secrets:
- `SITE_URL`, `CRON_SECRET`

### Critical Reliability Notes (March 2026)
- Protected automation actions require `CRON_SECRET` and fail closed if it is missing.
- Canonical domain is `https://www.networthtennis.com`; non-www redirects to www.
- Reliability migration `migrations/02_reliability_automation.sql` must be applied in Supabase.
- New reconcile endpoint: `POST /api/system` with `action: reconcile_month`.

---

## Vercel Configuration

### vercel.json
```json
{
  "functions": {
    "api/*.py": {
      "runtime": "@vercel/python@6.51.1",
      "maxDuration": 60
    }
  }
}
```

### Hobby plan limit: 12 serverless functions max

Current count: 10 (2 slots available for future features)
```
api/admin.py      api/auth.py       api/email.py
api/join.py       api/matches.py    api/pairings.py
api/players.py    api/profile.py    api/system.py
api/upload.py
```
Utility modules in `api/` (no handler, don't count toward limit):
- `api/supabase_http.py` - Custom Supabase REST client
- `api/reliability.py` - Automation preflight helpers
- `api/sentry_init.py` - Sentry initialization
- `api/__init__.py` - Package init

CI check uses `grep -rl "class handler" api/*.py` — counts only files with a real Vercel handler. New utility modules added to `api/` will NOT trip the check unless they define `class handler`.

Consolidated: `health.py` + `report_issue.py` → `system.py`; deleted `migrate-passwords.py`

---

## Common Pitfalls & How to Avoid Them

### 1. File Name Confusion
- `profiles.html` = Players directory (grid of all players)
- `profile.html` = Individual player profile (single player view)
- **Always verify which file you're editing before making changes**

### 2. Auth Redirect Loops
**Symptom:** User logs in and gets bounced back to login
**Cause:** `window.location.reload()` before localStorage write completes
**Fix:** Set variables directly, update UI without reload

### 3. "Failed to Fetch" on Login
**Symptom:** Network error while posting login/reset request
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

### 7. Doubled Scores from Duplicate Match Inserts
**Symptom:** Player total_games and matches_played are doubled (e.g., 11 becomes 22)
**Cause:** The `update_player_games()` trigger fires on every INSERT to matches table. If a match is submitted twice (double-click, network retry), the trigger runs twice and doubles the scores.
**Fix:** Added unique index to prevent duplicate matches:
```sql
CREATE UNIQUE INDEX idx_unique_match_per_period
ON matches (LEAST(player1_id, player2_id), GREATEST(player1_id, player2_id), period_label);
```
This ensures each player pair can only have ONE match per period. Duplicate submissions return HTTP 409.

### 8. NULL Ranks Appearing at Top of Rankings
**Symptom:** Players with NULL rank appear at position #1 instead of bottom
**Cause:** JavaScript's `null < 99` returns `true` (null coerces to 0), so NULL-ranked players pass filters and sort to top
**Fix:** Don't rely on database rank field. Compute rank from array position:
```javascript
// DON'T: .sort((a, b) => a.rank - b.rank)
// DO: Use index from API-ordered results
players.map((player, index) => {
    const rank = index + 1;  // Compute from position
});
```
The API returns players ordered by `total_games DESC NULLS LAST`, so position IS the rank.

### 9. Paused Players Never Get Reactivation Reminders
**Symptom:** Players who pause never receive availability emails, so they have no way to know they need to reactivate
**Cause:** Email queries filtered by `is_active = true`, excluding paused players
**Fix:** Include all Players (active + paused) in availability emails, but filter by `membership_tier = 'player'` to exclude admins and Social Butterflies
**Note:** Use `membership_tier = 'admin'` for non-playing admins (like Khamel) so they're excluded from automated emails

### 10. Match History Not Showing on Profiles
**Symptom:** Player profiles show "No matches yet" even though player has games/matches recorded
**Cause:** The custom `SelectBuilder` class in `api/supabase_http.py` was missing the `.in_()` method, causing queries to fail silently
**Fix:** Added `.in_()` method to `SelectBuilder` class:
```python
def in_(self, column: str, values: List[Any]) -> 'SelectBuilder':
    """Filter by list of values (IN operator)"""
    self.filters.append((column, 'in', values))
    return self
```
**Lesson:** Always verify all methods used in queries exist in custom ORM wrappers before deploying.

### 11. Admins Excluded from Rankings
**Symptom:** Players with `is_admin = true` show NULL rank even though they have games won
**Cause:** The `recalculate_rankings()` function filtered by `is_admin = false`, incorrectly assuming admins aren't players
**Fix:** Removed the `is_admin = false` filter - admins who are also players should be ranked:
```sql
-- BEFORE (wrong)
WHERE is_active = true AND is_admin = false

-- AFTER (correct)
WHERE is_active = true
```
**Note:** `is_admin` controls dashboard access, NOT whether someone is a ranked player.

### 13. Anti-Staleness Check Silently Disabled by Wrong Column Name
**Symptom:** Players get paired with the same person month after month
**Cause:** `match_assignments` uses `assigned_at` (not `created_at`). Querying `.order('created_at')` returns a Supabase error dict, which `Result` silently converts to `[]`. Empty list = empty staleness set = zero penalty on any repeated pair. The staleness system appeared to work but never did.
**Fix:** Use `assigned_at` in the recent_matches query in `api/pairings.py`
**Column names to remember:**
- `match_assignments`: `assigned_at`, `responded_at` (NO `created_at`)
- `matches`: `created_at` (standard Supabase default)
**Rule:** When adding `.order()` on any table, verify the column name in Supabase first.

### 15. Greedy Matching Can Drop Players in Cross-Band Pass
**Symptom:** With 2+ players who've all played each other, some players silently disappear from skipped list
**Cause:** Cross-band pass pops player1 from `unpaired`, tries all candidates, fails, adds player1 to `still_unpaired`. But remaining candidates (still in `unpaired` when loop exits because `len < 2`) get lost when `unpaired = still_unpaired`.
**Fix:** `still_unpaired.extend(unpaired)` before `unpaired = still_unpaired` — collect stragglers.
**Rule:** Any greedy while-loop that pops from a list must preserve all remaining items at the end.

### 16. Greedy Fresh Pairing Can Still Produce Avoidable Repeats
**Symptom:** Repeat pairs can appear even when a full fresh matching exists
**Cause:** Greedy local decisions can create dead ends for remaining players
**Fix:** Exact fresh matching solver (<=20 players) chooses the global best non-repeat matching before any repeat fallback
**Rule:** For small leagues, use exact matching first; use greedy only as fallback for larger pools.

### 17. Silent Result Failures from Custom ORM
**Symptom:** Queries return empty results with no error — algorithm runs on empty data, silent wrong behavior
**Cause:** `supabase_http.py` Result class had bare `except:` that set `self.data = []` without setting `self.error`. Callers saw empty data and proceeded normally.
**Fix:** Always check HTTP status first. Set `self.error` on any exception. Guard every `.execute()` call with `if result.error: return self._send_error(...)`.
**Rule:** Custom ORM wrappers must propagate errors explicitly. Never let a failed query look like an empty result.

### 18. CI Function Count Broken by New Utility Modules in api/
**Symptom:** Daily health check fails with "Exceeds Vercel limit" even though no new endpoints were added
**Cause:** Old check used a manual exclusion list (`grep -v supabase_http`). Adding any new utility module to `api/` without updating the list trips the count.
**Fix:** CI now uses `grep -rl "class handler" api/*.py` — counts only files that define a real Vercel handler. No exclusion list to maintain.
**Rule:** Never revert to an exclusion-list approach for this check.

### 14. Shell Date Zero-Padding Breaks Month-1st Comparisons
**Symptom:** Automated workflows silently no-op on the 1st of the month
**Cause:** `date +%d` returns `"01"` (zero-padded). Comparing `"01" = "1"` is false in bash.
**Fix:** Always use `date +%-d` (GNU coreutils, Linux/GitHub Actions) to strip the zero.
**Rule:** Any `date` output used in a bash comparison must use `%-d`, `%-m`, `%-H` etc.

### 19. Resend 429 Takes Down All Remaining Emails
**Symptom:** Mid-month reminder run sends 5 emails then stops; GitHub Actions reports `sent=0` (hides the 5 that succeeded)
**Cause:** (a) No retry on `RateLimitError`; (b) `break` in pairing email loop stops all remaining sends on first failure; (c) error response didn't include `sent` count
**Fix:**
- `send_email()` catches `resend.exceptions.RateLimitError` and retries once after 1s
- Removed `break` from pairings.py email loop — all pairs attempted even if one fails
- All bulk send `_send_error` calls include `extra={"sent": N, "failed": M}` so counts always appear in response
- `email_log` table records every successful send for post-incident auditing
**Rule:** Never `break` out of a bulk email loop on failure. Always collect errors and continue.

### 20. CI Auth Check Always Failing (Silent)
**Symptom:** `Automated Tests` workflow shows failure on "Check admin alert calls are authenticated" on every single commit
**Cause:** `grep -q "Authorization: Bearer ${{ secrets.CRON_SECRET }}" "$wf"` — GitHub Actions substitutes the actual secret value at runtime, so grep looks for the real secret string, not the template expression. They never match.
**Fix:** `grep -q "Authorization: Bearer" "$wf"` — just check the header exists, not its value
**Rule:** Never grep for `${{ secrets.X }}` in CI — the runtime value is substituted, not the template literal.

### 12. "#null" Displayed Instead of Rank
**Symptom:** Profile page shows "#null" instead of a rank number
**Cause:** JavaScript `null < 99` evaluates to `true`, so the condition passes and displays `#` + `null`
**Fix:** Add null check before comparison:
```javascript
// BEFORE
player.rank < 99 ? '#' + player.rank : '-'

// AFTER
player.rank && player.rank < 99 ? '#' + player.rank : '-'
```

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

- Store plain-text passwords
- Add complex features without asking (keep it simple for the players)
- Change the ranking formula (games won, period)
- Add new API endpoints without checking count first (12 max)
- Use DELETE operations on players table (RLS blocks them)
- Use `window.location.reload()` after setting localStorage
- Return different key formats for the same data in different endpoints
- Catch exceptions without logging or returning error messages
- Assume external email delivery can never fail

---

## Recent Changes Log

### January 2026
- Password reset flow: Players can request reset via email link (/reset-password?token=...)
- Fixed auth redirect loop (removed reload, set variables directly)
- Added email and phone display on player profile pages
- Fixed availability key mismatch between API response formats
- Added auto-save for availability checkboxes with visual feedback
- Extended Vercel function timeout to 60s for cold starts (raised again March 2026 — 30s wasn't enough for 28 bulk emails)
- Added rate limit handling for Supabase OTP requests
- Updated "Favorite Players" to "Favorite Pro Players" with better placeholder
- **Admin: Current Pairings view** - Shows who is matched with whom (names, emails, phones)
- **Admin: Payment tracking** - Added `has_paid` checkbox column in members table
- **Email filtering** - Reminder emails (27th, last day) now only go to Players, not Social Butterflies
- **Welcome email** - Now shows correct tier price ($35 Player / $45 Social Butterfly)
- **Fixed NULL ranks at top of rankings** - Removed JS sort by rank, compute rank from array position instead
- **Fixed doubled scores** - Added unique index `idx_unique_match_per_period` to prevent duplicate match inserts
- **Admin: update_games action** - New API action to manually correct player total_games values
- **Fixed paused player email exclusion** - Availability emails now go to ALL Players (active + paused) so they know to reactivate
- **Admin tier exclusion** - Changed Khamel from 'player' to 'admin' tier; emails now filter by membership_tier to exclude non-playing admins

### March 2026
- **Fixed CI function count check** - Replaced manual exclusion list with `grep -rl "class handler"` so new utility modules in `api/` never trip the Vercel limit check again
- **Fixed silent automation failures** - `date +%d` returns zero-padded "01"; changed to `date +%-d` everywhere so 1st-of-month comparisons actually work
- **Fixed anti-staleness never working** - `match_assignments` uses `assigned_at` not `created_at`; silent Supabase error made staleness check always return empty, so repeated pairings were never penalized
- **Added CRON_SECRET auth** - All GitHub Actions curl POSTs now send `Authorization: Bearer $CRON_SECRET`; pairings.py and email.py validate it server-side
- **Fixed CI/CD tests** - Added `api/__init__.py`, `tests/conftest.py`, fixed wrong mock patches; 28/28 tests now pass
- **March pairings generated** - 14 pairings, 14 emails sent (3rd, manually triggered after fixing automation)
- **Reliability refactor (exact fresh matching)** - Complete overhaul after repeat-pair incidents:
  - Algorithm: penalty-based anti-staleness → hard-block fresh pass → exact fresh matching solver (<=20 players) before repeat fallback
  - Full validation gate before any email: duplicate player check, avoidable repeat check, duplicate-run protection (409), DB insert + count verify
  - `supabase_http.py`: Result class now checks HTTP status first; fixes bare except swallowing errors silently
  - All API files: error guards after every `.execute()` call; HTTP 500 on errors (not 200 + fake data)
  - GitHub Actions: all curl calls now capture `-w "%{http_code}"` and check HTTP status before jq
  - `tests/test_pairings.py`: algorithm coverage + stress checks (suite currently 63 passing)
  - `migrations/01_security_fixes.sql`: run in Supabase Dashboard to fix 2 view ERRORs + 5 RLS warnings
  - Bug found by tests: cross-band pass was silently dropping players when loop exited with <2 remaining (`still_unpaired.extend(unpaired)` fix)
- **Email reliability overhaul** - After 429 rate-limit incident dropped 9 of 14 mid-month reminders:
  - `send_email()` retries once on `RateLimitError` (429) with 1s sleep before giving up
  - Removed `break` from pairings.py email loop — all pairings attempted even if one fails
  - All bulk send error responses include `{"sent": N, "failed": M, "errors": [...]}` so counts are always visible
  - `email_log` table: every successful bulk send writes a row (action, to_emails, period_label, match_id, resend_email_id)
  - `match_assignments.match_email_id`: stores Resend ID of the original match email for traceability
  - `match_assignments.reminder_sent_at/reminder_email_id`: idempotency for mid-month reminders (re-runs skip already-sent pairs)
  - `POST /api/system` with `action: check_email_connectivity` — formerly validated the Resend API key daily; it is now cron-protected and no-ops unless live delivery is explicitly enabled
  - Fixed CI auth check: grep for secret template literal was always failing (every commit since March 4); simplified to `grep -q "Authorization: Bearer"`
  - 69/69 tests passing
- **Security hardening (March 27)** — Full RLS + session token overhaul:
  - Real session tokens in `session_tokens` DB table; `verify_session()` in `api/auth.py`
  - All `if '@' in token` auth bypass patterns removed (6 endpoints)
  - CRON_SECRET endpoints now reject everything except the exact secret
  - `SUPABASE_SERVICE_ROLE_KEY` used server-side; anon key has deny-all RLS policies
  - Password fields (`password_hash`, reset tokens) never returned by any endpoint
  - Frontend: `networth_token` localStorage now stores real session token (not email)
  - `migrations/03_session_tokens_and_rls.sql` applied in Supabase
  - Error responses: `str(e)` replaced with generic message + `print()` for server logs
- **504 false alarm fix (March 27)** — 28 players × ~1s/email = >30s. Function was timing out
  AFTER all emails delivered. `maxDuration` raised to 60s (Vercel Hobby max).
- **Auto-verify after 504 (March 27)** — Workflow now checks `email_log` before alerting:
  if emails are in the log, exit 0 (no alert). Only fires alert if emails truly didn't go out.
  New `check_recent_send` action in `api/email.py` queries email_log by action + today's date.

### 21. Vercel 504 False Alarm on Bulk Email
**Symptom:** GitHub Actions shows failure, admin gets alert, but all emails were delivered
**Cause:** Bulk send to 28 players takes ~31s (0.6s sleep × emails + network). Old `maxDuration: 30` killed the function AFTER all emails sent but before it could return 200. GitHub Actions saw 504 → fired alert.
**First fix:** `maxDuration: 60` in vercel.json plus a workflow fallback that queries `email_log` via `check_recent_send`.
**Follow-up fix:** The fallback had a `timezone` scope collision and called an unimplemented `gte` query method; scheduled bulk sends also remained serial. The current implementation uses Resend batch sends, bulk audit writes, stable idempotency keys, and a working reconciliation query.
**Rule:** Keep scheduled bulk work bounded below the platform limit and reconcile provider-side acceptance before raising a failure alert.

### 22. Python dict.get() Doesn't Use Default When Key Exists But Is None
**Symptom:** Pairings generation crashes with `TypeError: '<' not supported between instances of 'NoneType' and 'int'`
**Cause:** `p.get('rank', 999)` returns `None` (not 999) when the key exists but the value is `None`. A new player had `rank = NULL` in the database.
**Fix:** Use `p.get('rank') or 999` instead of `p.get('rank', 999)`. The `or` pattern handles both missing key AND null value.
**Rule:** Never use `.get(key, default)` for database fields that can be NULL — always use `.get(key) or default`.

### 23. Pairings Preflight Auth Test Was Accidentally Running Pairings
**Symptom:** GitHub Actions preflight auth check for pairings returns 500, misreported as "CRON_SECRET not configured"
**Cause:** The pairings preflight sent `{}` to `/api/pairings` which actually tried to generate pairings (no `test_auth_check` action handler). Other jobs used `/api/email test_auth_check` which is safe. Any server error was misinterpreted as missing CRON_SECRET.
**Fix:** All preflight auth tests now use `/api/email test_auth_check` — same CRON_SECRET, no side effects.
**Rule:** Preflight tests must be side-effect-free. Never send data that could trigger real work.

### 24. Test Email Filter Caught Test Helper's Default Email Domain
**Symptom:** 12 test failures after adding test email rejection to `is_player_available()`
**Cause:** Test helper creates emails like `alice@test.com`, which matches the `'@test.' in _email` filter. All test players became "unavailable."
**Fix:** Changed test helper default domain from `@test.com` to `@example.net`.
**Rule:** When adding validation that filters by pattern, check that test fixtures don't accidentally match.

### April 2026
- **Fixed pairings crash on NULL rank** — `p.get('rank', 999)` returns None when key exists but is null; changed to `p.get('rank') or 999` (lines 382, 396)
- **Fixed preflight auth test** — pairings preflight was hitting /api/pairings with {} (actually ran pairings); now uses /api/email test_auth_check like all other jobs
- **April pairings generated** — 13 pairings, 13 emails sent, 0 repeats confirmed
- **CRON_SECRET synced** — Vercel + GitHub + vault all matching

### February 2026
- **Report Issue feature** - Users can report bugs from dashboard via `/api/report_issue` (sends admin alert email)
- **Daily health check** - GitHub Actions workflow runs daily health check with email alerts on failure
- **CI/CD tests** - Added `tests.yml` workflow for automated testing
- **Admin alert emails** - New email template for system alerts (8 templates total)
- **Documentation audit** - Updated CLAUDE.md to match actual codebase (12 functions at limit)
- **Extra match month selector** - "Log Extra Match" now lets players select which month the match was played (current + past 6 months)
- **Match history opponent names** - Fixed "VS. Unknown" by joining matches with players table in API
- **Profile match history** - Player profiles now show recent match history with opponents and scores
- **Fixed match history not showing** - Added `.in_()` method to `SelectBuilder` in `supabase_http.py` (was failing silently)
- **Fixed admin ranking exclusion** - Updated `recalculate_rankings()` to include admins in rankings (admins can be players too)
- **Fixed "#null" rank display** - Added null check in profile.html to show "-" instead of "#null"

<!--
  ONE-SHOT Heartbeat Metadata
  oneshot:last-check: 2026-02-01
  oneshot:machine: instance-first
-->

<!--
  ONE-SHOT Heartbeat Metadata
  oneshot:last-check: 2026-03-03
  oneshot:machine: instance-first
-->
