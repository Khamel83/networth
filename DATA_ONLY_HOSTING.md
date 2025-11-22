# NET WORTH - Push Once, Done Hosting

## The Problem
- Server management is a pain
- nginx keeps crashing
- SSL certificates expire
- Security updates needed
- You want to provide TENNIS DATA, not be a server admin

## The Solution
**GitHub Data-Only Hosting** - You push data, GitHub handles the rest

## Your Weekly Workflow (2 minutes):
1. Update match results in `tennis-data.json`
2. `git add tennis-data.json`
3. `git commit -m "Weekly ladder update"`
4. `git push`
5. ✅ Website automatically updates

## What GitHub Handles:
- ✅ Web hosting
- ✅ SSL certificates
- ✅ Security
- ✅ Backups (Git history)
- ✅ Global CDN
- ✅ Domain management

## Setup (One time):
1. Push your data to GitHub
2. Enable GitHub Pages
3. Connect domain `www.networthtennis.com`
4. Done forever

## Data Format:
```json
{
  "players": [...],
  "matches": [...],
  "ladder_date": "2025-11-22"
}
```

That's it. No servers. No nginx. No maintenance.

Just tennis data.