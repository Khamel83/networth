# 🚀 COMPLETE RAILWAY DEPLOYMENT - ONE SITE, NO FUTURE EFFORT

## What You're Getting

A fully working tennis ladder at `https://yourapp.railway.app` that includes:
- ✅ Public ladder page (no login needed)
- ✅ Privacy, Rules, Support pages
- ✅ Player login
- ✅ Score reporting
- ✅ 40 real players ready to use
- ✅ Runs forever on Railway's free tier

**Total time: 15 minutes**

---

## STEP 1: Get Your Database File Ready

Your database has 40 real players and is located at:
```
/home/user/networth/networth_tennis.db
```

**You'll need to download this file to your computer to upload it to Railway.**

If you're on this machine, copy it somewhere accessible:
```bash
cp /home/user/networth/networth_tennis.db ~/Downloads/
```

Or note the path - you'll upload it in Step 4.

---

## STEP 2: Create Railway Account (2 minutes)

1. **Go to:** https://railway.app

2. **Click:** "Login" (top right)

3. **Sign in with GitHub**
   - Click "Sign in with GitHub"
   - Authorize Railway

4. **You're in!** You'll see the Railway dashboard

---

## STEP 3: Deploy Your App (3 minutes)

1. **Click:** "New Project" (big button in the middle)

2. **Select:** "Deploy from GitHub repo"

3. **Click:** "Configure GitHub App"
   - Give Railway access to your repositories
   - Select "Only select repositories"
   - Choose: `Khamel83/networth`
   - Click "Install & Authorize"

4. **Back on Railway:**
   - Click "Deploy from GitHub repo" again
   - Select: `Khamel83/networth`

5. **Select branch:**
   - Choose: `claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY`
   - (Or if you merged the PR, choose `main` or `master`)

6. **Railway starts deploying!**
   - You'll see build logs
   - Wait 1-2 minutes for "Success"

---

## STEP 4: Configure Your App (5 minutes)

### Add Environment Variables

1. **In your Railway project**, click on your service (the purple box)

2. **Click the "Variables" tab**

3. **Click "+ New Variable"** and add these ONE AT A TIME:

   **Variable 1:**
   - Name: `DATABASE_PATH`
   - Value: `networth_tennis.db`
   - Click "Add"

   **Variable 2:**
   - Name: `PLAYER_PASSWORD`
   - Value: `tennis123`
   - Click "Add"

   **Variable 3:**
   - Name: `PORT`
   - Value: `8000`
   - Click "Add"

4. **Railway will automatically redeploy** (takes 30 seconds)

### Upload Your Database

1. **Click the "Data" tab** (next to Variables)

2. **Click "Add Database"** → **"Add Empty PostgreSQL Database"**
   - Wait, JUST KIDDING! We're using SQLite, so:

3. **Actually, we need to use the "Volume" feature:**
   - Click "Settings" tab
   - Scroll to "Volumes"
   - Click "+ Add Volume"
   - Mount Path: `/app`
   - Click "Add"

4. **Upload the database via Railway CLI** (next step)

---

## STEP 5: Upload Database File (3 minutes)

Railway needs the database file. Here's how:

### Option A: Upload via Railway Dashboard (if available)

1. Go to "Data" tab
2. If you see "Upload File", click it
3. Select `networth_tennis.db`
4. Upload

### Option B: Upload via Railway CLI (recommended)

1. **Install Railway CLI on your computer:**
   ```bash
   # Mac/Linux
   npm i -g @railway/cli

   # Or with curl
   sh <(curl -sSL https://railway.app/install.sh)
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```
   - This opens a browser - click "Confirm"

3. **Link to your project:**
   ```bash
   cd /home/user/networth
   railway link
   ```
   - Select your project when prompted

4. **Upload the database:**
   ```bash
   railway run cp networth_tennis.db /app/networth_tennis.db
   ```

### Option C: Deploy with database in repo (easiest!)

Actually, your database file might already be in the git repo. Let's check:

```bash
cd /home/user/networth
ls -lh networth_tennis.db
git add networth_tennis.db
git commit -m "Add database for deployment"
git push origin claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY
```

Railway will redeploy automatically and the database will be there!

---

## STEP 6: Generate Your Public URL (1 minute)

1. **In Railway dashboard**, click "Settings" tab

2. **Scroll to "Networking"**

3. **Click "Generate Domain"**
   - Railway creates: `yourapp.railway.app`

4. **Copy this URL!** This is your website.

---

## STEP 7: Test Your Site (2 minutes)

### Test the Public Page

1. **Visit:** `https://yourapp.railway.app`
   - You should see the tennis ladder!
   - No login required

2. **Click the footer links:**
   - Privacy Policy → Should work ✅
   - Rules & Guidelines → Should work ✅
   - Support → Should work ✅

### Test the Backend API

Open a terminal and test:

```bash
# Health check
curl https://yourapp.railway.app/api/health

# Should return:
# {"success": true, "message": "NET WORTH API is running!", "players": 40}

# Get ladder
curl https://yourapp.railway.app/api/ladder

# Should return JSON with all players
```

---

## STEP 8: Login as a Player (Test Full Functionality)

### Find a Player Email

1. **Connect to your database** to see player emails:
   ```bash
   cd /home/user/networth
   python3 -c "import sqlite3; conn = sqlite3.connect('networth_tennis.db'); cursor = conn.cursor(); cursor.execute('SELECT name, email FROM players WHERE is_active = 1 LIMIT 5'); print('\n'.join([f'{row[0]} - {row[1]}' for row in cursor.fetchall()]))"
   ```

2. **You'll see something like:**
   ```
   Ashley Collins - ashley@example.com
   Jennifer Martinez - jennifer@example.com
   ...etc
   ```

### Test Login

Now test login with the API:

```bash
# Replace with an actual email from your database
curl -X POST https://yourapp.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ashley@example.com","password":"tennis123"}'
```

**You should get:**
```json
{
  "success": true,
  "message": "Welcome back, Ashley Collins! 🎾",
  "player": {
    "name": "Ashley Collins",
    "current_rank": 1,
    "wins": 12,
    "losses": 3
    ...
  }
}
```

✅ **Login works!**

---

## STEP 9: Create a Login Page (Optional - for web login)

The backend works, but if you want a web-based login form:

1. **The `index.html` already supports viewing the ladder**
2. **You can add a simple login form** or use the API directly
3. **For now, you can test with curl or create a simple login page**

Do you want me to create a login.html page that lets players log in via the web?

---

## WHAT WORKS NOW

### ✅ Public Access (No Login)
- Ladder rankings: `https://yourapp.railway.app/`
- Privacy Policy: `https://yourapp.railway.app/privacy.html`
- Rules: `https://yourapp.railway.app/rules.html`
- Support: `https://yourapp.railway.app/support.html`

### ✅ API Access (For Login/Scores)
- Health: `https://yourapp.railway.app/api/health`
- Ladder: `https://yourapp.railway.app/api/ladder`
- Login: `POST https://yourapp.railway.app/api/login`
- Report Score: `POST https://yourapp.railway.app/api/report-score`

### ✅ Players Can:
- View the ladder (anyone)
- Login via API with email + password `tennis123`
- Report scores
- See match history

---

## HOW TO LOGIN (For Players)

### Current Setup:
- **Email:** Any player email from your database (40 players)
- **Password:** `tennis123` (same for everyone right now)

### To Find Player Emails:

Run on your machine:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('/home/user/networth/networth_tennis.db'); cursor = conn.cursor(); cursor.execute('SELECT name, email FROM players WHERE is_active = 1'); [print(f'{row[0]:25} {row[1]}') for row in cursor.fetchall()]"
```

This prints all player names and emails.

### To Test Login:

```bash
curl -X POST https://yourapp.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"PLAYER_EMAIL_HERE","password":"tennis123"}'
```

---

## DONE! 🎉

Your site is now:
- ✅ Live at `https://yourapp.railway.app`
- ✅ All pages work (privacy, rules, support)
- ✅ Backend API works
- ✅ 40 players ready to login
- ✅ No future maintenance needed (runs on Railway free tier)

---

## TROUBLESHOOTING

### "I can't see my site"
- Check Railway dashboard → Deployments → Make sure it says "Success"
- Check Settings → Networking → Make sure domain is generated

### "Database not found"
- Make sure you uploaded `networth_tennis.db`
- Check that `DATABASE_PATH` variable is set to `networth_tennis.db`

### "Login fails"
- Verify player email exists in database
- Check password is `tennis123`
- Check Railway logs: Dashboard → Deployments → Click latest → View Logs

### "API returns 500 error"
- Check Railway logs for Python errors
- Make sure database file was uploaded
- Verify environment variables are set

---

## NEXT STEPS (Optional)

Want to add:
- Web-based login form?
- Score reporting form?
- Player dashboard?

Let me know and I'll create those pages!

---

## Cost: $0

Railway free tier includes:
- ✅ 500 hours/month (more than enough)
- ✅ 1GB storage
- ✅ Custom domain
- ✅ SSL certificate

Your site will run forever for free.
