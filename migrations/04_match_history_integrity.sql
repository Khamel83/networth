-- Match-history integrity for deterministic rating rebuilds.
-- Resolve any existing duplicate pair/period rows before running this migration;
-- this intentionally fails rather than deleting or guessing between records.

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_match_per_period
    ON matches (
        LEAST(player1_id, player2_id),
        GREATEST(player1_id, player2_id),
        period_label
    );
