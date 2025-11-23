# ⚡ START HERE - Deploy in 20 Minutes

## ONE Path, NO Confusion

Everything (frontend + backend + database) runs on **Railway.app** for FREE.

---

## What You're Deploying

✅ Tennis ladder with 16 real players
✅ Public pages (ladder, privacy, rules, support)
✅ Login system (email + password)
✅ Score reporting
✅ Dynamic rankings
✅ Database included (already in git)

---

## The ONLY Steps You Need

### 1. Go to Railway (2 min)
- Visit: **https://railway.app**
- Click "Login"
- Sign in with GitHub

### 2. Deploy This Repo (3 min)
- Click "New Project"
- Select "Deploy from GitHub repo"
- Configure GitHub app (authorize Railway)
- Select repository: `Khamel83/networth`
- Select branch: `master`
- Railway starts building (wait 2 minutes)

### 3. Add Volume for Database (2 min)

**CRITICAL:** So scores don't get lost when you redeploy!

- Click "Data" tab (or "Volumes")
- Click "+ New Volume"
- Mount Path: `/app/data`
- Click "Add"

### 4. Add Environment Variables (2 min)
Click on your service → Variables tab → Add these:

| Variable | Value |
|----------|-------|
| `DATABASE_PATH` | `/app/data/networth_tennis.db` |
| `PLAYER_PASSWORD` | `tennis123` |

Railway auto-redeploys (wait 30 seconds)

### 5. Upload Database to Volume (3 min)

**One-time:** Copy your database file to the persistent volume

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link to your project
railway login
cd /home/user/networth
railway link

# Copy database to volume
railway run cp networth_tennis.db /app/data/networth_tennis.db
```

See `RAILWAY_VOLUME_SETUP.md` for alternative upload methods.

### 6. Generate Domain (1 min)
- Click "Settings" tab
- Scroll to "Networking"
- Click "Generate Domain"
- Copy your URL: `https://yourapp.railway.app`

**Want to use networthtennis.com instead?**
- See: `DEPLOY_TO_NETWORTHTENNIS.md`
- Takes 5 extra minutes + DNS propagation time

### 7. Test Everything (2 min)

**Visit your site:**
```
https://yourapp.railway.app
```

**Test the health check:**
```bash
curl https://yourapp.railway.app/api/health
```

**Test login:**
```bash
curl -X POST https://yourapp.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"[redacted-email]","password":"tennis123"}'
```

---

## ✅ DONE!

Your site is now live at `https://yourapp.railway.app`

---

## How to Login

**Password:** `tennis123` (same for everyone)

**Test with any of these emails:**
- [redacted-email] (Kim Ndombe - #1 ranked)
- nmcoffen@gmail.com (Natalie Coffen - #2 ranked)
- [redacted-email] (Sara Chrisman - #3 ranked)
- [redacted-email] (Alik Apelian - #6 ranked)
- [redacted-email] (Allison Dunne - #9 ranked)

(You have 16 total players - all use the same password)

---

## Pages That Work

- `https://yourapp.railway.app/` - Main ladder ✅
- `https://yourapp.railway.app/privacy.html` - Privacy ✅
- `https://yourapp.railway.app/rules.html` - Rules ✅
- `https://yourapp.railway.app/support.html` - Support ✅
- `https://yourapp.railway.app/api/health` - Health check ✅
- `https://yourapp.railway.app/api/ladder` - API ✅
- `https://yourapp.railway.app/api/login` - Login ✅

---

## Detailed Guides (If You Need Them)

- **`RAILWAY_COMPLETE_GUIDE.md`** - Full step-by-step with screenshots
- **`RAILWAY_LOGIN_GUIDE.md`** - How to login, all player emails, API docs

---

## Questions?

### Where's the database?
✅ Already in git at `networth_tennis.db` - Railway deploys it automatically

### Where's the frontend?
✅ `production_server.py` serves all HTML files (index.html, privacy.html, etc.)

### Where's the backend?
✅ Same `production_server.py` - it's one unified Flask app

### Do I need Vercel?
❌ NO - everything runs on Railway

### Cost?
**$0** - Railway free tier includes 500 hours/month (way more than you need)

---

## That's It!

No Vercel. No confusion. No future effort.

**Everything runs on Railway.**

Go to https://railway.app and follow the 7 steps above. See you in 20 minutes! 🎾

---

## ⚡ What Happens After Setup?

**100% AUTOMATIC** - see `WHATS_AUTOMATIC.md` for full details:
- ✅ Push code → Auto-deploys
- ✅ SSL renews automatically
- ✅ Database persists forever
- ✅ Runs 24/7 with zero maintenance
- ✅ No deployment management needed
