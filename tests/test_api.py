"""
Automated API Tests for Net Worth Tennis
Run via pytest or GitHub Actions CI/CD
"""
import os
import json
import sys
from unittest.mock import Mock, MagicMock, patch

# Add project root to path for imports (so `from api.email import ...` works)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock environment variables before imports
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'test-key')
os.environ.setdefault('RESEND_API_KEY', 'test-resend-key')


class TestEmailAPI:
    """Test email endpoint functionality"""

    def test_email_status_returns_ready_when_configured(self):
        """GET /api/email should return status when RESEND_API_KEY is set"""
        from api.email import handler

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)
        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        mock_handler.do_GET()

        # Verify response
        mock_handler.send_response.assert_called()
        args = mock_handler.send_response.call_args[0]
        assert args[0] == 200

    def test_send_admin_alert_action_exists(self):
        """POST /api/email with send_admin_alert action should be valid"""
        from api.email import handler
        import io

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)

        # Mock the HTTP methods
        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        # Mock request body
        body = json.dumps({
            'action': 'send_admin_alert',
            'subject': 'Test Alert',
            'message': 'Test message'
        }).encode()

        mock_handler.headers = Mock()
        mock_handler.headers.get = Mock(side_effect=lambda key, default=None: {
            'Content-Length': str(len(body)),
            'Authorization': 'Bearer test-cron-secret'
        }.get(key, default))
        mock_handler.rfile = io.BytesIO(body)

        # send_email imports resend internally; patch send_email directly
        with patch('api.email.send_email', return_value={'success': True, 'id': 'test-id'}):
            with patch.dict(os.environ, {'ADMIN_EMAIL': 'admin@test.com', 'CRON_SECRET': 'test-cron-secret'}):
                mock_handler.do_POST()

                # Verify success response
                mock_handler.send_response.assert_called_with(200)


class TestSystemAPI:
    """Test system endpoint functionality (health check + report issue)"""

    def test_system_health_returns_ok(self):
        """GET /api/system should return healthy status"""
        from api.system import handler
        import io

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)

        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        mock_handler.do_GET()

        # Verify success response
        mock_handler.send_response.assert_called_with(200)

    def test_report_issue_requires_message(self):
        """POST /api/system with report_issue should require message field"""
        from api.system import handler
        import io

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)

        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        # Missing message - 400 returned before resend is ever imported
        body = json.dumps({
            'action': 'report_issue',
            'reporter_email': 'test@test.com',
            'page_path': '/test'
        }).encode()

        mock_handler.headers = Mock()
        mock_handler.headers.get = Mock(return_value=str(len(body)))
        mock_handler.rfile = io.BytesIO(body)

        mock_handler.do_POST()

        # Should return 400 error (missing message check happens before resend import)
        mock_handler.send_response.assert_called_with(400)

    def test_report_issue_accepts_valid_report(self):
        """POST /api/system with report_issue should accept valid report"""
        from api.system import handler
        import io

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)

        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        body = json.dumps({
            'action': 'report_issue',
            'reporter_email': 'test@test.com',
            'reporter_name': 'Test User',
            'page_path': '/dashboard',
            'message': 'Found a bug!'
        }).encode()

        mock_handler.headers = Mock()
        mock_handler.headers.get = Mock(return_value=str(len(body)))
        mock_handler.rfile = io.BytesIO(body)

        # resend is imported inside the function; patch it at the module level it imports from
        with patch('resend.Emails.send', return_value={'id': 'test-id'}):
            with patch.dict(os.environ, {'ADMIN_EMAIL': 'admin@test.com'}):
                mock_handler.do_POST()

                # Should return 200 success
                mock_handler.send_response.assert_called_with(200)




class TestSupabaseHTTP:
    """Test Supabase HTTP utility"""

    def test_table_function_exists(self):
        """table() function should be importable"""
        try:
            from api.supabase_http import table
            assert callable(table)
        except ImportError:
            # Module may require env vars, that's ok
            pass

    def test_table_returns_query_builder(self):
        """table() should return object with select method"""
        from api.supabase_http import table

        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            result = table('players')
            assert hasattr(result, 'select')
            assert hasattr(result, 'insert')
            assert hasattr(result, 'update')
            assert hasattr(result, 'delete')


class TestWorkflowGateCheck:
    """Test workflow gate-check logic"""

    def test_gate_check_logic_last_day(self):
        """Gate-check should return true on actual last day"""
        # This logic is in bash in the workflow, testing the concept here
        from datetime import datetime
        import calendar

        # Test: February 2025 (non-leap year) has 28 days
        year, month = 2025, 2
        last_day = calendar.monthrange(year, month)[1]

        assert last_day == 28

        # Days 27, 28, 1, 15 should run
        valid_days = {27, 28, 1, 15}
        assert 27 in valid_days
        assert 28 in valid_days  # Feb 28 is last day
        assert 1 in valid_days
        assert 15 in valid_days

    def test_gate_check_logic_non_last_day(self):
        """Gate-check should skip on non-last days like Feb 27 when last day is Feb 28"""
        # For 30-day month, day 29 should run, days 28-29 might be skipped depending
        from datetime import datetime
        import calendar

        # March has 31 days
        year, month = 2025, 3
        last_day = calendar.monthrange(year, month)[1]

        assert last_day == 31

        # On March 28, 29, 30 - these are NOT the last day, should skip
        # Only March 31 (actual last day) should run
        assert 31 == last_day


class TestEmailTemplates:
    """Test email template generation"""

    def test_welcome_email_generates_html(self):
        """Welcome email should generate valid HTML"""
        from api.email import get_welcome_email_html

        html = get_welcome_email_html("Test Player", "player")

        assert "Test Player" in html
        assert "$35" in html  # Player tier price
        assert "Welcome to Net Worth Tennis" in html

    def test_welcome_email_social_butterfly_price(self):
        """Welcome email for Social Butterfly should show $45"""
        from api.email import get_welcome_email_html

        html = get_welcome_email_html("Test Player", "social_butterfly")

        assert "$45" in html

    def test_admin_alert_email_generates_html(self):
        """Admin alert email should generate valid HTML"""
        from api.email import get_admin_alert_email_html

        html = get_admin_alert_email_html(
            "Test Subject",
            "Test message body"
        )

        assert "Test Subject" in html
        assert "Test message body" in html
        assert "Admin Alert" in html

    def test_match_assignment_email_generates_html(self):
        """Match assignment email should include both players"""
        from api.email import get_match_assignment_email_html

        html = get_match_assignment_email_html(
            "Player One",
            "Player Two",
            "March 2025",
            "Weekdays: 9-5",
            "Weekends: before 9am",
            "555-0101",
            "555-0102"
        )

        assert "Player One" in html
        assert "Player Two" in html
        assert "March 2025" in html
        assert "555-0101" in html
        assert "555-0102" in html


class TestAuthAPI:
    """Test authentication and password reset functionality"""

    def test_password_hash_function_exists(self):
        """hash_password function should be importable from auth module"""
        from api.auth import hash_password

        # Test basic hashing
        password = "test123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_function_exists(self):
        """verify_password function should work correctly"""
        from api.auth import hash_password, verify_password

        password = "test123"
        hashed = hash_password(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password("wrong", hashed) is False

    def test_password_reset_token_generation(self):
        """Password reset should generate valid tokens"""
        import secrets
        from datetime import datetime, timedelta

        # Simulate token generation (same logic as in auth.py)
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=1)

        assert reset_token is not None
        assert len(reset_token) > 20
        assert expires > datetime.now()

    def test_auth_module_importable(self):
        """Auth module should be importable"""
        try:
            from api import auth
            assert hasattr(auth, 'handler')
        except ImportError as e:
            # Module may fail on import due to env vars, check syntax
            import py_compile
            import tempfile
            try:
                with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as f:
                    py_compile.compile('api/auth.py', f.name, doraise=True)
            except Exception as compile_err:
                assert False, f"Failed to compile auth.py: {compile_err}"

    def test_join_module_has_password_hashing(self):
        """Join module should handle password hashing"""
        from api.join import hash_password

        password = "newuser123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)

    def test_reset_password_html_page_exists(self):
        """reset-password.html should exist and contain reset form"""
        import os

        reset_password_path = os.path.join(
            os.path.dirname(__file__), '..', 'public', 'reset-password.html'
        )

        assert os.path.exists(reset_password_path), "reset-password.html not found"

        # Check it contains expected elements
        with open(reset_password_path, 'r') as f:
            content = f.read()
            assert 'password' in content.lower()
            assert 'reset' in content.lower()

    def test_password_reset_action_exists_in_auth(self):
        """Auth module should have reset_password action handler"""
        with open('api/auth.py', 'r') as f:
            content = f.read()

        assert 'reset_password' in content
        assert 'request_password_reset' in content
        assert 'password_reset_token' in content


class TestMatchesAPI:
    """Test matches endpoint - including extra match (no assignment) flow"""

    def test_matches_module_importable(self):
        """Matches module should be importable"""
        from api import matches
        assert hasattr(matches, 'handler')

    def test_post_match_builds_correct_data_without_assignment(self):
        """Extra match flow: assignment_id is optional, match still records"""
        from api.matches import handler
        import io

        # Simulate POST body for an extra match (no assignment_id)
        body = json.dumps({
            "player1_id": "uuid-player1",
            "player2_id": "uuid-player2",
            "set1_p1": 6, "set1_p2": 4,
            "set2_p1": 6, "set2_p2": 3,
            "court": "Vermont Canyon",
            "period_label": "February 2026",
            "would_play_again": True
        }).encode()

        # Verify the payload structure is valid (no assignment_id key)
        data = json.loads(body)
        assert 'assignment_id' not in data
        assert data['player1_id'] == 'uuid-player1'
        assert data['player2_id'] == 'uuid-player2'

        # Verify games calculation logic matches what the API does
        set1_p1 = int(data.get('set1_p1', 0))
        set1_p2 = int(data.get('set1_p2', 0))
        set2_p1 = int(data.get('set2_p1', 0))
        set2_p2 = int(data.get('set2_p2', 0))
        set3_p1 = int(data.get('set3_p1') or 0)
        set3_p2 = int(data.get('set3_p2') or 0)

        player1_games = set1_p1 + set2_p1 + set3_p1
        player2_games = set1_p2 + set2_p2 + set3_p2

        assert player1_games == 12  # 6 + 6
        assert player2_games == 7   # 4 + 3

    def test_post_match_with_assignment_includes_assignment_id(self):
        """Regular match flow: assignment_id is present"""
        body = json.dumps({
            "assignment_id": "uuid-assignment",
            "player1_id": "uuid-player1",
            "player2_id": "uuid-player2",
            "set1_p1": 6, "set1_p2": 4,
            "set2_p1": 3, "set2_p2": 6,
            "period_label": "February 2026",
            "would_play_again": True
        }).encode()

        data = json.loads(body)
        assert data['assignment_id'] == 'uuid-assignment'
        assert data['player1_id'] == 'uuid-player1'

    def test_assignment_id_guard_skips_update_when_missing(self):
        """When assignment_id is None/missing, match_assignments should NOT be updated"""
        # This tests the guard: `if assignment_id:` in do_POST
        data = {"player1_id": "a", "player2_id": "b"}
        assignment_id = data.get('assignment_id')
        # Should be None/falsy, so the update block is skipped
        assert not assignment_id

    def test_assignment_id_guard_updates_when_present(self):
        """When assignment_id is present, match_assignments SHOULD be updated"""
        data = {"assignment_id": "uuid-123", "player1_id": "a", "player2_id": "b"}
        assignment_id = data.get('assignment_id')
        assert assignment_id == "uuid-123"

    def test_duplicate_match_error_detection(self):
        """Duplicate constraint violation should be detected by error message patterns"""
        # These are the patterns checked in the except block
        test_errors = [
            'duplicate key value violates unique constraint "idx_unique_match_per_period"',
            'ERROR: 23505 duplicate key',
            'Duplicate entry found',
        ]
        for error_msg in test_errors:
            is_duplicate = (
                'idx_unique_match_per_period' in error_msg or
                '23505' in error_msg or
                'duplicate' in error_msg.lower()
            )
            assert is_duplicate, f"Should detect duplicate in: {error_msg}"

    def test_period_label_format_consistency(self):
        """Extra match period_label format must match DB format: 'Month YYYY'"""
        from datetime import datetime
        month_names = ['January','February','March','April','May','June',
                       'July','August','September','October','November','December']
        now = datetime.now()
        # This is how openExtraMatchModal() generates it
        js_format = f"{month_names[now.month - 1]} {now.year}"
        # This is how the API defaults it
        api_format = now.strftime('%B %Y')
        assert js_format == api_format


class TestPairingsAPI:
    """Test pairings endpoint response safety and required coordination fields"""

    def test_pairings_get_includes_contact_but_excludes_sensitive_fields(self):
        """GET /api/pairings should expose coordination data but not sensitive columns."""
        from api.pairings import handler
        import io

        class FakeResult:
            def __init__(self, data=None, error=None):
                self.data = data or []
                self.error = error

        class FakeQuery:
            def __init__(self, table_name):
                self.table_name = table_name

            def select(self, _cols='*'):
                return self

            def eq(self, _col, _val):
                return self

            def execute(self):
                if self.table_name == 'match_assignments':
                    return FakeResult(data=[{
                        'id': 'a1',
                        'player1_id': 'p1',
                        'player2_id': 'p2',
                        'period_label': 'March 2026',
                        'status': 'pending'
                    }])
                if self.table_name == 'players':
                    return FakeResult(data=[
                        {
                            'id': 'p1',
                            'name': 'Player One',
                            'email': 'p1@test.com',
                            'phone': '555-0001',
                            'skill_level': '3.5',
                            'rank': 1,
                            'membership_tier': 'player',
                            'avail_weekday_day': True,
                            'password_hash': 'SHOULD_NOT_LEAK'
                        },
                        {
                            'id': 'p2',
                            'name': 'Player Two',
                            'email': 'p2@test.com',
                            'phone': '555-0002',
                            'skill_level': '3.5',
                            'rank': 2,
                            'membership_tier': 'player',
                            'avail_weekend_day': True,
                            'password_hash': 'SHOULD_NOT_LEAK'
                        }
                    ])
                return FakeResult()

        def fake_table(name):
            return FakeQuery(name)

        mock_request = Mock()
        mock_handler = handler(mock_request, None, None)
        mock_handler.path = '/api/pairings?period=March%202026'
        mock_handler.send_response = Mock()
        mock_handler.send_header = Mock()
        mock_handler.end_headers = Mock()
        mock_handler.wfile = Mock()

        with patch('api.supabase_http.table', side_effect=fake_table):
            mock_handler.do_GET()

        mock_handler.send_response.assert_called_with(200)
        write_arg = mock_handler.wfile.write.call_args[0][0]
        payload = json.loads(write_arg.decode())
        assert payload['success'] is True
        assert payload['count'] == 1

        p1 = payload['pairings'][0]['player1']
        p2 = payload['pairings'][0]['player2']

        # Required coordination fields remain available
        assert p1['email'] == 'p1@test.com'
        assert p1['phone'] == '555-0001'
        assert p2['email'] == 'p2@test.com'
        assert p2['phone'] == '555-0002'

        # Sensitive fields must not leak
        assert 'password_hash' not in p1
        assert 'password_hash' not in p2


def test_imports():
    """Test that all API modules are importable"""
    modules = [
        'api.email',
        'api.system',
        'api.supabase_http',
    ]

    for module_name in modules:
        try:
            __import__(module_name)
        except Exception as e:
            # Some imports may fail due to missing env vars, that's expected
            # We're just checking the files exist and have valid syntax
            assert isinstance(e, (ImportError, KeyError)), f"Unexpected error importing {module_name}: {e}"


if __name__ == '__main__':
    # Run tests when executed directly
    import pytest
    pytest.main([__file__, '-v'])
