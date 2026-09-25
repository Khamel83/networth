"""Admin score entry/correction, monthly report, and player score-save failures."""
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch


class FakeResult(SimpleNamespace):
    def execute(self):
        return self


class FakeDB:
    """Tiny in-memory stand-in for api.supabase_http.table()."""

    def __init__(self, tables, fail_insert=None, empty_insert=(), before_update=None):
        self.tables = tables
        self.fail_insert = fail_insert or {}
        self.empty_insert = set(empty_insert)
        # Hook run before an UPDATE executes, to simulate a concurrent edit
        self.before_update = before_update
        self.no_reported_paid = False

    def __call__(self, name):
        return FakeTable(self, name)


class FakeTable:
    def __init__(self, db, name):
        self.db, self.name = db, name
        self.filters, self.op, self.payload = [], 'select', None
        self.select_error = None

    def select(self, columns='*'):
        if 'reported_paid' in columns and self.db.no_reported_paid:
            self.select_error = self.db.no_reported_paid if isinstance(self.db.no_reported_paid, str) \
                else 'HTTP 400: {"code":"42703","message":"column players.reported_paid does not exist"}'
        return self

    def update(self, data):
        self.op, self.payload = 'update', data
        return self

    def insert(self, data):
        if self.name in self.db.fail_insert:
            return FakeResult(data=[], error=self.db.fail_insert[self.name])
        if self.name in self.db.empty_insert:
            return FakeResult(data=[], error=None)
        row = {'id': f"{self.name}-{len(self.db.tables[self.name]) + 1}", **data}
        self.db.tables[self.name].append(row)
        # Mirror the update_player_games() INSERT trigger
        if self.name == 'matches':
            for pid, games in ((row['player1_id'], row['player1_games']), (row['player2_id'], row['player2_games'])):
                for p in self.db.tables['players']:
                    if p['id'] == pid:
                        p['total_games'] += games
                        p['matches_played'] += 1
        return FakeResult(data=[row], error=None)

    def eq(self, col, val):
        self.filters.append((col, val))
        return self

    def returning(self):
        return self

    def or_(self, *_args):
        return self

    def neq(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        if self.select_error:
            return FakeResult(data=[], error=self.select_error)
        if self.op == 'update' and self.db.before_update:
            self.db.before_update(self.name, self.db.tables, self.filters)
        rows = [r for r in self.db.tables[self.name]
                if all(str(r.get(c)) == str(v) for c, v in self.filters)]
        if self.op == 'update':
            for r in rows:
                r.update(self.payload)
        return SimpleNamespace(data=rows, error=None)


def seed():
    return {
        'players': [
            {'id': 'a', 'name': 'Alik', 'email': 'a@example.net', 'phone': '', 'total_games': 10,
             'matches_played': 1, 'is_active': True, 'membership_tier': 'player', 'has_paid': True},
            {'id': 'c', 'name': 'Christina', 'email': 'c@example.net', 'phone': '', 'total_games': 4,
             'matches_played': 1, 'is_active': True, 'membership_tier': 'player', 'has_paid': False},
        ],
        'match_assignments': [
            {'id': 'as1', 'player1_id': 'a', 'player2_id': 'c', 'period_label': 'August 2026',
             'status': 'pending', 'match_id': None},
        ],
        'matches': [],
    }


def make_handler(module, method, body=None, path='/api/admin'):
    handler = module.handler(Mock(), None, None)
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = io.BytesIO()
    handler.path = path
    raw = json.dumps(body or {}).encode()
    handler.rfile = io.BytesIO(raw)
    handler.headers = {'Authorization': 'Bearer tok', 'Content-Length': str(len(raw))}
    # Pin "today" so month-range checks don't depend on when tests run
    from datetime import datetime
    import api.matches as matches_module
    real_validate = matches_module.validate_player_period
    with patch.object(matches_module, 'validate_player_period',
                      lambda period, today=None: real_validate(period, datetime(2026, 9, 25))):
        getattr(handler, method)()
    return handler.send_response.call_args[0][0], json.loads(handler.wfile.getvalue())


NO_RPC = FakeResult(data=[], error='HTTP 404: {"code":"PGRST202","message":"Could not find the function"}')


def call_admin(db, method, body=None, path='/api/admin', rpc_result=NO_RPC):
    import api.admin as admin
    with patch('api.supabase_http.table', db), \
            patch('api.supabase_http.rpc', return_value=rpc_result) as rpc_mock, \
            patch('api.auth.verify_session', return_value='admin@example.net'), \
            patch.object(admin, 'verify_admin', return_value=True):
        call_admin.rpc_calls = rpc_mock
        return make_handler(admin, method, body, path)


def test_admin_records_unfinished_match_and_closes_pairing():
    db = FakeDB(seed())
    status, data = call_admin(db, 'do_POST', {
        'action': 'record_score', 'player1_id': 'a', 'player2_id': 'c',
        'period_label': 'August 2026', 'set1_p1': 6, 'set1_p2': 3, 'set2_p1': 2, 'set2_p2': 3,
    })
    assert status == 200, data
    assert db.tables['matches'][0]['player1_games'] == 8
    assert db.tables['match_assignments'][0]['status'] == 'completed'
    assert db.tables['match_assignments'][0]['match_id'] == db.tables['matches'][0]['id']
    assert db.tables['players'][0]['total_games'] == 18
    assert db.tables['players'][1]['total_games'] == 10


def test_admin_rejects_blank_or_out_of_range_scores():
    db = FakeDB(seed())
    base = {'action': 'record_score', 'player1_id': 'a', 'player2_id': 'c', 'period_label': 'August 2026'}
    status, _ = call_admin(db, 'do_POST', {**base, 'set1_p1': 0, 'set1_p2': 0, 'set2_p1': 0, 'set2_p2': 0})
    assert status == 400
    status, _ = call_admin(db, 'do_POST', {**base, 'set1_p1': 9, 'set1_p2': 0, 'set2_p1': 6, 'set2_p2': 0})
    assert status == 400
    assert db.tables['matches'] == []


def test_admin_duplicate_score_returns_409_not_success():
    db = FakeDB(seed(), fail_insert={'matches': 'HTTP 409: duplicate key value violates idx_unique_match_per_period'})
    status, data = call_admin(db, 'do_POST', {
        'action': 'record_score', 'player1_id': 'a', 'player2_id': 'c',
        'period_label': 'August 2026', 'set1_p1': 6, 'set1_p2': 3, 'set2_p1': 6, 'set2_p2': 3,
    })
    assert status == 409
    assert data['success'] is False
    assert db.tables['match_assignments'][0]['status'] == 'pending'


def test_pairings_include_scores_and_report_lists_unreported():
    tables = seed()
    db = FakeDB(tables)
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=August%202026')
    assert status == 200, data
    assert data['summary']['unreported'] == 1
    assert data['unpaid'][0]['name'] == 'Christina'
    assert data['standings'] == []
    assert [p['name'] for p in data['season_standings']] == ['Alik', 'Christina']

    call_admin(db, 'do_POST', {
        'action': 'record_score', 'player1_id': 'c', 'player2_id': 'a',
        'period_label': 'August 2026', 'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 6,
    })
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=pairings&period=August%202026')
    assert status == 200
    assert data['pairings'][0]['match']['player1_id'] == 'c'
    assert data['extra_matches'] == []

    # Month standings count only that month's games, not cumulative totals
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=August%202026')
    assert [(p['name'], p['total_games']) for p in data['standings']] == [('Christina', 12), ('Alik', 10)]
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=July%202026')
    assert data['standings'] == []


def test_player_score_insert_failure_is_not_reported_as_success():
    import api.matches as matches
    tables = seed()
    tables['players'][0]['is_admin'] = False
    db = FakeDB(tables, fail_insert={'matches': 'HTTP 403: permission denied'})
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_POST', {
            'assignment_id': 'as1', 'player1_id': 'a', 'player2_id': 'c',
            'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 3, 'period_label': 'August 2026',
        }, path='/api/matches')
    assert status == 500
    assert data['success'] is False
    # The pairing must stay open so the player can try again
    assert tables['match_assignments'][0]['status'] == 'pending'


def _seed_with_match():
    tables = seed()
    tables['matches'].append({
        'id': 'm1', 'player1_id': 'a', 'player2_id': 'c', 'period_label': 'August 2026',
        'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 4,
        'player1_games': 12, 'player2_games': 8, 'is_forfeit': False,
    })
    return tables


def test_empty_insert_result_is_not_a_saved_score():
    db = FakeDB(seed(), empty_insert={'matches'})
    status, data = call_admin(db, 'do_POST', {
        'action': 'record_score', 'player1_id': 'a', 'player2_id': 'c',
        'period_label': 'August 2026', 'set1_p1': 6, 'set1_p2': 3, 'set2_p1': 6, 'set2_p2': 3,
    })
    assert status == 500 and data['success'] is False
    assert db.tables['match_assignments'][0]['status'] == 'pending'

    import api.matches as matches
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_POST', {
            'assignment_id': 'as1', 'player1_id': 'a', 'player2_id': 'c',
            'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 3, 'period_label': 'August 2026',
        }, path='/api/matches')
    assert status == 500
    assert db.tables['match_assignments'][0]['status'] == 'pending'


def test_report_shows_says_paid_and_survives_missing_column():
    tables = seed()
    tables['players'][1]['reported_paid'] = True
    db = FakeDB(tables)
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=August%202026')
    assert status == 200
    assert data['reported_paid_tracked'] is True
    assert data['unpaid'][0]['reported_paid'] is True
    assert data['summary']['unpaid_says_paid'] == 1

    # Before migrations/05_reported_paid.sql is applied the report still loads
    db.no_reported_paid = True
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=August%202026')
    assert status == 200, data
    assert data['reported_paid_tracked'] is False
    assert data['unpaid'][0]['reported_paid'] is None


def _join(db, body):
    import api.join as join
    with patch('api.supabase_http.table', db), \
            patch('api.email_policy.public_transactional_email_enabled', return_value=False):
        return make_handler(join, 'do_POST', body, path='/api/join')


JOIN_BODY = {
    'name': 'Rosa Lee', 'email': 'rosa7@gmail.com', 'phone': '(555) 555-5555', 'password': 'secret1',
    'membership_tier': 'player', 'avail_weekday_early': True,
}


def test_join_records_reported_paid_checkbox():
    tables = seed()
    db = FakeDB(tables)
    status, data = _join(db, {**JOIN_BODY, 'reported_paid': True})
    assert status == 200, data
    rosa = [p for p in tables['players'] if p['email'] == 'rosa7@gmail.com'][0]
    assert rosa['reported_paid'] is True
    assert rosa['reported_paid_at']


def test_join_without_checkbox_leaves_reported_paid_unset():
    tables = seed()
    status, _ = _join(FakeDB(tables), JOIN_BODY)
    assert status == 200
    rosa = [p for p in tables['players'] if p['email'] == 'rosa7@gmail.com'][0]
    assert rosa['reported_paid'] is False


def test_removed_member_can_rejoin():
    tables = seed()
    tables['players'].append({'id': 'r', 'name': 'Rosa Lee', 'email': 'rosa7@gmail.com',
                              'is_active': False, 'total_games': 0, 'matches_played': 0})
    status, data = _join(FakeDB(tables), JOIN_BODY)
    assert status == 200, data
    assert tables['players'][-1]['is_active'] is True


def test_admin_rejects_assignment_for_other_players():
    tables = seed()
    tables['players'].append({'id': 'z', 'name': 'Zoe', 'email': 'z@example.net', 'total_games': 0,
                              'matches_played': 0, 'is_active': True, 'membership_tier': 'player'})
    db = FakeDB(tables)
    status, data = call_admin(db, 'do_POST', {
        'action': 'record_score', 'assignment_id': 'as1', 'player1_id': 'a', 'player2_id': 'z',
        'period_label': 'August 2026', 'set1_p1': 6, 'set1_p2': 3, 'set2_p1': 6, 'set2_p2': 3,
    })
    assert status == 400, data
    assert tables['matches'] == []  # nothing written
    assert tables['match_assignments'][0]['status'] == 'pending'


def test_retry_after_half_finished_save_closes_the_pairing():
    # Match saved earlier, but the pairing update failed and it stayed pending
    tables = _seed_with_match()
    db = FakeDB(tables, fail_insert={'matches': 'HTTP 409: duplicate key value violates idx_unique_match_per_period'})
    import api.matches as matches
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_POST', {
            'assignment_id': 'as1', 'player1_id': 'a', 'player2_id': 'c',
            'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 4, 'period_label': 'August 2026',
        }, path='/api/matches')
    assert status == 409
    assert data['pairing_closed'] is True
    assert tables['match_assignments'][0]['status'] == 'completed'
    assert tables['match_assignments'][0]['match_id'] == 'm1'


def test_player_sees_error_when_pairing_close_fails():
    tables = seed()

    def pairing_vanishes(name, tbls, _filters):
        if name == 'match_assignments':
            tbls['match_assignments'].clear()

    db = FakeDB(tables, before_update=pairing_vanishes)
    import api.matches as matches
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_POST', {
            'assignment_id': 'as1', 'player1_id': 'a', 'player2_id': 'c',
            'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 3, 'period_label': 'August 2026',
        }, path='/api/matches')
    assert status == 500
    assert data['score_saved'] is True


def test_update_score_uses_atomic_database_function_when_installed():
    tables = _seed_with_match()
    db = FakeDB(tables)
    updated = {**tables['matches'][0], 'set1_p1': 4, 'set1_p2': 6, 'player1_games': 10, 'player2_games': 10}
    status, data = call_admin(db, 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 4,
    }, rpc_result=FakeResult(data=[updated], error=None))
    assert status == 200, data
    name, params = call_admin.rpc_calls.call_args[0]
    assert name == 'admin_update_match_score'
    assert params == {'p_match_id': 'm1', 'p_set1_p1': 4, 'p_set1_p2': 6, 'p_set2_p1': 6, 'p_set2_p2': 4}
    # The database did the work; the REST fallback must not also adjust totals
    assert tables['players'][0]['total_games'] == 10
    assert tables['matches'][0]['player1_games'] == 12


def test_update_score_database_error_changes_nothing():
    tables = _seed_with_match()
    status, _ = call_admin(FakeDB(tables), 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 4,
    }, rpc_result=FakeResult(data=[], error='HTTP 500: deadlock detected'))
    assert status == 500
    assert tables['players'][0]['total_games'] == 10
    assert tables['matches'][0]['player1_games'] == 12


def test_update_score_without_migration_changes_nothing():
    # No non-atomic fallback: until migration 06 is applied, edits are refused
    tables = _seed_with_match()
    status, data = call_admin(FakeDB(tables), 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 4,
    })
    assert status == 503
    assert '06_admin_update_match_score' in data['error']
    assert tables['players'][0]['total_games'] == 10
    assert tables['players'][1]['total_games'] == 4
    assert tables['matches'][0]['player1_games'] == 12


def test_player_period_limits():
    from datetime import datetime
    from api.matches import validate_player_period
    today = datetime(2026, 9, 25)
    assert validate_player_period('September 2026', today) is None
    assert validate_player_period('March 2026', today) is None
    assert validate_player_period('February 2026', today)  # 7 months back
    assert validate_player_period('October 2026', today)   # future
    assert validate_player_period('Sept 2026', today)      # malformed
    assert validate_player_period(None, today)


def test_player_cannot_log_future_month_extra_match():
    import api.matches as matches
    tables = seed()
    db = FakeDB(tables)
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_POST', {
            'player1_id': 'a', 'player2_id': 'c', 'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 3,
            'period_label': 'December 2099',
        }, path='/api/matches')
    assert status == 400, data
    assert tables['matches'] == []


def test_rejoin_clears_old_i_paid_answer():
    tables = seed()
    tables['players'].append({'id': 'r', 'name': 'Rosa Lee', 'email': 'rosa7@gmail.com', 'is_active': False,
                              'total_games': 0, 'matches_played': 0,
                              'reported_paid': True, 'reported_paid_at': '2025-01-01T00:00:00Z'})
    status, _ = _join(FakeDB(tables), JOIN_BODY)
    assert status == 200
    assert tables['players'][-1]['reported_paid'] is False
    assert tables['players'][-1]['reported_paid_at'] is None


def test_report_does_not_hide_real_database_errors():
    db = FakeDB(seed())
    db.no_reported_paid = 'HTTP 503: service unavailable (reported_paid query)'
    status, data = call_admin(db, 'do_GET', path='/api/admin?action=report&period=August%202026')
    assert status == 500
    assert data['success'] is False


def test_dashboard_hides_pairing_once_its_match_is_recorded():
    # Match saved but the pairing close failed: pairing still "pending"
    import api.matches as matches
    tables = _seed_with_match()
    with patch('api.supabase_http.table', FakeDB(tables)), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_GET', path='/api/matches?action=outstanding')
    assert status == 200, data
    assert data['matches'] == []

    tables['matches'].clear()
    with patch('api.supabase_http.table', FakeDB(tables)), \
            patch('api.auth.verify_session', return_value='a@example.net'):
        status, data = make_handler(matches, 'do_GET', path='/api/matches?action=outstanding')
    assert [m['opponent_name'] for m in data['matches']] == ['Christina']


def test_close_pairing_works_without_match_id_column():
    from api.matches import close_assignment
    tables = seed()

    class NoMatchIdTable(FakeTable):
        def execute(self):
            if self.op == 'update' and 'match_id' in (self.payload or {}):
                return FakeResult(data=[], error='HTTP 400: {"code":"PGRST204","message":"Could not find the \'match_id\' column"}')
            return super().execute()

    db = FakeDB(tables)
    assert close_assignment(lambda name: NoMatchIdTable(db, name), 'as1', 'm1') is None
    assert tables['match_assignments'][0]['status'] == 'completed'
