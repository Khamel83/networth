-- Migration 03: Session Tokens + RLS Lockdown
-- Run in Supabase Dashboard → SQL Editor
-- ===========================================
-- 1. Creates session_tokens table for real server-side auth
-- 2. Locks down all tables: deny anon direct access
--    (app uses service role key which bypasses RLS)
-- 3. Adds auto-RLS trigger for future tables

-- ── Session Tokens ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS session_tokens (
    token        TEXT PRIMARY KEY,
    player_id    UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    player_email TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    expires_at   TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days'
);

CREATE INDEX IF NOT EXISTS idx_session_tokens_expires ON session_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_session_tokens_email   ON session_tokens(player_email);

ALTER TABLE session_tokens ENABLE ROW LEVEL SECURITY;
-- No anon access to session tokens ever
DROP POLICY IF EXISTS "deny_anon_session_tokens" ON session_tokens;
CREATE POLICY "deny_anon_session_tokens" ON session_tokens FOR ALL TO anon USING (false);

-- ── RLS Lockdown: deny anon on all tables ──────────────────────────────────
-- The app now uses SUPABASE_SERVICE_ROLE_KEY which bypasses RLS.
-- These policies prevent anyone using the public anon key from
-- reading or writing data directly (e.g., via DevTools or scripts).

-- players
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Players viewable by all"   ON players;
DROP POLICY IF EXISTS "Players updatable"         ON players;
DROP POLICY IF EXISTS "Players insertable"        ON players;
DROP POLICY IF EXISTS "deny_anon_players"         ON players;
CREATE POLICY "deny_anon_players" ON players FOR ALL TO anon USING (false);

-- matches
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Matches viewable by all" ON matches;
DROP POLICY IF EXISTS "Matches insertable"      ON matches;
DROP POLICY IF EXISTS "deny_anon_matches"       ON matches;
CREATE POLICY "deny_anon_matches" ON matches FOR ALL TO anon USING (false);

-- match_assignments
ALTER TABLE match_assignments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Assignments manageable"       ON match_assignments;
DROP POLICY IF EXISTS "deny_anon_match_assignments"  ON match_assignments;
CREATE POLICY "deny_anon_match_assignments" ON match_assignments FOR ALL TO anon USING (false);

-- match_feedback
ALTER TABLE match_feedback ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Feedback insertable"         ON match_feedback;
DROP POLICY IF EXISTS "Feedback viewable by admin"  ON match_feedback;
DROP POLICY IF EXISTS "deny_anon_match_feedback"    ON match_feedback;
CREATE POLICY "deny_anon_match_feedback" ON match_feedback FOR ALL TO anon USING (false);

-- email_log
ALTER TABLE email_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "deny_anon_email_log" ON email_log;
CREATE POLICY "deny_anon_email_log" ON email_log FOR ALL TO anon USING (false);

-- automation_runs
ALTER TABLE automation_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "deny_anon_automation_runs" ON automation_runs;
CREATE POLICY "deny_anon_automation_runs" ON automation_runs FOR ALL TO anon USING (false);

-- automation_events
ALTER TABLE automation_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "deny_anon_automation_events" ON automation_events;
CREATE POLICY "deny_anon_automation_events" ON automation_events FOR ALL TO anon USING (false);

-- league_settings (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='league_settings') THEN
        ALTER TABLE league_settings ENABLE ROW LEVEL SECURITY;
        EXECUTE 'DROP POLICY IF EXISTS "League settings viewable" ON league_settings';
        EXECUTE 'DROP POLICY IF EXISTS "deny_anon_league_settings" ON league_settings';
        EXECUTE 'CREATE POLICY "deny_anon_league_settings" ON league_settings FOR ALL TO anon USING (false)';
    END IF;
END $$;

-- ── Auto-RLS event trigger for future tables ───────────────────────────────

CREATE OR REPLACE FUNCTION auto_enable_rls()
RETURNS event_trigger LANGUAGE plpgsql AS $$
DECLARE obj RECORD;
BEGIN
  FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    WHERE command_tag = 'CREATE TABLE' LOOP
    EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY;', obj.object_identity);
  END LOOP;
END;
$$;

DROP EVENT TRIGGER IF EXISTS enable_rls_on_create;
CREATE EVENT TRIGGER enable_rls_on_create ON ddl_command_end
  WHEN TAG IN ('CREATE TABLE') EXECUTE FUNCTION auto_enable_rls();
