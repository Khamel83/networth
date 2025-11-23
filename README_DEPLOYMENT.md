# 🚀 NET WORTH Tennis Ladder - Deployment Guide

## Your Site: https://networthtennis.com

This repository contains everything needed to run the NET WORTH Tennis Ladder at your custom domain.

---

## 📖 Quick Start

**Want it at networthtennis.com?**
→ Read: **`DEPLOY_TO_NETWORTHTENNIS.md`**
→ Time: 20 minutes (+ DNS propagation)

**Just want to test on Railway first?**
→ Read: **`START_HERE.md`**
→ Time: 15 minutes

---

## 📚 All Guides

### Essential Guides (Pick One):

**1. DEPLOY_TO_NETWORTHTENNIS.md** ⭐ **← USE THIS FOR CUSTOM DOMAIN**
- Deploy to Railway
- Point networthtennis.com to Railway
- Complete walkthrough in 20 minutes
- Includes DNS setup for all registrars

**2. START_HERE.md** (if you want to test first)
- Deploy to Railway only
- Get temporary URL: yourapp.railway.app
- Add custom domain later

### Detailed Reference Guides:

**3. RAILWAY_COMPLETE_GUIDE.md**
- Every Railway deployment detail
- Database upload options
- Troubleshooting
- Testing procedures

**4. CUSTOM_DOMAIN_SETUP.md**
- DNS configuration for all registrars
- GoDaddy, Namecheap, Google Domains, Cloudflare
- SSL certificate info
- Email (MX records) considerations

**5. RAILWAY_LOGIN_GUIDE.md**
- How to login after deployment
- All 40 player emails
- API documentation
- What to share with players

---

## 🎯 What You're Deploying

### Frontend (Static Pages):
- `index.html` - Main tennis ladder with rankings
- `privacy.html` - Privacy policy
- `rules.html` - Ladder rules and guidelines
- `support.html` - FAQ and support

### Backend (API):
- `production_server.py` - Flask server with:
  - Player login
  - Score reporting
  - Dynamic rankings
  - Match history

### Database:
- `networth_tennis.db` - SQLite database with:
  - 40 real players
  - Match history
  - Scoring records
  - Player stats

---

## ✅ What Works After Deployment

### Public Access (No Login):
- ✅ View ladder rankings
- ✅ See player stats (wins/losses)
- ✅ Read privacy policy
- ✅ Read rules and guidelines
- ✅ Access support/FAQ
- ✅ View court locations with maps

### Player Access (With Login):
- ✅ Personal dashboard
- ✅ Report match scores
- ✅ View match history
- ✅ See current ranking
- ✅ Track statistics

### Admin Features:
- ✅ API for managing players
- ✅ Score confirmation system
- ✅ Match tracking

---

## 🔑 Login Information

**Password (all players):** `tennis123`

**Player emails (40 total):**
- [redacted-email]
- [redacted-email]
- [redacted-email]
- [redacted-email]
- Ashleybrooke.kaufman@gmail.com
- ... and 35 more

(See `RAILWAY_LOGIN_GUIDE.md` for complete list)

---

## 💰 Cost

- **Hosting:** $0 (Railway free tier)
- **SSL Certificate:** $0 (included)
- **Domain:** ~$12-15/year (networthtennis.com)

**Total ongoing cost: Just domain renewal**

---

## 🏗️ Architecture

```
networthtennis.com
        ↓
    Railway.app
        ↓
    ┌─────────────────┐
    │ production_     │
    │ server.py       │
    │ (Flask)         │
    └─────────────────┘
        ↓
    ┌─────────────────┐
    │ HTML Pages      │
    │ - index.html    │
    │ - privacy.html  │
    │ - rules.html    │
    │ - support.html  │
    └─────────────────┘
        ↓
    ┌─────────────────┐
    │ API Endpoints   │
    │ /api/login      │
    │ /api/ladder     │
    │ /api/health     │
    └─────────────────┘
        ↓
    ┌─────────────────┐
    │ networth_       │
    │ tennis.db       │
    │ (40 players)    │
    └─────────────────┘
```

---

## 📋 Deployment Checklist

### Part 1: Railway (15 min)
- [ ] Go to https://railway.app
- [ ] Sign in with GitHub
- [ ] Deploy from GitHub repo
- [ ] Add environment variables
- [ ] Verify app works at railway.app URL

### Part 2: Custom Domain (5 min + DNS)
- [ ] Add networthtennis.com in Railway
- [ ] Get DNS records from Railway
- [ ] Login to domain registrar
- [ ] Add A record for @
- [ ] Add CNAME record for www
- [ ] Wait for DNS propagation
- [ ] Verify site works at networthtennis.com

### Part 3: Testing
- [ ] Visit https://networthtennis.com
- [ ] Check SSL certificate (lock icon)
- [ ] Test all pages (privacy, rules, support)
- [ ] Test API: curl https://networthtennis.com/api/health
- [ ] Test login with a player email

---

## 🆘 Need Help?

### "Which guide should I follow?"

**Use:** `DEPLOY_TO_NETWORTHTENNIS.md`

It has everything in one place.

### "DNS isn't working"

**Check propagation:**
https://www.whatsmydns.net/#A/networthtennis.com

**See:** `CUSTOM_DOMAIN_SETUP.md` → Troubleshooting section

### "Railway deployment failed"

**Check:**
- Environment variables are set correctly
- DATABASE_PATH = `networth_tennis.db`
- PLAYER_PASSWORD = `tennis123`

**See:** `RAILWAY_COMPLETE_GUIDE.md` → Troubleshooting

### "Can't login"

**Verify:**
- Using correct email (see RAILWAY_LOGIN_GUIDE.md)
- Password is `tennis123`
- API is working: curl https://networthtennis.com/api/health

---

## 📱 Share With Players

Once deployed, send this to your tennis players:

```
🎾 NET WORTH Tennis Ladder is LIVE!

🌐 Website: https://networthtennis.com

📊 View Ladder: See current rankings and stats
📋 Rules: Learn how the ladder works
💡 Support: Get help and FAQ

Login to report scores:
  Email: [your registered email]
  Password: tennis123

Questions? Email matches@networthtennis.com

See you on the courts! 🎾
```

---

## 🔧 Technical Details

### Stack:
- **Backend:** Python Flask
- **Database:** SQLite
- **Frontend:** Static HTML/CSS/JS
- **Hosting:** Railway.app
- **SSL:** Let's Encrypt (automatic)

### Files:
- `production_server.py` - Main Flask application
- `networth_tennis.db` - Database (40 players)
- `index.html` - Main ladder page
- `privacy.html`, `rules.html`, `support.html` - Static pages
- `requirements_backend.txt` - Python dependencies
- `Procfile` - Railway configuration
- `railway.json` - Railway deployment settings

### Environment Variables:
- `DATABASE_PATH` - Path to SQLite database
- `PLAYER_PASSWORD` - Shared password for players
- `PORT` - Auto-set by Railway

---

## 📞 Support

**For deployment issues:**
- Check the troubleshooting sections in each guide
- Review Railway logs: Dashboard → Deployments → View Logs

**For ladder operation:**
- Email: matches@networthtennis.com

---

## 🎉 You're Ready!

Everything is set up and ready to deploy.

**Next step:** Open `DEPLOY_TO_NETWORTHTENNIS.md` and follow the steps.

Total time: 20 minutes + DNS propagation

See you at **https://networthtennis.com**! 🎾
