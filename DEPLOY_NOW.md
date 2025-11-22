# 🚀 DEPLOY NOW - Complete Guide

## Current Status

❌ **Your new pages (privacy, rules, support) are NOT live yet**
- Changes are in git branch `claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY`
- Need to deploy to make them work on production

✅ **Backend is ready to deploy**
- 40 real players in database
- Production Flask server ready
- Login + score reporting ready

---

## STEP 1: Deploy Frontend (Make Links Work) - 2 MINUTES

### Option A: Merge & Auto-Deploy (If Vercel is connected to GitHub)

1. **Go to GitHub:**
   - Visit: https://github.com/Khamel83/networth
   - Click "Pull requests"
   - Find PR from branch: `claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY`
   - Click "Merge pull request"

2. **Vercel auto-deploys** (if connected)
   - Takes 30-60 seconds
   - Links will work on production

### Option B: Manual Vercel Deploy (If no auto-deploy)

```bash
# Install Vercel CLI (if needed)
npm i -g vercel

# Deploy to production
cd /home/user/networth
vercel --prod
```

**Test:** Visit your Vercel URL and click Privacy Policy - it should work!

---

## STEP 2: Deploy Backend (Enable Login/Dashboard) - 10 MINUTES

### Recommended: Railway.app (Easiest)

1. **Go to https://railway.app**

2. **Sign in with GitHub**

3. **Click "New Project"**

4. **Select "Deploy from GitHub repo"**

5. **Choose repository:** `Khamel83/networth`

6. **Branch:** `claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY` (or merge to main first)

7. **Railway detects Python** and auto-configures

8. **Add environment variables:**
   - Click "Variables" tab
   - Add:
     - `DATABASE_PATH` = `networth_tennis.db`
     - `PLAYER_PASSWORD` = `tennis123`

9. **Upload database:**
   - Click "Data" tab
   - Upload: `/home/user/networth/networth_tennis.db`

10. **Deploy!**
    - Railway automatically deploys
    - Get your URL: `https://yourapp.railway.app`

11. **Test it:**
    ```bash
    curl https://yourapp.railway.app/api/health
    # Should return: {"success": true, "players": 40}
    ```

### Alternative: Render.com

1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo
4. **Build Command:** `pip install -r requirements_backend.txt`
5. **Start Command:** `gunicorn production_server:app`
6. Add persistent disk (required for SQLite!)
7. Upload database file
8. Deploy

---

## STEP 3: Connect Frontend to Backend (Optional - For Dynamic Features)

If you want the static site to call the backend API for login/scores:

1. **Get your backend URL** (from Railway or Render)
   - Example: `https://networth-production.up.railway.app`

2. **Update frontend** to call API:
   - In `index.html`, add fetch calls to your backend
   - Or keep it static and coordinate via email (works fine!)

---

## What Will Work After Deployment

### After STEP 1 (Frontend Deploy):
✅ Privacy Policy page
✅ Rules & Guidelines page
✅ Support & FAQ page
✅ All footer links work
✅ Court location maps
✅ Email links

### After STEP 2 (Backend Deploy):
✅ Player login via email
✅ Personal dashboard
✅ Report match scores
✅ View dynamic rankings
✅ Match history

---

## Quick Checklist

- [ ] Merge PR or run `vercel --prod`
- [ ] Visit Vercel site and test links
- [ ] Deploy backend to Railway
- [ ] Upload database file
- [ ] Test backend: `curl https://yourapp.railway.app/api/health`
- [ ] (Optional) Connect frontend to backend

---

## Files Ready for Deployment

### Frontend (Vercel):
- `index.html` - Main ladder
- `privacy.html` - Privacy policy ✨ NEW
- `rules.html` - Rules ✨ NEW
- `support.html` - Support ✨ NEW
- `vercel.json` - Configured

### Backend (Railway/Render):
- `production_server.py` - Flask API ✨ NEW
- `requirements_backend.txt` - Dependencies ✨ NEW
- `Procfile` - Deploy config ✨ NEW
- `railway.json` - Railway config ✨ NEW
- `networth_tennis.db` - Your data (40 players)

---

## Need Help?

- **Frontend not deploying?** Check Vercel dashboard for build logs
- **Backend not working?** Check Railway logs (Settings → View Logs)
- **Database issues?** Make sure you uploaded `networth_tennis.db`

---

## The Answer to "How are we gonna do the backend?"

**Railway.app or Render.com** - Both have:
- ✅ Free tier
- ✅ One-click GitHub deploy
- ✅ Persistent storage for SQLite
- ✅ Auto HTTPS
- ✅ Environment variables
- ✅ Takes 10 minutes

**Railway is recommended** because it's simpler and handles SQLite better.

You're 10 minutes away from a fully working tennis ladder with login, scoring, and dynamic rankings!
