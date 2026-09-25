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

    def __call__(self, name):
        return FakeTable(self, name)


class FakeTable:
    def __init__(self, db, name):
        self.db, self.name = db, name
        self.filters, self.op, self.payload = [], 'select', None

    def select(self, *_args):
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

    def neq(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
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
    getattr(handler, method)()
    return handler.send_response.call_args[0][0], json.loads(handler.wfile.getvalue())


def call_admin(db, method, body=None, path='/api/admin'):
    import api.admin as admin
    with patch('api.supabase_http.table', db), \
            patch('api.auth.verify_session', return_value='admin@example.net'), \
            patch.object(admin, 'verify_admin', return_value=True):
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


def test_admin_update_score_adjusts_totals_by_difference():
    tables = seed()
    tables['matches'].append({
        'id': 'm1', 'player1_id': 'a', 'player2_id': 'c', 'period_label': 'August 2026',
        'set1_p1': 6, 'set1_p2': 4, 'set2_p1': 6, 'set2_p2': 4,
        'player1_games': 12, 'player2_games': 8, 'is_forfeit': False,
    })
    db = FakeDB(tables)
    status, data = call_admin(db, 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 6,
    })
    assert status == 200, data
    assert tables['matches'][0]['player1_games'] == 10
    assert tables['matches'][0]['player2_games'] == 12
    assert tables['players'][0]['total_games'] == 10 - 2
    assert tables['players'][1]['total_games'] == 4 + 4


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


def test_concurrent_score_edit_is_rejected_and_totals_rolled_back():
    tables = _seed_with_match()
    fired = []

    def someone_else_edits(name, tbls, _filters):
        # Another admin changes the match right before our match UPDATE
        if name == 'matches' and not fired:
            fired.append(True)
            tbls['matches'][0].update({'set1_p1': 6, 'set1_p2': 0, 'player1_games': 12, 'player2_games': 4})

    db = FakeDB(tables, before_update=someone_else_edits)
    status, data = call_admin(db, 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 6,
    })
    assert status == 409, data
    assert tables['players'][0]['total_games'] == 10
    assert tables['players'][1]['total_games'] == 4


def test_player_total_changed_mid_edit_is_rejected_without_partial_update():
    tables = _seed_with_match()

    def total_moves(name, tbls, filters):
        # A score insert for Christina lands between our read and conditional write
        if name == 'players' and ('id', 'c') in filters and tbls['players'][1]['total_games'] == 4:
            tbls['players'][1]['total_games'] = 9

    db = FakeDB(tables, before_update=total_moves)
    status, _ = call_admin(db, 'do_POST', {
        'action': 'update_score', 'match_id': 'm1', 'set1_p1': 4, 'set1_p2': 6, 'set2_p1': 6, 'set2_p2': 6,
    })
    assert status == 409
    assert tables['players'][0]['total_games'] == 10  # Alik's adjustment rolled back
    assert tables['matches'][0]['player1_games'] == 12  # match untouched


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
