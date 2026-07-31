"""Safety tests for outbound email and public API boundaries."""

import ast
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _handler_request(handler_class, payload, headers=None):
    body = json.dumps(payload).encode()
    request = Mock()
    instance = handler_class(request, None, None)
    instance.send_response = Mock()
    instance.send_header = Mock()
    instance.end_headers = Mock()
    instance.wfile = Mock()
    request_headers = {
        'Content-Length': str(len(body)),
        **(headers or {}),
    }
    instance.headers = Mock()
    instance.headers.get = Mock(side_effect=lambda key, default=None: request_headers.get(key, default))
    instance.rfile = io.BytesIO(body)
    return instance


def test_default_delivery_mode_is_disabled(monkeypatch):
    monkeypatch.delenv('EMAIL_DELIVERY_MODE', raising=False)

    from api.email_policy import delivery_mode, is_live_delivery

    assert delivery_mode() == 'disabled'
    assert is_live_delivery() is False


def test_unknown_delivery_mode_fails_closed(monkeypatch):
    monkeypatch.setenv('EMAIL_DELIVERY_MODE', 'surprise')

    from api.email_policy import delivery_mode, is_live_delivery

    assert delivery_mode() == 'disabled'
    assert is_live_delivery() is False


def test_disabled_single_send_never_calls_resend(monkeypatch):
    monkeypatch.delenv('EMAIL_DELIVERY_MODE', raising=False)

    from api import email
    import resend

    provider_called = []
    monkeypatch.setattr(
        resend.Emails,
        'send',
        lambda *args, **kwargs: provider_called.append(True),
    )

    result = email.send_email('player@example.com', 'Subject', '<p>Body</p>')

    assert result['success'] is True
    assert not result['sent']
    assert result['blocked'] is True
    assert result['delivery_mode'] == 'disabled'
    assert provider_called == []


def test_dry_run_bulk_send_never_calls_resend(monkeypatch):
    monkeypatch.setenv('EMAIL_DELIVERY_MODE', 'dry_run')

    from api import email
    import resend

    provider_called = []
    monkeypatch.setattr(
        resend.Batch,
        'send',
        lambda *args, **kwargs: provider_called.append(True),
    )

    result = email.send_bulk_emails([
        {
            'from': 'Net Worth Tennis <hello@networthtennis.com>',
            'to': ['player@example.com'],
            'subject': 'Subject',
            'html': '<p>Body</p>',
        }
    ])

    assert result['success'] is True
    assert result['sent'] == 0
    assert result['failed'] == 0
    assert result['blocked'] is True
    assert result['would_send'] == 1
    assert result['delivery_mode'] == 'dry_run'
    assert result['deliveries'] == []
    assert provider_called == []


def test_email_status_exposes_delivery_mode(monkeypatch):
    monkeypatch.delenv('EMAIL_DELIVERY_MODE', raising=False)
    from api.email import handler

    instance = _handler_request(handler, {})
    instance.do_GET()

    payload = json.loads(instance.wfile.write.call_args[0][0].decode())
    assert payload['delivery_mode'] == 'disabled'


def test_provider_send_calls_are_only_in_email_module():
    violations = []

    for path in Path('api').glob('*.py'):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            owner = node.func.value
            if not isinstance(owner, ast.Attribute):
                continue
            if owner.attr == 'Emails' and method == 'send':
                if path.name != 'email.py':
                    violations.append(f'{path}: resend.Emails.send')
            if owner.attr == 'Batch' and method == 'send':
                if path.name != 'email.py':
                    violations.append(f'{path}: resend.Batch.send')

    assert violations == []


def test_email_post_requires_an_explicit_action():
    from api.email import handler

    instance = _handler_request(handler, {})

    with patch('api.email.send_email') as send_email:
        instance.do_POST()

    instance.send_response.assert_called_with(400)
    send_email.assert_not_called()


def test_arbitrary_send_action_requires_cron_secret(monkeypatch):
    monkeypatch.setenv('CRON_SECRET', 'cron-secret')
    from api.email import handler

    instance = _handler_request(handler, {
        'action': 'send',
        'to': 'player@example.com',
        'subject': 'Subject',
        'html': '<p>Body</p>',
    })

    with patch('api.email.send_email') as send_email:
        instance.do_POST()

    instance.send_response.assert_called_with(403)
    send_email.assert_not_called()


def test_paused_player_bulk_action_requires_cron_secret(monkeypatch):
    monkeypatch.setenv('CRON_SECRET', 'cron-secret')
    from api.email import handler

    instance = _handler_request(handler, {
        'action': 'send_availability_check_paused_only',
    })

    with patch('api.supabase_http.table') as table:
        instance.do_POST()

    instance.send_response.assert_called_with(401)
    table.assert_not_called()


def test_pairings_post_requires_cron_or_verified_admin(monkeypatch):
    monkeypatch.delenv('CRON_SECRET', raising=False)
    from api.pairings import handler

    instance = _handler_request(handler, {'action': 'generate'})

    with patch('api.supabase_http.table') as table:
        instance.do_POST()

    instance.send_response.assert_called_with(401)
    table.assert_not_called()


def test_pairings_get_requires_cron_or_verified_admin(monkeypatch):
    monkeypatch.delenv('CRON_SECRET', raising=False)
    from api.pairings import handler

    instance = _handler_request(handler, {})
    instance.path = '/api/pairings?period=July%202026'

    with patch('api.supabase_http.table') as table:
        instance.do_GET()

    instance.send_response.assert_called_with(401)
    table.assert_not_called()


def test_public_players_response_contains_only_allowlisted_fields():
    from api.players import PUBLIC_PLAYER_FIELDS, handler

    class FakeQuery:
        def select(self, _columns):
            return self

        def eq(self, _column, _value):
            return self

        def neq(self, _column, _value):
            return self

        def order(self, _column, **_kwargs):
            return self

        def execute(self):
            return SimpleNamespace(data=[{
                'id': 'p1',
                'name': 'Player One',
                'skill_level': '3.5',
                'rank': 1,
                'total_games': 10,
                'matches_played': 2,
                'trend': 'up',
                'membership_tier': 'player',
                'avatar_url': None,
                'rms_band': 'competitive',
                'email': 'private@example.com',
                'phone': '555-0001',
                'is_admin': True,
                'password_hash': 'private',
                'avail_weekday_day': True,
            }], error=None)

    instance = _handler_request(handler, {})
    with patch('api.supabase_http.table', return_value=FakeQuery()):
        instance.do_GET()

    payload = json.loads(instance.wfile.write.call_args[0][0].decode())
    assert set(payload['players'][0]) == set(PUBLIC_PLAYER_FIELDS)
    assert 'email' not in payload['players'][0]
    assert 'phone' not in payload['players'][0]
    assert 'is_admin' not in payload['players'][0]
    assert 'password_hash' not in payload['players'][0]
    assert not any(key.startswith('avail_') for key in payload['players'][0])


def test_profiles_fetch_uses_authenticated_token():
    source = Path('public/profiles.html').read_text()
    assert "localStorage.getItem('networth_token')" in source
    assert "'Authorization': `Bearer ${token}`" in source


def test_report_issue_queues_without_resend(monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY', 'test-key')
    from api.system import handler

    fake_table = Mock()
    fake_table.insert.return_value.execute.return_value = SimpleNamespace(
        data=[{'id': 'issue-1'}], error=None
    )
    instance = _handler_request(handler, {
        'action': 'report_issue',
        'reporter_email': 'player@example.com',
        'reporter_name': 'Player',
        'page_path': '/dashboard',
        'message': 'Something is wrong',
    })

    with patch('api.supabase_http.table', return_value=fake_table):
        with patch('resend.Emails.send') as provider_send:
            instance.do_POST()

    instance.send_response.assert_called_with(200)
    payload = json.loads(instance.wfile.write.call_args[0][0].decode())
    assert payload['queued'] is True
    assert payload['delivery_mode'] == 'disabled'
    provider_send.assert_not_called()
    fake_table.insert.assert_called_once()


def test_check_email_connectivity_requires_cron_secret(monkeypatch):
    monkeypatch.setenv('CRON_SECRET', 'cron-secret')
    monkeypatch.setenv('RESEND_API_KEY', 'test-key')
    from api.system import handler

    instance = _handler_request(handler, {'action': 'check_email_connectivity'})

    with patch('resend.ApiKeys.list') as provider_probe:
        instance.do_POST()

    instance.send_response.assert_called_with(401)
    provider_probe.assert_not_called()
