# NET WORTH Tennis Ladder

East Side LA Women's Tennis - Monthly pairings, games-won ranking.

## Live Site

**[networthtennis.com](https://networthtennis.com)**

## How It Works

1. **Monthly Pairings** - On the 1st, players get paired by skill level
2. **Play 2 Sets** - Coordinate via email, play at any approved court
3. **Report Score** - Log results on dashboard, games won count toward ranking
4. **Climb the Ladder** - Rankings based on total games won, not match wins

## Tech Stack

- **Frontend**: Static HTML/CSS/JS on Vercel
- **Backend**: Vercel Python serverless functions (11/12 used on Hobby plan)
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth with magic links (no passwords)
- **Email**: Gmail SMTP via Ashley's account

## Project Structure

```
networth/
├── public/                 # Static site
│   ├── index.html         # Homepage + ladder
│   ├── login.html         # Magic link login
│   ├── join.html          # Request to join
│   ├── dashboard.html     # Player dashboard
│   ├── admin.html         # Admin dashboard
│   ├── rules.html         # How it works
│   ├── support.html       # FAQs
│   └── privacy.html       # Privacy policy
├── api/                    # Serverless functions (11/12 on Vercel Hobby)
│   ├── admin.py           # Admin operations (approve/reject/pause)
│   ├── auth.py            # Magic link auth
│   ├── email.py           # Gmail SMTP + 6 email templates
│   ├── join.py            # Player registration
│   ├── matches.py         # Match reporting
│   ├── pairings.py        # Monthly matching algorithm
│   ├── players.py         # Player list
│   ├── profile.py         # Player self-service
│   ├── health.py          # Health check
│   ├── migrate.py         # Admin migrations
│   └── upload.py          # Image uploads
├── .github/workflows/
│   └── biweekly-emails.yml # Automated email schedule
└── vercel.json            # Routing config
```

## Email System

Emails are sent via Gmail SMTP using Ashley's account (`ashleybrooke.kaufman@gmail.com`).

### 5 Automated Emails

| Email | When | Description |
|-------|------|-------------|
| Welcome | On signup | Thanks for joining, pay via Venmo |
| Match Assignment | 1st of month | You're paired with {player} |
| Availability Check | 27th of month | Update your status for next month |
| Final Reminder | Last day of month | Last call before pairings |
| Mid-Month Reminder | 15th of month | Don't forget to play your match |

### Email Schedule (GitHub Actions)

- **27th**: Availability check to all active players
- **Last day**: Final availability reminder
- **1st**: Generate pairings + send match emails
- **15th**: Mid-month reminder for pending matches

## Environment Variables (Vercel)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SMTP_PASSWORD` | Gmail app password (16 chars) |
| `SITE_URL` | `https://networthtennis.com` |
| `ADMIN_EMAIL` | Admin email for notifications |
| `CRON_SECRET` | Secret for GitHub Actions auth |

## Database (Supabase)

Key tables:
- `players` - Name, email, skill, total_games, rank, availability, is_active
- `matches` - Scores, who played, when
- `match_assignments` - Monthly pairings
- `match_feedback` - "Would play again" for silent blocking

Run `supabase-final-setup.sql` for fresh setup.

**Important:** The players table has no DELETE RLS policy. Use UPDATE/deactivate instead of delete.

## GitHub Actions

**biweekly-emails.yml** runs on schedule:
- Generates new pairings on the 1st
- Sends reminder emails on 15th, 27th, last day

Requires `SITE_URL` and `CRON_SECRET` in GitHub secrets.

## Local Development

```bash
python serve.py
# Open http://localhost:3000
```

## Documentation

- [CLONE_AND_CUSTOMIZE.md](./CLONE_AND_CUSTOMIZE.md) - Create your own tennis league
- [GMAIL_SETUP.md](./GMAIL_SETUP.md) - Set up Gmail SMTP
- [RUNBOOK.md](./RUNBOOK.md) - Operations manual
- [CONTENT_LOCATIONS.md](./CONTENT_LOCATIONS.md) - Where all editable content lives

## License

MIT
