# 🌐 Setup networthtennis.com on Railway

## Overview

After deploying to Railway, you'll point your domain `networthtennis.com` to Railway's servers. Takes 5 minutes + DNS propagation time (up to 48 hours, usually 15 minutes).

---

## Step 1: Deploy to Railway First

Follow **START_HERE.md** to deploy your app to Railway.

You'll get: `https://yourapp.railway.app`

**Make sure this works first** before adding your custom domain.

---

## Step 2: Add Custom Domain in Railway

### In Railway Dashboard:

1. **Click on your deployed service** (the purple box)

2. **Click "Settings" tab**

3. **Scroll to "Networking" section**

4. **Under "Custom Domains"**, click "**+ Add Domain**"

5. **Enter:** `networthtennis.com`

6. **Click "Add"**

7. **Railway shows you DNS records** - keep this tab open!

You'll see something like:

```
Type: A
Name: @
Value: 67.205.154.xxx (Railway's IP)

Type: AAAA
Name: @
Value: 2604:a880:400:d1::xxx (Railway's IPv6)

Type: CNAME
Name: www
Value: yourapp.railway.app
```

---

## Step 3: Configure DNS at Your Domain Registrar

### Where Did You Buy networthtennis.com?

Common registrars:
- GoDaddy
- Namecheap
- Google Domains
- Cloudflare
- Hover
- Domain.com

### General Steps (works for any registrar):

1. **Login to your domain registrar** (where you bought networthtennis.com)

2. **Find DNS Settings**
   - Usually called: "DNS Management", "DNS Settings", "Name Servers", or "Advanced DNS"

3. **Add the records Railway gave you:**

   **Record 1: A Record**
   - Type: `A`
   - Name: `@` (or leave blank, or enter `networthtennis.com`)
   - Value: `[IP from Railway]` (example: 67.205.154.217)
   - TTL: `3600` (or leave default)

   **Record 2: AAAA Record** (optional but recommended)
   - Type: `AAAA`
   - Name: `@`
   - Value: `[IPv6 from Railway]` (example: 2604:a880:400:d1::xxx)
   - TTL: `3600`

   **Record 3: CNAME for www**
   - Type: `CNAME`
   - Name: `www`
   - Value: `yourapp.railway.app` (your Railway URL)
   - TTL: `3600`

4. **Remove any conflicting records**
   - Delete old A records for `@` or `networthtennis.com`
   - Delete old CNAME records for `www`
   - Keep MX records (for email) if you have them

5. **Save changes**

---

## Step 4: Wait for DNS Propagation

- **Typical time:** 15-30 minutes
- **Maximum time:** 48 hours
- **Check status:** https://www.whatsmydns.net/#A/networthtennis.com

When DNS propagates, `networthtennis.com` will show Railway's IP address.

---

## Step 5: Verify SSL Certificate

Railway automatically provisions SSL certificates (HTTPS) via Let's Encrypt.

1. **Wait 5-10 minutes** after DNS propagates

2. **Visit:** `https://networthtennis.com`

3. **Check for the lock icon** 🔒 in browser

If you see "Not Secure":
- Wait a few more minutes
- Railway is still provisioning the cert
- It happens automatically

---

## Specific Registrar Instructions

### If You Use GoDaddy:

1. Login to GoDaddy
2. My Products → Domains → networthtennis.com → DNS
3. Click "Add" for each record:
   - Type: A, Name: @, Value: [Railway IP]
   - Type: CNAME, Name: www, Value: yourapp.railway.app
4. Save

### If You Use Namecheap:

1. Login to Namecheap
2. Domain List → Manage → Advanced DNS
3. Add New Record:
   - Type: A Record, Host: @, Value: [Railway IP]
   - Type: CNAME, Host: www, Value: yourapp.railway.app
4. Save

### If You Use Cloudflare:

1. Login to Cloudflare
2. Select networthtennis.com
3. DNS → Add Record:
   - Type: A, Name: @, IPv4: [Railway IP], Proxy: OFF (gray cloud)
   - Type: CNAME, Name: www, Target: yourapp.railway.app, Proxy: OFF
4. **Important:** Turn OFF Cloudflare proxy (gray cloud) initially
5. After it works, you can turn ON proxy if desired

### If You Use Google Domains:

1. Login to Google Domains
2. My Domains → networthtennis.com → DNS
3. Custom Records → Manage Custom Records:
   - Type: A, Host: @, Data: [Railway IP]
   - Type: CNAME, Host: www, Data: yourapp.railway.app
4. Save

---

## Step 6: Redirect www to Root (Optional)

You might want `www.networthtennis.com` to redirect to `networthtennis.com`.

### In Railway:

1. Add both domains:
   - `networthtennis.com` (primary)
   - `www.networthtennis.com` (secondary)

2. Railway automatically redirects www → non-www

### Or in DNS:

The CNAME record for `www` pointing to Railway handles this automatically.

---

## Testing Your Domain

### Check DNS Propagation:

```bash
# Check if DNS is updated
nslookup networthtennis.com

# Should return Railway's IP
```

Or use online tool:
https://www.whatsmydns.net/#A/networthtennis.com

### Test Your Site:

Once DNS propagates:

```bash
# Test HTTP (redirects to HTTPS)
curl -L http://networthtennis.com

# Test HTTPS
curl https://networthtennis.com

# Test API
curl https://networthtennis.com/api/health
```

**Visit in browser:**
- https://networthtennis.com → Should show your ladder ✅
- https://networthtennis.com/privacy.html → Privacy policy ✅
- https://networthtennis.com/rules.html → Rules ✅
- https://www.networthtennis.com → Redirects to https://networthtennis.com ✅

---

## Troubleshooting

### "Domain not working after 24 hours"

**Check DNS:**
```bash
dig networthtennis.com
```

Should show Railway's IP. If not:
- DNS records not saved at registrar
- Wrong IP address entered
- Conflicting records exist

**Fix:**
- Re-check DNS settings at your registrar
- Make sure you saved changes
- Delete any old/conflicting A records

### "Not Secure" warning in browser

- SSL cert is still provisioning (wait 10 more minutes)
- DNS not fully propagated yet
- Try in incognito/private browsing mode

### "This site can't be reached"

- DNS not propagated yet (wait longer)
- Wrong IP address in A record
- Railway app not running (check Railway dashboard)

### "Works on railway.app but not my domain"

- DNS not propagated (check whatsmydns.net)
- Forgot to add domain in Railway settings
- Conflicting DNS records at registrar

---

## Email Considerations

### If You Have Email at networthtennis.com

**Don't delete MX records!**

When editing DNS, make sure you keep:
- All MX records (for email)
- SPF records (TXT record with `v=spf1`)
- DKIM records (TXT records)

You're only adding/changing:
- A record for `@`
- CNAME record for `www`

### If You Want to Add Email Later

You can set up email with:
- Google Workspace (paid)
- Microsoft 365 (paid)
- Zoho Mail (has free tier)
- Forward to Gmail (free via Cloudflare)

---

## Summary Checklist

- [ ] Deploy to Railway (follow START_HERE.md)
- [ ] Verify app works at `https://yourapp.railway.app`
- [ ] Add custom domain in Railway settings
- [ ] Copy DNS records Railway provides
- [ ] Login to domain registrar
- [ ] Add A record: @ → Railway IP
- [ ] Add CNAME record: www → yourapp.railway.app
- [ ] Save DNS changes
- [ ] Wait 15-30 minutes for propagation
- [ ] Test: https://networthtennis.com
- [ ] Verify SSL certificate (lock icon)
- [ ] Test all pages (privacy, rules, support)
- [ ] Test API: https://networthtennis.com/api/health

---

## Final Result

After completing these steps:

✅ **https://networthtennis.com** - Your tennis ladder
✅ **https://www.networthtennis.com** - Redirects to above
✅ **https://networthtennis.com/privacy.html** - Privacy policy
✅ **https://networthtennis.com/rules.html** - Rules
✅ **https://networthtennis.com/support.html** - Support
✅ **https://networthtennis.com/api/health** - API health check
✅ **HTTPS with valid SSL certificate** (free from Let's Encrypt)

---

## Cost

**Domain:** Whatever you paid for networthtennis.com (~$12-15/year)
**Hosting:** $0 (Railway free tier)
**SSL Certificate:** $0 (Railway includes it free)

**Total ongoing cost:** Just your domain renewal fee

---

## What to Tell Your Players

Once it's live:

```
NET WORTH Tennis Ladder is now at:
🌐 https://networthtennis.com

View ladder, rules, and login to report scores.
Password for all players: tennis123

Questions? Email matches@networthtennis.com
```

---

## Need Help?

**Can't find DNS settings at your registrar?**
- Tell me which registrar you use (GoDaddy, Namecheap, etc.)
- I'll give you exact step-by-step instructions

**Domain not propagating?**
- Share the output of: `nslookup networthtennis.com`
- I'll help debug

**SSL certificate issues?**
- Check Railway logs: Dashboard → Deployments → View Logs
- Usually resolves automatically within 10 minutes
