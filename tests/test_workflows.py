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


def test_pairing_result_accepts_endpoint_delivery_outcome():
    source, _ = _workflow('biweekly-emails.yml')
    assert '.outcome // .delivery_outcome // "pre_send_failure"' in source


def test_pairings_health_checks_require_nonempty_pairings():
    source, _ = _workflow('biweekly-emails.yml')
    assert source.count('.pairings | length > 0') >= 2
    assert source.count('No pairings found for') >= 2


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


def test_every_month_dependent_workflow_honors_the_league_calendar():
    for name in ('biweekly-emails.yml', 'daily-health-check.yml', 'monthly-report.yml'):
        source, _ = _workflow(name)
        assert 'paused_periods' in source


def test_pause_gate_reads_status_and_fails_when_unreadable():
    source, _ = _workflow('biweekly-emails.yml')
    assert 'Unable to read the league calendar' in source
    assert 'monthly_availability|final_availability)' in source
    assert '+1 month' in source


def test_keep_alive_reenables_every_scheduled_workflow():
    source, parsed = _workflow('keep-alive.yml')
    assert parsed['jobs']['keep-schedules-on']['permissions'] == {'actions': 'write'}
    for name in ('biweekly-emails.yml', 'daily-health-check.yml', 'monthly-report.yml', 'keep-alive.yml'):
        assert name in source
    assert '/enable' in source


# ---------------------------------------------------------------------------
# Behavioral check of the scheduled-run gate.
#
# These tests run the real `gate-check` bash from biweekly-emails.yml with a
# frozen Pacific clock and a fake `curl` that returns a canned GET /api/email
# body. The runner's own `date` does the month arithmetic, so CI proves the
# gate on the same image the scheduled run uses. Nothing is sent: the fake
# curl only answers GET /api/email and records every call.
# ---------------------------------------------------------------------------

import json
import os
import shutil
import stat
import subprocess

import pytest


GATE_NEEDS = ('bash', 'jq', 'date')


def _gate_script(event_name='schedule', schedule='', dispatch_action=''):
    _, parsed = _workflow('biweekly-emails.yml')
    script = parsed['jobs']['gate-check']['steps'][0]['run']
    return (
        script
        .replace('${{ github.event_name }}', event_name)
        .replace('${{ inputs.action }}', dispatch_action)
        .replace('${{ github.event.schedule }}', schedule)
    )


def _write_exe(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run_gate(tmp_path, now, schedule, status_body=None, status_code=200,
              event_name='schedule', dispatch_action=''):
    for tool in GATE_NEEDS:
        if shutil.which(tool) is None:
            pytest.skip(f'{tool} is not installed')
    real_date = shutil.which('date')
    shims = tmp_path / 'shims'
    shims.mkdir()
    calls = tmp_path / 'curl-calls.log'
    body = tmp_path / 'status.json'
    body.write_text(json.dumps(
        status_body if status_body is not None
        else {'success': True, 'delivery_mode': 'live', 'paused_periods': ['December 2026']}
    ))
    # Freeze "now" unless the caller already passes an explicit date.
    _write_exe(shims / 'date', f'''#!/usr/bin/env bash
for arg in "$@"; do
  case "$arg" in -d|--date|--date=*|-d*) exec "{real_date}" "$@" ;; esac
done
exec "{real_date}" -d "$FAKE_NOW" "$@"
''')
    # Answer only a GET with -o FILE -w "%{{http_code}}"; record every call.
    _write_exe(shims / 'curl', f'''#!/usr/bin/env bash
echo "$*" >> "{calls}"
out=""
prev=""
for arg in "$@"; do
  case "$arg" in -X|--request|-d|--data|--data-raw) echo "unexpected write call" >&2; exit 99 ;; esac
  if [ "$prev" = "-o" ]; then out="$arg"; fi
  prev="$arg"
done
cp "{body}" "$out"
printf '%s' "{status_code}"
''')
    output = tmp_path / 'github_output'
    summary = tmp_path / 'step_summary'
    output.touch()
    summary.touch()
    script = tmp_path / 'gate.sh'
    script.write_text(_gate_script(event_name, schedule, dispatch_action))
    env = {
        'PATH': f'{shims}:{os.environ["PATH"]}',
        'HOME': str(tmp_path),
        'FAKE_NOW': now,
        'TZ': 'America/Los_Angeles',
        'SITE_URL': 'https://example.invalid',
        'GITHUB_OUTPUT': str(output),
        'GITHUB_STEP_SUMMARY': str(summary),
    }
    result = subprocess.run(
        ['bash', '--noprofile', '--norc', '-eo', 'pipefail', str(script)],
        env=env, capture_output=True, text=True, timeout=30,
    )
    outputs = dict(
        line.split('=', 1) for line in output.read_text().splitlines() if '=' in line
    )
    return result, outputs, summary.read_text(), calls.read_text() if calls.exists() else ''


@pytest.mark.parametrize('now, schedule, skipped_action', [
    # Friday Nov 27, on time and after a typical GitHub delay.
    ('2026-11-27 09:00', '0 17 27 * *', 'monthly_availability'),
    ('2026-11-27 13:31', '0 17 27 * *', 'monthly_availability'),
    # Last day of November: the final reminder about December.
    ('2026-11-30 09:00', '0 17 28-31 * *', 'final_availability'),
    # December's own jobs.
    ('2026-12-01 09:00', '0 17 1 * *', 'generate_pairings'),
    ('2026-12-01 12:00', '0 20 1 * *', 'health_check'),
    ('2026-12-15 09:00', '0 17 15 * *', 'mid_month_reminder'),
])
def test_gate_skips_every_league_job_about_paused_december(tmp_path, now, schedule, skipped_action):
    result, outputs, summary, calls = _run_gate(tmp_path, now, schedule)
    assert result.returncode == 0, result.stderr
    assert outputs['action'] == 'skip'
    assert f'League paused for December 2026; skipped {skipped_action}' in summary
    assert '/api/email' in calls


@pytest.mark.parametrize('now', ['2026-11-28 09:00', '2026-11-29 09:00'])
def test_gate_skips_days_before_the_last_day_without_reading_status(tmp_path, now):
    result, outputs, _, calls = _run_gate(tmp_path, now, '0 17 28-31 * *')
    assert result.returncode == 0, result.stderr
    assert outputs['action'] == 'skip'
    assert calls == ''


@pytest.mark.parametrize('now, schedule, action, period', [
    ('2026-12-27 09:00', '0 17 27 * *', 'monthly_availability', 'December 2026'),
    ('2026-12-31 09:00', '0 17 28-31 * *', 'final_availability', 'December 2026'),
    ('2027-01-01 09:00', '0 17 1 * *', 'generate_pairings', 'January 2027'),
    ('2026-10-27 09:00', '0 17 27 * *', 'monthly_availability', 'October 2026'),
])
def test_gate_runs_jobs_outside_the_pause(tmp_path, now, schedule, action, period):
    result, outputs, summary, _ = _run_gate(tmp_path, now, schedule)
    assert result.returncode == 0, result.stderr
    assert outputs['action'] == action
    assert outputs['period'] == period
    assert 'League paused' not in summary


def test_gate_needs_the_pause_list_to_skip_november_27(tmp_path):
    result, outputs, _, _ = _run_gate(
        tmp_path, '2026-11-27 09:00', '0 17 27 * *',
        status_body={'success': True, 'delivery_mode': 'live', 'paused_periods': []},
    )
    assert result.returncode == 0, result.stderr
    assert outputs['action'] == 'monthly_availability'


def _run_step():
    _, parsed = _workflow('biweekly-emails.yml')
    job = parsed['jobs']['run-automation']
    step = next(s for s in job['steps'] if s.get('name') == 'Execute automation action')
    return job, step['run']


def test_run_job_posts_the_gate_period_as_period_label():
    job, script = _run_step()
    assert job['env']['ACTION'] == '${{ needs.gate-check.outputs.action }}'
    assert job['env']['PERIOD'] == '${{ needs.gate-check.outputs.period }}'
    assert '--arg action "$EMAIL_ACTION" --arg period "$PERIOD"' in script
    assert "'{action:$action,period_label:$period}'" in script


@pytest.mark.parametrize('now, schedule, paused', [
    ('2026-11-27 09:00', '0 17 27 * *', 'December 2026'),
    ('2026-11-30 09:00', '0 17 28-31 * *', 'December 2026'),
    ('2026-12-15 09:00', '0 17 15 * *', 'December 2026'),
    ('2026-11-15 09:00', '0 17 15 * *', None),
    ('2026-12-27 09:00', '0 17 27 * *', None),
    ('2026-12-31 09:00', '0 17 28-31 * *', None),
])
def test_site_check_refuses_exactly_what_the_gate_skips(tmp_path, now, schedule, paused):
    """Let the gate through with an empty pause list, then build the body the
    run job would post. The site's own check must still catch paused runs."""
    import re
    import sys

    sys.path.insert(0, str(ROOT))
    from api.league_calendar import paused_month_for_league_email

    result, outputs, _, _ = _run_gate(
        tmp_path, now, schedule,
        status_body={'success': True, 'delivery_mode': 'live', 'paused_periods': []},
    )
    assert result.returncode == 0, result.stderr

    _, script = _run_step()
    email_actions = dict(re.findall(r'(\w+)\) EMAIL_ACTION=(\w+) ;;', script))
    email_action = email_actions[outputs['action']]
    assert paused_month_for_league_email(email_action, outputs['period']) == paused


def test_gate_fails_closed_when_the_calendar_is_unreadable(tmp_path):
    result, outputs, _, _ = _run_gate(tmp_path, '2026-11-27 09:00', '0 17 27 * *', status_code=503)
    assert result.returncode != 0
    assert 'action' not in outputs


def test_gate_fails_closed_when_the_pause_list_is_missing(tmp_path):
    result, outputs, _, _ = _run_gate(
        tmp_path, '2026-11-27 09:00', '0 17 27 * *',
        status_body={'success': True, 'delivery_mode': 'live'},
    )
    assert result.returncode != 0
    assert 'action' not in outputs


def test_manual_dispatch_is_paused_too(tmp_path):
    result, outputs, summary, _ = _run_gate(
        tmp_path, '2026-11-27 09:00', '', event_name='workflow_dispatch',
        dispatch_action='monthly_availability',
    )
    assert result.returncode == 0, result.stderr
    assert outputs['action'] == 'skip'
    assert 'League paused for December 2026' in summary
