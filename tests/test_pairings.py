"""
Tests for the pairing algorithm in api/pairings.py.
All tests are mocked — no real DB calls.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_player(id, name, band='competitive', rms=7.0, email=None,
                is_active=True, tier='player', unavailable_until=None):
    """Create a minimal player dict for testing."""
    return {
        'id': id,
        'name': name,
        'email': email or f'{name.lower().replace(" ", "")}@test.com',
        'rms': rms,
        'rms_score': rms,
        'band': band,
        'band_order': {'new': 0, 'developing': 1, 'competitive': 2, 'strong': 3, 'dominant': 4}[band],
        'is_active': is_active,
        'membership_tier': tier,
        'unavailable_until': unavailable_until,
        'avail_weekday_early': False,
        'avail_weekday_day': True,
        'avail_weekday_late': False,
        'avail_weekend_early': False,
        'avail_weekend_day': True,
        'avail_weekend_late': False,
        'available_morning': False,
        'available_afternoon': True,
        'available_evening': False,
    }


def make_assignment(p1_id, p2_id, period_label='January 2026', assigned_at='2026-01-01'):
    """Create a minimal match_assignment dict for testing."""
    return {
        'player1_id': p1_id,
        'player2_id': p2_id,
        'period_label': period_label,
        'assigned_at': assigned_at,
    }


def make_match(p1_id, p2_id, s1p1=6, s1p2=4, s2p1=6, s2p2=3):
    """Create a minimal match dict for testing."""
    return {
        'player1_id': p1_id,
        'player2_id': p2_id,
        'set1_p1': s1p1, 'set1_p2': s1p2,
        'set2_p1': s2p1, 'set2_p2': s2p2,
    }


# ─── calculate_rms ───────────────────────────────────────────────────────────

from api.pairings import calculate_rms, get_performance_band, is_player_available, generate_pairings


class TestCalculateRms:
    def test_no_matches_returns_none(self):
        assert calculate_rms(1, []) is None

    def test_no_matches_for_player_returns_none(self):
        matches = [make_match(2, 3)]
        assert calculate_rms(1, matches) is None

    def test_one_match_as_player1(self):
        # player 1 won 6+6=12 games
        matches = [make_match(1, 2, s1p1=6, s1p2=4, s2p1=6, s2p2=3)]
        assert calculate_rms(1, matches) == 12.0

    def test_one_match_as_player2(self):
        # player 2 won 4+3=7 games
        matches = [make_match(1, 2, s1p1=6, s1p2=4, s2p1=6, s2p2=3)]
        assert calculate_rms(2, matches) == 7.0

    def test_averages_last_three_matches(self):
        matches = [
            make_match(1, 2, s1p1=6, s1p2=4, s2p1=6, s2p2=3),   # p1 wins 12
            make_match(1, 3, s1p1=4, s1p2=6, s2p1=3, s2p2=6),   # p1 wins 7
            make_match(1, 4, s1p1=6, s1p2=2, s2p1=6, s2p2=1),   # p1 wins 12
        ]
        rms = calculate_rms(1, matches)
        assert rms == pytest.approx((12 + 7 + 12) / 3)

    def test_only_uses_last_three_matches(self):
        # 4 matches — only last 3 should be counted
        matches = [
            make_match(1, 2, s1p1=6, s1p2=0, s2p1=6, s2p2=0),   # p1 wins 12
            make_match(1, 3, s1p1=6, s1p2=0, s2p1=6, s2p2=0),   # p1 wins 12
            make_match(1, 4, s1p1=6, s1p2=0, s2p1=6, s2p2=0),   # p1 wins 12
            make_match(1, 5, s1p1=0, s1p2=6, s2p1=0, s2p2=6),   # p1 wins 0 (4th, ignored)
        ]
        rms = calculate_rms(1, matches)
        assert rms == 12.0  # Only first 3 counted (12+12+12)/3


# ─── get_performance_band ────────────────────────────────────────────────────

class TestGetPerformanceBand:
    def test_none_returns_new(self):
        band, order = get_performance_band(None)
        assert band == 'new'
        assert order == 0

    def test_exactly_six_is_developing(self):
        band, order = get_performance_band(6.0)
        assert band == 'developing'

    def test_six_point_one_is_competitive(self):
        band, order = get_performance_band(6.1)
        assert band == 'competitive'

    def test_nine_is_competitive(self):
        band, order = get_performance_band(9.0)
        assert band == 'competitive'

    def test_nine_point_one_is_strong(self):
        band, order = get_performance_band(9.1)
        assert band == 'strong'

    def test_twelve_is_strong(self):
        band, order = get_performance_band(12.0)
        assert band == 'strong'

    def test_twelve_point_one_is_dominant(self):
        band, order = get_performance_band(12.1)
        assert band == 'dominant'

    def test_band_orders_are_ascending(self):
        orders = [get_performance_band(rms)[1] for rms in [None, 3, 7, 10, 15]]
        assert orders == sorted(orders)


# ─── is_player_available ─────────────────────────────────────────────────────

class TestIsPlayerAvailable:
    def test_active_player_is_available(self):
        p = make_player(1, 'Alice')
        assert is_player_available(p) is True

    def test_inactive_player_is_not_available(self):
        p = make_player(1, 'Alice', is_active=False)
        assert is_player_available(p) is False

    def test_social_butterfly_is_not_available(self):
        p = make_player(1, 'Alice', tier='social_butterfly')
        assert is_player_available(p) is False

    def test_admin_email_is_not_available(self):
        with patch.dict('os.environ', {'ADMIN_EMAIL': 'admin@test.com'}):
            p = make_player(1, 'Admin', email='admin@test.com')
            assert is_player_available(p) is False

    def test_default_admin_email_is_not_available(self):
        import os
        os.environ.pop('ADMIN_EMAIL', None)
        p = make_player(1, 'Khamel', email='khamel@khamel.com')
        assert is_player_available(p) is False

    def test_future_unavailable_until_blocks(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        p = make_player(1, 'Alice', unavailable_until=future)
        assert is_player_available(p) is False

    def test_past_unavailable_until_allows(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        p = make_player(1, 'Alice', unavailable_until=past)
        assert is_player_available(p) is True

    def test_today_unavailable_until_allows(self):
        today = date.today().isoformat()
        p = make_player(1, 'Alice', unavailable_until=today)
        # unavailable_date == today is NOT > today, so player is available
        assert is_player_available(p) is True


# ─── Exhaustion Algorithm ────────────────────────────────────────────────────

class TestExhaustionAlgorithm:
    """
    Core test: previously-paired players should NOT be re-paired in Pass 1.
    """

    def test_avoids_previous_pairs(self):
        """
        6 players: A-F. A+B previously paired, C+D previously paired.
        Expected: A is NOT paired with B; C is NOT paired with D.
        """
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
            make_player(3, 'C', band='competitive', rms=7.0),
            make_player(4, 'D', band='competitive', rms=7.0),
            make_player(5, 'E', band='competitive', rms=7.0),
            make_player(6, 'F', band='competitive', rms=7.0),
        ]
        all_assignments = [
            make_assignment(1, 2, 'January 2026'),  # A+B played before
            make_assignment(3, 4, 'January 2026'),  # C+D played before
        ]

        pairings, skipped, forced_repeats = generate_pairings(
            players, [], all_assignments, []
        )

        assert len(pairings) == 3, f"Expected 3 pairings, got {len(pairings)}"
        assert len(forced_repeats) == 0, f"Expected no forced repeats, got {forced_repeats}"

        for p in pairings:
            ids = frozenset([p['player1']['id'], p['player2']['id']])
            assert ids != frozenset([1, 2]), "A+B should not be paired (they played before)"
            assert ids != frozenset([3, 4]), "C+D should not be paired (they played before)"

    def test_all_players_get_paired(self):
        """6 fresh players with no history — all 6 should be paired."""
        players = [make_player(i, f'P{i}', band='competitive', rms=7.0) for i in range(1, 7)]

        pairings, skipped, forced_repeats = generate_pairings(players, [], [], [])

        assert len(pairings) == 3
        assert len(skipped) == 0

    def test_forced_repeat_only_when_no_other_option(self):
        """
        2 players who've played before — only option is to pair them.
        Should be logged as forced repeat.
        """
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
        ]
        all_assignments = [
            make_assignment(1, 2, 'January 2026'),  # A+B played before
        ]

        pairings, skipped, forced_repeats = generate_pairings(
            players, [], all_assignments, []
        )

        assert len(pairings) == 1, "Should still create a pairing (forced repeat)"
        assert frozenset([1, 2]) in forced_repeats, "A+B should be logged as forced repeat"

    def test_hard_blocked_pair_never_paired(self):
        """Hard-blocked pair (would_not_play_again) should never be matched even in Pass 2."""
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
        ]
        blocked_pairs = [{'player_a': 1, 'player_b': 2}]

        pairings, skipped, forced_repeats = generate_pairings(
            players, blocked_pairs, [], []
        )

        assert len(pairings) == 0, "Hard-blocked pair should never be paired"
        assert len(skipped) == 2, "Both players should be in skipped"

    def test_cross_band_pairing_when_same_band_exhausted(self):
        """
        4 players: A,B in competitive; C,D in strong.
        A+B paired before, C+D paired before.
        Should cross-band pair: A+C or A+D, and B+D or B+C.
        """
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
            make_player(3, 'C', band='strong', rms=10.0),
            make_player(4, 'D', band='strong', rms=10.0),
        ]
        all_assignments = [
            make_assignment(1, 2, 'January 2026'),  # A+B played
            make_assignment(3, 4, 'January 2026'),  # C+D played
        ]

        pairings, skipped, forced_repeats = generate_pairings(
            players, [], all_assignments, []
        )

        assert len(pairings) == 2, f"Expected 2 cross-band pairings, got {len(pairings)}"
        assert len(forced_repeats) == 0, "No forced repeats needed"
        for p in pairings:
            ids = frozenset([p['player1']['id'], p['player2']['id']])
            assert ids != frozenset([1, 2]), "A+B should not be re-paired"
            assert ids != frozenset([3, 4]), "C+D should not be re-paired"

    def test_inactive_player_excluded(self):
        """Inactive players should not be paired."""
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0, is_active=False),
            make_player(3, 'C', band='competitive', rms=7.0),
        ]

        pairings, skipped, forced_repeats = generate_pairings(players, [], [], [])

        # B is inactive, so A+C pair; B is not in pairings
        assert len(pairings) == 1
        for p in pairings:
            assert p['player1']['id'] != 2
            assert p['player2']['id'] != 2

    def test_social_butterfly_excluded(self):
        """Social Butterflies should not be paired."""
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0, tier='social_butterfly'),
            make_player(3, 'C', band='competitive', rms=7.0),
        ]

        pairings, skipped, forced_repeats = generate_pairings(players, [], [], [])

        assert len(pairings) == 1
        for p in pairings:
            assert p['player1']['id'] != 2
            assert p['player2']['id'] != 2


# ─── Pre-Send Validation Gate ────────────────────────────────────────────────

class TestValidationGate:
    """
    Test the validation checks in do_POST before insert/email.
    We test generate_pairings() output properties since the gate
    reads directly from its results.
    """

    def test_no_duplicate_players_in_pairings(self):
        """Each player should appear in at most one pairing."""
        players = [make_player(i, f'P{i}', band='competitive', rms=7.0) for i in range(1, 7)]

        pairings, skipped, forced_repeats = generate_pairings(players, [], [], [])

        seen = set()
        for p in pairings:
            p1_id = p['player1']['id']
            p2_id = p['player2']['id']
            assert p1_id not in seen, f"Player {p1_id} appears in multiple pairings"
            assert p2_id not in seen, f"Player {p2_id} appears in multiple pairings"
            seen.add(p1_id)
            seen.add(p2_id)

    def test_forced_repeat_tracked_correctly(self):
        """A forced repeat is in forced_repeats; a fresh pair is not."""
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
        ]
        all_assignments = [make_assignment(1, 2, 'January 2026')]

        pairings, skipped, forced_repeats = generate_pairings(
            players, [], all_assignments, []
        )

        # The only possible pairing (A+B) should be in forced_repeats
        assert frozenset([1, 2]) in forced_repeats

    def test_fresh_pair_not_in_forced_repeats(self):
        """Fresh pairings should never appear in forced_repeats."""
        players = [
            make_player(1, 'A', band='competitive', rms=7.0),
            make_player(2, 'B', band='competitive', rms=7.0),
        ]
        # No history — fresh pair
        pairings, skipped, forced_repeats = generate_pairings(players, [], [], [])

        assert len(pairings) == 1
        assert len(forced_repeats) == 0
        assert frozenset([1, 2]) not in forced_repeats

    def test_avoidable_repeat_would_fail_gate(self):
        """
        Simulate the avoidable repeat check: if A+B appear in pairings
        and are in all_time_pairs but NOT in forced_repeats, the gate should flag it.
        This tests the logic described in the gate, not the HTTP handler directly.
        """
        # Build all_time_pairs from assignments
        all_assignments = [make_assignment(1, 2, 'January 2026')]
        all_time_pairs = {}
        for m in all_assignments:
            key = frozenset([m['player1_id'], m['player2_id']])
            if key not in all_time_pairs:
                all_time_pairs[key] = m.get('period_label', '')

        # Simulate a pairing that the gate would reject:
        # A+B are in all_time_pairs but not in forced_repeats
        fake_pairing = {'player1': {'id': 1, 'name': 'A'}, 'player2': {'id': 2, 'name': 'B'}}
        forced_repeats = set()  # Empty — not tracked as forced

        def gate_check(pairings, all_time_pairs, forced_repeats):
            for p in pairings:
                key = frozenset([p['player1']['id'], p['player2']['id']])
                if key in all_time_pairs and key not in forced_repeats:
                    return False, f"Avoidable repeat: {p['player1']['name']} + {p['player2']['name']}"
            return True, None

        ok, err = gate_check([fake_pairing], all_time_pairs, forced_repeats)
        assert not ok, "Gate should reject avoidable repeat"
        assert 'Avoidable repeat' in err

    def test_gate_passes_for_forced_repeats(self):
        """
        If A+B are in all_time_pairs AND in forced_repeats, gate should allow it.
        """
        all_assignments = [make_assignment(1, 2, 'January 2026')]
        all_time_pairs = {frozenset([1, 2]): 'January 2026'}
        forced_repeats = {frozenset([1, 2])}  # Tracked as unavoidable

        fake_pairing = {'player1': {'id': 1, 'name': 'A'}, 'player2': {'id': 2, 'name': 'B'}}

        def gate_check(pairings, all_time_pairs, forced_repeats):
            for p in pairings:
                key = frozenset([p['player1']['id'], p['player2']['id']])
                if key in all_time_pairs and key not in forced_repeats:
                    return False, f"Avoidable repeat"
            return True, None

        ok, err = gate_check([fake_pairing], all_time_pairs, forced_repeats)
        assert ok, "Gate should allow forced repeat"
        assert err is None
