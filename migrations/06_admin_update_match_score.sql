-- Atomic admin score correction.
-- The update_player_games() trigger only runs on INSERT, so correcting a
-- score must also move both players' total_games by the difference. Doing
-- that as separate REST writes can't be all-or-nothing; this function does
-- the match update and both total adjustments in one transaction, with the
-- match row locked so concurrent edits serialize.
-- api/admin.py calls it via /rest/v1/rpc and falls back to guarded REST
-- writes until this migration is applied. Safe to re-run.

CREATE OR REPLACE FUNCTION public.admin_update_match_score(
    p_match_id UUID,
    p_set1_p1 INT, p_set1_p2 INT,
    p_set2_p1 INT, p_set2_p2 INT
) RETURNS matches
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    old_row matches;
    new_row matches;
    old_p1 INT;
    old_p2 INT;
    new_p1 INT := p_set1_p1 + p_set2_p1;
    new_p2 INT := p_set1_p2 + p_set2_p2;
BEGIN
    IF LEAST(p_set1_p1, p_set1_p2, p_set2_p1, p_set2_p2) < 0
       OR GREATEST(p_set1_p1, p_set1_p2, p_set2_p1, p_set2_p2) > 7
       OR (p_set1_p1 + p_set1_p2 + p_set2_p1 + p_set2_p2) = 0 THEN
        RAISE EXCEPTION 'invalid set scores' USING ERRCODE = '22023';
    END IF;

    SELECT * INTO old_row FROM matches WHERE id = p_match_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'match not found' USING ERRCODE = 'P0002';
    END IF;

    -- What the INSERT trigger credited originally (forfeit = 6 to player 1)
    IF old_row.is_forfeit THEN
        old_p1 := 6; old_p2 := 0;
    ELSE
        old_p1 := COALESCE(old_row.player1_games, 0);
        old_p2 := COALESCE(old_row.player2_games, 0);
    END IF;

    UPDATE matches SET
        set1_p1 = p_set1_p1, set1_p2 = p_set1_p2,
        set2_p1 = p_set2_p1, set2_p2 = p_set2_p2,
        player1_games = new_p1, player2_games = new_p2,
        is_forfeit = FALSE
    WHERE id = p_match_id
    RETURNING * INTO new_row;

    UPDATE players SET total_games = GREATEST(COALESCE(total_games, 0) + (new_p1 - old_p1), 0), updated_at = NOW()
    WHERE id = old_row.player1_id;
    UPDATE players SET total_games = GREATEST(COALESCE(total_games, 0) + (new_p2 - old_p2), 0), updated_at = NOW()
    WHERE id = old_row.player2_id;

    RETURN new_row;
END;
$$;

-- Server-side only (service role); never callable with the public anon key
REVOKE ALL ON FUNCTION public.admin_update_match_score(UUID, INT, INT, INT, INT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_update_match_score(UUID, INT, INT, INT, INT) TO service_role;
