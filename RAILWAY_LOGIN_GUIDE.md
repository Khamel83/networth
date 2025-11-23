# 🎾 How to Login After Railway Deployment

## Your Site URL
After deploying to Railway, your site will be at:
```
https://your-project-name.railway.app
```

(Railway generates this URL when you click "Generate Domain" in Settings → Networking)

---

## Login Credentials

### Password (Same for Everyone)
```
tennis123
```

### Player Emails (Pick Any)

Here are 10 real players in your database you can test with:

| Name | Email |
|------|-------|
| Alik Apelian | [redacted-email] |
| Allison Dunne | [redacted-email] |
| [redacted-name] | [redacted-email] |
| Arianna Hairston | [redacted-email] |
| Ashley Brooke Kaufman | Ashleybrooke.kaufman@gmail.com |
| Camille Tsalik | [redacted-email] |
| Carlyn Hudson | [redacted-email] |
| [redacted-name] | [redacted-email] |
| Carolina Ciappa | [redacted-email] |
| [redacted-name] | [redacted-email] |

**You have 40 total players** - these are just the first 10 alphabetically.

---

## How to Test Login

### Option 1: Via API (curl)

```bash
curl -X POST https://your-project-name.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"[redacted-email]","password":"tennis123"}'
```

**Expected response:**
```json
{
  "success": true,
  "message": "Welcome back, Alik Apelian! 🎾",
  "player": {
    "id": "...",
    "name": "Alik Apelian",
    "email": "[redacted-email]",
    "skill_level": 3.5,
    "total_score": 1250,
    "current_rank": 5,
    "total_players": 40,
    "wins": 8,
    "losses": 2
  },
  "recent_matches": [...]
}
```

### Option 2: Via Web (if you build a login page)

1. Go to `https://your-project-name.railway.app/login.html` (if you create this)
2. Enter email: `[redacted-email]`
3. Enter password: `tennis123`
4. Click "Login"

---

## All Available Endpoints

Once deployed, your site has:

### Public Pages (No Login)
- `https://yourapp.railway.app/` - Main ladder
- `https://yourapp.railway.app/privacy.html` - Privacy policy
- `https://yourapp.railway.app/rules.html` - Rules
- `https://yourapp.railway.app/support.html` - Support/FAQ

### API Endpoints
- `GET /api/health` - Check if API is working
- `GET /api/ladder` - Get full ladder rankings
- `GET /api/players` - Get all player names (for dropdowns)
- `POST /api/login` - Player login
- `POST /api/report-score` - Report match score

---

## Test Everything

### 1. Check Health
```bash
curl https://yourapp.railway.app/api/health
```

Should return:
```json
{
  "success": true,
  "message": "NET WORTH API is running!",
  "timestamp": "2025-11-23T...",
  "players": 40
}
```

### 2. Get Ladder
```bash
curl https://yourapp.railway.app/api/ladder
```

Should return JSON with all 40 players ranked.

### 3. Login
```bash
curl -X POST https://yourapp.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"[redacted-email]","password":"tennis123"}'
```

Should return player info.

### 4. Get All Players
```bash
curl https://yourapp.railway.app/api/players
```

Should return list of all 40 players with IDs and names.

---

## To Share With Your Players

Send this to your tennis players:

```
The NET WORTH Tennis Ladder is now live!

🌐 View Ladder: https://yourapp.railway.app
📋 Rules: https://yourapp.railway.app/rules.html
💡 Support: https://yourapp.railway.app/support.html

To login and report scores:
- Email: Your email address (as registered)
- Password: tennis123

Contact: matches@networthtennis.com
```

---

## Security Note

**Current setup:** Everyone uses password `tennis123`

This is fine for a closed group of 40 tennis players you know. If you want individual passwords later, let me know and I'll add:
- Password reset via email
- Individual password hashing
- Email verification

For now, this works perfectly for your tennis ladder!

---

## What Players Can Do After Login

Via the API, players can:
- ✅ View their personal stats
- ✅ See their current ranking
- ✅ Report match scores
- ✅ View match history
- ✅ See upcoming matches

(You can build web forms for these features later if you want)
