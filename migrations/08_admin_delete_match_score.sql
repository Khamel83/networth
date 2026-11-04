-- Atomic admin score removal (the match itself is the "score": the pairing stays).
-- Deleting a match row alone would leave both players' total_games and
-- matches_played inflated and the pairing marked completed. This function, in
-- one row-locked transaction:
--   1. takes back what the INSERT trigger credited (forfeit = 6 to player 1),
--   2. deletes the match (match_feedback rows cascade),
--   3. reopens the pairing for that pair + month so a score can be entered again,
--   4. recalculates rankings.
-- api/admin.py calls it via /rest/v1/rpc (action delete_score). There is no
-- fallback: until this is applied, delete returns 503 and changes nothing.
-- Safe to re-run.

CREATE OR REPLACE FUNCTION public.admin_delete_match_score(
    p_match_id UUID
) RETURNS matches
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    old_row matches;
    old_p1 INT;
    old_p2 INT;
BEGIN
    SELECT * INTO old_row FROM matches WHERE id = p_match_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'match not found' USING ERRCODE = 'P0002';
    END IF;

    IF old_row.is_forfeit THEN
        old_p1 := 6; old_p2 := 0;
    ELSE
        old_p1 := COALESCE(old_row.player1_games, 0);
        old_p2 := COALESCE(old_row.player2_games, 0);
    END IF;

    UPDATE players SET
        total_games = GREATEST(COALESCE(total_games, 0) - old_p1, 0),
        matches_played = GREATEST(COALESCE(matches_played, 0) - 1, 0),
        updated_at = NOW()
    WHERE id = old_row.player1_id;
    UPDATE players SET
        total_games = GREATEST(COALESCE(total_games, 0) - old_p2, 0),
        matches_played = GREATEST(COALESCE(matches_played, 0) - 1, 0),
        updated_at = NOW()
    WHERE id = old_row.player2_id;

    -- Reopen the pairing that this match closed
    UPDATE match_assignments
    SET status = 'pending', match_id = NULL
    WHERE match_id = old_row.id
       OR (period_label = old_row.period_label
           AND status = 'completed'
           AND LEAST(player1_id, player2_id) = LEAST(old_row.player1_id, old_row.player2_id)
           AND GREATEST(player1_id, player2_id) = GREATEST(old_row.player1_id, old_row.player2_id));

    DELETE FROM matches WHERE id = p_match_id;

    PERFORM recalculate_rankings();
    RETURN old_row;
END;
$$;

-- Server-side only (service role); never callable with the public anon key
REVOKE ALL ON FUNCTION public.admin_delete_match_score(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_delete_match_score(UUID) TO service_role;
