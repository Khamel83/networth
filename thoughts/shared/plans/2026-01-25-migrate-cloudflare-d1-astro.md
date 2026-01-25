# Plan: Migrate Net Worth Tennis from Vercel/Supabase to Cloudflare Pages/D1

**Created**: 2026-01-25
**Status**: Draft
**Type**: Feasibility Study + Migration Plan

---

## Summary

Evaluating whether to migrate the Net Worth Tennis website from its current stack (GitHub → Vercel → Supabase + Resend) to a fully Cloudflare-based stack (GitHub → Cloudflare Pages + D1 + Astro). The primary motivation is to eliminate the need to log into Supabase SQL Editor for database management, though the current site is working fine.

**TL;DR: This migration is NOT recommended.** The work required is substantial (~60-80 hours), the benefits are minimal, and you'd be trading one vendor lock-in (Supabase) for another (Cloudflare) with fewer features.

---

## Problem Statement

### Current Pain Points
- "Frustrated by having to log into Supabase SQL Editor"
- Want everything managed via GitHub/GitOps
- Want to avoid vendor-specific UIs

### Current Stack (Working Well)
| Component | Technology | Monthly Cost | Status |
|-----------|-----------|--------------|--------|
| Hosting | Vercel (Hobby) | $0 | ✅ Working |
| Database | Supabase (Free tier) | $0 | ✅ Working |
| Email | Resend (3,000/mo) | $0 | ✅ Working |
| Auth | Custom password hash | $0 | ✅ Working |
| Cron | GitHub Actions | $0 | ✅ Working |

### Current Setup
- **12 serverless functions** (Python on Vercel)
- **7 database tables** with triggers, views, RLS policies
- **7 email templates** via Resend API
- **12 HTML pages** with vanilla JS
- **~3,372 lines** of Python API code

---

## Proposed Stack

| Component | Current | Proposed | Change Complexity |
|-----------|---------|----------|-------------------|
| Frontend | Vanilla HTML/JS | Astro (SSR) | **HIGH** - Rewrite all pages |
| Hosting | Vercel | Cloudflare Pages | **MEDIUM** - Config changes |
| Backend | Python serverless | TypeScript/JS Cloudflare Functions | **VERY HIGH** - Rewrite all APIs |
| Database | Supabase (PostgreSQL) | Cloudflare D1 (SQLite) | **VERY HIGH** - Migrate schema + queries |
| Auth | Custom hash | Would need new solution | **HIGH** - No native auth on D1 |
| Email | Resend | Resend (keep) | **NONE** - No change |
| Cron | GitHub Actions | Cloudflare Cron Triggers | **LOW** - Reconfigure |

---

## Key Technical Differences

### Database: PostgreSQL vs SQLite

| Feature | Supabase (PostgreSQL) | Cloudflare D1 (SQLite) | Impact |
|---------|----------------------|------------------------|--------|
| **SQL Dialect** | Full PostgreSQL | SQLite subset | **HIGH** - Rewrite many queries |
| **Stored Procedures** | ✅ `plpgsql` functions | ❌ No stored procedures | **CRITICAL** - Rewrite logic in app code |
| **Triggers** | ✅ Database triggers | ❌ No triggers | **CRITICAL** - Move to application layer |
| **Views** | ✅ Complex views | ⚠️ Limited view support | **MEDIUM** - Denormalize or use app queries |
| **Row Level Security** | ✅ Built-in RLS | ❌ No RLS | **MEDIUM** - Implement in middleware |
| **Generated Columns** | ✅ Full support | ⚠️ Limited | **LOW** - Use app defaults |
| **Full-text Search** | ✅ Native | ❌ Not available | **N/A** - Not using currently |
| **Connection Pooling** | ✅ Managed | ✅ Built-in | None |
| **Data Types** | UUID, JSONB, ARRAY | INTEGER, TEXT, BLOB | **MEDIUM** - UUID → TEXT, no JSONB |
| **Max DB Size** | 500MB (free) | 5GB (free) | Better on D1 |

### What Breaks in Migration

#### 1. **Database Triggers** (CRITICAL)
Your current setup relies on `update_player_games()` trigger that auto-updates player stats when matches are inserted. D1 has no triggers, so you'd need to:
```python
# Current (automatic via trigger)
INSERT INTO matches (...) VALUES (...)

# Migrated (manual stat updates)
INSERT INTO matches (...) VALUES (...)
UPDATE players SET total_games = total_games + X WHERE id = ...
UPDATE players SET rank = (calculated_rank) WHERE id = ...
```

#### 2. **Stored Functions** (CRITICAL)
You use PostgreSQL functions like:
- `recalculate_rankings()` - Would need to become application code
- `update_player_games()` - Would need to become application code
- `blocked_pairs` VIEW - Would need to become a query builder

#### 3. **UUID vs Integer**
```sql
-- Current (PostgreSQL)
id UUID DEFAULT gen_random_uuid() PRIMARY KEY

-- D1 (SQLite)
id TEXT DEFAULT lower(hex(randomblob(16))) PRIMARY KEY
```

#### 4. **Complex Queries**
Your `player_match_compatibility` view does cross-joins and window functions. In D1, this becomes complex application code.

---

## Migration Scope

### What Would Need to be Rewritten

#### 1. **All 12 API Endpoints** (Python → TypeScript)
- `admin.py` (13K LOC) → TypeScript Cloudflare Functions
- `auth.py` (9K LOC) → TypeScript Cloudflare Functions
- `email.py` (25K LOC) → TypeScript Cloudflare Functions
- `join.py` (6K LOC) → TypeScript Cloudflare Functions
- `matches.py` (8K LOC) → TypeScript Cloudflare Functions
- `pairings.py` (22K LOC) → TypeScript Cloudflare Functions
- `profile.py` (17K LOC) → TypeScript Cloudflare Functions
- `players.py` (4K LOC) → TypeScript Cloudflare Functions
- `upload.py` (11K LOC) → TypeScript Cloudflare Functions
- `health.py`, `migrate-passwords.py`, `supabase_http.py`

**Estimate:** 3,372 lines Python → ~4,500 lines TypeScript (boilerplate)

#### 2. **Database Schema** (PostgreSQL → SQLite)
- Rewrite all `CREATE TABLE` statements
- Convert UUID columns to TEXT
- Remove trigger definitions
- Remove function definitions
- Convert views to application queries
- Remove RLS policies (implement in middleware)

**Estimate:** 366 lines SQL → ~200 lines SQL + ~500 lines TypeScript query builders

#### 3. **Frontend** (Vanilla HTML/JS → Astro)
- 12 HTML pages → Astro components
- Authentication flows
- Admin dashboard
- Profile views
- Form handling

**Estimate:** ~2,000 lines HTML/JS → ~1,500 lines Astro (cleaner, but new framework)

#### 4. **Environment Variables**
- Vercel env vars → Cloudflare env vars
- Update all `.env` references
- Update GitHub Actions workflows

---

## Implementation Plan (If Proceeding)

### Phase 1: Database Migration (Week 1-2)
- [ ] Export all data from Supabase
- [ ] Convert schema from PostgreSQL to SQLite
- [ ] Rewrite triggers as application logic
- [ ] Rewrite views as query builders
- [ ] Create migration scripts
- [ ] Set up D1 database locally for testing
- [ ] Migrate all data to D1
- [ ] Verify data integrity

### Phase 2: Backend Rewrite (Week 3-5)
- [ ] Set up Cloudflare Pages project
- [ ] Configure TypeScript + Astro
- [ ] Create D1 binding in wrangler.toml
- [ ] Rewrite `auth.py` → `auth.ts`
- [ ] Rewrite `admin.py` → `admin.ts`
- [ ] Rewrite `matches.py` → `matches.ts`
- [ ] Rewrite `pairings.py` → `pairings.ts`
- [ ] Rewrite `profile.py` → `profile.ts`
- [ ] Rewrite remaining API endpoints
- [ ] Implement middleware for auth/authorization

### Phase 3: Frontend Migration (Week 6)
- [ ] Convert HTML pages to Astro components
- [ ] Migrate authentication flows
- [ ] Migrate admin dashboard
- [ ] Migrate profile views
- [ ] Update all API calls

### Phase 4: DevOps & Cron (Week 7)
- [ ] Migrate GitHub Actions to Cloudflare Cron Triggers
- [ ] Update environment variables
- [ ] Set up staging environment
- [ ] Configure custom domain
- [ ] Set up monitoring

### Phase 5: Testing & Launch (Week 8)
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Security audit
- [ ] Cut over DNS
- [ ] Monitor for issues

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Data loss during migration** | Low | HIGH | Multiple backups, test migrations, dry runs |
| **Auth system breaks** | Medium | HIGH | Thorough testing of password verification, token handling |
| **Performance regression** | Medium | MEDIUM | Benchmark before/after, D1 may actually be faster for reads |
| **Email delivery breaks** | Low | MEDIUM | Keep Resend (no change), test email flows |
| **Cron jobs fail** | Medium | MEDIUM | Test Cloudflare Cron triggers thoroughly |
| **Feature gaps in D1** | High | HIGH | Already identified triggers/views - will rewrite |
| **Vendor lock-in remains** | High | LOW | You're just trading Supabase lock-in for Cloudflare lock-in |
| **Time overrun** | High | MEDIUM | This is a 2-month project, not a weekend |

---

## Decision Matrix

### "Is it worth it?" Analysis

#### Reasons TO Migrate ❌
1. **"No more Supabase SQL Editor"** - But you'll still use Cloudflare Dashboard
2. **"Everything in GitHub"** - You can already do 95% via GitHub Actions + Supabase REST API
3. **"Learn new tech"** - Astro is cool but not necessary for this project
4. **"Potential cost savings"** - Both are free at your scale

#### Reasons NOT to Migrate ✅
1. **Site works fine now** - No downtime, no complaints
2. **Huge time investment** - 60-80 hours minimum
3. **High risk** - Data migrations always have surprises
4. **Losing features** - No triggers, no stored procedures, no RLS
5. **Same lock-in problem** - Cloudflare is just as proprietary as Supabase
6. **Opportunity cost** - What else could you build in 2 months?

### Better Alternative: Improve Current Setup

If the frustration is "logging into Supabase SQL Editor," consider:

1. **Create a DB management API endpoint**
   ```python
   # /api/admin?action=schema_update
   # Run SQL via API instead of UI
   ```

2. **Use Supabase REST API for everything**
   - You already have `supabase_http.py`
   - Create migration scripts that run via GitHub Actions

3. **Set up Supabase CLI locally**
   - Run migrations from your terminal
   - No UI needed

4. **Create an admin "SQL Runner" page**
   - Protected admin route
   - Run queries from `/admin?action=sql`

---

## Cost Comparison

| Service | Current Monthly | Cloudflare Monthly | Savings |
|---------|-----------------|---------------------|---------|
| Vercel | $0 (Hobby) | $0 | $0 |
| Supabase | $0 (Free tier) | $0 | $0 |
| Resend | $0 (3,000 emails) | $0 (keep) | $0 |
| **Total** | **$0** | **$0** | **$0** |

**Financial ROI: $0**
**Time Cost: 60-80 hours**

---

## Success Metrics

If you proceed, success means:
- [ ] Zero data loss
- [ ] All features working identically
- [ ] No performance regression
- [ ] Auth flows working for all existing users
- [ ] Cron jobs firing on schedule
- [ ] Email delivery unchanged
- [ ] Can deploy from `git push`

---

## Recommendation

### ❌ DO NOT MIGRATE

**This is a "dumb thing you're frustrated by," not a real problem.**

#### Why:
1. **You're trading one proprietary platform for another**
   - Supabase → Cloudflare
   - Both have dashboards
   - Both have vendor lock-in
   - Neither is "managed via GitHub" in the way you want

2. **The pain point is solvable**
   - If you hate the SQL Editor, build an API wrapper
   - Or use Supabase CLI
   - Or create migration scripts

3. **The site works**
   - Resend emails are working
   - Auth is working
   - Ranking is working
   - Users are happy

4. **Migration risk is high**
   - 60+ hours of work
   - Data migration always has edge cases
   - You'll lose database features (triggers, RLS)

### When This MIGHT Make Sense:
- You're hitting Supabase free tier limits (you're not - ~30 players, minimal DB size)
- You need global edge deployment with sub-50ms latency everywhere (you don't - LA-only league)
- You want to learn Astro/Cloudflare for career reasons (valid, but be honest it's for learning)

### Better Use of 60 Hours:
1. **Add features users actually want**
   - Mobile app?
   - Better match scheduling?
   - Photo galleries?
   - Event calendar?

2. **Improve existing experience**
   - Better mobile responsive design
   - Push notifications for matches
   - Weather-based court recommendations

3. **Build new projects**
   - The ONE_SHOT skills system you mentioned
   - Other ideas in your backlog

---

## Alternative: Minimal "GitOps" Improvements

If you still want to reduce Supabase UI dependency, here's a **2-hour** solution:

### Add a `/api/db` Endpoint

```python
# api/db.py - Run SQL via API instead of Supabase UI
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Admin-only endpoint
        # Execute SQL via Supabase REST API
        # Return results
        # Now you can run migrations from scripts!
```

### Create Migration Scripts

```bash
# scripts/migrate_add_paid_column.sh
curl -X POST https://networthtennis.com/api/db \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"sql": "ALTER TABLE players ADD COLUMN has_paid BOOLEAN DEFAULT FALSE"}'
```

### Run via GitHub Actions

```yaml
# .github/workflows/db-migrate.yml
on:
  workflow_dispatch:
    inputs:
      sql:
        description: 'SQL to run'
        required: true

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - name: Run migration
        run: |
          curl -X POST ${{ secrets.API_URL }}/api/db \
            -d '{"sql": "${{ github.event.inputs.sql }}"}'
```

**Result:** You can now manage DB from GitHub UI, no Supabase SQL Editor needed.

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-25 | Claude (Opus 4.5) | Initial feasibility study - Recommendation: DO NOT MIGRATE |
