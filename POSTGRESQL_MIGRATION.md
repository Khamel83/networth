# PostgreSQL Migration Guide

## Why Migrate to PostgreSQL?

Your NET WORTH Tennis Ladder currently uses **SQLite**, which is great for development and small-scale use. However, for production with 40+ players, **PostgreSQL is strongly recommended** for:

✅ **Better concurrency** - Multiple users can report scores simultaneously
✅ **Automatic backups** - Railway backs up PostgreSQL automatically
✅ **Better performance** - Optimized for web applications
✅ **Data integrity** - ACID compliance and foreign key constraints
✅ **No file corruption** - SQLite files can corrupt on crashes

**Bottom line:** Migrate to PostgreSQL before launch to avoid data loss and performance issues.

---

## When to Migrate

### Before Launch (Recommended)
- ✅ Migrate during setup before going live
- ✅ Zero downtime concerns
- ✅ Easy rollback if needed
- ✅ Start with production-grade infrastructure

### After Launch (More Complex)
- ⚠️ Requires maintenance window
- ⚠️ Need to notify users
- ⚠️ Risk of downtime
- ⚠️ More testing required

**Recommendation:** Migrate NOW before announcing the site to players.

---

## Prerequisites

Before starting, ensure you have:

1. ✅ Railway account with project deployed
2. ✅ Working site on Railway with SQLite
3. ✅ Access to Railway dashboard
4. ✅ Existing `networth_tennis.db` with player data
5. ✅ All latest code deployed (including migration scripts)

---

## Migration Steps

### Phase 1: Add PostgreSQL to Railway (5 min)

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Select your NET WORTH project

2. **Add PostgreSQL Service**
   - Click "+ New" in your project
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provision a PostgreSQL instance
   - Railway automatically sets `DATABASE_URL` environment variable

3. **Wait for Deployment**
   - PostgreSQL service will show "Active" when ready
   - Click on PostgreSQL service to see connection details

### Phase 2: Initialize PostgreSQL Schema (5 min)

1. **Connect to Railway via CLI** (or use Railway Shell in dashboard)
   ```bash
   # If using Railway CLI locally
   railway link
   railway run bash
   ```

2. **Run Initialization Script**
   ```bash
   # This creates all tables, indexes, views, and triggers
   ./init_postgresql.sh
   ```

   Or manually:
   ```bash
   psql "$DATABASE_URL" -f schema_postgresql.sql
   ```

3. **Verify Schema Created**
   ```bash
   psql "$DATABASE_URL" -c "\dt"
   ```

   You should see:
   - `players`
   - `match_reports`
   - `match_history`
   - `monthly_matches`

### Phase 3: Migrate Data from SQLite (10 min)

1. **Ensure SQLite Database is Accessible**
   ```bash
   # Check if database file exists
   ls -lh /app/data/networth_tennis.db
   ```

2. **Run Migration Script**
   ```bash
   # This will copy all players and match reports to PostgreSQL
   python3 migrate_sqlite_to_postgresql.py
   ```

   Expected output:
   ```
   ============================================================
   NET WORTH Tennis Ladder - SQLite to PostgreSQL Migration
   ============================================================

   Connecting to databases...
     ✓ Connected to both databases

   Migrating players...
     ✓ Migrated 40 players

   Migrating match reports...
     ✓ Migrated 156 match reports

   Verifying migration...
     Players: SQLite=40, PostgreSQL=40 ✓
     Match Reports: SQLite=156, PostgreSQL=156 ✓
     Top Player: John Smith (1450 pts) ✓

   ============================================================
   Migration completed successfully!
   ============================================================
   ```

3. **Handle Migration Errors**

   **If migration fails:**
   ```bash
   # Check database connections
   echo $DATABASE_URL  # Should show PostgreSQL URL
   ls -lh /app/data/networth_tennis.db  # Should show SQLite file

   # Check Python dependencies
   pip list | grep psycopg2

   # Re-run migration (it's safe to run multiple times)
   python3 migrate_sqlite_to_postgresql.py
   ```

### Phase 4: Switch to PostgreSQL (2 min)

1. **Remove SQLite Environment Variable**
   - Go to Railway dashboard
   - Select your service
   - Click "Variables" tab
   - **Remove** `DATABASE_PATH` variable (or comment it out)
   - Keep `DATABASE_URL` (set automatically by Railway PostgreSQL)

2. **Restart Service**
   - Railway will automatically restart
   - Or manually trigger: Click "Deploy" → "Redeploy"

3. **Monitor Logs**
   ```bash
   railway logs
   ```

   Look for:
   ```
   🎾 NET WORTH Tennis Ladder
   🚀 Starting server on port 8000...
   📊 Database: PostgreSQL (Railway)
   🔗 Connection: postgresql://postgres:***...
   🔐 Admin: your@email.com
   ```

### Phase 5: Verify Migration (10 min)

1. **Test Public Ladder**
   - Visit https://networthtennis.com
   - Verify all 40 players are listed
   - Check rankings are correct
   - Verify scores display properly

2. **Test Player Login**
   - Log in with a test player account
   - Check dashboard shows correct stats
   - Verify rank is accurate
   - Check match history displays

3. **Test Score Reporting**
   - Report a test match
   - Verify it appears in pending scores
   - Check opponent dropdown works

4. **Test Admin Panel**
   - Log in with admin account
   - Go to `/admin`
   - Check player count matches
   - Review pending scores
   - Approve a test score
   - Verify ladder updates correctly

5. **Database Query Test**
   ```bash
   # Connect to PostgreSQL directly
   psql "$DATABASE_URL"

   # Run test queries
   SELECT COUNT(*) FROM players;
   SELECT COUNT(*) FROM match_reports;
   SELECT * FROM ladder_rankings LIMIT 10;

   \q
   ```

### Phase 6: Backup SQLite (Just in Case)

1. **Download SQLite Database**
   ```bash
   # Via Railway CLI
   railway run cat /app/data/networth_tennis.db > networth_backup_$(date +%Y%m%d).db
   ```

2. **Store Backup Safely**
   - Keep local copy
   - Upload to Google Drive / Dropbox
   - Keep for at least 30 days

3. **Remove SQLite from Production** (Optional)
   ```bash
   # After confirming PostgreSQL works perfectly for 7+ days
   railway run rm /app/data/networth_tennis.db
   ```

---

## Rollback Plan

If something goes wrong, you can rollback to SQLite:

1. **Re-add DATABASE_PATH Variable**
   - Railway dashboard → Variables
   - Add: `DATABASE_PATH=/app/data/networth_tennis.db`

2. **Remove DATABASE_URL** (Don't delete PostgreSQL service yet)
   - Just remove the variable temporarily
   - Or rename it: `DATABASE_URL_BACKUP`

3. **Restart Service**
   - Railway will restart with SQLite

4. **Test Application**
   - Verify everything works

5. **Debug PostgreSQL Issue**
   - Check logs: `railway logs`
   - Review migration output
   - Test queries in PostgreSQL directly

6. **Retry Migration**
   - Once fixed, switch back to PostgreSQL
   - Re-run verification steps

---

## Environment Variables Summary

### Before Migration (SQLite)
```bash
DATABASE_PATH=/app/data/networth_tennis.db
PLAYER_PASSWORD=tennis123
SECRET_KEY=<your-secret-key>
ADMIN_EMAIL=<your-email>
```

### After Migration (PostgreSQL)
```bash
DATABASE_URL=postgresql://... (set automatically by Railway)
PLAYER_PASSWORD=tennis123
SECRET_KEY=<your-secret-key>
ADMIN_EMAIL=<your-email>
```

**NOTE:** `production_server.py` automatically detects which database to use:
- If `DATABASE_URL` starts with `postgres` → Uses PostgreSQL
- Otherwise → Uses SQLite (`DATABASE_PATH`)

---

## Monitoring PostgreSQL

### Check Database Size
```bash
psql "$DATABASE_URL" -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

### Check Table Sizes
```bash
psql "$DATABASE_URL" -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Check Connection Count
```bash
psql "$DATABASE_URL" -c "SELECT count(*) FROM pg_stat_activity;"
```

### View Recent Activity
```bash
psql "$DATABASE_URL" -c "SELECT * FROM match_reports ORDER BY created_at DESC LIMIT 10;"
```

---

## Troubleshooting

### Error: "DATABASE_URL environment variable not set"
**Solution:** Railway PostgreSQL service not added or environment variable not set
```bash
# Check if PostgreSQL service exists
railway services
# Add PostgreSQL if missing
railway add --service postgresql
```

### Error: "psycopg2 module not found"
**Solution:** Dependency not installed
```bash
# Verify requirements_backend.txt includes:
# psycopg2-binary==2.9.9

# Force redeploy to install dependencies
railway up
```

### Error: "relation 'players' does not exist"
**Solution:** Schema not initialized
```bash
# Run initialization script
./init_postgresql.sh
# Or manually
psql "$DATABASE_URL" -f schema_postgresql.sql
```

### Error: "Could not connect to PostgreSQL"
**Solution:** Check PostgreSQL service status
```bash
# In Railway dashboard
# Click PostgreSQL service → Check status
# If stopped, restart it
```

### Migration Shows Mismatched Counts
**Solution:** Run migration again (safe to re-run)
```bash
# The migration script uses ON CONFLICT DO UPDATE
# So it's safe to run multiple times
python3 migrate_sqlite_to_postgresql.py
```

### Players Can't Log In After Migration
**Solution:** Check UUID conversion
```bash
# In PostgreSQL
psql "$DATABASE_URL" -c "SELECT id, email FROM players LIMIT 5;"

# Compare with SQLite
sqlite3 /app/data/networth_tennis.db "SELECT id, email FROM players LIMIT 5;"

# IDs should be the same (migration preserves UUIDs)
```

---

## PostgreSQL Best Practices

### Regular Backups
Railway backs up PostgreSQL automatically, but you can also:
```bash
# Manual backup
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql

# Restore from backup
psql "$DATABASE_URL" < backup_20251123.sql
```

### Monitor Disk Usage
- Railway PostgreSQL has storage limits
- Monitor: Railway dashboard → PostgreSQL service → Metrics
- Current schema uses minimal space (~10MB for 40 players + 1000 matches)

### Index Maintenance
PostgreSQL automatically maintains indexes, but you can manually:
```bash
# Analyze tables to update statistics
psql "$DATABASE_URL" -c "ANALYZE;"

# Vacuum to reclaim space
psql "$DATABASE_URL" -c "VACUUM;"
```

---

## Cost Considerations

### Railway PostgreSQL Pricing (as of Nov 2025)
- **Hobby Plan:** $5/month for PostgreSQL service
- **Pro Plan:** Scales with usage
- **Shared CPU:** Sufficient for 40-100 players
- **Storage:** 1GB included (plenty for tennis ladder)

### Cost Comparison
- **SQLite:** Free but risky (data corruption, no concurrent writes)
- **PostgreSQL:** $5/month but production-grade

**Recommendation:** The $5/month is worth it for data safety and reliability.

---

## Next Steps After Migration

1. ✅ Update `DEPLOY_TO_NETWORTHTENNIS.md` to mention PostgreSQL option
2. ✅ Update `PLATFORM_COMPLETE.md` to mark Phase 3 complete
3. ✅ Document PostgreSQL setup in `START_HERE.md`
4. ✅ Add PostgreSQL monitoring to admin dashboard (future enhancement)
5. ✅ Set up automated backups (future enhancement)

---

## Questions?

**Q: Can I migrate back to SQLite later?**
A: Yes, but not recommended. You can dump PostgreSQL data and convert back if absolutely necessary.

**Q: Will migration cause downtime?**
A: Minimal. Phase 4 (switching) takes ~30 seconds. Do it during low-traffic time.

**Q: What if I have 1000+ matches already?**
A: Migration script handles it. Tested with large datasets. May take a few minutes.

**Q: Do I need to change my code?**
A: No! `production_server.py` automatically detects and uses PostgreSQL when `DATABASE_URL` is set.

**Q: Can I test PostgreSQL locally first?**
A: Yes! Install PostgreSQL locally, set `DATABASE_URL`, and test before deploying.

---

## Summary

✅ **Prepare:** Add PostgreSQL service to Railway
✅ **Initialize:** Run `init_postgresql.sh`
✅ **Migrate:** Run `migrate_sqlite_to_postgresql.py`
✅ **Switch:** Remove `DATABASE_PATH`, keep `DATABASE_URL`
✅ **Verify:** Test all features thoroughly
✅ **Backup:** Keep SQLite backup for 30 days
✅ **Monitor:** Check logs and database metrics

**Total Time:** 30-45 minutes
**Difficulty:** Easy (all scripts provided)
**Risk:** Low (full rollback plan included)

---

Last Updated: November 23, 2025
For issues: Check `CRITICAL_CONSIDERATIONS.md`
