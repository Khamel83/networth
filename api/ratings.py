"""Deterministic, uncertainty-aware ratings for Net Worth's two-set matches.

The database match history remains authoritative.  This module deliberately
keeps the model pure: it reads plain dictionaries and returns a new snapshot,
which makes corrections, rebuilds, and tests deterministic.
"""

from datetime import date, datetime, timezone
from math import sqrt
from typing import Any, Dict, Iterable, List, Optional, Tuple


MODEL_VERSION = "elo-two-set-v1"
INITIAL_RATING = 1500.0
INITIAL_UNCERTAINTY = 350.0
MIN_UNCERTAINTY = 60.0
MAX_UNCERTAINTY = 400.0
BASE_K = 24.0
INACTIVITY_SCALE = 45.0

_INVALID_STATUSES = {
    "pending",
    "incomplete",
    "unplayed",
    "disputed",
    "cancelled",
    "declined",
    "expired",
}


def _normalise_id(value: Any) -> str:
    return str(value)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse the timestamp/date shapes used by Supabase and the tests."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = datetime.strptime(text, "%B %Y")
            except ValueError:
                try:
                    parsed = datetime.strptime(text, "%Y-%m-%d")
                except ValueError:
                    return None
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _match_time(match: Dict[str, Any]) -> datetime:
    """Choose a stable event time for chronological replay."""
    for field in ("match_date", "created_at", "updated_at", "period_label"):
        parsed = _parse_datetime(match.get(field))
        if parsed is not None:
            return parsed
    return datetime.min.replace(tzinfo=timezone.utc)


def _record_recency(match: Dict[str, Any]) -> datetime:
    """Choose the timestamp that identifies the latest correction record."""
    for field in ("updated_at", "created_at", "match_date", "period_label"):
        parsed = _parse_datetime(match.get(field))
        if parsed is not None:
            return parsed
    return datetime.min.replace(tzinfo=timezone.utc)


def _canonical_key(match: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    player1 = match.get("player1_id")
    player2 = match.get("player2_id")
    if player1 is None or player2 is None or player1 == player2:
        return None
    first, second = sorted((_normalise_id(player1), _normalise_id(player2)))
    period = str(match.get("period_label") or "").strip()
    return first, second, period


def canonicalize_matches(matches: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return one deterministic record per unordered player/period key.

    Supabase normally enforces one match per pair and period.  The extra
    canonicalisation protects rebuilds from legacy duplicates: the most recent
    record wins, with the record id as a deterministic final tie-breaker.
    """
    latest: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    recency: Dict[Tuple[str, str, str], Tuple[datetime, str]] = {}

    for match in matches:
        key = _canonical_key(match)
        if key is None:
            continue
        candidate_key = (_record_recency(match), str(match.get("id") or ""))
        if key not in latest or candidate_key > recency[key]:
            latest[key] = dict(match)
            recency[key] = candidate_key

    return [
        latest[key]
        for key in sorted(latest, key=lambda item: (item[2], item[0], item[1]))
    ]


def _score_value(match: Dict[str, Any], field: str) -> Optional[int]:
    value = match.get(field)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _two_set_games(match: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    values = {
        field: _score_value(match, field)
        for field in ("set1_p1", "set1_p2", "set2_p1", "set2_p2")
    }
    if any(value is None for value in values.values()):
        return None

    set1 = (values["set1_p1"], values["set1_p2"])
    set2 = (values["set2_p1"], values["set2_p2"])
    for player1_games, player2_games in (set1, set2):
        # A two-set match records finished sets only.  This rejects blank
        # forms (0-0), ties, and impossible values without overfitting to a
        # particular tiebreak scoring convention.
        if not (0 <= player1_games <= 7 and 0 <= player2_games <= 7):
            return None
        high, low = max(player1_games, player2_games), min(player1_games, player2_games)
        # Net Worth has no tiebreakers: a set may finish 6-0 through 6-4,
        # finish 7-5, or finish 6-6 as a draw.
        valid_set = (high == 6 and low <= 4) or (high == 6 and low == 6) or (high == 7 and low == 5)
        if not valid_set:
            return None

    return set1[0] + set2[0], set1[1] + set2[1]


def _rating_games(match: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """Get the score evidence used by ratings, including explicit forfeits."""
    if match.get("is_forfeit"):
        player1_games = _score_value(match, "player1_games")
        player2_games = _score_value(match, "player2_games")
        if (
            player1_games is not None
            and player2_games is not None
            and player1_games >= 0
            and player2_games >= 0
            and player1_games != player2_games
        ):
            return player1_games, player2_games
    return _two_set_games(match)


def is_valid_rating_match(match: Dict[str, Any]) -> bool:
    """Return whether a stored match may influence the rating model."""
    player1 = match.get("player1_id")
    player2 = match.get("player2_id")
    if player1 is None or player2 is None or player1 == player2:
        return False

    status = str(match.get("status") or "reported").strip().lower()
    if status in _INVALID_STATUSES:
        return False

    games = _rating_games(match)
    if games is None:
        return False

    # A forfeit is valid only when it is explicitly marked and still contains
    # a decisive score.  The current score flow records the winning player as
    # player 1; a future winner_id field is also accepted.
    if match.get("is_forfeit"):
        winner_id = match.get("winner_id")
        if winner_id is not None and winner_id not in (player1, player2):
            return False
        if winner_id is None and games[0] == games[1]:
            return False

    return True


def _initial_state() -> Dict[str, Any]:
    return {
        "rating": INITIAL_RATING,
        "uncertainty": INITIAL_UNCERTAINTY,
        "valid_results": 0,
        "last_result_at": None,
        "model_version": MODEL_VERSION,
    }


def new_rating_state() -> Dict[str, Any]:
    """Return a fresh neutral state for a player with no valid results."""
    return _initial_state()


def _player_ids(player_roster: Optional[Iterable[Any]]) -> List[Any]:
    ids: List[Any] = []
    for player in player_roster or []:
        player_id = player.get("id") if isinstance(player, dict) else player
        if player_id is not None and player_id not in ids:
            ids.append(player_id)
    return ids


def _inflate_uncertainty(state: Dict[str, Any], as_of: datetime) -> None:
    last_result = _parse_datetime(state.get("last_result_at"))
    if last_result is None or as_of <= last_result:
        return
    inactive_months = (as_of - last_result).total_seconds() / (30.4375 * 86400)
    state["uncertainty"] = min(
        MAX_UNCERTAINTY,
        sqrt(state["uncertainty"] ** 2 + (INACTIVITY_SCALE ** 2) * inactive_months),
    )


def _actual_result(match: Dict[str, Any], games: Tuple[int, int]) -> float:
    winner_id = match.get("winner_id")
    if match.get("is_forfeit") and winner_id is not None:
        return 1.0 if winner_id == match.get("player1_id") else 0.0
    if games[0] > games[1]:
        return 1.0
    if games[0] < games[1]:
        return 0.0
    return 0.5


def _expected_result(rating1: float, rating2: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating2 - rating1) / 400.0))


def rebuild_ratings(
    canonical_matches: Iterable[Dict[str, Any]],
    player_roster: Optional[Iterable[Any]] = None,
    as_of: Any = None,
) -> Dict[Any, Dict[str, Any]]:
    """Replay valid two-set results and return a deterministic rating snapshot."""
    records = canonicalize_matches(canonical_matches)
    states: Dict[Any, Dict[str, Any]] = {
        player_id: _initial_state() for player_id in _player_ids(player_roster)
    }

    valid_records = [record for record in records if is_valid_rating_match(record)]
    for record in valid_records:
        player1 = record["player1_id"]
        player2 = record["player2_id"]
        states.setdefault(player1, _initial_state())
        states.setdefault(player2, _initial_state())

    if as_of is None:
        replay_as_of = max((_match_time(record) for record in valid_records), default=None)
    else:
        replay_as_of = _parse_datetime(as_of)

    valid_records.sort(key=lambda record: (_match_time(record), str(record.get("id") or "")))
    for record in valid_records:
        player1 = record["player1_id"]
        player2 = record["player2_id"]
        event_time = _match_time(record)
        state1 = states[player1]
        state2 = states[player2]
        _inflate_uncertainty(state1, event_time)
        _inflate_uncertainty(state2, event_time)

        games = _rating_games(record)
        if games is None:  # Defensive: valid_records already filtered.
            continue
        expected = _expected_result(state1["rating"], state2["rating"])
        actual = _actual_result(record, games)
        margin_multiplier = 1.0 + min(abs(games[0] - games[1]) / 7.0, 1.0)
        uncertainty_factor = min(
            1.5,
            max(
                0.5,
                (state1["uncertainty"] + state2["uncertainty"])
                / (2.0 * INITIAL_UNCERTAINTY),
            ),
        )
        delta = BASE_K * uncertainty_factor * margin_multiplier * (actual - expected)

        state1["rating"] += delta
        state2["rating"] -= delta
        state1["uncertainty"] = max(MIN_UNCERTAINTY, state1["uncertainty"] * 0.88)
        state2["uncertainty"] = max(MIN_UNCERTAINTY, state2["uncertainty"] * 0.88)
        state1["valid_results"] += 1
        state2["valid_results"] += 1
        timestamp = event_time.isoformat()
        state1["last_result_at"] = timestamp
        state2["last_result_at"] = timestamp

    if replay_as_of is not None:
        for state in states.values():
            _inflate_uncertainty(state, replay_as_of)

    # Rounding makes JSON snapshots stable across equivalent floating point
    # execution paths while preserving more precision than the UI needs.
    for state in states.values():
        state["rating"] = round(state["rating"], 6)
        state["uncertainty"] = round(state["uncertainty"], 6)

    return states
