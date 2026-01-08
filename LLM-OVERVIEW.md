# LLM Overview - NET WORTH Tennis

> Context for any LLM working on this project.

## What This Project Does

Women's tennis ladder league for East Side LA. Players are paired monthly based on skill level, play 2 sets, and report scores. Rankings based on total games won.

## Tech Stack

- **Language**: Python (API), HTML/CSS/JS (frontend)
- **Framework**: Vercel Serverless Functions
- **Database**: Supabase (PostgreSQL with RLS)
- **Auth**: Supabase magic links
- **Email**: Gmail SMTP (`ashleybrooke.kaufman@gmail.com`)
- **Deployment**: Vercel (Hobby plan - 12 function limit)
- **Automation**: GitHub Actions (cron for emails)

## Project Structure

```
api/           # 12 Python serverless functions (AT LIMIT)
public/        # Static HTML/CSS/JS
.github/       # GitHub Actions workflows
```

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Detailed project instructions |
| `api/email.py` | Gmail SMTP + 5 email templates |
| `api/join.py` | Player registration |
| `api/pairings.py` | Monthly matching algorithm |
| `api/admin.py` | Admin dashboard API |
| `supabase-final-setup.sql` | Database schema + RLS policies |

## How to Run

```bash
python serve.py  # Serves on localhost:3000
```

## Current State

- **Status**: Production
- **Live URL**: networthtennis.com
- **Last Updated**: January 2026

## Important Context

### Vercel 12 Function Limit
The project has exactly 12 API functions. DO NOT add new `.py` files to `api/` without removing one first.

### RLS Policy Gap
The `players` table has NO DELETE policy. Delete operations fail silently. Use UPDATE to deactivate records instead.

### Email System
Uses Gmail SMTP with app password. Requires `SMTP_PASSWORD` env var in Vercel. Sender is hardcoded to Ashley's email.

### Join Flow
When a player re-registers with an email that exists but is inactive, the code UPDATEs the existing record instead of delete+insert (because RLS blocks deletes).
