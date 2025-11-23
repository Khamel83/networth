# 🎾 Deploy to networthtennis.com - Complete Guide

## The Full Path (20 Minutes)

1. Deploy to Railway (15 min)
2. Point your domain to Railway (5 min)
3. Wait for DNS (15-30 min)
4. Done! Working at networthtennis.com

---

## PART 1: Deploy to Railway (15 minutes)

### 1. Go to Railway
- Visit: **https://railway.app**
- Click "Login"
- Sign in with GitHub

### 2. Deploy Your Repo
- Click "New Project"
- Select "Deploy from GitHub repo"
- Authorize Railway to access your repos
- Select: `Khamel83/networth`
- Select branch: `claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY`
- Wait 2 minutes (Railway builds)

### 3. Add Environment Variables
Click your service → "Variables" tab → Add:

| Variable Name | Value |
|--------------|-------|
| `DATABASE_PATH` | `networth_tennis.db` |
| `PLAYER_PASSWORD` | `tennis123` |

Railway redeploys automatically (30 seconds)

### 4. Generate Railway Domain (Temporary)
- Click "Settings" tab
- Scroll to "Networking"
- Click "Generate Domain"
- You get: `https://yourapp.railway.app`

### 5. Test It Works
Visit `https://yourapp.railway.app`

Should see your tennis ladder! ✅

**Test the API:**
```bash
curl https://yourapp.railway.app/api/health
```

Should return: `{"success": true, "players": 40}`

---

## PART 2: Point networthtennis.com to Railway (5 minutes)

### 6. Add Custom Domain in Railway

Still in Railway dashboard:

1. **Settings tab** → Scroll to "Networking"

2. **Custom Domains** section → Click "**+ Add Domain**"

3. **Type:** `networthtennis.com`

4. **Click "Add"**

5. **Railway displays DNS records** - copy these! Should look like:

```
A Record:
  Name: @
  Value: 67.205.xxx.xxx

CNAME Record:
  Name: www
  Value: yourapp.railway.app
```

### 7. Update DNS at Your Domain Registrar

**Where is networthtennis.com registered?**
- GoDaddy?
- Namecheap?
- Google Domains?
- Cloudflare?
- Other?

**General Steps (works for all):**

1. **Login to your domain registrar** (where you bought networthtennis.com)

2. **Find "DNS Settings"** or "DNS Management"

3. **Add these two records:**

   **Record 1:**
   - Type: `A`
   - Name: `@` (or blank, or `networthtennis.com`)
   - Value: `[IP address Railway gave you]`
   - TTL: `3600` (or default)

   **Record 2:**
   - Type: `CNAME`
   - Name: `www`
   - Value: `yourapp.railway.app`
   - TTL: `3600` (or default)

4. **Delete conflicting records:**
   - Remove any old A records for `@`
   - Remove any old CNAME for `www`
   - **Keep MX records** (if you have email)

5. **Save changes**

---

## PART 3: Wait for DNS (15-30 minutes, sometimes instant)

### Check DNS Propagation

Visit: **https://www.whatsmydns.net/#A/networthtennis.com**

When it shows Railway's IP address in green checkmarks worldwide → DNS is ready!

Or check via terminal:
```bash
nslookup networthtennis.com
```

Should return the IP Railway gave you.

---

## PART 4: Verify Everything Works

### After DNS Propagates:

**Visit:** https://networthtennis.com

Should see your tennis ladder! 🎾

**Test all pages:**
- https://networthtennis.com/ ✅ Ladder
- https://networthtennis.com/privacy.html ✅ Privacy
- https://networthtennis.com/rules.html ✅ Rules
- https://networthtennis.com/support.html ✅ Support

**Test API:**
```bash
curl https://networthtennis.com/api/health
curl https://networthtennis.com/api/ladder
```

**Test Login:**
```bash
curl -X POST https://networthtennis.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aapelian@gmail.com","password":"tennis123"}'
```

Should return player info!

---

## SSL Certificate (HTTPS)

Railway automatically provisions a free SSL certificate from Let's Encrypt.

- Usually takes 5-10 minutes after DNS propagates
- You'll see the lock icon 🔒 in your browser
- If not, wait a bit longer - it's automatic

---

## ✅ YOU'RE DONE!

Your tennis ladder is now live at:
**https://networthtennis.com**

---

## What Works

✅ **https://networthtennis.com** - Public ladder
✅ **https://www.networthtennis.com** - Redirects to above
✅ All static pages (privacy, rules, support)
✅ Player login via API
✅ Score reporting
✅ 40 players ready to use
✅ Free SSL certificate
✅ Runs forever on Railway free tier

---

## How Players Login

**Password:** `tennis123` (everyone uses this)

**Test emails:**
- aapelian@gmail.com
- Allison.n.dunne@gmail.com
- Alyssa.j.perry@gmail.com
- ariannahairston@gmail.com

(See RAILWAY_LOGIN_GUIDE.md for all 40 emails)

---

## Ongoing Cost

- **Domain:** ~$12-15/year (what you already pay)
- **Hosting:** $0 (Railway free tier)
- **SSL:** $0 (included)

**Total: Just your domain renewal fee**

---

## Share With Players

Once live, send this:

```
🎾 NET WORTH Tennis Ladder is now live!

🌐 Website: https://networthtennis.com
📋 Rules: https://networthtennis.com/rules.html
💡 FAQ: https://networthtennis.com/support.html

Login:
  Email: [your registered email]
  Password: tennis123

Contact: matches@networthtennis.com
```

---

## Quick Reference: DNS Records

Add these at your domain registrar (GoDaddy, Namecheap, etc.):

```
Type: A
Name: @
Value: [IP from Railway]

Type: CNAME
Name: www
Value: yourapp.railway.app
```

That's it!

---

## Troubleshooting

**"Domain not working after 30 minutes"**
- Check DNS: https://www.whatsmydns.net/#A/networthtennis.com
- Verify records at your registrar
- Make sure you saved changes

**"Not Secure" warning**
- SSL is still provisioning (wait 10 min)
- Clear browser cache
- Try incognito mode

**"Can't find DNS settings at my registrar"**
- Tell me which registrar you use
- See CUSTOM_DOMAIN_SETUP.md for specific instructions

---

## Need Help?

Detailed guides:
- **CUSTOM_DOMAIN_SETUP.md** - Full DNS guide with all registrars
- **RAILWAY_COMPLETE_GUIDE.md** - Detailed Railway deployment
- **RAILWAY_LOGIN_GUIDE.md** - After deployment

Questions? Just ask!

---

## The Complete Checklist

- [ ] Deploy to Railway
- [ ] Add environment variables
- [ ] Test at yourapp.railway.app
- [ ] Add custom domain in Railway
- [ ] Get DNS records from Railway
- [ ] Login to domain registrar
- [ ] Add A record for @
- [ ] Add CNAME record for www
- [ ] Save DNS changes
- [ ] Wait for DNS propagation (check whatsmydns.net)
- [ ] Visit https://networthtennis.com
- [ ] Verify SSL certificate
- [ ] Test all pages
- [ ] Test API endpoints
- [ ] Share with players!

See you at networthtennis.com! 🎾
