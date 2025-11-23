# Railway Volume Setup for Database Persistence

## Why You Need This

SQLite databases on Railway need a persistent volume, otherwise:
- ❌ Score updates get lost on redeploy
- ❌ Player data changes disappear
- ❌ Match history doesn't persist

With a volume:
- ✅ Database persists across deploys
- ✅ Scores are saved permanently
- ✅ Zero data loss

---

## Setup (Add to Your Deployment)

### In Railway Dashboard (After Deploying):

1. **Click your service** (the deployed app)

2. **Click "Data" tab** (or "Volumes")

3. **Click "+ New Volume"**

4. **Configure:**
   - **Mount Path:** `/app/data`
   - **Name:** `networth-db` (or anything)
   - Click "Add"

5. **Update Environment Variable:**
   - Go to "Variables" tab
   - Change `DATABASE_PATH` from `networth_tennis.db` to `/app/data/networth_tennis.db`
   - Railway will redeploy

6. **Initialize the database** (one-time):

   **Option A: Upload via Railway CLI**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli

   # Login
   railway login

   # Link to your project
   cd /home/user/networth
   railway link

   # Copy database to volume
   railway run cp networth_tennis.db /app/data/networth_tennis.db
   ```

   **Option B: Let the app create it**
   - The Flask app can initialize an empty database on first run
   - Then you manually add the 40 players via SQL or API

   **Option C: Use Railway Shell**
   - Railway Dashboard → Service → Shell tab
   - Upload the database file there

---

## Updated Environment Variables

After adding volume, your variables should be:

| Variable | Value |
|----------|-------|
| `DATABASE_PATH` | `/app/data/networth_tennis.db` |
| `PLAYER_PASSWORD` | `tennis123` |

---

## How It Works After This

1. **Database lives in the volume** (persistent storage)
2. **Git has your code** (production_server.py, HTML files)
3. **When you push to git:**
   - Railway redeploys your code ✅
   - Database in volume is NOT touched ✅
   - All scores/data persist ✅

4. **Players report scores:**
   - Writes go to `/app/data/networth_tennis.db`
   - Persists forever ✅

---

## Alternative: Use PostgreSQL (More Robust)

Railway offers free PostgreSQL. Benefits:
- ✅ Better for production
- ✅ Automatic backups
- ✅ More reliable
- ✅ No volume management

Want to use PostgreSQL instead? Let me know and I'll convert the app.

For now, the volume approach works great for 40 players.
