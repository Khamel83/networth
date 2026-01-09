# Content Locations Guide

This document shows where all editable text and branding lives in the codebase. Use this when you want to request changes from a developer, or if you're making changes yourself.

---

## Quick Reference

| I want to change... | Location |
|---------------------|----------|
| League name | `lib/config.py` line 17 |
| Homepage hero text | `content/landing.json` |
| Membership prices | `content/landing.json` + `public/index.html` + `public/join.html` |
| Venmo handle | `content/landing.json` + `public/index.html` + `public/join.html` + `api/email.py` |
| Email templates | `api/email.py` (Python functions) |
| Contact email | `content/landing.json` line 65 |
| Court list | `lib/config.py` lines 97-106 |
| Colors/branding | `lib/config.py` lines 22-31 |
| Game rules | `public/rules.html` |
| FAQ/Support | `public/support.html` |

---

## Detailed Content Map

### 1. Branding (`lib/config.py`)

```python
# Line 17-19
LEAGUE_NAME = "NET WORTH"
LEAGUE_TAGLINE = "East Side LA Women's Tennis"
SITE_URL = "https://networthtennis.com"

# Line 22-31: Colors
COLORS = {
    'background': '#0a0a0a',
    'gold': '#D4AF37',      # Primary accent
    'lime': '#CCFF00',      # Secondary accent
    # ...
}
```

### 2. Homepage Content (`content/landing.json`)

```json
{
  "hero": {
    "subtitle": "A WOMEN'S TENNIS LEAGUE ON LA'S EAST SIDE",
    "title": "Net Worth",
    "tagline": "Tennis. Events. Community."
  },
  "membership": {
    "description": "...Venmo @NCOFFEN...",
    "tier1": {
      "name": "THE PLAYERS",
      "price": "$35/year"
    },
    "tier2": {
      "name": "THE SOCIAL BUTTERFLIES",
      "price": "$45/year"
    }
  },
  "footer": {
    "contactEmail": "ashleybrooke.kaufman@gmail.com,nmcoffen@gmail.com"
  }
}
```

### 3. Email Templates (`content/emails.json`)

```json
{
  "welcome": {
    "subject": "Welcome to Net Worth Tennis!",
    "greeting": "Hi {{playerName}},"
    // ... body text
  },
  "matching": {
    "subject": "You're matched for {{month}}",
    // ...
  }
}
```

**Note:** The actual HTML templates are in `api/email.py`. The JSON file exists but may not be fully wired up - the Python templates take precedence.

### 4. Email HTML Templates (`api/email.py`)

The actual email content is in Python functions:

| Function | Lines | Purpose |
|----------|-------|---------|
| `get_welcome_email_html()` | 113-150 | Welcome email after signup |
| `get_match_assignment_email_html()` | 152-206 | Monthly pairing notification |
| `get_availability_check_email_html()` | 208-255 | End-of-month availability check |
| `get_final_reminder_email_html()` | 257-299 | Last day reminder |
| `get_midmonth_reminder_email_html()` | 301-340 | Mid-month match reminder |
| `get_sitout_confirmation_email_html()` | 342-377 | Pause confirmation |
| `get_rejoin_confirmation_email_html()` | 379-416 | Rejoin confirmation |

**To change email text:** Edit the HTML strings inside these functions.

### 5. Membership Prices

Prices appear in THREE places:

1. **`content/landing.json`** - lines 13, 24
2. **`public/index.html`** - search for `$35` and `$45`
3. **`public/join.html`** - search for `$35` and `$45`
4. **`api/email.py`** - welcome email mentions price

### 6. Venmo Handle

The Venmo handle appears in FOUR places:

1. **`content/landing.json`** - line 9 (`@NCOFFEN`)
2. **`public/index.html`** - search for `@NCOFFEN`
3. **`public/join.html`** - search for `@NCOFFEN`
4. **`api/email.py`** - welcome email

### 7. Courts List (`lib/config.py`)

```python
# Lines 97-106
APPROVED_COURTS = [
    "Vermont Canyon",
    "Griffith Park - Riverside",
    "Griffith Park - Merry-Go-Round",
    "Echo Park",
    "Hermon Park",
    "Eagle Rock",
    "Cheviot Hills",
    "Poinsettia Park",
]
```

### 8. Skill Levels (`lib/config.py`)

```python
# Lines 115-122
SKILL_LEVELS = [
    ('4.5', '4.5 Advanced+'),
    ('4.0', '4.0 Advanced'),
    ('3.5+', '3.5+ Intermediate+'),
    ('3.5', '3.5 Intermediate'),
    ('3.0', '3.0 Beginner+'),
    ('2.5', '2.5 Beginner'),
]
```

### 9. Static Pages

| Page | File |
|------|------|
| Homepage | `public/index.html` |
| Join form | `public/join.html` |
| Player dashboard | `public/dashboard.html` |
| Admin dashboard | `public/admin.html` |
| Game rules | `public/rules.html` |
| FAQ/Support | `public/support.html` |
| Privacy policy | `public/privacy.html` |

### 10. Admin Emails (Pairing Logic)

In `api/pairings.py`:

```python
# Line 181: Admin "flex" accounts (removed from pairing if odd number)
return email in ['nmcoffen@gmail.com', 'ashleybrooke.kaufman@gmail.com']

# Line 237: Specific admin handling
ashley = next((p for p in available_players
               if p.get('email', '').lower() == 'ashleybrooke.kaufman@gmail.com'), None)
```

---

## How to Request Changes

### For simple text changes:
1. Tell the developer WHAT text you want changed
2. Tell them WHERE it currently appears (use this guide)
3. Tell them what the NEW text should be

**Example request:**
> "Can you change the membership price from $35 to $40?
> It's in content/landing.json and the HTML files."

### For email template changes:
1. Provide the new subject line and body text
2. Specify which email (welcome, match assignment, reminder, etc.)
3. Include any personalization variables you want (like `{{playerName}}`)

**Example request:**
> "Can you update the welcome email subject to 'You're in! Welcome to Net Worth Tennis'
> and add a line about joining the WhatsApp group?"

---

## Future Improvement: Admin Settings UI

A planned feature would let admins edit this content directly from the admin dashboard without needing a developer. This would include:

- Email template editor
- Membership pricing
- Contact info / Venmo handle
- Court list management

Until then, content changes require editing code files.
