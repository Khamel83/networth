# Tennis Match LA

🎾 **Zero-maintenance tennis player matching system for Los Angeles**

Built with the ONE_SHOT methodology - ask everything upfront, then execute autonomously.

## Quick Start

### Demo Accounts
- john@tennis.com / password123
- jane@tennis.com / password123  
- sarah@tennis.com / password123

### Running Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Visit http://localhost:8000

## What This Does

✅ **Automatic Matching**: Runs every night at 2 AM
✅ **Smart Compatibility**: Skill level + location + schedule matching
✅ **Mobile Friendly**: Works on phones and tablets
✅ **Zero Maintenance**: Self-healing, auto-backup, never touch it again
✅ **Admin Tools**: Full control and analytics

## Architecture

- **Backend**: FastAPI + SQLite
- **Frontend**: Simple HTML/CSS (no frameworks)
- **Deployment**: systemd + Caddy + Tailscale
- **Testing**: pytest with comprehensive coverage

## Zero-Maintenance Features

### Automated Operations
- **Daily at 2 AM**: Run matching algorithm
- **Daily at 2:05 AM**: Backup database to GitHub
- **Weekly**: Service restart and health check
- **On errors**: Immediate email alerts

### Self-Healing
- Auto-restart on crashes
- Database corruption recovery
- Graceful external service failures

---

**Built with ONE_SHOT methodology**: One questionnaire. Complete execution. Zero maintenance forever.

*Last updated: November 21, 2024*
