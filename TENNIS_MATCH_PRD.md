# TENNIS MATCH LA - COMPLETE PRD

**Project**: tennis-match-la
**Repo**: https://github.com/Khamel83/networth
**Deployment**: https://tennis-match.deer-panga.ts.net

## Overview

Zero-maintenance tennis player matching system for LA that gets smarter over time and runs forever without human intervention.

**Ready for autonomous build execution.**

---

## Quick Start (For Your Girlfriend)

### What I Need From You Tomorrow

1. **Player List (Excel/CSV)**:
   - Name, Email, Skill Level (1.0-7.0), Zip Code
   - Preferred days/times to play
   - How far they're willing to travel

2. **Match History (if available)**:
   - Who played who, scores, dates, locations
   - Any feedback on matches (good/bad experiences)

3. **API Key (optional)**:
   - SendGrid account for email notifications
   - Or we can use free Gmail SMTP

### What You'll Get

- **Working site**: https://tennis-match.deer-panga.ts.net
- **Admin access**: Full control of players and matches
- **Daily matching**: Automatic email notifications
- **Mobile-friendly**: Works on phones
- **Zero maintenance**: Runs forever automatically

---

## Technical Architecture

### Stack
- FastAPI + SQLite (zero maintenance)
- Simple HTML/CSS/JS (no frameworks)
- systemd + Caddy + Tailscale (auto-SSL)
- Daily automated matching and backups

### Key Features
- Smart matching algorithm (gets better over time)
- Player reliability scoring
- Match feedback system
- Automatic email notifications
- Complete data export/backup
- Health monitoring and alerts

### Zero-Maintenance Guarantee
- Auto-restart on crashes
- Daily database backups to GitHub
- Weekly health checks
- Error email alerts
- Graceful degradation
- Break-up proof design

---

## Database Schema

```sql
-- Core player data
CREATE TABLE players (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    skill_level DECIMAL(3,1) NOT NULL, -- NTRP 1.0-7.0
    reliability_score DECIMAL(3,2) DEFAULT 1.0,
    preferred_days TEXT, -- JSON array
    preferred_times TEXT, -- JSON array
    location_zip VARCHAR(10),
    travel_radius INTEGER DEFAULT 15,
    match_types TEXT, -- JSON array
    total_matches INTEGER DEFAULT 0,
    feedback_score DECIMAL(3,1) DEFAULT 0.0,
    competitive_level VARCHAR(20) DEFAULT 'casual',
    is_active BOOLEAN DEFAULT true,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match tracking
CREATE TABLE matches (
    id UUID PRIMARY KEY,
    player1_id UUID NOT NULL REFERENCES players(id),
    player2_id UUID NOT NULL REFERENCES players(id),
    match_type VARCHAR(20) NOT NULL, -- singles, doubles
    suggested_location VARCHAR(255),
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    scores TEXT,
    player1_feedback TEXT, -- JSON
    player2_feedback TEXT, -- JSON
    match_quality_score DECIMAL(3,1),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Matching Algorithm

### Version 1: Basic (Launch)
- Skill level +/- 1.0
- Location radius match
- Day/time compatibility
- Avoid recent repeat matches

### Version 2: Smart (After 50 matches)
- Reliability scoring
- Historical feedback compatibility
- Skill progression tracking
- Time preference accuracy

### Version 3: ML Enhanced (After 200 matches)
- Machine learning prediction
- Pattern recognition
- Advanced compatibility scoring

---

## API Endpoints

```python
# User interfaces
GET  /                    # Login page
GET  /dashboard           # Main dashboard
GET  /preferences         # Settings page
GET  /history            # Match history
POST /login              # Authentication
POST /preferences        # Save settings
POST /match/{id}/confirm # Accept/reject matches
POST /match/{id}/feedback # Post-match feedback

# Admin interfaces
GET  /admin/dashboard     # System overview
POST /admin/trigger_match # Manual matching
POST /admin/import        # CSV player import
GET  /export             # Full data export
GET  /health             # System health check
```

---

## Automated Operations

### Daily at 2 AM
- Run matching algorithm
- Send match notifications
- Backup database to GitHub
- Update reliability scores
- Clean old logs
- Health check

### Weekly on Sunday
- Service restart
- Database optimization
- Analytics calculation
- Admin summary email

### Error Handling
- Auto-restart on crashes
- Immediate error emails
- Graceful degradation
- Backup restoration

---

## Data Import Format

### Players (CSV)
```csv
name,email,skill_level,zip_code,preferred_days,preferred_times,match_types
John Doe,john@example.com,3.5,90210,"monday,wednesday","evening","singles,doubles"
Jane Smith,jane@example.com,4.0,90401,"tuesday,thursday","morning","singles"
```

### Match History (CSV)
```csv
player1,player2,date,scores,location,player1_rating,player2_rating
John Doe,Jane Smith,2024-11-15,"6-4,7-5","Beverly Hills Tennis",4,5
```

---

## Deployment Configuration

### systemd Service
```ini
[Unit]
Description=Tennis Match LA
After=network.target

[Service]
Type=simple
User=tennis-match
WorkingDirectory=/opt/tennis-match
Environment=DATABASE_URL=sqlite:///./tennis_match.db
Environment=SENDGRID_API_KEY=${SENDGRID_API_KEY}
ExecStart=/opt/tennis-match/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Caddy Configuration
```caddy
tennis-match.deer-panga.ts.net {
    reverse_proxy localhost:8000
    encode gzip
}
```

---

## Monitoring

### Health Endpoint
`GET /health` returns:
```json
{
    "status": "healthy",
    "total_players": 127,
    "active_matches": 8,
    "last_backup": "2024-11-20T02:00:00Z",
    "uptime": "45 days",
    "errors_24h": 0
}
```

### Daily Admin Email
- Total players and new signups
- Matches made and acceptance rate
- System status and any issues
- Backup verification

---

## Security

- Passwords hashed with bcrypt
- Email privacy protection
- Rate limiting on all endpoints
- No third-party tracking
- Complete data export rights

---

## Zero-Maintenance Checklist

✅ **Automatic Operations**
- Service restart on crashes
- Database backups to GitHub
- SSL certificate renewal
- Daily matching algorithm
- Email notifications
- Error alerts to admin
- Log cleanup
- Health monitoring

✅ **Break-up Proof**
- Data backed up to GitHub repo
- Admin access transferable
- Service runs under system user
- Environment variable configuration
- Complete data export anytime
- Documentation for handover

✅ **Set and Forget**
- No manual intervention required
- Self-healing on failures
- Automated monitoring and alerts
- Scheduled maintenance tasks
- Graceful degradation capabilities

---

## Timeline

**Day 1**: Deploy core functionality and basic matching
**Day 2**: Import seed data and test matching algorithm
**Day 3**: Monitor performance and optimize
**Day 4**: Complete automation and document handover

**Result**: Forever-running tennis matching system that requires zero maintenance.

---

## Next Steps

1. **Tomorrow**: Collect player data from your girlfriend
2. **Upload**: CSV files via admin interface
3. **Review**: Initial matches and player preferences
4. **Launch**: Open to all players
5. **Monitor**: Daily summary emails

---

**Status**: Ready for autonomous build execution.

**Command**: `PRD approved. Execute autonomous build.`

---

*This system will run forever without you touching it. Set it up once, and it will continue matching LA tennis players automatically until the servers shut down.*