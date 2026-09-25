-- Self-reported payment from the join page's "I've sent my $X to Natalie" checkbox.
-- Separate from has_paid, which stays the admin-verified Venmo check.
-- Safe to re-run. Until this is applied, signup still works (the flag is
-- written in a best-effort follow-up update) and the report shows it as unknown.

ALTER TABLE players ADD COLUMN IF NOT EXISTS reported_paid BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS reported_paid_at TIMESTAMPTZ;
