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
- **Auth**: Supabase Auth with magic links (no passwords)

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
├── api/                    # Serverless functions (12 max on Vercel Hobby)
│   ├── auth.py            # Magic link auth
│   ├── players.py         # Player list
│   ├── matches.py         # Match reporting
│   ├── pairings.py        # Monthly matching algorithm
│   ├── profile.py         # Player self-service
│   ├── join.py            # Join requests
│   ├── migrate.py         # Admin migrations
│   └── cron/monthly.py    # Scheduled tasks
├── lib/                    # Shared code (not serverless)
│   └── config.py          # Centralized config (colors, copy, courts)
└── vercel.json            # Routing config
```

## Configuration

**`lib/config.py`** - Centralized config (colors, courts list, skill levels)

**CSS Variables** (in each HTML file):
```css
--pink: #d165a4;
--orange: #ec613e;
--peach: #e7b4b5;
```

**Email Templates** - Configured in Supabase Auth dashboard (magic links)

## Environment Variables (Vercel)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SITE_URL` | `https://networthtennis.com` |
| `ADMIN_EMAIL` | Admin email for join requests |
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

**biweekly-emails.yml** runs on 1st of each month:
- Generates new pairings for the month
- Updates admin dashboard with pending notifications

Requires `SITE_URL` and `CRON_SECRET` in GitHub secrets.

## Local Development

```bash
python serve.py
# Open http://localhost:3000
```

## License

MIT
