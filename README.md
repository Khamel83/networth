# NET WORTH Tennis Ladder

East Side LA Women's Tennis - Monthly pairings, games-won ranking.

## Live Site

**[networthtennis.com](https://networthtennis.com)**

## How It Works

1. **Monthly Pairings** - On the 1st, players get paired by skill level (RMS algorithm)
2. **Play 2 Sets** - Coordinate via email, play at any approved court
3. **Report Score** - Log results on dashboard, games won count toward ranking
4. **Climb the Ladder** - Rankings based on total games won, not match wins

## Tech Stack

- **Frontend**: Static HTML/CSS/JS on Vercel
- **Backend**: Vercel Python serverless functions (12/12 on Hobby plan - at limit)
- **Database**: Supabase (PostgreSQL)
- **Auth**: Magic links + password login
- **Email**: Resend API (noreply@networthtennis.com)

## Project Structure

```
networth/
├── public/                 # Static site
│   ├── index.html         # Homepage + ladder
│   ├── login.html         # Magic link / password login
│   ├── join.html          # Player registration
│   ├── dashboard.html     # Player dashboard
│   ├── admin.html         # Admin dashboard
│   ├── profile.html       # Individual player profile
│   ├── profiles.html      # Players directory
│   ├── rules.html         # How it works
│   ├── support.html       # FAQs
│   └── privacy.html       # Privacy policy
├── api/                    # Serverless functions (12/12 on Vercel Hobby - at limit)
│   ├── admin.py           # Admin operations (approve/reject/pause/pairings)
│   ├── auth.py            # Magic link + password auth
│   ├── email.py           # Resend API + 8 email templates (including admin alerts)
│   ├── join.py            # Player registration
│   ├── matches.py         # Match reporting
│   ├── pairings.py        # Monthly matching algorithm (RMS-based)
│   ├── players.py         # Player list
│   ├── profile.py         # Player self-service
│   ├── health.py          # Health check
│   ├── migrate-passwords.py # Password migration utility
│   ├── report_issue.py    # User bug reports (sends email to admins)
│   ├── supabase_http.py   # Supabase REST API client (utility, not a function)
│   └── upload.py          # Image uploads
├── .github/workflows/
│   ├── biweekly-emails.yml   # Automated email schedule
│   ├── daily-health-check.yml # Daily health check + alerts
│   ├── tests.yml             # CI/CD tests
│   ├── keep-alive.yml        # Prevent function cold starts
│   └── backup.yml            # Database backup automation
└── vercel.json            # Routing config
```

## Email System

Emails are sent via **Resend API** from `noreply@networthtennis.com`.

### 8 Email Templates

| Email | When | Description |
|-------|------|-------------|
| Welcome | On signup | Thanks for joining |
| Match Assignment | 1st of month | You're paired with {player} |
| Availability Check | 27th of month | Update your status for next month |
| Final Reminder | Last day of month | Last call before pairings |
| Mid-Month Reminder | 15th of month | Don't forget to play your match |
| Sit-Out Confirmation | Player pauses | You're sitting out this month |
| Rejoin Confirmation | Player unpauses | Welcome back! |
| Admin Alert | Health check fail / Bug report | System alerts to admins |

### Email Schedule (GitHub Actions)

Runs automatically:
- **27th**: Availability check to all active players
- **Last day**: Final availability reminder
- **1st**: Generate pairings + send match emails
- **15th**: Mid-month reminder for pending matches

## Environment Variables

### Vercel Dashboard

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `RESEND_API_KEY` | Resend API key |
| `SITE_URL` | `https://networthtennis.com` |
| `ADMIN_EMAIL` | Admin email for notifications |

### GitHub Secrets

| Variable | Description |
|----------|-------------|
| `SITE_URL` | `https://networthtennis.com` |

## Database (Supabase)

Key tables:
- `players` - Name, email, skill, total_games, rank, availability, is_active
- `matches` - Scores, who played, when
- `match_assignments` - Monthly pairings
- `match_feedback` - "Would play again" for silent blocking

## Matching Algorithm (RMS)

Players are matched based on Rolling Match Score (RMS):
- RMS = Average total games won in last 3 matches
- Performance bands: developing, competitive, strong, dominant
- New players paired together when possible
- Anti-staleness: avoids same matchup within 3 months
- Admin flex: Ashley/Natalie rotate sitting out if odd count

## Local Development

```bash
python serve.py
# Open http://localhost:3000
```

## License

MIT
