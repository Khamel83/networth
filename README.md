# NET WORTH Tennis Ladder

> *"Greed, for lack of a better word, is good. Greed for wins. Greed for ranking points. Greed for that number one spot."*

**An 80s Wall Street-themed competitive women's tennis ladder for East Side Los Angeles.**

![Version](https://img.shields.io/badge/version-2.0.0-gold)
![Platform](https://img.shields.io/badge/platform-Vercel-black)
![Database](https://img.shields.io/badge/database-Supabase-green)

## Features

- **Real-time ladder rankings** with Bloomberg-style ticker
- **80s Wall Street aesthetic** - Gordon Gekko meets tennis
- **Tennis ball cursor** - custom SVG cursor throughout
- **Tyler McGillivary-style centered navigation**
- **Player dashboard** with match history and score reporting
- **Responsive design** - works on mobile and desktop
- **Serverless API** - Vercel Python functions
- **Supabase database** - PostgreSQL with real-time capabilities

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/Khamel83/networth.git
cd networth

# Start local server
python serve.py

# Open http://localhost:3000
# Demo login: any email + password "tennis123"
```

### Deploy to Vercel

1. **Set up Supabase**
   - Create project at [supabase.com](https://supabase.com)
   - Run `supabase-schema.sql` in SQL Editor
   - Copy URL and anon key

2. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel

   # Deploy
   vercel

   # Add environment variables
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_ANON_KEY
   ```

3. **Configure custom domain** (optional)
   - Add `networthtennis.com` in Vercel dashboard

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes (production) |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes (production) |
| `PLAYER_PASSWORD` | Demo login password | No (default: tennis123) |

## Architecture

```
networth/
├── public/               # Static files (served by Vercel)
│   ├── index.html       # Main landing page (80s Wall Street aesthetic)
│   ├── login.html       # Player login
│   ├── dashboard.html   # Player dashboard
│   └── ...
├── api/                  # Vercel serverless functions
│   ├── players.py       # GET players list
│   ├── matches.py       # GET/POST matches
│   ├── auth.py          # POST login
│   └── health.py        # GET health check
├── serve.py             # Local development server
├── supabase-schema.sql  # Database schema
└── vercel.json          # Vercel configuration
```

## Design System

### 80s Wall Street Aesthetic

| Element | Value |
|---------|-------|
| Primary Color | `#D4AF37` (Bloomberg Gold) |
| Secondary Color | `#228B22` (Court Green) |
| Background | `#0a0a0a` (Terminal Black) |
| Accent | `#CCFF00` (Tennis Ball) |
| Danger | `#DC143C` (Power Red) |
| Font Display | Playfair Display |
| Font Mono | IBM Plex Mono |

### Typography

- **Headlines**: Playfair Display - Elegant, 80s magazine aesthetic
- **Body/UI**: IBM Plex Mono - Terminal/Bloomberg feel
- **Accents**: Cormorant Garamond - Italic quotes

### Special Features

- **Tennis Ball Cursor**: Custom SVG cursor with seam lines
- **Scanline Effect**: Subtle CRT terminal overlay
- **Grid Pattern**: Bloomberg-style background grid
- **Bloomberg Ticker**: Real-time stats scrolling bar

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/players` | GET | List all active players |
| `/api/matches` | GET | Recent match history |
| `/api/matches` | POST | Report a match score |
| `/api/auth` | POST | Player login |

## Database Schema

See `supabase-schema.sql` for full schema. Key tables:

- **players**: Ranks, points, wins/losses, skill levels
- **matches**: Match history with scores and courts

Triggers automatically update rankings after each match.

## Development

### Prerequisites

- Python 3.11+
- Supabase account (for production)

### Local Testing

The local server (`serve.py`) provides mock data and demo authentication:

```bash
python serve.py
```

- Open http://localhost:3000
- Login with any email + password `tennis123`
- All API endpoints return sample data

### Testing Production API

```bash
# Health check
curl https://networthtennis.com/api/health

# Get players
curl https://networthtennis.com/api/players
```

## Credits

- Design inspired by [Claude's Frontend Design Skill](https://www.claude.com/blog/improving-frontend-design-through-skills)
- Navigation pattern from [Tyler McGillivary](https://www.tylermcgillivary.com/)
- Built with the ONE_SHOT specification

## License

MIT

---

**Net Worth Tennis** - East Side LA Women's Tennis Ladder

Built with Claude Code and ONE_SHOT Skills
