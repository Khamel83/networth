"""
League months the organizers have explicitly switched off.

A month with no pairings is a production incident unless that exact month is
listed here. Add a month only on an organizer's explicit decision, and record
the decision in RUNBOOK.md. Workflows read this list from GET /api/email so
that the site, the watchdog, and GitHub Actions cannot disagree.
"""
from datetime import datetime

# Ashley Kaufman and Omar Zoheri, November 2026: no December matches; the
# league restarts with January 2027 pairings.
PAUSED_PERIODS = frozenset({'December 2026'})


def is_paused_period(period_label):
    return period_label in PAUSED_PERIODS


def next_period(period_label):
    parsed = datetime.strptime(period_label, '%B %Y')
    year, month = (parsed.year + 1, 1) if parsed.month == 12 else (parsed.year, parsed.month + 1)
    return datetime(year, month, 1).strftime('%B %Y')


def paused_periods_before(period_label):
    """Count listed pauses earlier than this month; unparseable labels count none."""
    try:
        target = datetime.strptime(period_label, '%B %Y')
    except (TypeError, ValueError):
        return 0
    return sum(datetime.strptime(paused, '%B %Y') < target for paused in PAUSED_PERIODS)
