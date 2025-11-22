# 🚀 Deploy Tennis Match LA Demo - Get a Public URL in 5 Minutes

**Choose ONE of these free hosting options to get a public URL for Ashley:**

---

## Option 1: Render.com (Recommended - Easiest)

### ⚡ One-Click Deploy

1. **Go to:** https://render.com/
2. **Sign up** with GitHub (free account)
3. **Click "New +" → "Web Service"**
4. **Connect this repository:** `Khamel83/networth`
5. **Select branch:** `claude/create-mockup-site-01N5DCXhjDgtyZ8kTAhhfHf5`
6. **Render will auto-detect** the `render.yaml` config
7. **Click "Create Web Service"**

**That's it!** Render will:
- Build the app automatically
- Give you a public URL like: `https://tennis-match-la-demo.onrender.com`
- Auto-deploy on every push

**Share this URL with Ashley** - she can access it immediately!

---

## Option 2: Railway.app (Also Free & Fast)

1. **Go to:** https://railway.app/
2. **Sign up** with GitHub
3. **Click "Start a New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose:** `Khamel83/networth`
6. **Select branch:** `claude/create-mockup-site-01N5DCXhjDgtyZ8kTAhhfHf5`
7. **Railway auto-detects** the `railway.json` config
8. **Click "Deploy"**

You'll get a URL like: `https://tennismatchla-production.up.railway.app`

---

## Option 3: Fly.io (More Control)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
flyctl launch --name tennis-match-la-demo

# Get your URL
flyctl status
```

---

## What Ashley Will See

Once deployed, share the URL and tell Ashley to:

1. **Go to the URL** (e.g., `https://tennis-match-la-demo.onrender.com`)
2. **Login with any demo account:**
   - Email: `john@tennis.com`
   - Password: `password123`
3. **Explore the interface:**
   - Dashboard with match history
   - Preferences page
   - Admin view at `/admin/dashboard`

---

## Demo Features

✅ **5 Sample Players** - John, Jane, Mike, Sarah, Tom
✅ **Professional Design** - Clean, modern interface
✅ **Mobile-Friendly** - Works on any device
✅ **Sample Matches** - Pre-populated data to showcase functionality
✅ **Admin Dashboard** - Management view

---

## Free Tier Limits

All these services offer **free tiers** perfect for demos:

- **Render:** Free tier sleeps after 15 min of inactivity (wakes up in ~30 seconds)
- **Railway:** 500 hours/month free (plenty for a demo)
- **Fly.io:** 3 shared-cpu VMs free

---

## Need Help?

If you want me to set up the deployment for you, just provide:
- Your preferred service (Render, Railway, or Fly.io)
- Access to deploy (or I can give you the exact steps)

**Goal:** Get Ashley a working URL she can click and explore immediately!
