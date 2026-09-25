"""Independent watchdog: catches skipped/failed jobs and failed emails."""
import io
import json
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from api.watchdog import expected_jobs, run_watchdog, watchdog_email_html


class Result(SimpleNamespace):
    def execute(self):
        return self


class Query:
    def __init__(self, db, name):
        self.db, self.name, self.filters = db, name, []

    def select(self, *_args):
        return self

    def eq(self, col, val):
        self.filters.append(lambda r, c=col, v=val: str(r.get(c)) == str(v))
        return self

    def gte(self, col, val):
        self.filters.append(lambda r, c=col, v=val: str(r.get(c) or '') >= str(v))
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        if self.name in self.db.get('_errors', {}):
            return Result(data=[], error=self.db['_errors'][self.name])
        rows = [r for r in self.db.get(self.name, []) if all(f(r) for f in self.filters)]
        return Result(data=rows, error=None)


def fake(db):
    return lambda name: Query(db, name)


NOW = datetime(2026, 10, 5, 16, 0, tzinfo=timezone.utc)
RECENT = '2026-10-01T20:00:00+00:00'


def healthy_october():
    return {
        'automation_runs': [
            {'action': 'generate_pairings', 'period_label': 'October 2026', 'status': 'succeeded', 'started_at': RECENT},
            {'action': 'send_final_reminder', 'period_label': 'September 2026', 'status': 'succeeded', 'started_at': '2026-09-30T20:00:00+00:00'},
            {'action': 'send_monthly_report', 'period_label': 'September 2026', 'status': 'succeeded', 'started_at': '2026-10-02T19:00:00+00:00'},
            {'action': 'send_availability_check', 'period_label': 'September 2026', 'status': 'succeeded', 'started_at': '2026-09-27T20:00:00+00:00'},
        ],
        'match_assignments': [{'id': 1, 'period_label': 'October 2026'}, {'id': 2, 'period_label': 'October 2026'}],
        'email_delivery_log': [
            {'action': 'generate_pairings', 'period_label': 'October 2026', 'delivery_status': 'accepted',
             'message_key': 'generate_pairings:October 2026:1', 'created_at': RECENT},
            {'action': 'generate_pairings', 'period_label': 'October 2026', 'delivery_status': 'accepted',
             'message_key': 'generate_pairings:October 2026:2', 'created_at': RECENT},
        ],
    }


def test_healthy_month_has_no_problems():
    problems, summary = run_watchdog(fake(healthy_october()), now=NOW)
    assert problems == []
    assert summary['pairings'] == 2
    assert summary['match_emails_accepted'] == 2


def test_skipped_pairing_job_is_caught_even_with_github_silent():
    db = healthy_october()
    db['automation_runs'] = [r for r in db['automation_runs'] if r['action'] != 'generate_pairings']
    db['match_assignments'] = []
    db['email_delivery_log'] = []
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert any('October 2026 pairings + match emails (1st) never ran' in p for p in problems)
    assert any('no October 2026 pairings' in p for p in problems)


def test_unconfirmed_match_emails_are_caught():
    db = healthy_october()
    db['email_delivery_log'][1]['delivery_status'] = 'unknown'
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert any('Only 1 of 2 October 2026 match emails' in p for p in problems)
    assert any("'unknown'" in p for p in problems)


def test_failed_job_that_was_retried_successfully_is_not_reported():
    db = healthy_october()
    db['automation_runs'].append({'action': 'generate_pairings', 'period_label': 'October 2026',
                                  'status': 'failed_terminal', 'started_at': '2026-10-01T18:00:00+00:00'})
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert problems == []


def test_failed_job_never_fixed_is_reported():
    db = healthy_october()
    db['automation_runs'][2]['status'] = 'failed_terminal'
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert any('September 2026 report to Natalie + Ashley (2nd) did not finish cleanly' in p for p in problems)


def test_missing_availability_email_caught_after_the_27th():
    db = healthy_october()
    problems, _ = run_watchdog(fake(db), now=datetime(2026, 10, 29, 16, tzinfo=timezone.utc))
    assert any('October 2026 availability check (27th) never ran' in p for p in problems)


def test_expected_jobs_windows():
    names = lambda d: {a for a, _, _ in expected_jobs(d)}
    assert names(datetime(2026, 10, 1).date()) == {'send_availability_check'}
    assert names(datetime(2026, 10, 2).date()) == {'generate_pairings', 'send_final_reminder', 'send_availability_check'}
    assert names(datetime(2026, 10, 6).date()) == {'generate_pairings', 'send_final_reminder', 'send_monthly_report'}
    assert 'send_monthly_report' in names(datetime(2026, 10, 3).date())
    assert names(datetime(2026, 10, 16).date()) == {'send_midmonth_reminders'}
    assert names(datetime(2026, 2, 28).date()) == {'send_availability_check'}
    assert names(datetime(2026, 10, 12).date()) == set()
    # January looks back to December of the previous year
    jan = {(a, p) for a, p, _ in expected_jobs(datetime(2027, 1, 4).date())}
    assert ('send_final_reminder', 'December 2026') in jan


def test_database_error_is_a_problem_not_silence():
    problems, _ = run_watchdog(fake({'_errors': {'automation_runs': 'HTTP 503'}}), now=NOW)
    assert problems and 'Could not read job history' in problems[0]


def test_email_html_escapes():
    html = watchdog_email_html(['<b>x</b> broke'], {})
    assert '<b>x</b>' not in html and '&lt;b&gt;' in html


# ---------- Endpoint (Vercel Cron) ----------

def _call(db, auth='Bearer s3cret', now=NOW, send=None):
    import api.system as system
    send = send or Mock(return_value={'sent': True})
    handler = system.handler(Mock(), None, None)
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = io.BytesIO()
    handler.path = '/api/system?action=watchdog'
    handler.headers = {'Authorization': auth}

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    with patch.dict(os.environ, {'CRON_SECRET': 's3cret', 'ADMIN_EMAIL': 'owner@example.net'}), \
            patch('api.supabase_http.table', fake(db)), \
            patch('api.system.datetime', FrozenDatetime), \
            patch('api.email.send_email', send):
        handler.do_GET()
    body = handler.wfile.getvalue()
    return handler.send_response.call_args[0][0], (json.loads(body) if body else {}), send


def test_watchdog_requires_cron_secret():
    status, _, send = _call(healthy_october(), auth='Bearer wrong')
    assert status == 401
    send.assert_not_called()


def test_watchdog_emails_owner_on_problems():
    db = healthy_october()
    db['match_assignments'] = []
    status, data, send = _call(db)
    assert status == 200 and data['emailed'] is True
    to, subject, html = send.call_args[0]
    assert to == 'owner@example.net'
    assert 'problem' in subject
    assert 'no October 2026 pairings' in html


def test_watchdog_quiet_when_healthy_except_monthly_all_clear():
    status, data, send = _call(healthy_october())
    assert status == 200 and data['problems'] == []
    send.assert_not_called()

    status, data, send = _call(healthy_october(), now=datetime(2026, 10, 3, 16, tzinfo=timezone.utc))
    assert send.call_args[0][1] == 'Net Worth: monthly all-clear'


def test_plain_health_check_unchanged():
    import api.system as system
    handler = system.handler(Mock(), None, None)
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = io.BytesIO()
    handler.path = '/api/system'
    with patch('api.supabase_http.table', fake({})):
        handler.do_GET()
    assert json.loads(handler.wfile.getvalue())['status'] == 'healthy'


def test_vercel_cron_is_configured_daily():
    from pathlib import Path
    config = json.loads((Path(__file__).resolve().parents[1] / 'vercel.json').read_text())
    assert {'path': '/api/system?action=watchdog', 'schedule': '0 16 * * *'} in config['crons']


def test_late_february_availability_check_still_checked_in_march():
    jobs = {(a, p) for a, p, _ in expected_jobs(datetime(2027, 3, 2).date())}
    assert ('send_availability_check', 'February 2027') in jobs
    problems, _ = run_watchdog(fake({'automation_runs': [], 'match_assignments': [], 'email_delivery_log': []}),
                               now=datetime(2027, 3, 2, 16, tzinfo=timezone.utc))
    assert any('February 2027 availability check (27th) never ran' in p for p in problems)


def test_duplicate_accepted_rows_do_not_hide_a_missing_match_email():
    db = healthy_october()
    db['email_delivery_log'][1]['message_key'] = db['email_delivery_log'][0]['message_key']
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert any('Only 1 of 2 October 2026 match emails' in p for p in problems)


def test_failed_alert_email_fails_the_cron_request():
    db = healthy_october()
    db['match_assignments'] = []
    status, data, _ = _call(db, send=Mock(return_value={'sent': False, 'error': 'resend down'}))
    assert status == 500
    assert data['success'] is False and data['emailed'] is False


def test_failure_after_an_earlier_success_is_still_reported():
    db = healthy_october()
    db['automation_runs'].append({'action': 'send_monthly_report', 'period_label': 'September 2026',
                                  'status': 'failed_terminal', 'started_at': '2026-10-04T19:00:00+00:00'})
    problems, _ = run_watchdog(fake(db), now=NOW)
    assert any("send_monthly_report for September 2026 ended as 'failed_terminal'" in p for p in problems)


def test_accepted_email_for_a_different_pairing_does_not_count():
    db = healthy_october()
    # Pairing 2's email is missing; an unrelated accepted row must not fill the gap
    db['email_delivery_log'][1]['message_key'] = 'generate_pairings:October 2026:999'
    db['email_delivery_log'].append({'action': 'generate_pairings', 'period_label': 'October 2026',
                                     'delivery_status': 'accepted',
                                     'message_key': 'generate_pairings:October 2026:1000', 'created_at': RECENT})
    problems, summary = run_watchdog(fake(db), now=NOW)
    assert summary['match_emails_accepted'] == 1
    assert any('Only 1 of 2 October 2026 match emails' in p for p in problems)
