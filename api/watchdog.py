"""
Independent daily watchdog (runs on Vercel Cron, not GitHub Actions).

Checks, from the database's own records, that every scheduled job actually
happened and that no email failed. GitHub scheduled workflows can be skipped
or disabled without anyone noticing; this catches that because it looks for
the evidence each job leaves behind (an `automation_runs` row and
`email_delivery_log` rows), not for the job itself.

Problems are emailed to ADMIN_EMAIL (the owner) through Resend. On the 3rd
of each month an all-clear goes out so silence never means "the watchdog
died". Utility module: no Vercel handler, called from api/system.py.
"""
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from html import escape

# Statuses in automation_runs that mean a job did not finish cleanly
_BAD_RUN_STATUSES = {'failed_terminal', 'preflight_failed', 'postcheck_failed', 'repairing'}
_LOOKBACK_DAYS = 10


def _label(year, month):
    return datetime(year, month, 1).strftime('%B %Y')


def _previous(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def expected_jobs(today):
    """Scheduled jobs whose evidence should exist by `today` (UTC date).

    Each entry: (action, period_label, human description). Windows start
    the day after the job is scheduled (GitHub often runs hours late) and
    stop after a week so an old miss doesn't alert forever.
    """
    year, month, day = today.year, today.month, today.day
    this_month = _label(year, month)
    prev_month = _label(*_previous(year, month))
    last_day = monthrange(year, month)[1]
    jobs = []
    if 2 <= day <= 7:
        jobs.append(('generate_pairings', this_month, f'{this_month} pairings + match emails (1st)'))
        jobs.append(('send_final_reminder', prev_month, f'{prev_month} final availability reminder (last day)'))
    if 1 <= day <= 5:
        # The 27th job can run days late; keep checking last month's into this one
        jobs.append(('send_availability_check', prev_month, f'{prev_month} availability check (27th)'))
    if 3 <= day <= 9:
        jobs.append(('send_monthly_report', prev_month, f'{prev_month} report to Natalie + Ashley (2nd)'))
    if 16 <= day <= 23:
        jobs.append(('send_midmonth_reminders', this_month, f'{this_month} mid-month reminders (15th)'))
    if 28 <= day <= last_day:
        jobs.append(('send_availability_check', this_month, f'{this_month} availability check (27th)'))
    return jobs


def run_watchdog(table, now=None):
    """Return (problems, summary). `problems` is a list of plain sentences."""
    now = now or datetime.now(timezone.utc)
    today = now.date()
    this_month = _label(today.year, today.month)
    problems = []
    summary = {'checked_at': now.isoformat(), 'period': this_month}

    since = (now - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    runs = table('automation_runs').select('action,period_label,status,started_at').gte('started_at', since).execute()
    if runs.error:
        return [f"Could not read job history from the database: {runs.error}"], summary
    runs = runs.data or []

    # 1. Every job that should have run did, and finished cleanly
    for action, period, description in expected_jobs(today):
        matching = [r for r in runs if r.get('action') == action and r.get('period_label') == period]
        if not matching:
            # Older than the lookback? Check directly before calling it missing
            direct = table('automation_runs').select('status').eq('action', action).eq('period_label', period).execute()
            if direct.error:
                problems.append(f"Could not check {description}: {direct.error}")
                continue
            matching = direct.data or []
        statuses = {r.get('status') for r in matching}
        if not matching:
            problems.append(f"{description} never ran. The scheduled job may be switched off or failing before it reaches the site.")
        elif 'succeeded' not in statuses and 'repaired' not in statuses:
            problems.append(f"{description} did not finish cleanly (status: {', '.join(sorted(s or '?' for s in statuses))}).")

    # 2. Any job in the last 10 days that failed and was never retried
    #    successfully. Bounded on purpose: older failures that were fixed by
    #    hand would otherwise alert forever; step 1 covers the current cycle.
    done = {(r.get('action'), r.get('period_label')) for r in runs if r.get('status') in ('succeeded', 'repaired')}
    reported = set()
    for r in runs:
        key = (r.get('action'), r.get('period_label'))
        if r.get('status') in _BAD_RUN_STATUSES and key not in done and key not in reported:
            reported.add(key)
            problems.append(f"{key[0]} for {key[1]} ended as '{r.get('status')}' and has not been fixed.")

    # 3. This month's pairings exist and every match email was accepted
    if today.day >= 2:
        pairs = table('match_assignments').select('id').eq('period_label', this_month).execute()
        if pairs.error:
            problems.append(f"Could not read {this_month} pairings: {pairs.error}")
        else:
            count = len(pairs.data or [])
            summary['pairings'] = count
            if count == 0:
                problems.append(f"There are no {this_month} pairings. Players have not been matched this month.")
            elif today.day <= 7:
                ledger = table('email_delivery_log').select('delivery_status,message_key')\
                    .eq('action', 'generate_pairings').eq('period_label', this_month).execute()
                if ledger.error:
                    problems.append(f"Could not read {this_month} match-email records: {ledger.error}")
                else:
                    # Count each pairing once (message_key is one per pairing), so
                    # duplicate rows can't make an incomplete month look complete
                    accepted = len({
                        row.get('message_key') or f"row-{i}"
                        for i, row in enumerate(ledger.data)
                        if row.get('delivery_status') == 'accepted'
                    })
                    summary['match_emails_accepted'] = accepted
                    if accepted < count:
                        problems.append(
                            f"Only {accepted} of {count} {this_month} match emails were confirmed sent."
                        )

    # 4. Any email that failed, is in doubt, or has been stuck for a day
    ledger = table('email_delivery_log').select('action,period_label,delivery_status,created_at')\
        .gte('created_at', since).execute()
    if ledger.error:
        problems.append(f"Could not read email delivery records: {ledger.error}")
    else:
        stuck_before = (now - timedelta(days=1)).isoformat()
        bad = {}
        for row in ledger.data:
            status = row.get('delivery_status')
            if status in ('failed', 'unknown') or (status == 'pending' and (row.get('created_at') or '') < stuck_before):
                key = (row.get('action'), row.get('period_label'), status)
                bad[key] = bad.get(key, 0) + 1
        for (action, period, status), n in sorted(bad.items()):
            problems.append(f"{n} {action} email(s) for {period} are '{status}' (not confirmed delivered).")

    return problems, summary


def watchdog_email_html(problems, summary):
    """Short plain email: what's wrong and where to look."""
    if problems:
        heading = 'Something needs attention'
        body = '<ul>' + ''.join(f'<li>{escape(p)}</li>' for p in problems) + '</ul>'
        footer = ('Where to look: GitHub > Actions for the job that failed, then '
                  '<a href="https://www.networthtennis.com/admin">the admin page</a>. '
                  'RUNBOOK.md has recovery steps. This email repeats daily until fixed.')
    else:
        heading = 'All clear'
        parts = [f"{summary.get('period')}: {summary.get('pairings', 0)} pairings"]
        if 'match_emails_accepted' in summary:
            parts.append(f"{summary['match_emails_accepted']} match emails confirmed")
        body = '<p>' + escape(', '.join(parts)) + '. Every scheduled job ran.</p>'
        footer = 'Monthly check-in so you know the watchdog itself is still running.'
    return f"""
    <!DOCTYPE html>
    <html><body style="font-family: -apple-system, Segoe UI, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #d165a4;">Net Worth watchdog: {heading}</h2>
        {body}
        <p style="color: #666; font-size: 13px;">{footer}</p>
    </body></html>
    """
