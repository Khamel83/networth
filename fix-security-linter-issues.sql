-- =============================================================
-- FIX SUPABASE SECURITY LINTER ISSUES
-- Run this in Supabase SQL Editor to fix security warnings
-- =============================================================

-- =============================================================
-- 1. FIX SECURITY DEFINER VIEW (ERROR)
-- Drop and recreate blocked_pairs view without SECURITY DEFINER
-- =============================================================

DROP VIEW IF EXISTS blocked_pairs CASCADE;

CREATE VIEW blocked_pairs AS
SELECT DISTINCT
    LEAST(from_player_id, about_player_id) as player_a,
    GREATEST(from_player_id, about_player_id) as player_b
FROM match_feedback
WHERE would_play_again = false;

-- =============================================================
-- 2. FIX FUNCTION SEARCH_PATH ISSUES (WARN)
-- Add search_path protection to all functions to prevent
-- search path injection attacks
-- =============================================================

-- Fix recalculate_rankings function
CREATE OR REPLACE FUNCTION recalculate_rankings()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    WITH ranked AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY total_games DESC, name ASC) as new_rank
        FROM public.players
        WHERE is_active = true AND is_admin = false
    )
    UPDATE public.players p
    SET rank = r.new_rank
    FROM ranked r
    WHERE p.id = r.id;
END;
$$;

-- Fix update_player_games function
CREATE OR REPLACE FUNCTION update_player_games()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Handle forfeits: winner gets 6, loser gets 0
    IF NEW.is_forfeit THEN
        -- player1 is winner for forfeits
        UPDATE public.players SET
            total_games = total_games + 6,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player1_id;

        UPDATE public.players SET
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player2_id;
    ELSE
        -- Normal match: add actual games won
        UPDATE public.players SET
            total_games = total_games + NEW.player1_games,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player1_id;

        UPDATE public.players SET
            total_games = total_games + NEW.player2_games,
            matches_played = matches_played + 1,
            updated_at = NOW()
        WHERE id = NEW.player2_id;
    END IF;

    -- Recalculate rankings
    PERFORM public.recalculate_rankings();
    RETURN NEW;
END;
$$;

-- Fix update_player_rankings function (if it exists)
-- This function may have been created separately
CREATE OR REPLACE FUNCTION update_player_rankings()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    PERFORM public.recalculate_rankings();
    RETURN NEW;
END;
$$;

-- Fix update_updated_at function (common timestamp trigger)
-- This function is typically used for automatically updating updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- =============================================================
-- VERIFY FIXES
-- =============================================================

-- Check that blocked_pairs view exists and works
SELECT COUNT(*) as blocked_pair_count FROM blocked_pairs;

-- Verify functions have search_path set
SELECT
    routine_name,
    routine_type,
    security_type,
    external_language
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN ('recalculate_rankings', 'update_player_games', 'update_player_rankings', 'update_updated_at')
ORDER BY routine_name;

-- Test that rankings still work
SELECT rank, name, total_games, matches_played
FROM players
WHERE is_admin = false
ORDER BY rank
LIMIT 10;
