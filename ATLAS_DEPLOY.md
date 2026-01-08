# Atlas Deploy

**One config, managed auth, free tier friendly.**

Deploy a complete web app with authentication and admin panel - either self-hosted on your own accounts or Atlas Hosted on shared infrastructure.

## What You Get

- **Magic link auth** (Supabase Auth - no passwords)
- **Admin "backstage" panel** (benevolent dictator model)
- **Database** (Supabase Postgres)
- **Auto-deploy** (Vercel + GitHub)
- **Keep-alive cron** (prevents Supabase free tier pause)

## Two Modes

### Self-Hosted (Free)
You create your own accounts, you own everything:
- Your GitHub repo
- Your Supabase project (includes Auth for magic links)
- Your Vercel deployment
- Your custom domain (optional)

**Cost: $0** (within free tier limits)

### Atlas Hosted (Managed)
I manage the infrastructure, you just configure:
- Shared Supabase org (isolated projects)
- Vercel team deployment
- API keys managed via SOPS/secrets-vault
- Custom domain included

**Cost: TBD** (covers infrastructure overhead)

---

## Self-Hosted Setup

### Prerequisites
- GitHub account
- 15 minutes

### Step 1: Create Accounts (one-time)

#### Supabase (Database + Auth)
1. Go to [supabase.com](https://supabase.com)
2. Create account → New Project
3. Save your:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon Key: `eyJhbG...` (in Settings → API)
4. Configure Auth email templates in Authentication → Email Templates

#### Vercel (Hosting)
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub

### Step 2: Fork & Deploy

```bash
# Fork the template repo
gh repo fork atlas-deploy/template --clone
cd template

# Or manually: github.com/atlas-deploy/template → Fork
```

### Step 3: Configure Supabase

1. Go to Supabase Dashboard → SQL Editor
2. Paste contents of `supabase/schema.sql`
3. Run it

### Step 4: Set Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables:

| Variable | Value | Example |
|----------|-------|---------|
| `SUPABASE_URL` | Your Supabase URL | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | Your Supabase anon key | `eyJhbG...` |
| `SITE_URL` | Your deployed URL | `https://myapp.vercel.app` |
| `ADMIN_EMAIL` | Admin notifications | `admin@myapp.com` |

### Step 5: Set GitHub Secrets

In GitHub → Your Repo → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `SUPABASE_URL` | Same as above |
| `SUPABASE_ANON_KEY` | Same as above |

This enables the keep-alive cron to prevent Supabase pausing.

### Step 6: Done

Your app is live at `https://your-project.vercel.app`

---

## Atlas Hosted Setup

### Prerequisites
- GitHub account
- Access to Atlas admin (request from @khamel83)

### Step 1: Request Project

Contact admin with:
- Project name
- Admin email
- Custom domain (optional)

### Step 2: Receive Config

Admin provisions:
- Supabase project (isolated in Atlas org)
- Vercel deployment
- All env vars pre-configured

### Step 3: Clone & Customize

```bash
# Clone your provisioned repo
git clone https://github.com/atlas-hosted/your-project
cd your-project

# Edit your config
nano league.config.js
git push  # Auto-deploys
```

### Step 4: Done

Your app is live at `https://your-project.atlashosted.com`

---

## Configuration

All customization lives in `league.config.js`:

```js
export default {
  // Branding
  name: "My League",
  tagline: "The best league",

  colors: {
    primary: "#D4AF37",
    accent: "#CCFF00",
    background: "#0a0a0a",
  },

  // What you're tracking
  entity: {
    name: "Player",          // or "Member", "Guest", "Owner"
    namePlural: "Players",
    fields: [
      { key: "name", type: "text", required: true },
      { key: "email", type: "email", required: true },
      // ... custom fields
    ],
  },

  // What happens
  action: {
    name: "Match",           // or "Game", "Vote", "RSVP"
    type: "pairing",         // pairing | free-form | one-time
    cadence: "monthly",      // weekly | monthly | one-time
    fields: [
      // ... scoring fields
    ],
  },

  features: {
    publicLadder: true,
    adminPanel: true,
    emailNotifications: true,
  },
}
```

---

## Free Tier Limits

| Service | Limit | Typical Usage |
|---------|-------|---------------|
| **Supabase** | 500MB DB, 50k auth | ~10,000 members easily |
| **Vercel** | 100GB bandwidth, 12 functions | ~50,000 page views |
| **GitHub** | Unlimited | No limit |

**Keep-alive cron** runs every 5 days to prevent Supabase pause (7 day inactivity limit on free tier).

---

## Architecture

```
User → Vercel (static + API) → Supabase (auth + data)

GitHub Actions:
  - Auto-deploy on push
  - Keep-alive ping every 5 days
  - Monthly cron for pairings (if enabled)
```

---

## Security Model

- **Auth**: Email magic links (Supabase Auth)
- **Access**: Admin adds you → you can login
- **No passwords**: Nothing to leak or forget
- **Admin**: Benevolent dictator controls guest list

---

## Integrations

### ONE_SHOT Stack
- `AGENTS.md`: Universal Claude instructions (read-only, pulled from oneshot repo)
- `CLAUDE.md`: Project-specific instructions
- `secrets-vault`: Encrypted secrets management (Atlas Hosted only)

### secrets-vault (Atlas Hosted)
```bash
# Secrets stored encrypted, decrypted at deploy
secrets-vault/
├── atlas/
│   ├── supabase-org-key.age
│   └── vercel-team-token.age
```

---

## Roadmap

- [ ] `npx create-atlas` CLI for guided setup
- [ ] Web wizard for non-technical users
- [ ] Auto-provision Supabase via API
- [ ] Multi-tenant Atlas Hosted dashboard
- [ ] Usage analytics per project

---

## Examples

| Project | Entity | Action | Use Case |
|---------|--------|--------|----------|
| NET WORTH Tennis | Player | Match | Monthly tennis ladder |
| Fantasy Draft | Owner | Pick | Snake draft board |
| Book Club | Member | Vote | Monthly book selection |
| Poker Night | Player | Session | Weekly results tracking |
| Birthday Party | Guest | RSVP | Event management |
| Office Picks | Player | Pick | Sports predictions |

---

## Support

- Self-Hosted: Open issue on GitHub
- Atlas Hosted: Contact admin

---

*Atlas Deploy - Ship it and forget it.*
