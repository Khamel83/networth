# Backend Deployment Guide

## What You Have

- **40 real players** in the database
- Working Flask backend (`production_server.py`)
- Login, score reporting, ladder rankings
- Database: `networth_tennis.db` (SQLite)

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

**Why Railway?**
- Free tier with persistent storage
- Works with SQLite out of the box
- Auto-deploys from GitHub
- Takes 5 minutes

**Steps:**

1. **Go to https://railway.app**
2. **Sign in with GitHub**
3. **New Project → Deploy from GitHub repo**
4. **Select your `networth` repository**
5. **Railway auto-detects Python and deploys**
6. **Add environment variable:**
   - `DATABASE_PATH` = `networth_tennis.db`
   - `PLAYER_PASSWORD` = `tennis123` (or whatever you want)
7. **Upload your database:**
   - Railway dashboard → Data tab → Upload `networth_tennis.db`
8. **Done!** Backend is live at `https://yourapp.railway.app`

### Option 2: Render.com

1. **Go to https://render.com**
2. **New Web Service → Connect GitHub repo**
3. **Build Command:** `pip install -r requirements_backend.txt`
4. **Start Command:** `gunicorn production_server:app`
5. **Add disk storage** for SQLite database (required!)
6. **Deploy**

### Option 3: Fly.io (Best for Persistence)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch --name networth-tennis

# Deploy
fly deploy

# Upload database
fly ssh console
# Then upload networth_tennis.db via scp
```

## After Backend is Deployed

### Connect Frontend to Backend

Update your `index.html` (or create a separate version) to call the API:

```javascript
// Replace the hardcoded ladder data with:
fetch('https://yourbackend.railway.app/api/ladder')
  .then(res => res.json())
  .then(data => {
    // Update ladder display with data.ladder
  });
```

### Test the Backend

```bash
# Health check
curl https://yourbackend.railway.app/api/health

# Get ladder
curl https://yourbackend.railway.app/api/ladder

# Login (test)
curl -X POST https://yourbackend.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"player@example.com","password":"tennis123"}'
```

## Environment Variables Needed

Set these in your deployment platform:

- `DATABASE_PATH` - Path to SQLite file (default: `networth_tennis.db`)
- `PLAYER_PASSWORD` - Password for all players (default: `tennis123`)
- `PORT` - Auto-set by most platforms
- `FRONTEND_URL` - Your Vercel URL for CORS (optional, defaults to `*`)

## Database Upload

Your database file is: `/home/user/networth/networth_tennis.db`

**For Railway:**
- Dashboard → Data → Upload file

**For Render:**
- Add persistent disk → Upload via CLI

**For Fly.io:**
- Use `fly ssh console` and `scp`

## Files Created for Deployment

- ✅ `production_server.py` - Production-ready Flask backend
- ✅ `requirements_backend.txt` - Python dependencies
- ✅ `Procfile` - For Render/Heroku
- ✅ `railway.json` - For Railway configuration

## What Works After Deploy

✅ Player login (email + password)
✅ View personalized dashboard
✅ Report match scores
✅ View dynamic ladder rankings
✅ See match history

## Current Status

- **Frontend**: On Vercel (static pages work)
- **Backend**: Ready to deploy (choose Railway/Render/Fly)
- **Database**: 40 real players, ready to go

## Quick Start (Railway)

```bash
# 1. Commit the backend files
git add production_server.py requirements_backend.txt Procfile railway.json
git commit -m "Add production backend"
git push

# 2. Go to railway.app and deploy
# 3. Upload networth_tennis.db
# 4. Test: https://yourapp.railway.app/api/health
# 5. Update index.html to call your API
```

**Total time: 10 minutes**
