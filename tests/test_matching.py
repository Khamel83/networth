"""Behavioral tests for the scalable general-graph pairing solver."""

from api.matching import build_pairing_plan


def make_player(player_id, name=None):
    return {
        "id": player_id,
        "name": name or f"Player {player_id}",
        "email": f"player{player_id}@example.net",
        "avail_weekday_day": True,
        "avail_weekend_day": True,
    }


def make_result(player1_id, player2_id, *, player1_wins, period):
    year = 2026 + (period - 1) // 12
    month = (period - 1) % 12 + 1
    return {
        "id": f"{period}-{player1_id}-{player2_id}",
        "player1_id": player1_id,
        "player2_id": player2_id,
        "set1_p1": 6 if player1_wins else 0,
        "set1_p2": 0 if player1_wins else 6,
        "set2_p1": 6 if player1_wins else 0,
        "set2_p2": 0 if player1_wins else 6,
        "period_label": f"Test {period}",
        "created_at": f"{year}-{month:02d}-15T12:00:00+00:00",
        "status": "confirmed",
    }


def ids_from_plan(plan):
    return {
        frozenset((pair["player1"]["id"], pair["player2"]["id"]))
        for pair in plan["pairings"]
    }


def test_solver_pairs_fifty_players_without_a_size_fallback():
    players = [make_player(i) for i in range(1, 51)]

    plan = build_pairing_plan(
        players,
        assignment_history=[],
        canonical_matches=[],
        hard_blocks=[],
        period_label="August 2026",
    )

    assert len(plan["pairings"]) == 25
    assert plan["unpaired"] == []
    assert len(ids_from_plan(plan)) == 25


def test_solver_handles_one_hundred_players_without_a_greedy_branch():
    players = [make_player(i) for i in range(1, 101)]

    plan = build_pairing_plan(
        players,
        assignment_history=[],
        canonical_matches=[],
        hard_blocks=[],
        period_label="August 2026",
    )

    assert len(plan["pairings"]) == 50
    assert plan["unpaired"] == []


def test_hard_exclusion_is_never_overridden():
    players = [make_player(1), make_player(2)]

    plan = build_pairing_plan(
        players,
        assignment_history=[],
        canonical_matches=[],
        hard_blocks=[{"player_a": 1, "player_b": 2}],
        period_label="August 2026",
    )

    assert plan["pairings"] == []
    assert {player["id"] for player in plan["unpaired"]} == {1, 2}


def test_fresh_pairings_beat_repeats_when_a_complete_fresh_plan_exists():
    players = [make_player(i) for i in range(1, 5)]
    history = [{"player1_id": 1, "player2_id": 2, "period_label": "July 2026"}]

    plan = build_pairing_plan(
        players,
        assignment_history=history,
        canonical_matches=[],
        hard_blocks=[],
        period_label="August 2026",
    )

    assert len(plan["pairings"]) == 2
    assert frozenset((1, 2)) not in ids_from_plan(plan)
    assert plan["forced_repeats"] == []


def test_solver_maximizes_assignments_before_similarity():
    players = [make_player(1), make_player(2), make_player(3)]

    plan = build_pairing_plan(
        players,
        assignment_history=[],
        canonical_matches=[],
        hard_blocks=[{"player_a": 1, "player_b": 2}],
        period_label="August 2026",
    )

    assert len(plan["pairings"]) == 1
    assert len(plan["unpaired"]) == 1
    assert plan["pairings"][0]["player1"]["id"] != 1 or plan["pairings"][0]["player2"]["id"] != 2


def test_rating_history_drives_similarity_priority():
    players = [make_player(i) for i in range(1, 5)]
    results = []
    for index in range(10):
        results.extend(
            [
                make_result(1, 101 + index, player1_wins=True, period=1 + index),
                make_result(2, 201 + index, player1_wins=True, period=21 + index),
                make_result(3, 301 + index, player1_wins=False, period=41 + index),
                make_result(4, 401 + index, player1_wins=False, period=61 + index),
            ]
        )

    plan = build_pairing_plan(
        players,
        assignment_history=[],
        canonical_matches=results,
        hard_blocks=[],
        period_label="August 2026",
    )

    assert ids_from_plan(plan) == {
        frozenset((1, 2)),
        frozenset((3, 4)),
    }


def test_plan_is_deterministic_for_same_inputs():
    players = [make_player(i) for i in range(1, 9)]
    kwargs = {
        "assignment_history": [],
        "canonical_matches": [],
        "hard_blocks": [],
        "period_label": "August 2026",
    }

    first = build_pairing_plan(players, **kwargs)
    second = build_pairing_plan(players, **kwargs)

    assert [
        (pair["player1"]["id"], pair["player2"]["id"])
        for pair in first["pairings"]
    ] == [
        (pair["player1"]["id"], pair["player2"]["id"])
        for pair in second["pairings"]
    ]
