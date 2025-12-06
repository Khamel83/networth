-- =============================================================
-- MIGRATION 001: SIMPLIFIED MATCHING SYSTEM
-- =============================================================
-- Changes:
-- 1. Add player availability (time of day preferences)
-- 2. Add "unavailable_until" for monthly pause feature
-- 3. Add "scheduled_month" to matches for late completion tracking
-- 4. Remove court preference constraints from matching
-- =============================================================

-- Step 1: Add new columns to players table
-- =========================================

-- Time of day availability (self-service profile)
ALTER TABLE players
ADD COLUMN IF NOT EXISTS available_morning BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS available_afternoon BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS available_evening BOOLEAN DEFAULT true;

-- Monthly pause feature: if set, player is skipped until this date passes
-- After this date, they're automatically available again (auto-reset)
ALTER TABLE players
ADD COLUMN IF NOT EXISTS unavailable_until DATE DEFAULT NULL;

-- Comment for clarity
COMMENT ON COLUMN players.unavailable_until IS
  'If set, player is excluded from matching until this date. Auto-resets (no action needed to come back).';

COMMENT ON COLUMN players.available_morning IS 'Player prefers morning matches (6am-12pm)';
COMMENT ON COLUMN players.available_afternoon IS 'Player prefers afternoon matches (12pm-6pm)';
COMMENT ON COLUMN players.available_evening IS 'Player prefers evening matches (6pm-10pm)';


-- Step 2: Add scheduled_month to match_assignments for late completion tracking
-- ==============================================================================

-- Track which month the match was ORIGINALLY scheduled for
-- vs when it was actually completed (which could be later)
ALTER TABLE match_assignments
ADD COLUMN IF NOT EXISTS match_id UUID REFERENCES matches(id) ON DELETE SET NULL;

-- Add index for finding incomplete assignments from previous months
CREATE INDEX IF NOT EXISTS idx_assignments_incomplete
ON match_assignments(period_label, status)
WHERE status IN ('pending', 'accepted');


-- Step 3: Add scheduled_period to matches table
-- ==============================================
-- This tracks which period the match was SCHEDULED for (from assignment)
-- period_label still tracks when it was COMPLETED/REPORTED

ALTER TABLE matches
ADD COLUMN IF NOT EXISTS scheduled_period VARCHAR(30),
ADD COLUMN IF NOT EXISTS assignment_id UUID REFERENCES match_assignments(id) ON DELETE SET NULL;

COMMENT ON COLUMN matches.scheduled_period IS
  'The month the match was originally scheduled for (e.g., "December 2024"), may differ from period_label if completed late';
COMMENT ON COLUMN matches.assignment_id IS
  'Links to the original match_assignment that created this pairing';


-- Step 4: Create view for player availability summary (for emails)
-- ================================================================

CREATE OR REPLACE VIEW player_availability_summary AS
SELECT
    id,
    name,
    email,
    skill_level,
    -- Build availability string for emails
    CASE
        WHEN available_morning AND available_afternoon AND available_evening
            THEN 'Any time'
        WHEN NOT available_morning AND NOT available_afternoon AND NOT available_evening
            THEN 'No times specified'
        ELSE CONCAT_WS(', ',
            CASE WHEN available_morning THEN 'Mornings' END,
            CASE WHEN available_afternoon THEN 'Afternoons' END,
            CASE WHEN available_evening THEN 'Evenings' END
        )
    END as availability_text,
    -- Is player currently available for matching?
    CASE
        WHEN unavailable_until IS NOT NULL AND unavailable_until > CURRENT_DATE
            THEN false
        ELSE is_active
    END as currently_available,
    unavailable_until
FROM players
WHERE is_admin = false;


-- Step 5: Create view for incomplete matches (across all periods)
-- ===============================================================

CREATE OR REPLACE VIEW incomplete_matches AS
SELECT
    ma.id as assignment_id,
    ma.period_label as scheduled_month,
    ma.player1_id,
    p1.name as player1_name,
    p1.email as player1_email,
    ma.player2_id,
    p2.name as player2_name,
    p2.email as player2_email,
    ma.status,
    ma.assigned_at,
    -- How old is this assignment?
    CURRENT_DATE - ma.assigned_at::date as days_since_assigned,
    -- Is this from a previous month?
    CASE
        WHEN ma.period_label != TO_CHAR(CURRENT_DATE, 'FMMonth YYYY')
            THEN true
        ELSE false
    END as is_past_month
FROM match_assignments ma
JOIN players p1 ON ma.player1_id = p1.id
JOIN players p2 ON ma.player2_id = p2.id
WHERE ma.status IN ('pending', 'accepted')
  AND ma.match_id IS NULL  -- Not yet completed
ORDER BY ma.assigned_at;


-- Step 6: Update blocked_pairs view (no changes needed, just documenting)
-- ========================================================================
-- The blocked_pairs view already exists and works correctly.
-- Matching algorithm will continue to respect blocks.


-- Step 7: Simplified matching view (skill-based only, no court constraints)
-- =========================================================================

CREATE OR REPLACE VIEW matchable_players AS
SELECT
    p.id,
    p.name,
    p.email,
    p.skill_level,
    -- Numeric skill for sorting/matching
    CASE
        WHEN p.skill_level LIKE '4.5%' THEN 4.5
        WHEN p.skill_level LIKE '4.0%' THEN 4.0
        WHEN p.skill_level LIKE '3.5+%' THEN 3.75
        WHEN p.skill_level LIKE '3.5%' THEN 3.5
        WHEN p.skill_level LIKE '3.0%' THEN 3.0
        ELSE 2.5
    END as skill_numeric,
    p.available_morning,
    p.available_afternoon,
    p.available_evening,
    p.unavailable_until
FROM players p
WHERE p.is_active = true
  AND p.is_admin = false
  -- Auto-reset: if unavailable_until has passed, they're available
  AND (p.unavailable_until IS NULL OR p.unavailable_until <= CURRENT_DATE);


-- Step 8: Function to mark player unavailable for a month
-- ========================================================

CREATE OR REPLACE FUNCTION set_player_unavailable(
    player_id_param UUID,
    until_date DATE DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    -- If no date provided, default to end of next month (skip current + next month)
    IF until_date IS NULL THEN
        until_date := (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 months')::DATE;
    END IF;

    UPDATE players
    SET unavailable_until = until_date,
        updated_at = NOW()
    WHERE id = player_id_param;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_player_unavailable IS
  'Marks a player as unavailable until a specific date. After that date, they auto-return to the pool.';


-- Step 9: Function to mark player as available again (manual override)
-- =====================================================================

CREATE OR REPLACE FUNCTION set_player_available(player_id_param UUID)
RETURNS void AS $$
BEGIN
    UPDATE players
    SET unavailable_until = NULL,
        updated_at = NOW()
    WHERE id = player_id_param;
END;
$$ LANGUAGE plpgsql;


-- Step 10: Function to link completed match to assignment
-- ========================================================

CREATE OR REPLACE FUNCTION complete_assignment(
    assignment_id_param UUID,
    match_id_param UUID
)
RETURNS void AS $$
BEGIN
    -- Update the assignment
    UPDATE match_assignments
    SET status = 'completed',
        match_id = match_id_param,
        responded_at = NOW()
    WHERE id = assignment_id_param;

    -- Update the match with the scheduled period
    UPDATE matches
    SET assignment_id = assignment_id_param,
        scheduled_period = (SELECT period_label FROM match_assignments WHERE id = assignment_id_param)
    WHERE id = match_id_param;
END;
$$ LANGUAGE plpgsql;


-- =============================================================
-- VERIFY MIGRATION
-- =============================================================

-- Show updated player structure
SELECT
    name,
    skill_level,
    available_morning,
    available_afternoon,
    available_evening,
    unavailable_until,
    is_active
FROM players
WHERE is_admin = false
ORDER BY rank
LIMIT 5;
