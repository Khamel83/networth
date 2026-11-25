"""
League months the organizers have explicitly switched off.

A month with no pairings is a production incident unless that exact month is
listed here. Add a month only on an organizer's explicit decision, and record
the decision in RUNBOOK.md. Workflows read this list from GET /api/email so
that the site, the watchdog, and GitHub Actions cannot disagree.
"""
from datetime import datetime

# Organizer decision, November 2026: no December matches; the
# league restarts with January 2027 pairings.
PAUSED_PERIODS = frozenset({'December 2026'})


def is_paused_period(period_label):
    return period_label in PAUSED_PERIODS


def next_period(period_label):
    parsed = datetime.strptime(period_label, '%B %Y')
    year, month = (parsed.year + 1, 1) if parsed.month == 12 else (parsed.year, parsed.month + 1)
    return datetime(year, month, 1).strftime('%B %Y')


# League emails about the following month (availability questions) and about
# the current month (mid-month reminders). Pairings are refused in pairings.py.
NEXT_MONTH_EMAIL_ACTIONS = frozenset({
    'send_availability_check',
    'send_availability_check_paused_only',
    'send_final_reminder',
})
SAME_MONTH_EMAIL_ACTIONS = frozenset({'send_midmonth_reminders'})


def paused_month_for_league_email(action, period_label):
    """Return the paused month a league email would be about, or None.

    ``period_label`` is the month the job runs in, e.g. "November 2026".
    Raises ValueError when it is not in that form.
    """
    if action in NEXT_MONTH_EMAIL_ACTIONS:
        month = next_period(period_label)
    elif action in SAME_MONTH_EMAIL_ACTIONS:
        month = datetime.strptime(period_label, '%B %Y').strftime('%B %Y')
    else:
        return None
    return month if is_paused_period(month) else None
