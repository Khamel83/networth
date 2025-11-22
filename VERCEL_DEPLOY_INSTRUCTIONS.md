# EXACT VERCEL DEPLOYMENT INSTRUCTIONS

## STEP 1: PUSH TO GITHUB (Copy-paste these commands)

```bash
git add index.html
git commit -m "Production tennis ladder site"
git push origin main
```

## STEP 2: DEPLOY TO VERCEL (Exact clicks)

1. Go to **https://vercel.com**
2. Click **"Sign up"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub
5. Click **"New Project"**
6. Find and select your **"networth"** repository
7. Click **"Import"**
8. Leave all settings as default (Framework preset: Other)
9. Click **"Deploy"**
10. Wait 30-60 seconds
11. ✅ **SUCCESS** - Click the provided URL to see your site

## STEP 3: CONNECT CUSTOM DOMAIN (Exact steps)

1. In your Vercel project, click **"Settings"** tab
2. Click **"Domains"** in left menu
3. Type: **`www.networthtennis.com`**
4. Click **"Add"**
5. Vercel will show you DNS records like:
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
6. Go to your domain registrar (where you bought networthtennis.com)
7. Find DNS settings for your domain
8. **DELETE** any existing A records or CNAME records for "www"
9. **ADD** the CNAME record Vercel gave you:
   - Type: **CNAME**
   - Host/Name: **www**
   - Value: **cname.vercel-dns.com**
   - TTL: **Automatic** (or 1 hour)
10. Save DNS changes
11. Wait 5 minutes to 24 hours for DNS to propagate

## STEP 4: VERIFY IT WORKS

1. Visit: **`https://www.networthtennis.com`**
2. You should see the full tennis ladder site with:
   - 🎾 NET WORTH logo
   - Player rankings
   - Match reporting forms
   - Beautiful design

## IF DNS DOESN'T WORK IMMEDIATELY:

- Check DNS status at: https://dnschecker.org
- Enter: `www.networthtennis.com`
- Look for the CNAME to point to Vercel
- DNS can take up to 24 hours

## YOUR SITE FEATURES:

✅ **Professional Design**: Modern, responsive tennis ladder
✅ **Player Rankings**: Live leaderboard with scores
✅ **Match Reporting**: Forms to submit match results
✅ **Player Profiles**: Contact info and preferences
✅ **Match History**: Recent games and results
✅ **Mobile Ready**: Works on phones/tablets
✅ **Auto SSL**: HTTPS included automatically

## UPDATING THE SITE:

1. Edit `index.html` with new scores/data
2. Run: `git add index.html && git commit -m "Update ladder scores" && git push`
3. Vercel auto-updates in 30 seconds

## THAT'S IT - ZERO MAINTENANCE:

- ✅ No servers to manage
- ✅ SSL auto-renews
- ✅ Global CDN included
- ✅ 99.99% uptime
- ✅ Free hosting

Your tennis ladder is now live and maintenance-free!