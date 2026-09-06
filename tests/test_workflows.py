"""Static safety checks for scheduled workflows."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'


def _workflow(name):
    path = WORKFLOWS / name
    text = path.read_text()
    return text, yaml.safe_load(text)


def test_workflows_parse_as_yaml():
    for path in WORKFLOWS.glob('*.yml'):
        assert yaml.safe_load(path.read_text()) is not None


def test_scheduled_automation_uses_pacific_time_and_delivery_gate():
    source, parsed = _workflow('biweekly-emails.yml')
    assert parsed['name'] == 'Tennis League Emails'
    assert 'TZ: America/Los_Angeles' in source
    assert 'export TZ=America/Los_Angeles' in source
    assert 'delivery_mode' in source
    assert 'reconciliation_required' in source
    assert 'delivery_summary' in source
    assert 'GITHUB_STEP_SUMMARY' in source
    assert "env.ACTION == 'generate_pairings'" in source
    assert 'non-pairing email actions will be skipped' in source


def test_scheduled_action_uses_triggering_cron_not_runner_clock():
    source, _ = _workflow('biweekly-emails.yml')
    assert 'github.event.schedule' in source
    assert 'SCHEDULE=' in source
    assert '0 17 1 * *' in source
    assert '0 20 1 * *' in source
    assert 'HOUR=' not in source
    assert 'date +%H' not in source


def test_pairing_schedule_fails_closed_when_delivery_is_not_live():
    source, _ = _workflow('biweekly-emails.yml')
    assert 'Pairing generation requires live delivery' in source
    assert 'env.ACTION == \'generate_pairings\'' in source


def test_pairings_health_get_has_cron_auth_and_period():
    source, _ = _workflow('biweekly-emails.yml')
    assert '/api/pairings?period=' in source
    assert 'Authorization: Bearer ${{ secrets.CRON_SECRET }}' in source


def test_automatic_workflows_never_send_admin_alerts():
    for name in ('biweekly-emails.yml', 'daily-health-check.yml'):
        source, _ = _workflow(name)
        assert 'send_admin_alert' not in source


def test_daily_health_check_is_read_only_and_timezone_correct():
    source, _ = _workflow('daily-health-check.yml')
    assert 'TZ: America/Los_Angeles' in source
    assert 'GET /api/email' in source
    assert '-X POST' not in source
    assert 'No POST' in source
    assert 'GITHUB_STEP_SUMMARY' in source


def test_daily_health_check_fails_when_monthly_pairings_are_missing():
    source, _ = _workflow('daily-health-check.yml')
    assert 'DAY="$(date +%-d)"' in source
    assert 'No pairings exist for' in source
    assert '.pairings | length == 0' in source


def test_daily_health_check_uses_canonical_site_host():
    source, _ = _workflow('daily-health-check.yml')
    assert 'SITE_URL: https://www.networthtennis.com' in source
    assert 'SITE_URL: https://networthtennis.com' not in source
