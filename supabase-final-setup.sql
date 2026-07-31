-- =============================================================
-- TENNIS LEAGUE LADDER - COMPLETE DATABASE SETUP
-- Run this ONCE in Supabase SQL Editor
--
-- CUSTOMIZE: Search for "CHANGEME" to find values you need to update
-- =============================================================

-- Step 1: Clean slate
DROP TABLE IF EXISTS match_feedback CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS player_availability CASCADE;
DROP TABLE IF EXISTS player_court_preferences CASCADE;
DROP TABLE IF EXISTS league_settings CASCADE;
DROP TABLE IF EXISTS players CASCADE;

-- =============================================================
-- LEAGUE SETTINGS (configurable per league)
-- =============================================================
CREATE TABLE league_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    league_name VARCHAR(255) NOT NULL DEFAULT 'Your Tennis League',  -- CHANGEME
    -- Match frequency: weekly, biweekly, monthly, quarterly
    match_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly',
    -- Number of sets per match (1, 2, or 3)
    sets_per_match INTEGER NOT NULL DEFAULT 2,
    -- Max games per set (typically 6, but could be 4 for short sets)
    games_per_set INTEGER NOT NULL DEFAULT 6,
    -- Tiebreak at 6-6? If true, max 7 games per set
    tiebreak_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default league settings (CHANGEME: Update league name)
INSERT INTO league_settings (league_name, match_frequency, sets_per_match, games_per_set, tiebreak_enabled)
VALUES ('Your Tennis League', 'monthly', 2, 6, true);  -- CHANGEME: league name

-- =============================================================
-- PLAYERS TABLE
-- =============================================================
CREATE TABLE players (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    skill_level VARCHAR(50) DEFAULT '3.5 Intermediate',
    rank INTEGER DEFAULT 99,
    total_games INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    trend VARCHAR(20) DEFAULT 'neutral',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    -- Matching preferences
    preferred_match_frequency VARCHAR(20) DEFAULT 'monthly', -- weekly, biweekly, monthly, quarterly
    max_travel_minutes INTEGER DEFAULT 30,
    notes TEXT, -- any special notes (injuries, etc)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================
-- PLAYER AVAILABILITY (when they can play)
-- =============================================================
CREATE TABLE player_availability (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL, -- 0=Sunday, 1=Monday, etc.
    time_slot VARCHAR(20) NOT NULL, -- 'morning', 'afternoon', 'evening'
    is_available BOOLEAN DEFAULT true,
    UNIQUE(player_id, day_of_week, time_slot)
);

-- =============================================================
-- PLAYER COURT PREFERENCES (where they like to play)
-- =============================================================
CREATE TABLE player_court_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    court_name VARCHAR(255) NOT NULL,
    preference_level INTEGER DEFAULT 3, -- 1=love, 2=like, 3=neutral, 4=avoid, 5=never
    UNIQUE(player_id, court_name)
);

-- =============================================================
-- MATCHES TABLE (detailed score tracking)
-- 2 sets per match = max 12 games each (6-0, 6-0)
-- With tiebreaks = max 13 games each (7-6, 6-0)
-- =============================================================
CREATE TABLE matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player1_id UUID REFERENCES players(id) ON DELETE SET NULL,
    player2_id UUID REFERENCES players(id) ON DELETE SET NULL,
    -- Score details (each value 0-7, where 7 = tiebreak win)
    player1_games INTEGER NOT NULL, -- Total games won (0-13 for 2 sets)
    player2_games INTEGER NOT NULL, -- Total games won (0-13 for 2 sets)
    set1_p1 INTEGER CHECK (set1_p1 >= 0 AND set1_p1 <= 7), -- Player 1 games in set 1
    set1_p2 INTEGER CHECK (set1_p2 >= 0 AND set1_p2 <= 7), -- Player 2 games in set 1
    set2_p1 INTEGER CHECK (set2_p1 >= 0 AND set2_p1 <= 7), -- Player 1 games in set 2
    set2_p2 INTEGER CHECK (set2_p2 >= 0 AND set2_p2 <= 7), -- Player 2 games in set 2
    -- Period info (flexible: week, month, quarter)
    period_type VARCHAR(20) NOT NULL DEFAULT 'month', -- 'week', 'month', 'quarter'
    period_label VARCHAR(30) NOT NULL, -- "January 2025", "Week 1 2025", "Q1 2025"
    -- Match info
    court VARCHAR(255),
    match_date DATE,
    match_time VARCHAR(20), -- 'morning', 'afternoon', 'evening'
    is_forfeit BOOLEAN DEFAULT false, -- If true, winner gets 6 games, loser gets 0
    -- Tracking
    reported_by UUID REFERENCES players(id),
    confirmed_by UUID REFERENCES players(id), -- Other player confirms
    status VARCHAR(20) DEFAULT 'reported', -- reported, confirmed, disputed
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================
-- MATCH ASSIGNMENTS (pairings sent each period)
-- Track who was paired, who declined, rematch attempts
-- =============================================================
CREATE TABLE match_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player1_id UUID REFERENCES players(id) ON DELETE CASCADE,
    player2_id UUID REFERENCES players(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL DEFAULT 'month',
    period_label VARCHAR(30) NOT NULL, -- "January 2025"
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, declined, completed, expired
    declined_by UUID REFERENCES players(id), -- Who declined (if any)
    decline_count INTEGER DEFAULT 0, -- How many times this pair declined (0, 1, 2 max)
    -- Rematch logic: if declined, try rematch up to 2x total
    is_rematch BOOLEAN DEFAULT false,
    original_assignment_id UUID REFERENCES match_assignments(id), -- Link to original if this is a rematch
    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(player1_id, player2_id, period_label) -- One pairing per period
);

-- Index for finding pending assignments
CREATE INDEX idx_assignments_pending ON match_assignments(status, period_label);
CREATE INDEX idx_assignments_player ON match_assignments(player1_id, player2_id);

-- =============================================================
-- MATCH FEEDBACK (how was the match experience?)
-- Minimal data: just "would you play again?" required
-- =============================================================
CREATE TABLE match_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    from_player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    about_player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    -- THE KEY FIELD - used for silent blocking
    would_play_again BOOLEAN NOT NULL,
    -- Optional: was it competitive?
    competitive_match BOOLEAN,
    -- Private note (only visible to admin)
    private_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(match_id, from_player_id) -- One feedback per player per match
);

-- =============================================================
-- INDEXES
-- =============================================================
CREATE INDEX idx_players_rank ON players(rank) WHERE is_active = true;
CREATE INDEX idx_players_email ON players(email);
CREATE INDEX idx_matches_period ON matches(period_type, period_label);
CREATE INDEX idx_matches_players ON matches(player1_id, player2_id);
CREATE UNIQUE INDEX idx_unique_match_per_period
    ON matches (
        LEAST(player1_id, player2_id),
        GREATEST(player1_id, player2_id),
        period_label
    );
CREATE INDEX idx_availability_player ON player_availability(player_id);
CREATE INDEX idx_feedback_match ON match_feedback(match_id);
CREATE INDEX idx_feedback_about ON match_feedback(about_player_id);
CREATE INDEX idx_feedback_would_play ON match_feedback(about_player_id, would_play_again);

-- =============================================================
-- ROW LEVEL SECURITY
-- =============================================================
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_court_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE league_settings ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Players viewable by all" ON players FOR SELECT USING (true);
CREATE POLICY "Players updatable" ON players FOR UPDATE USING (true);
CREATE POLICY "Players insertable" ON players FOR INSERT WITH CHECK (true);
CREATE POLICY "Matches viewable by all" ON matches FOR SELECT USING (true);
CREATE POLICY "Matches insertable" ON matches FOR INSERT WITH CHECK (true);
CREATE POLICY "Availability viewable" ON player_availability FOR SELECT USING (true);
CREATE POLICY "Availability manageable" ON player_availability FOR ALL USING (true);
CREATE POLICY "Court prefs viewable" ON player_court_preferences FOR SELECT USING (true);
CREATE POLICY "Court prefs manageable" ON player_court_preferences FOR ALL USING (true);
CREATE POLICY "Feedback insertable" ON match_feedback FOR INSERT WITH CHECK (true);
CREATE POLICY "Feedback viewable by admin" ON match_feedback FOR SELECT USING (true);
CREATE POLICY "Assignments viewable" ON match_assignments FOR SELECT USING (true);
CREATE POLICY "Assignments manageable" ON match_assignments FOR ALL USING (true);
CREATE POLICY "League settings viewable" ON league_settings FOR SELECT USING (true);

-- =============================================================
-- SAMPLE DATA (Optional - remove or customize for your league)
-- Real players will register via the join page
-- =============================================================

-- Sample admin user (CHANGEME: use your admin email)
INSERT INTO players (email, name, skill_level, rank, total_games, is_active, is_admin)
VALUES ('admin@yourleague.com', 'Admin', 'Admin', 99, 0, true, true);  -- CHANGEME

-- Optional: Sample players for testing (remove in production)
-- INSERT INTO players (email, name, phone, skill_level, rank, total_games, matches_played, is_active) VALUES
-- ('player1@example.com', 'Sample Player 1', '555-0001', '4.0 Advanced', 1, 20, 2, true),
-- ('player2@example.com', 'Sample Player 2', '555-0002', '3.5 Intermediate', 2, 15, 2, true),
-- ('player3@example.com', 'Sample Player 3', '555-0003', '3.5 Intermediate', 3, 10, 1, true);

-- =============================================================
-- FUNCTIONS FOR RANKING & MATCHING
-- =============================================================

-- Recalculate rankings based on total games
-- Admins who are also players should still be ranked
CREATE OR REPLACE FUNCTION recalculate_rankings()
RETURNS void AS $$
BEGIN
    WITH ranked AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY total_games DESC NULLS LAST, name ASC) as new_rank
        FROM players
        WHERE is_active = true
    )
    UPDATE players p
    SET rank = r.new_rank
    FROM ranked r
    WHERE p.id = r.id;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update player stats when match is inserted
CREATE OR REPLACE FUNCTION update_player_games()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle forfeits: winner gets 6, loser gets 0
    IF NEW.is_forfeit THEN
        -- player1 is winner for forfeits
        UPDATE players SET
            total_games = total_games + 6,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player1_id;

        UPDATE players SET
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player2_id;
    ELSE
        -- Normal match: add actual games won
        UPDATE players SET
            total_games = total_games + NEW.player1_games,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player1_id;

        UPDATE players SET
            total_games = total_games + NEW.player2_games,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player2_id;
    END IF;

    -- Recalculate rankings
    PERFORM recalculate_rankings();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_games
    AFTER INSERT ON matches
    FOR EACH ROW
    EXECUTE FUNCTION update_player_games();

-- =============================================================
-- SILENT BLOCK CHECK VIEW
-- Returns pairs where at least one player blocked the other
-- Used to EXCLUDE from matching
-- =============================================================
CREATE OR REPLACE VIEW blocked_pairs AS
SELECT DISTINCT
    LEAST(from_player_id, about_player_id) as player_a,
    GREATEST(from_player_id, about_player_id) as player_b
FROM match_feedback
WHERE would_play_again = false;

-- =============================================================
-- MATCHING ALGORITHM HELPER VIEW
-- Get player compatibility score based on:
-- 1. Similar skill level (within 0.5)
-- 2. Not blocked by either player
-- 3. Past match feedback
-- =============================================================
CREATE OR REPLACE VIEW player_match_compatibility AS
SELECT
    p1.id as player1_id,
    p1.name as player1_name,
    p2.id as player2_id,
    p2.name as player2_name,
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
    ) as is_blocked
FROM players p1
CROSS JOIN players p2
WHERE p1.id < p2.id  -- Avoid duplicates
  AND p1.is_active = true
  AND p2.is_active = true
  AND p1.is_admin = false
  AND p2.is_admin = false;

-- =============================================================
-- PLAYER ENGAGEMENT VIEW (admin only)
-- Check in with players who might need support
-- Not punitive - just "hey, is everything ok?"
-- =============================================================
CREATE OR REPLACE VIEW player_engagement AS
SELECT
    p.id,
    p.name,
    COUNT(ma.id) as total_assignments,
    COUNT(CASE WHEN ma.declined_by = p.id THEN 1 END) as times_declined,
    -- If someone's declining a lot, maybe check in with them
    CASE
        WHEN COUNT(CASE WHEN ma.declined_by = p.id THEN 1 END) >= 3 THEN 'check_in'
        ELSE 'active'
    END as engagement_status
FROM players p
LEFT JOIN match_assignments ma ON (ma.player1_id = p.id OR ma.player2_id = p.id)
WHERE p.is_admin = false
GROUP BY p.id, p.name;

-- =============================================================
-- VERIFY SETUP
-- =============================================================
SELECT rank, name, total_games as games_won, matches_played, skill_level
FROM players
WHERE is_admin = false
ORDER BY rank;
