-- Migration 04: canonical email delivery ledger and safe automation state
--
-- Review the live schema before running this migration. These are read-only
-- inventory queries; do not call an email endpoint while reviewing them.
--
-- SELECT table_name, column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name IN ('email_log', 'email_delivery_log',
--                      'automation_runs', 'automation_events')
-- ORDER BY table_name, ordinal_position;
--
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
--   AND tablename IN ('email_log', 'email_delivery_log', 'automation_runs');

BEGIN;

-- The reliability migration is normally applied first, but this hardening
-- migration is safe to run on an installation where it was skipped. Create
-- the run-lock table before declaring the ledger foreign key below.
CREATE TABLE IF NOT EXISTS public.automation_runs (
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
    ON public.automation_runs(action, period_label, started_at DESC);

CREATE TABLE IF NOT EXISTS public.automation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES public.automation_runs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    message TEXT NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_automation_events_run
    ON public.automation_events(run_id, created_at DESC);

-- The new ledger branch now works even when migration 02 was skipped.
CREATE TABLE IF NOT EXISTS public.email_delivery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES public.automation_runs(id) ON DELETE SET NULL,
    action VARCHAR(80) NOT NULL,
    period_label VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255),
    message_key VARCHAR(160),
    recipient_emails JSONB NOT NULL DEFAULT '[]'::jsonb,
    template VARCHAR(80) NOT NULL,
    delivery_status VARCHAR(20) NOT NULL,
    idempotency_key VARCHAR(255),
    provider_id VARCHAR(255),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ
);

-- The existing-table branch preserves recipient_email for historical rows and
-- adds the batch/message fields required by the new delivery contract.
ALTER TABLE public.email_delivery_log
    ADD COLUMN IF NOT EXISTS recipient_email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS message_key VARCHAR(160),
    ADD COLUMN IF NOT EXISTS recipient_emails JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMPTZ;

-- The old inline CHECK permits only sent/failed, so remove it before changing
-- legacy sent rows to the canonical accepted state.
ALTER TABLE public.email_delivery_log
    DROP CONSTRAINT IF EXISTS email_delivery_log_delivery_status_check;

UPDATE public.email_delivery_log
SET delivery_status = 'accepted'
WHERE delivery_status = 'sent';

UPDATE public.email_delivery_log
SET recipient_emails = jsonb_build_array(recipient_email)
WHERE recipient_emails = '[]'::jsonb
  AND recipient_email IS NOT NULL;

UPDATE public.email_delivery_log
SET message_key = action || ':' || period_label || ':' || id::text,
    idempotency_key = 'legacy:' || id::text,
    accepted_at = CASE
        WHEN delivery_status = 'accepted' THEN COALESCE(accepted_at, created_at)
        ELSE accepted_at
    END
WHERE message_key IS NULL OR idempotency_key IS NULL;

-- email_log is a separate legacy table in some environments. Map it only when
-- the read-only inventory proves the required columns and supported types exist.
DO $$
DECLARE
    required_columns TEXT[] := ARRAY[
        'id', 'action', 'period_label', 'to_emails', 'resend_email_id', 'sent_at'
    ];
    missing_column TEXT;
    email_data_type TEXT;
    email_udt_name TEXT;
    recipient_expression TEXT;
    recipient_first_expression TEXT;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'email_log'
    ) THEN
        SELECT column_name
        INTO missing_column
        FROM unnest(required_columns) AS required(column_name)
        WHERE NOT EXISTS (
            SELECT 1
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
              AND c.table_name = 'email_log'
              AND c.column_name = required.column_name
        )
        LIMIT 1;

        IF missing_column IS NOT NULL THEN
            RAISE EXCEPTION
                'email_log migration stopped: required column % is absent; inspect the live schema and map it explicitly',
                missing_column;
        END IF;

        SELECT data_type, udt_name
        INTO email_data_type, email_udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'email_log'
          AND column_name = 'to_emails';

        IF email_data_type = 'ARRAY' THEN
            recipient_expression := 'to_jsonb(e.to_emails)';
            recipient_first_expression := '(e.to_emails)[1]::text';
        ELSIF email_udt_name IN ('json', 'jsonb') THEN
            recipient_expression := 'e.to_emails::jsonb';
            recipient_first_expression := '(e.to_emails::jsonb ->> 0)';
        ELSIF email_data_type IN ('text', 'character varying') THEN
            recipient_expression := 'jsonb_build_array(e.to_emails::text)';
            recipient_first_expression := 'e.to_emails::text';
        ELSE
            RAISE EXCEPTION
                'email_log migration stopped: unsupported to_emails type %/%; map it explicitly before retrying',
                email_data_type, email_udt_name;
        END IF;

        EXECUTE format($sql$
            INSERT INTO public.email_delivery_log (
                action,
                period_label,
                recipient_email,
                message_key,
                recipient_emails,
                template,
                delivery_status,
                idempotency_key,
                provider_id,
                created_at,
                updated_at,
                accepted_at
            )
            SELECT
                e.action::text,
                e.period_label::text,
                %s,
                'legacy:email_log:' || e.id::text,
                %s,
                'legacy',
                'accepted',
                'legacy:email_log:' || e.id::text,
                e.resend_email_id::text,
                e.sent_at::timestamptz,
                e.sent_at::timestamptz,
                e.sent_at::timestamptz
            FROM public.email_log e
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.email_delivery_log d
                WHERE d.message_key = 'legacy:email_log:' || e.id::text
            )
        $sql$, recipient_first_expression, recipient_expression);
    END IF;
END $$;

ALTER TABLE public.email_delivery_log
    ALTER COLUMN message_key SET NOT NULL,
    ALTER COLUMN idempotency_key SET NOT NULL;

ALTER TABLE public.email_delivery_log
    ADD CONSTRAINT email_delivery_log_delivery_status_check
    CHECK (delivery_status IN ('pending', 'accepted', 'failed', 'unknown'));

DROP INDEX IF EXISTS public.idx_email_delivery_idempotency;

CREATE UNIQUE INDEX IF NOT EXISTS idx_email_delivery_message_key
    ON public.email_delivery_log(action, period_label, message_key);

CREATE INDEX IF NOT EXISTS idx_email_delivery_status
    ON public.email_delivery_log(delivery_status, created_at DESC);

-- This is the database-side run lock. Failed-terminal runs remain retryable.
CREATE UNIQUE INDEX IF NOT EXISTS idx_automation_runs_action_period_active
    ON public.automation_runs(action, period_label)
    WHERE status IN ('running', 'succeeded', 'repairing', 'repaired');

-- Public issue reporting is queued for later admin review; it is never an
-- implicit outbound-email trigger.
CREATE TABLE IF NOT EXISTS public.issue_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_email VARCHAR(255) NOT NULL DEFAULT 'Anonymous',
    reporter_name VARCHAR(255) NOT NULL DEFAULT '',
    page_path VARCHAR(500) NOT NULL DEFAULT 'Unknown',
    message TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'reviewed', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.email_delivery_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "deny_anon_email_delivery_log" ON public.email_delivery_log;
CREATE POLICY "deny_anon_email_delivery_log"
    ON public.email_delivery_log FOR ALL TO anon USING (false);

ALTER TABLE public.issue_reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "deny_anon_issue_reports" ON public.issue_reports;
CREATE POLICY "deny_anon_issue_reports"
    ON public.issue_reports FOR ALL TO anon USING (false);

COMMIT;
