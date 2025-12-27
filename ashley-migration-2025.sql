-- =============================================================
-- ASHLEY'S CHRISTMAS 2025 MIGRATION
-- NET WORTH Tennis - Major Feature Update
-- Run this in Supabase SQL Editor after backing up data
-- =============================================================

-- =============================================================
-- PHASE 1: MEMBERSHIP TIERS
-- =============================================================

-- Add membership tier column (player or social_butterfly)
ALTER TABLE players ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'player';

-- All existing players default to 'player' tier (already done by DEFAULT)
-- Social Butterflies will self-identify when they sign up or update profile

-- =============================================================
-- PHASE 2: PROFILE ENHANCEMENTS
-- =============================================================

-- Avatar URL for profile photos (stored in Supabase Storage)
ALTER TABLE players ADD COLUMN IF NOT EXISTS avatar_url TEXT DEFAULT NULL;

-- Favorite players (free text field)
ALTER TABLE players ADD COLUMN IF NOT EXISTS favorite_players TEXT DEFAULT NULL;

-- =============================================================
-- PHASE 3: NEW AVAILABILITY SYSTEM (6 slots replacing 3)
-- =============================================================

-- New granular availability slots
-- Weekday slots
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekday_early BOOLEAN DEFAULT false;   -- before 9am
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekday_day BOOLEAN DEFAULT false;     -- 9-5
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekday_late BOOLEAN DEFAULT false;    -- after 5pm

-- Weekend slots
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekend_early BOOLEAN DEFAULT false;   -- before 9am
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekend_day BOOLEAN DEFAULT false;     -- 9-5
ALTER TABLE players ADD COLUMN IF NOT EXISTS avail_weekend_late BOOLEAN DEFAULT false;    -- after 5pm

-- Clear old availability data (starting fresh per user decision)
UPDATE players SET
    available_morning = NULL,
    available_afternoon = NULL,
    available_evening = NULL;

-- =============================================================
-- PHASE 4: PERFORMANCE TRACKING (RMS - Rolling Match Score)
-- =============================================================

-- Rolling Match Score = average games won in last 3 matches
ALTER TABLE players ADD COLUMN IF NOT EXISTS rms_score DECIMAL(4,2) DEFAULT NULL;

-- Performance band (internal only, not shown to players)
-- developing (<=6), competitive (6.1-9), strong (9.1-12), dominant (>12)
ALTER TABLE players ADD COLUMN IF NOT EXISTS rms_band VARCHAR(20) DEFAULT NULL;

-- =============================================================
-- PHASE 5: MATCH TABLE ENHANCEMENT (Set 3)
-- =============================================================

-- Add set 3 columns if they don't exist
ALTER TABLE matches ADD COLUMN IF NOT EXISTS set3_p1 INTEGER CHECK (set3_p1 >= 0 AND set3_p1 <= 7);
ALTER TABLE matches ADD COLUMN IF NOT EXISTS set3_p2 INTEGER CHECK (set3_p2 >= 0 AND set3_p2 <= 7);

-- =============================================================
-- PHASE 6: ADMIN UPDATES
-- =============================================================

-- Make Natalie an admin
UPDATE players SET is_admin = true WHERE email = 'nmcoffen@gmail.com';

-- Verify admins
SELECT name, email, is_admin FROM players WHERE is_admin = true;

-- =============================================================
-- PHASE 7: RMS CALCULATION FUNCTION
-- =============================================================

-- Function to calculate RMS for a player
CREATE OR REPLACE FUNCTION calculate_player_rms(player_uuid UUID)
RETURNS DECIMAL(4,2) AS $$
DECLARE
    rms DECIMAL(4,2);
BEGIN
    SELECT AVG(games_won)::DECIMAL(4,2) INTO rms
    FROM (
        SELECT
            CASE
                WHEN player1_id = player_uuid THEN player1_games
                WHEN player2_id = player_uuid THEN player2_games
            END as games_won
        FROM matches
        WHERE (player1_id = player_uuid OR player2_id = player_uuid)
        ORDER BY created_at DESC
        LIMIT 3
    ) recent_matches
    WHERE games_won IS NOT NULL;

    RETURN rms;
END;
$$ LANGUAGE plpgsql;

-- Function to determine performance band
CREATE OR REPLACE FUNCTION get_rms_band(rms DECIMAL(4,2))
RETURNS VARCHAR(20) AS $$
BEGIN
    IF rms IS NULL THEN
        RETURN NULL;
    ELSIF rms <= 6 THEN
        RETURN 'developing';
    ELSIF rms <= 9 THEN
        RETURN 'competitive';
    ELSIF rms <= 12 THEN
        RETURN 'strong';
    ELSE
        RETURN 'dominant';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to update RMS for a player
CREATE OR REPLACE FUNCTION update_player_rms(player_uuid UUID)
RETURNS void AS $$
DECLARE
    new_rms DECIMAL(4,2);
BEGIN
    new_rms := calculate_player_rms(player_uuid);

    UPDATE players SET
        rms_score = new_rms,
        rms_band = get_rms_band(new_rms)
    WHERE id = player_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to update RMS for all active players
CREATE OR REPLACE FUNCTION update_all_rms()
RETURNS void AS $$
DECLARE
    player_record RECORD;
BEGIN
    FOR player_record IN
        SELECT id FROM players WHERE is_active = true AND is_admin = false
    LOOP
        PERFORM update_player_rms(player_record.id);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update RMS when match is reported
CREATE OR REPLACE FUNCTION trigger_update_rms()
RETURNS TRIGGER AS $$
BEGIN
    -- Update RMS for both players after match is recorded
    PERFORM update_player_rms(NEW.player1_id);
    PERFORM update_player_rms(NEW.player2_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_match_rms ON matches;

-- Create new trigger
CREATE TRIGGER trigger_match_rms
    AFTER INSERT ON matches
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_rms();

-- =============================================================
-- PHASE 8: UPDATE MATCHING VIEW TO INCLUDE TIER
-- =============================================================

-- Drop and recreate the player_match_compatibility view to include tier
DROP VIEW IF EXISTS player_match_compatibility;

CREATE OR REPLACE VIEW player_match_compatibility AS
SELECT
    p1.id as player1_id,
    p1.name as player1_name,
    p1.membership_tier as player1_tier,
    p1.rms_band as player1_band,
    p2.id as player2_id,
    p2.name as player2_name,
    p2.membership_tier as player2_tier,
    p2.rms_band as player2_band,
    -- Skill difference (lower = better match)
    ABS(
        CASE
            WHEN p1.skill_level LIKE '4.5%' THEN 4.5
            WHEN p1.skill_level LIKE '4.0%' THEN 4.0
            WHEN p1.skill_level LIKE '3.5+%' THEN 3.75
            WHEN p1.skill_level LIKE '3.5%' THEN 3.5
            ELSE 3.0
        END -
        CASE
            WHEN p2.skill_level LIKE '4.5%' THEN 4.5
            WHEN p2.skill_level LIKE '4.0%' THEN 4.0
            WHEN p2.skill_level LIKE '3.5+%' THEN 3.75
            WHEN p2.skill_level LIKE '3.5%' THEN 3.5
            ELSE 3.0
        END
    ) as skill_diff,
    -- How many times they've played
    (SELECT COUNT(*) FROM matches m
     WHERE (m.player1_id = p1.id AND m.player2_id = p2.id)
        OR (m.player1_id = p2.id AND m.player2_id = p1.id)
    ) as times_played,
    -- Is this pair blocked?
    EXISTS (
        SELECT 1 FROM blocked_pairs bp
        WHERE (bp.player_a = LEAST(p1.id, p2.id) AND bp.player_b = GREATEST(p1.id, p2.id))
    ) as is_blocked,
    -- Same RMS band? (for band-based matching)
    (p1.rms_band = p2.rms_band) as same_band
FROM players p1
CROSS JOIN players p2
WHERE p1.id < p2.id  -- Avoid duplicates
  AND p1.is_active = true
  AND p2.is_active = true
  AND p1.is_admin = false
  AND p2.is_admin = false
  AND p1.membership_tier = 'player'  -- Only match players, not social butterflies
  AND p2.membership_tier = 'player';

-- =============================================================
-- PHASE 9: CALCULATE INITIAL RMS FOR ALL PLAYERS
-- =============================================================

-- Run this to populate RMS for all players based on existing match data
SELECT update_all_rms();

-- =============================================================
-- VERIFICATION
-- =============================================================

-- Check new columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'players'
AND column_name IN (
    'membership_tier',
    'avatar_url',
    'favorite_players',
    'avail_weekday_early',
    'avail_weekday_day',
    'avail_weekday_late',
    'avail_weekend_early',
    'avail_weekend_day',
    'avail_weekend_late',
    'rms_score',
    'rms_band'
);

-- Check players with RMS calculated
SELECT name, total_games, rms_score, rms_band
FROM players
WHERE is_admin = false
ORDER BY rms_score DESC NULLS LAST
LIMIT 10;

-- Check admins
SELECT name, email, is_admin FROM players WHERE is_admin = true;
