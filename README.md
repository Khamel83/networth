# NET WORTH Tennis Ladder

A complete, self-service tennis ladder platform for managing player rankings, match reporting, and competition.

![Status](https://img.shields.io/badge/status-production%20ready-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Database](https://img.shields.io/badge/database-SQLite%20%7C%20PostgreSQL-orange)

---

## What Is This?

NET WORTH Tennis Ladder is a **complete web application** that lets tennis players:
- 🏆 View real-time ladder rankings
- 🎾 Report match scores
- 📊 Track their match history and stats
- 🔐 Log in to personal dashboards
- ⚡ Self-manage their tennis league

Plus an **admin panel** to:
- 👥 Manage players (add/edit/deactivate)
- ✅ Review and approve match scores
- 📈 Monitor league activity
- 🎯 Control league settings

**Built for:** Competitive tennis groups of 10-100 players
**Hosting:** Railway.app (zero maintenance, automatic SSL)
**Cost:** ~$5-10/month
**Maintenance:** None after setup

---

## Current Status

✅ **Phase 1 & 2: COMPLETE** - Full platform built and tested
✅ **Phase 3: READY** - PostgreSQL migration prepared
⏳ **Phase 4: PENDING** - Awaiting deployment to networthtennis.com

### What Works Now

| Feature | Status | Notes |
|---------|--------|-------|
| Public ladder page | ✅ Complete | Shows all players ranked by score |
| Player login | ✅ Complete | Email + password authentication |
| Player dashboard | ✅ Complete | Rank, stats, recent matches |
| Score reporting | ✅ Complete | Self-report with admin approval |
| Match history | ✅ Complete | View all past matches |
| Admin panel | ✅ Complete | Full management interface |
| Add/edit players | ✅ Complete | Admin can manage roster |
| Approve/reject scores | ✅ Complete | Admin reviews submissions |
| Auto ladder updates | ✅ Complete | Rankings update on approval |
| Static pages | ✅ Complete | Privacy, rules, support |
| PostgreSQL support | ✅ Ready | Migration scripts prepared |
| Local testing | ✅ Complete | Full test environment |

---

## Quick Start

### I Want To... Deploy to Production

**→ Follow [`START_HERE.md`](START_HERE.md)**

Step-by-step guide to deploy to Railway in 15 minutes:
1. Create Railway account
2. Deploy from GitHub
3. Add environment variables
4. Configure database
5. Go live!

### I Want To... Test Locally First

**→ Follow [`LOCAL_TESTING.md`](LOCAL_TESTING.md)** or use quick-start:

**One-command setup:**
```bash
./quick-start.sh
```

**Manual setup:**
```bash
pip3 install -r requirements_backend.txt
python3 init_database.py --force
python3 production_server.py
# Visit http://localhost:5000
```

### I Want To... Use Custom Domain (networthtennis.com)

**→ Follow [`DEPLOY_TO_NETWORTHTENNIS.md`](DEPLOY_TO_NETWORTHTENNIS.md)**

Configure DNS and deploy to your domain.

### I Want To... Migrate to PostgreSQL

**→ Follow [`POSTGRESQL_MIGRATION.md`](POSTGRESQL_MIGRATION.md)**

Upgrade from SQLite to production-grade PostgreSQL (30-45 min).

---

## Documentation

### For Deployment
- **[START_HERE.md](START_HERE.md)** - Main deployment guide (Railway)
- **[DEPLOY_TO_NETWORTHTENNIS.md](DEPLOY_TO_NETWORTHTENNIS.md)** - Custom domain setup
- **[POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md)** - Database upgrade guide

### For Development
- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - Test before deploying
- **[BUILD_SPEC.md](BUILD_SPEC.md)** - Original build specification
- **[PLATFORM_COMPLETE.md](PLATFORM_COMPLETE.md)** - Platform overview

### For Operations
- **[CRITICAL_CONSIDERATIONS.md](CRITICAL_CONSIDERATIONS.md)** - Important issues to know
- **[SITE_STATUS.md](SITE_STATUS.md)** - What requires backend vs frontend
- **[CLEANUP_GUIDE.md](CLEANUP_GUIDE.md)** - Remove old/unused files
- **[DOCS_INDEX.md](DOCS_INDEX.md)** - Complete documentation index

### Helpful Scripts

- **`quick-start.sh`** - One-command local testing setup
  ```bash
  ./quick-start.sh  # Installs deps, inits DB, starts server
  ```

- **`validate.py`** - Pre-deployment validation (runs 46 checks)
  ```bash
  python3 validate.py  # Check if ready to deploy
  ```

- **`import_players.py`** - Import player data from CSV
  ```bash
  python3 import_players.py --template    # Create CSV template
  python3 import_players.py players.csv   # Import players
  ```

- **`.env.template`** - Environment variable template
  ```bash
  cp .env.template .env  # Copy and edit for local testing
  ```

---

## Architecture

### Tech Stack

**Backend:**
- Python 3.9+ with Flask
- SQLite (development) or PostgreSQL (production)
- Gunicorn WSGI server
- Flask sessions for authentication

**Frontend:**
- Static HTML/CSS/JavaScript
- No framework (vanilla JS)
- Responsive design
- Server-side rendering with Jinja2

**Hosting:**
- Railway.app (backend + database)
- Automatic SSL/HTTPS
- Automatic deployments from GitHub
- Railway Volumes for data persistence

### Database Schema

Four main tables:
1. **players** - Player roster with rankings
2. **match_reports** - Submitted match scores (pending/confirmed/rejected)
3. **match_history** - Confirmed matches
4. **monthly_matches** - Match count tracking

See `schema_postgresql.sql` for complete schema.

### Project Structure

```
networth/
├── production_server.py         # Flask application (main backend)
├── init_database.py              # Local database setup
├── requirements_backend.txt      # Python dependencies
│
├── templates/                    # HTML templates (Jinja2)
│   ├── base.html                 # Base template with navbar
│   ├── login.html                # Login form
│   ├── dashboard.html            # Player dashboard
│   ├── report_score.html         # Score reporting form
│   ├── history.html              # Match history
│   ├── admin_dashboard.html      # Admin overview
│   ├── admin_players.html        # Manage players
│   ├── admin_add_player.html     # Add player form
│   ├── admin_edit_player.html    # Edit player form
│   └── admin_scores.html         # Review pending scores
│
├── index.html                    # Public ladder (frontend)
├── privacy.html                  # Privacy policy
├── rules.html                    # Ladder rules
├── support.html                  # Support/contact
│
├── schema_postgresql.sql         # PostgreSQL schema
├── migrate_sqlite_to_postgresql.py  # Migration script
├── init_postgresql.sh            # PostgreSQL setup
│
├── Procfile                      # Railway deployment config
├── railway.json                  # Railway settings
├── vercel.json                   # Static file routing
│
└── Documentation
    ├── README.md                 # This file
    ├── START_HERE.md
    ├── LOCAL_TESTING.md
    ├── DEPLOY_TO_NETWORTHTENNIS.md
    ├── POSTGRESQL_MIGRATION.md
    ├── BUILD_SPEC.md
    ├── PLATFORM_COMPLETE.md
    ├── CRITICAL_CONSIDERATIONS.md
    └── SITE_STATUS.md
```

---

## Key Features

### For Players

✅ **View Ladder** - See real-time rankings without logging in
✅ **Login** - Secure email/password authentication
✅ **Dashboard** - View rank, stats, win rate, recent matches
✅ **Report Scores** - Submit match results with set scores
✅ **Match History** - View all past matches with W/L records
✅ **Pending Scores** - Track submitted scores awaiting approval

### For Admins

✅ **Admin Dashboard** - Overview of players, matches, activity
✅ **Manage Players** - Add, edit, activate/deactivate players
✅ **Review Scores** - Approve or reject submitted match reports
✅ **Auto Updates** - Ladder automatically updates on score approval
✅ **Player Search** - Find players by name or email
✅ **Activity Log** - Monitor recent league activity

### Security Features

✅ **Password-protected logins** - Shared password for all players
✅ **Role-based access** - Admin vs player permissions
✅ **Session management** - 7-day persistent sessions
✅ **CSRF protection** - Via Flask sessions
✅ **Secure cookies** - HTTP-only, SameSite protection
✅ **SQL injection prevention** - Parameterized queries
✅ **HTTPS enforcement** - Automatic via Railway

---

## Environment Variables

### Required

```bash
PLAYER_PASSWORD=tennis123           # Shared password for all players
ADMIN_EMAIL=admin@networthtennis.com  # Email for admin access
SECRET_KEY=<random-secret-key>      # Flask session key (auto-generated)
```

### Database (Choose One)

**Option A: SQLite (Simple, Development)**
```bash
DATABASE_PATH=/app/data/networth_tennis.db
```

**Option B: PostgreSQL (Recommended, Production)**
```bash
DATABASE_URL=postgresql://...       # Auto-set by Railway
```

**Note:** `production_server.py` automatically detects which database to use.

---

## Default Credentials

### Player Login
```
Email: Any registered player email
Password: tennis123 (or your custom PLAYER_PASSWORD)
```

### Admin Access
```
Email: admin@networthtennis.com (or your custom ADMIN_EMAIL)
Password: tennis123
```

**Note:** Admin is determined by matching email to `ADMIN_EMAIL` environment variable.

---

## Deployment Options

### Option A: Railway Only (Recommended)

**Pros:**
- ✅ Single platform for everything
- ✅ Automatic SSL/HTTPS
- ✅ Automatic backups (with PostgreSQL)
- ✅ Zero maintenance
- ✅ Custom domain support

**Cons:**
- ❌ Costs ~$5-10/month

**Guide:** [`START_HERE.md`](START_HERE.md)

### Option B: Vercel (Frontend) + Railway (Backend)

**Pros:**
- ✅ Free Vercel hosting for static pages
- ✅ CDN for faster load times

**Cons:**
- ❌ More complex setup
- ❌ Two platforms to manage
- ❌ CORS configuration needed

**Not recommended** - added complexity for minimal benefit.

---

## Database Options

### SQLite (Default)

**When to use:**
- Testing locally
- Small leagues (< 10 players)
- Low traffic

**Limitations:**
- ❌ Limited concurrent writes
- ❌ File corruption risk
- ❌ No automatic backups
- ❌ Not recommended for production

### PostgreSQL (Recommended)

**When to use:**
- Production deployment
- 10+ players
- Multiple concurrent users

**Benefits:**
- ✅ Better concurrency
- ✅ Automatic Railway backups
- ✅ Production-grade reliability
- ✅ Better performance
- ✅ ACID compliance

**Migration:** See [`POSTGRESQL_MIGRATION.md`](POSTGRESQL_MIGRATION.md)

---

## Costs

### Railway Hosting

| Service | Cost | Notes |
|---------|------|-------|
| Web service | $5/month | Shared CPU, sufficient for 10-100 players |
| PostgreSQL | $5/month | 1GB storage included |
| **Total** | **$10/month** | Or $5/month with SQLite |

**Note:** Railway has a free tier with $5 credit/month, but not reliable for production.

### Domain Name

| Registrar | Cost |
|-----------|------|
| Namecheap | ~$10/year for .com |
| Google Domains | ~$12/year |
| GoDaddy | ~$15/year |

**Total Annual Cost:** ~$130-145 ($10/month Railway + domain)

---

## Development Roadmap

### ✅ Phase 1: Core Player Features (COMPLETE)
- Login/logout system
- Player dashboard
- Score reporting
- Match history

### ✅ Phase 2: Admin Panel (COMPLETE)
- Admin dashboard
- Manage players (add/edit/deactivate)
- Review/approve scores
- Auto ladder updates

### ✅ Phase 3: PostgreSQL Migration (READY)
- PostgreSQL schema
- Migration scripts
- Dual database support

### ⏳ Phase 4: Polish & Launch (PENDING)
- Deploy to networthtennis.com
- Production testing
- Player onboarding
- Launch announcement

### 🔮 Future Enhancements (Optional)
- Email notifications (score approved, new matches)
- Password reset via email
- Player profile photos
- Match scheduling calendar
- Head-to-head statistics
- Season/tournament management
- Mobile app (React Native)
- Individual player passwords
- Two-factor authentication
- Advanced analytics dashboard

---

## FAQ

**Q: Do players need individual accounts?**
A: Currently, all players share one password. They login with their email and the shared password. Admin access is based on matching the `ADMIN_EMAIL`.

**Q: Can I change the password?**
A: Yes! Set the `PLAYER_PASSWORD` environment variable on Railway.

**Q: How do I add new players?**
A: Login as admin, go to Admin Panel → Manage Players → Add New Player.

**Q: What if two players dispute a score?**
A: Admin reviews both versions and approves the correct one. The platform doesn't automatically resolve disputes.

**Q: Can I import existing player data?**
A: Yes! Edit `init_database.py` with your player list, or use the admin panel to add players manually.

**Q: Is this mobile-friendly?**
A: The public ladder is responsive. Admin panel and player features work on mobile but aren't optimized yet.

**Q: Can I customize the look and feel?**
A: Yes! Edit the HTML/CSS files. The design uses inline styles for easy customization.

**Q: What happens if Railway goes down?**
A: Railway has 99.9% uptime. If down, the site is inaccessible until it recovers. Your data is safe in the database.

**Q: How do I backup my data?**
A: With PostgreSQL, Railway handles backups. With SQLite, download the database file regularly. See `CRITICAL_CONSIDERATIONS.md`.

**Q: Can I run this on my own server?**
A: Yes! Deploy anywhere that supports Python/Flask (AWS, DigitalOcean, Heroku, etc.). Railway is just the easiest option.

---

## Support

### Documentation
- Check the guides in this repository
- Read `CRITICAL_CONSIDERATIONS.md` for common issues

### Contact
- Email: matches@networthtennis.com
- GitHub Issues: (if public repo)

---

## Credits

Built for the NET WORTH Tennis Ladder community.

**Technologies:**
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Railway](https://railway.app/) - Hosting platform
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine

---

## Quick Links

📖 **[Start Deployment](START_HERE.md)**
🧪 **[Test Locally](LOCAL_TESTING.md)**
🌐 **[Custom Domain Setup](DEPLOY_TO_NETWORTHTENNIS.md)**
🗄️ **[PostgreSQL Migration](POSTGRESQL_MIGRATION.md)**
⚠️ **[Critical Considerations](CRITICAL_CONSIDERATIONS.md)**

---

**Ready to launch?** → Start with [`START_HERE.md`](START_HERE.md)

**Want to test first?** → Start with [`LOCAL_TESTING.md`](LOCAL_TESTING.md)
