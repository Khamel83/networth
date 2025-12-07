# League/Event Platform Spec

## Vision

One-click deploy for any recurring competition, event, or group activity. User fills out a form, gets a live site with auth, admin, and data collection - all self-hosted on their own Vercel/Supabase.

## Core Concept

Everything is defined by a single `league.config.js` file:

```js
export default {
  // Branding
  name: "NET WORTH",
  tagline: "East Side LA Women's Tennis",
  domain: "networthtennis.com",  // optional custom domain

  colors: {
    primary: "#D4AF37",      // gold
    accent: "#CCFF00",       // tennis ball
    background: "#0a0a0a",   // dark
    danger: "#DC143C",       // red
  },

  // What we're tracking
  entity: {
    name: "Player",
    namePlural: "Players",
    fields: [
      { key: "name", type: "text", required: true },
      { key: "email", type: "email", required: true, unique: true },
      { key: "phone", type: "phone" },
      { key: "skill_level", type: "select", options: ["4.5 Advanced+", "4.0 Advanced", "3.5 Intermediate", "3.0 Beginner"] },
      { key: "rank", type: "number", computed: true },
      { key: "total_points", type: "number", computed: true, default: 0 },
    ],
    ranking: {
      field: "total_points",
      order: "desc",
    },
  },

  // What happens between entities
  action: {
    name: "Match",
    namePlural: "Matches",
    type: "pairing",  // pairing | free-form | bracket | round-robin
    cadence: "monthly",  // weekly | monthly | season | one-time
    fields: [
      { key: "score_p1", type: "number", label: "Player 1 Games" },
      { key: "score_p2", type: "number", label: "Player 2 Games" },
      { key: "court", type: "select", options: ["Vermont Canyon", "Griffith Park", "Echo Park"] },
      { key: "would_play_again", type: "boolean", private: true },
    ],
    scoring: {
      // How actions affect entity rankings
      pointsFrom: "score",  // each entity gets their score added to total_points
    },
  },

  // Features to enable
  features: {
    publicLadder: true,       // show rankings on homepage
    adminPanel: true,         // backstage for admins
    emailNotifications: true, // pairing emails, reminders
    joinRequests: true,       // new people can request to join
    pauseFeature: true,       // entities can sit out
  },

  // Email settings
  email: {
    from: "NET WORTH Tennis <noreply@networthtennis.com>",
    replyTo: "admin@networthtennis.com",
  },
}
```

## How It Works

### For NET WORTH Tennis (current)
- Entity = Player
- Action = Match (monthly pairing)
- Ranking = Total games won
- Features = All enabled

### For Fantasy Football Draft
```js
{
  name: "The League",
  entity: {
    name: "Owner",
    fields: [
      { key: "name", type: "text" },
      { key: "email", type: "email" },
      { key: "team_name", type: "text" },
      { key: "draft_position", type: "number" },
    ],
  },
  action: {
    name: "Pick",
    type: "sequential",  // one at a time, snake draft
    fields: [
      { key: "player_name", type: "text" },
      { key: "position", type: "select", options: ["QB", "RB", "WR", "TE", "K", "DEF"] },
      { key: "round", type: "number", computed: true },
    ],
  },
  features: {
    publicLadder: false,
    draftBoard: true,
    timer: true,
  },
}
```

### For Birthday Party
```js
{
  name: "Sarah's 30th",
  entity: {
    name: "Guest",
    fields: [
      { key: "name", type: "text" },
      { key: "email", type: "email" },
      { key: "dietary", type: "select", options: ["None", "Vegetarian", "Vegan", "Gluten-free"] },
      { key: "plus_one", type: "boolean" },
      { key: "song_request", type: "text" },
    ],
  },
  action: {
    name: "RSVP",
    type: "one-time",
    fields: [
      { key: "attending", type: "select", options: ["Yes!", "Maybe", "Can't make it"] },
      { key: "message", type: "textarea" },
    ],
  },
  features: {
    publicLadder: false,
    guestList: true,
    countdown: true,
  },
}
```

### For Poker Night
```js
{
  name: "Tuesday Poker",
  entity: {
    name: "Player",
    fields: [
      { key: "name", type: "text" },
      { key: "email", type: "email" },
      { key: "total_winnings", type: "number", computed: true },
      { key: "games_played", type: "number", computed: true },
    ],
    ranking: { field: "total_winnings", order: "desc" },
  },
  action: {
    name: "Session",
    type: "free-form",
    cadence: "weekly",
    fields: [
      { key: "buy_in", type: "number", default: 20 },
      { key: "cash_out", type: "number" },
      { key: "bounties", type: "number", default: 0 },
    ],
    scoring: {
      pointsFrom: "calculated",
      formula: "cash_out - buy_in + bounties",
    },
  },
}
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Setup Wizard                      │
│  (hosted at launchleague.com or whatever)           │
│                                                      │
│  1. Pick template (league/event/group)              │
│  2. Customize fields                                │
│  3. Set branding                                    │
│  4. Connect GitHub                                  │
│  5. Deploy                                          │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Generated Project                       │
│                                                      │
│  GitHub Repo (user owns it)                         │
│  ├── league.config.js    ← all customization here  │
│  ├── public/                                        │
│  │   ├── index.html      ← generated from config   │
│  │   ├── dashboard.html  ← generated from config   │
│  │   └── admin.html      ← if enabled              │
│  ├── api/                                           │
│  │   ├── auth.py         ← standard, unchanged     │
│  │   ├── entities.py     ← CRUD for entities       │
│  │   ├── actions.py      ← CRUD for actions        │
│  │   └── admin.py        ← if enabled              │
│  └── supabase/                                      │
│      └── schema.sql      ← generated from config   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Deployed Infrastructure                 │
│                                                      │
│  Vercel (auto-deploy from GitHub)                   │
│  └── Serves static + API functions                  │
│                                                      │
│  Supabase (provisioned automatically)               │
│  ├── Auth (magic links)                             │
│  ├── Database (entities, actions, admins)           │
│  └── Storage (if needed for images)                 │
│                                                      │
│  Resend (optional, for custom domain email)         │
└─────────────────────────────────────────────────────┘
```

## What's Shared vs Custom

### Shared (never changes)
- Auth system (magic links)
- Admin backstage pattern
- Email sending infrastructure
- Deployment pipeline
- Base CSS/design system

### Generated from Config
- Database schema
- HTML pages (fields, labels, options)
- API validation
- Email templates
- Ranking calculations

### User Customizes
- `league.config.js` - everything about their specific use case
- Logo/images (upload)
- Custom domain (optional)

## MVP Path

1. **Extract from NET WORTH** - Pull out the reusable pieces
2. **Create config loader** - Code reads from `league.config.js` instead of hardcoded
3. **Build generator** - Takes config, outputs schema.sql and HTML
4. **Setup wizard** - Simple form UI that creates the config
5. **One-click deploy** - GitHub + Vercel + Supabase automation

## Revenue Model (if productized)

- **Free**: 1 league, 50 entities, Supabase free tier
- **Pro ($10/mo)**: Unlimited, custom domain, remove branding
- **Team ($25/mo)**: Multiple admins, API access, priority support

Or just open source it and let people self-host for free.
