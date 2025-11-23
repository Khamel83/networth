# Pre-Deployment Checklist

Complete this checklist before deploying NET WORTH Tennis Ladder to production.

---

## Part 1: Local Testing ✅

Complete all items in [`LOCAL_TESTING.md`](LOCAL_TESTING.md)

- [ ] Dependencies installed (`pip3 install -r requirements_backend.txt`)
- [ ] Database initialized (`python3 init_database.py --force`)
- [ ] Server starts without errors
- [ ] Public ladder page loads
- [ ] Player login works (test with `admin@networthtennis.com` / `tennis123`)
- [ ] Dashboard displays correctly
- [ ] Score reporting form works
- [ ] Admin panel accessible
- [ ] Admin can add/edit players
- [ ] Admin can approve scores
- [ ] Ladder updates after score approval
- [ ] Match history displays
- [ ] Logout works
- [ ] Protected pages require login
- [ ] Admin pages require admin email
- [ ] Static pages load (privacy, rules, support)
- [ ] API endpoints return valid JSON

**If any test fails, fix before proceeding!**

---

## Part 2: Player Data Preparation 📋

- [ ] **Collect Real Player List**
  - Player names
  - Player emails
  - Skill levels (2.0-7.0)
  - Initial rankings/scores (optional)

- [ ] **Prepare Player Data**
  - Edit `init_database.py` with real players OR
  - Plan to add via admin panel after deployment

- [ ] **Verify Email Addresses**
  - All emails are valid
  - No duplicates
  - Can receive notifications (for future features)

- [ ] **Designate Admin**
  - Choose admin email address
  - Confirm admin will manage approvals

---

## Part 3: Environment Variables 🔐

Prepare these values (you'll add them to Railway):

- [ ] **PLAYER_PASSWORD**
  - Default: `tennis123`
  - Or create custom: `____________________`
  - Communicate to all players

- [ ] **ADMIN_EMAIL**
  - Admin's email: `____________________`
  - Must match exactly for admin access

- [ ] **SECRET_KEY** (optional, auto-generated if not set)
  - Generate random key: `python3 -c "import secrets; print(secrets.token_hex(32))"`
  - Value: `____________________`

- [ ] **DATABASE_PATH** (for SQLite) OR **DATABASE_URL** (for PostgreSQL)
  - SQLite: `/app/data/networth_tennis.db`
  - PostgreSQL: Auto-set by Railway

---

## Part 4: Railway Account Setup 🚂

- [ ] **Create Railway Account**
  - Visit https://railway.app
  - Sign up with GitHub
  - Verify email address

- [ ] **Add Payment Method** (for production)
  - Railway requires card for paid plans
  - Free tier available but limited

- [ ] **Review Pricing**
  - Understand monthly costs ($5-10/month)
  - Set spending limits if desired

---

## Part 5: GitHub Repository 📦

- [ ] **Commit All Code**
  ```bash
  git add .
  git commit -m "Prepare for production deployment"
  git push
  ```

- [ ] **Verify Repository**
  - All files pushed
  - No sensitive data in repo (passwords, keys)
  - `.gitignore` excludes database files

- [ ] **Repository Visibility**
  - Public or private (your choice)
  - Railway can access both

---

## Part 6: Domain Setup (Optional) 🌐

**If deploying to networthtennis.com:**

- [ ] **Domain Ownership**
  - Domain purchased
  - Access to DNS settings
  - Know your registrar (Namecheap, GoDaddy, etc.)

- [ ] **Review DNS Guide**
  - Read [`DEPLOY_TO_NETWORTHTENNIS.md`](DEPLOY_TO_NETWORTHTENNIS.md)
  - Understand CNAME/A record setup

**If using Railway domain only:**

- [ ] Accept `yourapp.up.railway.app` URL
- [ ] Plan to add custom domain later (can be done anytime)

---

## Part 7: Database Decision 🗄️

Choose your production database:

### Option A: SQLite (Simpler, Quick Start)

- [ ] Understand limitations:
  - Limited concurrent writes
  - File corruption risk
  - Manual backups required
- [ ] Plan to migrate to PostgreSQL later (optional)
- [ ] Railway Volume configured for persistence

### Option B: PostgreSQL (Recommended)

- [ ] Read [`POSTGRESQL_MIGRATION.md`](POSTGRESQL_MIGRATION.md)
- [ ] Understand setup steps (30-45 min)
- [ ] Willing to pay extra $5/month
- [ ] Plan to run migration after initial deployment

**Recommendation:** Start with SQLite, migrate to PostgreSQL before launch.

---

## Part 8: Player Communication 📢

Before launch, prepare to notify players:

- [ ] **Launch Announcement Email/Message**
  - Explain how to access site
  - Provide login instructions
  - Include password (`PLAYER_PASSWORD`)
  - Explain how to report scores
  - Set expectations (admin approval required)

- [ ] **Create Onboarding Guide** (optional)
  - How to log in
  - How to report a score
  - How to view history
  - Who to contact with questions

- [ ] **Communicate Expectations**
  - Scores need admin approval
  - How long approvals take
  - Dispute resolution process

---

## Part 9: Testing Strategy 🧪

- [ ] **Beta Testing Plan** (recommended)
  - Deploy to Railway with test URL first
  - Invite 2-3 players to test
  - Report test scores
  - Approve scores as admin
  - Verify everything works
  - Fix any issues before full launch

- [ ] **Production Testing Plan**
  - Test immediately after deployment
  - Add 1-2 test players
  - Submit & approve test scores
  - Verify ladder updates
  - Delete test data before launch

---

## Part 10: Backup & Recovery Plan 💾

- [ ] **Understand Backup Options**
  - PostgreSQL: Railway auto-backups
  - SQLite: Manual download via Railway CLI

- [ ] **Recovery Plan**
  - Know how to download database
  - Have rollback plan (see `POSTGRESQL_MIGRATION.md`)
  - Understand Railway redeploy process

- [ ] **Data Export**
  - Know how to export player data if needed
  - Understand database schema (`schema_postgresql.sql`)

---

## Part 11: Support & Maintenance 🛠️

- [ ] **Designate Support Contact**
  - Email: matches@networthtennis.com (update if different)
  - Update in `support.html`
  - Include in player communications

- [ ] **Admin Availability**
  - Admin commits to regular score reviews
  - Set SLA (e.g., approve scores within 24 hours)
  - Backup admin if primary unavailable

- [ ] **Monitoring Plan**
  - Check Railway logs periodically
  - Monitor for errors or issues
  - Review player feedback

---

## Part 12: Legal & Privacy 📜

- [ ] **Privacy Policy**
  - Review `privacy.html`
  - Update with accurate information
  - Ensure GDPR/privacy law compliance (if applicable)

- [ ] **Rules & Guidelines**
  - Review `rules.html`
  - Update with league-specific rules
  - Communicate to players

- [ ] **Terms of Service** (optional)
  - Create if needed for your league
  - Add link to footer

---

## Part 13: Final Code Review ✨

- [ ] **All Features Implemented**
  - Phase 1 complete (player features)
  - Phase 2 complete (admin panel)
  - Phase 3 ready (PostgreSQL migration)

- [ ] **No TODO Comments** in code
- [ ] **No Debug Code** left in production
- [ ] **No Hardcoded Secrets** in repository

- [ ] **Security Review**
  - Passwords not in code
  - SQL injection prevention (parameterized queries)
  - CSRF protection enabled
  - HTTPS enforced (automatic on Railway)

---

## Part 14: Deployment Readiness 🚀

Answer these questions:

- [ ] **Do I have 11+ players ready to join?**
  - Yes: Proceed with deployment
  - No: Wait until you have enough players

- [ ] **Is the admin available to manage scores daily?**
  - Yes: Proceed
  - No: Delay until admin is ready

- [ ] **Have I tested everything locally?**
  - Yes: Ready to deploy
  - No: Complete local testing first

- [ ] **Do I understand Railway costs?**
  - Yes: Comfortable with $5-10/month
  - No: Review pricing before proceeding

- [ ] **Am I prepared to troubleshoot issues?**
  - Yes: Can read logs, debug problems
  - No: Get help or learn first

---

## Deployment Decision Matrix

| Scenario | Recommendation |
|----------|----------------|
| All checkboxes ✅ | **READY TO DEPLOY** - Proceed with `START_HERE.md` |
| Local tests failing ❌ | **STOP** - Fix issues, retest |
| < 10 players ⚠️ | **WAIT** - Recruit more players first |
| No admin availability ⚠️ | **WAIT** - Delay until admin ready |
| Budget concerns 💰 | **WAIT** - Review costs, get approval |
| Any security issues 🔒 | **STOP** - Fix immediately before deploying |

---

## Next Steps

### If Ready to Deploy:

1. ✅ **All checkboxes complete**
2. ✅ **No blockers or concerns**
3. ➡️ **Proceed to [`START_HERE.md`](START_HERE.md)**

### If Not Ready:

1. ❌ **Identify incomplete items**
2. ❌ **Complete missing tasks**
3. ❌ **Retest everything**
4. ❌ **Return to this checklist**

---

## Emergency Contacts

Before deploying, prepare these contacts:

| Issue | Contact |
|-------|---------|
| Technical problems | [Your developer/support email] |
| Railway billing | support@railway.app |
| Domain issues | [Your registrar support] |
| Player questions | matches@networthtennis.com |
| Admin issues | [Admin email] |

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] Site accessible at production URL
- [ ] Public ladder loads
- [ ] Player login works
- [ ] Admin login works
- [ ] Can add players via admin panel
- [ ] Can report scores
- [ ] Can approve scores
- [ ] Ladder updates correctly
- [ ] Match history displays
- [ ] All static pages accessible
- [ ] Custom domain works (if configured)
- [ ] SSL certificate valid (https://)
- [ ] No errors in Railway logs
- [ ] Database persisting data (volume configured)

---

## Documentation for Players

Prepare short guide for players:

### Quick Start for Players

1. **Go to:** https://networthtennis.com (or your URL)
2. **Click:** LOGIN (top right)
3. **Enter:**
   - Email: [your registered email]
   - Password: tennis123
4. **View:** Your rank and stats on dashboard
5. **Report score:** Click "Report Score"
6. **Check history:** Click "History"

### Admin Guide

1. **Access admin panel:** Click "Admin" in navbar
2. **Add players:** Manage Players → Add New Player
3. **Review scores:** Review Scores → Approve/Reject
4. **Check activity:** Admin Dashboard shows overview

---

## Final Checklist Summary

Count your checkboxes:

- **Total checkboxes:** ~100+
- **Completed:** _____ / _____
- **Percentage:** _____%

**Minimum to deploy:** 80% complete
**Recommended:** 95%+ complete

---

## Ready to Launch? 🚀

If you've completed this checklist:

### 🎯 Your mission is clear
### 📋 Your data is prepared
### 🔐 Your security is solid
### 🧪 Your testing is complete
### 👥 Your players are ready
### 💪 You're ready to launch!

**Next:** [`START_HERE.md`](START_HERE.md) → Deploy in 15 minutes

---

Last Updated: November 23, 2025
