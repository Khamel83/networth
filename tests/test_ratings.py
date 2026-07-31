"""Behavioral tests for the deterministic two-set player rating model."""

from api.ratings import (
    canonicalize_matches,
    is_valid_rating_match,
    rebuild_ratings,
)


def make_match(
    player1_id,
    player2_id,
    *,
    match_id=None,
    set1_p1=6,
    set1_p2=4,
    set2_p1=6,
    set2_p2=3,
    period_label="January 2026",
    created_at="2026-01-15T12:00:00+00:00",
    updated_at=None,
    status="confirmed",
    is_forfeit=False,
):
    return {
        "id": match_id,
        "player1_id": player1_id,
        "player2_id": player2_id,
        "set1_p1": set1_p1,
        "set1_p2": set1_p2,
        "set2_p1": set2_p1,
        "set2_p2": set2_p2,
        "period_label": period_label,
        "created_at": created_at,
        "updated_at": updated_at,
        "status": status,
        "is_forfeit": is_forfeit,
    }


def test_two_set_scores_are_complete_without_a_third_set():
    match = make_match(1, 2, set1_p1=6, set1_p2=0, set2_p1=6, set2_p2=0)

    assert is_valid_rating_match(match) is True

    ratings = rebuild_ratings([match], player_roster=[{"id": 1}, {"id": 2}])
    assert ratings[1]["valid_results"] == 1
    assert ratings[2]["valid_results"] == 1
    assert ratings[1]["rating"] > ratings[2]["rating"]


def test_six_six_set_draw_is_valid_under_league_rules():
    match = make_match(1, 2, set1_p1=6, set1_p2=6, set2_p1=6, set2_p2=4)

    assert is_valid_rating_match(match) is True


def test_game_margin_changes_rating_update():
    straight_sets = make_match(1, 2, set1_p1=6, set1_p2=0, set2_p1=6, set2_p2=0)
    close_sets = make_match(1, 2, set1_p1=7, set1_p2=5, set2_p1=7, set2_p2=5)

    straight = rebuild_ratings([straight_sets], player_roster=[{"id": 1}, {"id": 2}])
    close = rebuild_ratings([close_sets], player_roster=[{"id": 1}, {"id": 2}])

    assert straight[1]["rating"] > close[1]["rating"]


def test_explicit_forfeit_uses_stored_valid_total_without_two_played_sets():
    forfeit = make_match(
        1,
        2,
        set1_p1=0,
        set1_p2=0,
        set2_p1=0,
        set2_p2=0,
        is_forfeit=True,
    )
    forfeit["player1_games"] = 6
    forfeit["player2_games"] = 0

    assert is_valid_rating_match(forfeit) is True
    ratings = rebuild_ratings([forfeit], player_roster=[{"id": 1}, {"id": 2}])
    assert ratings[1]["rating"] > ratings[2]["rating"]


def test_optional_third_set_fields_do_not_change_two_set_rating():
    two_set = make_match(1, 2, match_id="m1")
    legacy_with_set3 = {**two_set, "set3_p1": 0, "set3_p2": 6}

    without_set3 = rebuild_ratings([two_set], player_roster=[{"id": 1}, {"id": 2}])
    with_set3 = rebuild_ratings([legacy_with_set3], player_roster=[{"id": 1}, {"id": 2}])

    assert with_set3 == without_set3


def test_pending_incomplete_and_disputed_matches_do_not_update_ratings():
    pending = make_match(1, 2, status="pending")
    incomplete = make_match(1, 3, set2_p1=None, set2_p2=None)
    disputed = make_match(1, 4, status="disputed")
    unfinished_set = make_match(1, 5, set1_p1=6, set1_p2=5)

    assert is_valid_rating_match(pending) is False
    assert is_valid_rating_match(incomplete) is False
    assert is_valid_rating_match(disputed) is False
    assert is_valid_rating_match(unfinished_set) is False

    ratings = rebuild_ratings(
        [pending, incomplete, disputed],
        player_roster=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
    )
    assert all(state["valid_results"] == 0 for state in ratings.values())


def test_rebuild_is_order_independent_and_a_correction_replaces_the_result():
    first = make_match(1, 2, match_id="m1")
    second = make_match(
        2,
        3,
        match_id="m2",
        period_label="February 2026",
        created_at="2026-02-15T12:00:00+00:00",
    )
    roster = [{"id": 1}, {"id": 2}, {"id": 3}]

    forward = rebuild_ratings([first, second], player_roster=roster)
    reverse = rebuild_ratings([second, first], player_roster=roster)
    assert forward == reverse

    corrected = {**first, "set1_p1": 0, "set1_p2": 6, "set2_p1": 0, "set2_p2": 6}
    rebuilt = rebuild_ratings([corrected, second], player_roster=roster)
    assert rebuilt[1]["rating"] < forward[1]["rating"]


def test_duplicate_natural_match_key_uses_latest_canonical_record():
    original = make_match(
        1,
        2,
        match_id="old",
        created_at="2026-01-15T12:00:00+00:00",
    )
    correction = make_match(
        2,
        1,
        match_id="new",
        set1_p1=0,
        set1_p2=6,
        set2_p1=0,
        set2_p2=6,
        created_at="2026-01-16T12:00:00+00:00",
    )

    canonical = canonicalize_matches([original, correction])

    assert len(canonical) == 1
    assert canonical[0]["id"] == "new"
    ratings = rebuild_ratings(canonical, player_roster=[{"id": 1}, {"id": 2}])
    # The correction stores player 2 as player 1 but gives the win to the
    # second participant, player 1.
    assert ratings[1]["rating"] > ratings[2]["rating"]


def test_updated_record_wins_even_when_created_at_is_older():
    original = make_match(
        1,
        2,
        match_id="m1",
        created_at="2026-01-15T12:00:00+00:00",
        updated_at="2026-01-15T12:00:00+00:00",
    )
    correction = make_match(
        1,
        2,
        match_id="m2",
        set1_p1=0,
        set1_p2=6,
        set2_p1=0,
        set2_p2=6,
        created_at="2026-01-15T12:00:00+00:00",
        updated_at="2026-01-20T12:00:00+00:00",
    )

    canonical = canonicalize_matches([original, correction])

    assert canonical[0]["id"] == "m2"


def test_returning_player_has_wider_uncertainty_after_long_inactivity():
    match = make_match(
        1,
        2,
        created_at="2025-01-15T12:00:00+00:00",
        period_label="January 2025",
    )

    recent = rebuild_ratings(
        [match],
        player_roster=[{"id": 1}, {"id": 2}],
        as_of="2025-02-15T12:00:00+00:00",
    )
    returning = rebuild_ratings(
        [match],
        player_roster=[{"id": 1}, {"id": 2}],
        as_of="2026-07-31T12:00:00+00:00",
    )

    assert returning[1]["uncertainty"] > recent[1]["uncertainty"]
    assert returning[1]["rating"] == recent[1]["rating"]
