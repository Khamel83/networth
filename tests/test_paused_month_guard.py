"""The site refuses league emails about a month the organizers paused.

The workflow gate skips these runs already; this is the second line of
defence if a run reaches the site anyway (a gate bug, a manual dispatch with a
wrong date, or a delayed run). No test here may reach Resend.
"""

import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.league_calendar import paused_month_for_league_email  # noqa: E402


@pytest.mark.parametrize('action,period,expected', [
    # Availability questions ask about the following month.
    ('send_availability_check', 'November 2026', 'December 2026'),
    ('send_availability_check_paused_only', 'November 2026', 'December 2026'),
    ('send_final_reminder', 'November 2026', 'December 2026'),
    ('send_availability_check', 'December 2026', None),
    ('send_final_reminder', 'October 2026', None),
    # Mid-month reminders are about the current month.
    ('send_midmonth_reminders', 'December 2026', 'December 2026'),
    ('send_midmonth_reminders', 'November 2026', None),
    ('send_midmonth_reminders', 'January 2027', None),
    # Other actions are not league emails about a month.
    ('send_monthly_report', 'December 2026', None),
    ('check_recent_send', 'December 2026', None),
    ('send_admin_alert', 'not a month', None),
])
def test_paused_month_for_league_email(action, period, expected):
    assert paused_month_for_league_email(action, period) == expected


def test_league_email_with_bad_period_label_raises():
    with pytest.raises(ValueError):
        paused_month_for_league_email('send_availability_check', 'Nov 2026')


def _post(payload):
    from api.email import handler

    body = json.dumps(payload).encode()
    instance = handler(Mock(), None, None)
    instance.send_response = Mock()
    instance.send_header = Mock()
    instance.end_headers = Mock()
    instance.wfile = Mock()
    headers = {
        'Content-Length': str(len(body)),
        'Authorization': 'Bearer test-cron-secret',
    }
    instance.headers = Mock()
    instance.headers.get = Mock(side_effect=lambda key, default=None: headers.get(key, default))
    instance.rfile = io.BytesIO(body)
    return instance


def _response(instance):
    status = instance.send_response.call_args[0][0]
    payload = json.loads(instance.wfile.write.call_args[0][0].decode())
    return status, payload


def _run(payload):
    """POST with live delivery configured and every outbound path forbidden."""
    import resend

    instance = _post(payload)
    forbidden = AssertionError('a paused month must not reach this call')
    with patch.dict(os.environ, {
        'CRON_SECRET': 'test-cron-secret',
        'RESEND_API_KEY': 'test-resend-key',
        'EMAIL_DELIVERY_MODE': 'live',
    }):
        with patch('api.email.try_start_run', side_effect=forbidden) as start_run, \
                patch('api.supabase_http.table', side_effect=forbidden), \
                patch.object(resend.Batch, 'send', side_effect=forbidden), \
                patch.object(resend.Emails, 'send', side_effect=forbidden):
            instance.do_POST()
    return instance, start_run


@pytest.mark.parametrize('action,period,paused', [
    ('send_availability_check', 'November 2026', 'December 2026'),
    ('send_availability_check_paused_only', 'November 2026', 'December 2026'),
    ('send_final_reminder', 'November 2026', 'December 2026'),
    ('send_midmonth_reminders', 'December 2026', 'December 2026'),
])
def test_paused_month_league_email_sends_nothing(action, period, paused):
    instance, start_run = _run({'action': action, 'period_label': period})

    status, payload = _response(instance)
    assert status == 200
    assert payload['outcome'] == 'paused'
    assert payload['paused_period'] == paused
    assert payload['sent'] == 0
    assert payload['failed'] == 0
    assert payload['reconciliation_required'] is False
    start_run.assert_not_called()


def test_unpaused_month_still_starts_the_run():
    from api.email import handler  # noqa: F401  (import before patching)

    instance = _post({'action': 'send_availability_check', 'period_label': 'December 2026'})
    with patch.dict(os.environ, {'CRON_SECRET': 'test-cron-secret'}):
        with patch('api.email.try_start_run', return_value=(None, 'stop here')) as start_run:
            instance.do_POST()

    start_run.assert_called_once_with(
        'send_availability_check', 'December 2026', {'source': 'api/email'},
    )
    status, _ = _response(instance)
    assert status == 409


def test_league_email_with_bad_period_label_is_refused():
    instance, start_run = _run({'action': 'send_final_reminder', 'period_label': '2026-11'})

    status, payload = _response(instance)
    assert status == 400
    assert payload['success'] is False
    start_run.assert_not_called()


def test_paused_check_still_requires_the_cron_secret():
    instance = _post({'action': 'send_availability_check', 'period_label': 'November 2026'})
    with patch.dict(os.environ, {'CRON_SECRET': 'a-different-secret'}):
        instance.do_POST()

    status, payload = _response(instance)
    assert status == 401
    assert 'paused_period' not in payload


@pytest.mark.parametrize('field,email_action,period,paused', [
    ('email_action', 'send_availability_check', 'November 2026', 'December 2026'),
    ('email_action', 'send_availability_check_paused_only', 'November 2026', 'December 2026'),
    ('email_action', 'send_final_reminder', 'November 2026', 'December 2026'),
    ('email_action', 'send_midmonth_reminders', 'December 2026', 'December 2026'),
    ('target_action', 'send_availability_check', 'November 2026', 'December 2026'),
])
def test_reconcile_of_paused_month_league_email_sends_nothing(field, email_action, period, paused):
    """A reconcile resends the original email, so it gets the same check."""
    forbidden = AssertionError('a paused month must not be reconciled')
    with patch('api.email.find_reconciliation_required', side_effect=forbidden) as find_rows:
        instance, start_run = _run({
            'action': 'reconcile_email_delivery',
            field: email_action,
            'period_label': period,
        })

    status, payload = _response(instance)
    assert status == 200
    assert payload['outcome'] == 'paused'
    assert payload['paused_period'] == paused
    assert payload['sent'] == 0
    assert payload['reconciliation_required'] is False
    find_rows.assert_not_called()
    start_run.assert_not_called()


@pytest.mark.parametrize('email_action,period', [
    ('send_availability_check', 'December 2026'),
    ('send_final_reminder', 'October 2026'),
    ('send_midmonth_reminders', 'November 2026'),
    ('send_monthly_report', 'December 2026'),
    ('generate_pairings', 'November 2026'),
])
def test_reconcile_of_unpaused_month_still_runs(email_action, period):
    instance = _post({
        'action': 'reconcile_email_delivery',
        'email_action': email_action,
        'period_label': period,
    })
    nothing_pending = {'success': True, 'rows': [], 'summary': {}}
    with patch.dict(os.environ, {'CRON_SECRET': 'test-cron-secret'}):
        with patch('api.email.find_reconciliation_required', return_value=nothing_pending) as find_rows:
            instance.do_POST()

    find_rows.assert_called_once_with(action=email_action, period_label=period)
    status, payload = _response(instance)
    assert status == 200
    assert payload['outcome'] == 'already_complete'
