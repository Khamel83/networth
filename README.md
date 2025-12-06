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
- **Backend**: Vercel Python serverless functions
- **Database**: Supabase (PostgreSQL)
- **Email**: Resend API
- **Auth**: Magic links (no passwords)

## Project Structure

```
networth/
├── public/                 # Static site
│   ├── index.html         # Homepage + ladder
│   ├── login.html         # Magic link login
│   ├── join.html          # Request to join
│   ├── dashboard.html     # Player dashboard
│   ├── rules.html         # How it works
│   ├── support.html       # FAQs
│   └── privacy.html       # Privacy policy
├── api/                    # Serverless functions
│   ├── auth.py            # Magic link auth
│   ├── players.py         # Player list
│   ├── matches.py         # Match reporting
│   ├── email.py           # Email sending
│   ├── pairings.py        # Monthly matching algorithm
│   ├── profile.py         # Player self-service
│   ├── join.py            # Join requests
│   └── config.py          # Centralized config (colors, copy, courts)
├── .github/workflows/
│   └── biweekly-emails.yml # 1st + 15th of month emails
└── vercel.json            # Routing config
```

## Configuration

All user-facing content is centralized:

**`api/config.py`** - Email subjects, body copy, colors, courts list, skill levels

**CSS Variables** (in each HTML file):
```css
--gold: #D4AF37;
--tennis-ball: #CCFF00;
--terminal-black: #0a0a0a;
```

## Environment Variables (Vercel)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `RESEND_API_KEY` | Resend email API key |
| `SITE_URL` | `https://networthtennis.com` |
| `EMAIL_FROM` | `NET WORTH Tennis <noreply@networthtennis.com>` |
| `ADMIN_EMAIL` | Admin email for join requests |
| `EMAIL_ENABLED` | `true` to send emails, `false` to block |
| `CRON_SECRET` | Secret for GitHub Actions cron jobs |

## Database (Supabase)

Key tables:
- `players` - Name, email, skill, total_games, rank, availability
- `matches` - Scores, who played, when
- `match_assignments` - Monthly pairings
- `match_feedback` - "Would play again" for silent blocking

Run `supabase-final-setup.sql` for fresh setup.

## Backup & Fallback

- **Database**: Supabase has point-in-time recovery
- **Static Fallback**: `public/fallback.html` - works with just mailto links if everything else fails

## GitHub Actions

**biweekly-emails.yml** runs on 1st and 15th of each month:
- 1st: Generate new pairings + remind about last month
- 15th: Mid-month check-in + outstanding match reminders

Requires `SITE_URL` and `CRON_SECRET` in GitHub secrets.

## Local Development

```bash
python serve.py
# Open http://localhost:3000
```

## License

MIT
