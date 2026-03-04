-- Reliability automation tables and guardrails
-- Run in Supabase SQL editor after 01_security_fixes.sql

-- -----------------------------------------------------------------------------
-- Automation run tracking
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS automation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(80) NOT NULL,
    period_label VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN (
        'running',
        'succeeded',
        'failed_terminal',
        'preflight_failed',
        'postcheck_failed',
        'repairing',
        'repaired'
    )),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    summary_json JSONB DEFAULT '{}'::jsonb,
    error_json JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_automation_runs_action_period
    ON automation_runs(action, period_label, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_automation_runs_status
    ON automation_runs(status, started_at DESC);

-- -----------------------------------------------------------------------------
-- Automation event log
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS automation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES automation_runs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    message TEXT NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_automation_events_run
    ON automation_events(run_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_automation_events_severity
    ON automation_events(severity, created_at DESC);

-- -----------------------------------------------------------------------------
-- Email delivery log (for non-silent delivery failures)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS email_delivery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES automation_runs(id) ON DELETE SET NULL,
    action VARCHAR(80) NOT NULL,
    period_label VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    template VARCHAR(80) NOT NULL,
    delivery_status VARCHAR(20) NOT NULL CHECK (delivery_status IN ('sent', 'failed')),
    provider_id VARCHAR(255),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_email_delivery_idempotency
    ON email_delivery_log(action, period_label, recipient_email, template);

CREATE INDEX IF NOT EXISTS idx_email_delivery_status
    ON email_delivery_log(delivery_status, created_at DESC);

-- -----------------------------------------------------------------------------
-- Guardrails on existing core tables
-- -----------------------------------------------------------------------------

ALTER TABLE match_assignments
    DROP CONSTRAINT IF EXISTS valid_status;

ALTER TABLE match_assignments
    ADD CONSTRAINT valid_status
    CHECK (status IN ('pending', 'accepted', 'completed', 'cancelled', 'failed'));

ALTER TABLE match_assignments
    DROP CONSTRAINT IF EXISTS valid_period_type;

ALTER TABLE match_assignments
    ADD CONSTRAINT valid_period_type
    CHECK (period_type IN ('week', 'month', 'quarter'));

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_assignment_pair_period
    ON match_assignments (
        LEAST(player1_id, player2_id),
        GREATEST(player1_id, player2_id),
        period_label
    );
