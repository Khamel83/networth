-- Close a pairing in the same transaction that records its match.
-- The API also closes the pairing after inserting a match, but that is a
-- second request; if it failed, the pairing stayed "pending" until someone
-- retried. This trigger makes insert + close atomic. The API's own close is
-- then a harmless no-op. Safe to re-run.

-- The API and reconcile_month already write match_assignments.match_id, but
-- the base schema file doesn't declare it. Make sure it exists before the
-- trigger relies on it (no-op if it's already there).
ALTER TABLE match_assignments
    ADD COLUMN IF NOT EXISTS match_id UUID REFERENCES matches(id) ON DELETE SET NULL;

CREATE OR REPLACE FUNCTION public.close_pairing_for_match()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    UPDATE match_assignments
    SET status = 'completed',
        match_id = NEW.id
    WHERE period_label = NEW.period_label
      AND status <> 'completed'
      AND LEAST(player1_id, player2_id) = LEAST(NEW.player1_id, NEW.player2_id)
      AND GREATEST(player1_id, player2_id) = GREATEST(NEW.player1_id, NEW.player2_id);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trigger_close_pairing_for_match ON matches;
CREATE TRIGGER trigger_close_pairing_for_match
    AFTER INSERT ON matches
    FOR EACH ROW
    EXECUTE FUNCTION public.close_pairing_for_match();
