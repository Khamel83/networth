# Local Testing Guide

## Test NET WORTH Tennis Ladder Locally (Before Deployment)

This guide helps you test the complete platform on your local machine **before deploying to Railway**. This ensures everything works perfectly before going live.

---

## Prerequisites

1. **Python 3.9+** installed
   ```bash
   python3 --version
   ```

2. **pip** (Python package manager)
   ```bash
   pip3 --version
   ```

3. **Git** (to clone the repository)
   ```bash
   git --version
   ```

---

## Step 1: Set Up Local Environment (5 min)

### 1. Clone the Repository (if not already)
```bash
git clone <your-repo-url>
cd networth
```

### 2. Install Python Dependencies
```bash
pip3 install -r requirements_backend.txt
```

Expected output:
```
Successfully installed flask-3.0.0 flask-cors-4.0.0 gunicorn-21.2.0 jinja2-3.1.2 psycopg2-binary-2.9.9
```

**Note:** `psycopg2-binary` is for PostgreSQL support, but we'll use SQLite for local testing.

---

## Step 2: Initialize Test Database (2 min)

### Run the Database Initialization Script
```bash
python3 init_database.py --force
```

Expected output:
```
============================================================
NET WORTH Tennis Ladder - Database Initialization
============================================================

✓ Removed existing database
Creating database: networth_tennis.db
Creating tables...
✓ Tables created

Adding sample players...
  ✓ Added Admin Player (admin@networthtennis.com) - Rank score: 1200
  ✓ Added John Smith (john.smith@example.com) - Rank score: 1450
  ...
  ✓ Added Amy Thomas (amy.thomas@example.com) - Rank score: 800

============================================================
✓ Database initialized successfully!
============================================================

📊 Players added: 11
🏆 Top player: John Smith (1450 pts)
```

### What This Does
- Creates `networth_tennis.db` (SQLite database)
- Creates all 4 tables (players, match_reports, match_history, monthly_matches)
- Adds 11 sample players with varying skill levels
- Sets up test admin account

### Default Login Credentials
```
Email: admin@networthtennis.com
Password: tennis123
```

---

## Step 3: Start the Server (1 min)

### Run the Flask Application
```bash
python3 production_server.py
```

Expected output:
```
🎾 NET WORTH Tennis Ladder
🚀 Starting server on port 5000...
📊 Database: SQLite
📁 Path: networth_tennis.db
🔐 Admin: admin@networthtennis.com
 * Serving Flask app 'production_server'
 * Running on http://0.0.0.0:5000
```

**Note:** Leave this terminal window open. The server must stay running.

---

## Step 4: Test All Features (15 min)

### Test 1: Public Ladder Page ✅
1. **Open browser**: http://localhost:5000
2. **Verify:**
   - Page loads with NET WORTH branding
   - All 11 players listed in ladder
   - Ranked by total score (John Smith at #1 with 1450 pts)
   - Skill levels displayed (2.5 - 4.5 range)
   - Win/loss records shown
   - Footer links work (Privacy, Rules, Support)

### Test 2: Player Login ✅
1. **Click "LOGIN"** in header
2. **Enter credentials:**
   - Email: `admin@networthtennis.com`
   - Password: `tennis123`
3. **Click "Login"**
4. **Verify:**
   - Redirects to `/dashboard`
   - Shows welcome message
   - Navbar shows: Dashboard | Report Score | History | Admin | Logout
   - Player name shown in header: "Admin Player"

### Test 3: Player Dashboard ✅
1. **Should see:**
   - Current rank (#5 of 11)
   - Stats: 8 wins, 2 losses, 80% win rate
   - Total score: 1200
   - Recent matches section (empty if no matches yet)
   - Pending scores section (empty initially)

### Test 4: Report a Score ✅
1. **Click "Report Score"** in navbar
2. **Fill out form:**
   - Opponent: Select "John Smith" from dropdown
   - Match Date: Pick today's date
   - Your Set 1: 6
   - Opponent Set 1: 4
   - Your Set 2: 6
   - Opponent Set 2: 3
   - Notes: "Great match at Central Park"
3. **Click "Submit Score"**
4. **Verify:**
   - Success message: "Score reported successfully! Pending admin review."
   - Redirects to dashboard
   - Score appears in "Pending Scores" section

### Test 5: Admin Panel ✅
1. **Click "Admin"** in navbar
2. **Verify admin dashboard shows:**
   - Total Players: 11
   - Pending Scores: 1
   - Confirmed Matches: 0
   - Recent activity list

### Test 6: Manage Players ✅
1. **Click "Manage Players"** in admin panel
2. **Verify:**
   - All 11 players listed
   - Shows rank, name, email, skill level, score, record
   - Edit and Deactivate buttons for each player

3. **Add a New Player:**
   - Click "Add New Player"
   - Name: "Test Player"
   - Email: "test@example.com"
   - Skill Level: 3.5
   - Click "Add Player"
   - Verify player appears in list at rank #12

4. **Edit a Player:**
   - Click "Edit" next to "Test Player"
   - Change skill level to 4.0
   - Click "Save Changes"
   - Verify skill level updated

### Test 7: Review Scores ✅
1. **Click "Review Scores"** in admin panel
2. **Verify:**
   - Pending score from Test 4 appears
   - Shows both players, date, score
   - "Approve" and "Reject" buttons

3. **Approve the Score:**
   - Click "✓ Approve"
   - Verify:
     - Success message: "Score approved and ladder updated!"
     - Score removed from pending
     - Redirects back to pending scores (now empty)

4. **Check Ladder Updated:**
   - Go to http://localhost:5000 (public ladder)
   - Verify Admin Player's stats updated:
     - Wins: 9 (was 8)
     - Total score: 1300 (was 1200, +100 for win)
   - Verify John Smith's stats updated:
     - Losses: 4 (was 3)
     - Total score: 1400 (was 1450, -50 for loss)
   - Verify rankings adjusted accordingly

### Test 8: Match History ✅
1. **Click "History"** in navbar
2. **Verify:**
   - Approved match appears
   - Shows opponent name, date, score
   - Shows W/L indicator
   - Status: "Confirmed"

### Test 9: Logout ✅
1. **Click "Logout"** in header
2. **Verify:**
   - Redirects to public ladder page
   - No longer see Dashboard/Admin links
   - See "LOGIN" button again

### Test 10: Try Different Player Login ✅
1. **Click "LOGIN"**
2. **Enter:**
   - Email: `john.smith@example.com`
   - Password: `tennis123`
3. **Verify:**
   - Login succeeds
   - Dashboard shows John Smith's stats
   - **No "Admin" link** in navbar (not admin)
   - Cannot access /admin (redirects to dashboard)

---

## Step 5: Test Error Handling (5 min)

### Test Invalid Login
1. Go to http://localhost:5000/login
2. Enter: `nonexistent@example.com` / `tennis123`
3. **Verify:** Error message: "Email not found. Contact matches@networthtennis.com to join!"

### Test Wrong Password
1. Enter: `admin@networthtennis.com` / `wrongpassword`
2. **Verify:** Error message: "Incorrect password."

### Test Unauthenticated Access
1. **Logout** (if logged in)
2. Try to visit: http://localhost:5000/dashboard
3. **Verify:** Redirects to login page with warning

### Test Non-Admin Access to Admin Panel
1. Login as: `john.smith@example.com` / `tennis123`
2. Try to visit: http://localhost:5000/admin
3. **Verify:** Redirects to dashboard with error: "Admin access required."

---

## Step 6: Test Static Pages (2 min)

### Privacy Policy
- Visit: http://localhost:5000/privacy.html
- Verify page loads with privacy policy content

### Rules & Guidelines
- Visit: http://localhost:5000/rules.html
- Verify page loads with ladder rules

### Support
- Visit: http://localhost:5000/support.html
- Verify page loads with contact information

---

## Step 7: Test API Endpoints (Optional)

### Health Check
```bash
curl http://localhost:5000/api/health
```

Expected:
```json
{
  "success": true,
  "message": "NET WORTH API is running!",
  "timestamp": "2025-11-23T...",
  "players": 12
}
```

### Ladder API
```bash
curl http://localhost:5000/api/ladder
```

Expected:
```json
{
  "success": true,
  "ladder": [
    {"id": "...", "name": "John Smith", "rank": 1, "total_score": 1400, ...},
    ...
  ]
}
```

---

## Troubleshooting

### Port Already in Use
**Error:** `Address already in use`

**Solution:**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
PORT=8000 python3 production_server.py
# Then visit http://localhost:8000
```

### Module Not Found
**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Reinstall dependencies
pip3 install -r requirements_backend.txt

# Or use pip instead of pip3
pip install -r requirements_backend.txt
```

### Database Locked
**Error:** `database is locked`

**Solution:**
```bash
# Stop the server (Ctrl+C)
# Delete the database
rm networth_tennis.db
# Reinitialize
python3 init_database.py --force
# Restart server
python3 production_server.py
```

### Templates Not Found
**Error:** `TemplateNotFound: login.html`

**Solution:**
```bash
# Ensure templates directory exists
ls -la templates/

# If missing, check you're in the right directory
pwd
# Should show: /path/to/networth
```

---

## Reset Database

To start fresh with clean data:

```bash
# Stop server (Ctrl+C)
python3 init_database.py --force
python3 production_server.py
```

This recreates the database with original 11 sample players.

---

## Environment Variables (Local Testing)

You can test environment variables locally:

```bash
# Test with custom admin email
ADMIN_EMAIL=your@email.com python3 production_server.py

# Test with custom password
PLAYER_PASSWORD=newpass123 python3 production_server.py

# Test with custom database path
DATABASE_PATH=/tmp/test.db python3 production_server.py

# Multiple variables
ADMIN_EMAIL=admin@test.com PLAYER_PASSWORD=secret123 python3 production_server.py
```

---

## Local Testing Checklist

Before deploying to Railway, ensure all of these work:

- [ ] Database initializes successfully
- [ ] Server starts without errors
- [ ] Public ladder displays all players
- [ ] Player login works
- [ ] Dashboard shows correct stats
- [ ] Score reporting form works
- [ ] Admin panel accessible (with admin email)
- [ ] Admin can add/edit players
- [ ] Admin can approve/reject scores
- [ ] Ladder updates after score approval
- [ ] Match history displays
- [ ] Logout works
- [ ] Login required for protected pages
- [ ] Admin required for admin pages
- [ ] Static pages load (privacy, rules, support)
- [ ] API endpoints return valid JSON
- [ ] Error messages display correctly

---

## Next Steps

Once local testing passes all checks:

1. ✅ **Commit your code** to git
2. ✅ **Push to GitHub**
3. ✅ **Follow `START_HERE.md`** for Railway deployment
4. ✅ **Optional:** Follow `POSTGRESQL_MIGRATION.md` for PostgreSQL setup

---

## Files Used in Local Testing

```
networth/
├── production_server.py       # Flask application
├── init_database.py            # Database initialization
├── networth_tennis.db          # SQLite database (created)
├── requirements_backend.txt    # Python dependencies
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── report_score.html
│   ├── history.html
│   ├── admin_dashboard.html
│   ├── admin_players.html
│   ├── admin_add_player.html
│   ├── admin_edit_player.html
│   └── admin_scores.html
├── index.html                  # Public ladder page
├── privacy.html
├── rules.html
└── support.html
```

---

## Common Questions

**Q: Can I use this database for production?**
A: No! This is for testing only. Use PostgreSQL on Railway for production.

**Q: How do I add real player data locally?**
A: Edit `init_database.py` to add your players, or use the admin panel to add them manually.

**Q: Can I test PostgreSQL locally?**
A: Yes! Install PostgreSQL locally, set `DATABASE_URL`, and it will auto-detect.

**Q: What if I want to test with more players?**
A: Add more entries to the `sample_players` list in `init_database.py`.

**Q: Do I need to test locally before deploying?**
A: Highly recommended! Catches issues before production.

---

Last Updated: November 23, 2025
