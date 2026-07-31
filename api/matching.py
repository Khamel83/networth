"""Scalable general-graph pairing engine.

The module is intentionally independent of Vercel, Supabase, and email.  It
turns a complete run snapshot into a pairing plan and leaves persistence to the
HTTP handler.
"""

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from api.ratings import new_rating_state, rebuild_ratings


# A single fresh-edge bonus must exceed the maximum possible aggregate
# similarity component for the supported 100-player roster (50 edges).
_MAX_SIMILARITY_SCORE = 1150


def _stable_id(value: Any) -> str:
    return str(value)


def _pair_key(player1_id: Any, player2_id: Any) -> frozenset:
    return frozenset((_stable_id(player1_id), _stable_id(player2_id)))


def _availability_text(player: Dict[str, Any]) -> str:
    six_slots = (
        "avail_weekday_early",
        "avail_weekday_day",
        "avail_weekday_late",
        "avail_weekend_early",
        "avail_weekend_day",
        "avail_weekend_late",
    )
    if not any(player.get(field, False) for field in six_slots):
        old_slots = (
            ("available_morning", "Mornings"),
            ("available_afternoon", "Afternoons"),
            ("available_evening", "Evenings"),
        )
        selected = [label for field, label in old_slots if player.get(field, False)]
        if len(selected) == len(old_slots):
            return "Any time"
        return ", ".join(selected)

    weekday = [
        label
        for field, label in (
            ("avail_weekday_early", "before 9am"),
            ("avail_weekday_day", "9-5"),
            ("avail_weekday_late", "after 5pm"),
        )
        if player.get(field, False)
    ]
    weekend = [
        label
        for field, label in (
            ("avail_weekend_early", "before 9am"),
            ("avail_weekend_day", "9-5"),
            ("avail_weekend_late", "after 5pm"),
        )
        if player.get(field, False)
    ]
    parts = []
    if weekday:
        parts.append(f"Weekdays: {', '.join(weekday)}")
    if weekend:
        parts.append(f"Weekends: {', '.join(weekend)}")
    return " | ".join(parts)


def _hard_block_set(hard_blocks: Iterable[Dict[str, Any]]) -> Set[frozenset]:
    blocked: Set[frozenset] = set()
    for block in hard_blocks or []:
        player1 = block.get("player_a", block.get("from_player_id"))
        player2 = block.get("player_b", block.get("about_player_id"))
        if player1 is not None and player2 is not None and player1 != player2:
            blocked.add(_pair_key(player1, player2))
    return blocked


def _history_pairs(
    assignment_history: Iterable[Dict[str, Any]],
    canonical_matches: Iterable[Dict[str, Any]],
) -> Set[frozenset]:
    pairs: Set[frozenset] = set()
    for record in list(assignment_history or []) + list(canonical_matches or []):
        player1 = record.get("player1_id")
        player2 = record.get("player2_id")
        if player1 is not None and player2 is not None and player1 != player2:
            pairs.add(_pair_key(player1, player2))
    return pairs


def _rating_state(ratings: Dict[Any, Dict[str, Any]], player_id: Any) -> Dict[str, Any]:
    state = ratings.get(player_id)
    if state is None:
        state = ratings.get(str(player_id))
    return state or new_rating_state()


def _enrich_players(players: Iterable[Dict[str, Any]], ratings: Dict[Any, Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for player in players:
        state = _rating_state(ratings, player.get("id"))
        copy = dict(player)
        copy.update(
            {
                "rating": state["rating"],
                "uncertainty": state["uncertainty"],
                "valid_results": state["valid_results"],
                "last_result_at": state["last_result_at"],
                "rating_model_version": state["model_version"],
                "is_new_player": state["valid_results"] == 0,
            }
        )
        enriched.append(copy)
    return enriched


def _similarity_score(player1: Dict[str, Any], player2: Dict[str, Any]) -> int:
    rating_gap = abs(float(player1["rating"]) - float(player2["rating"]))
    uncertainty_allowance = (
        float(player1["uncertainty"]) + float(player2["uncertainty"])
    ) * 0.35
    effective_gap = max(0.0, rating_gap - uncertainty_allowance)
    score = max(0, 1000 - int(round(effective_gap)))

    if player1["is_new_player"] and player2["is_new_player"]:
        score += 150
    elif player1["is_new_player"] or player2["is_new_player"]:
        score += 40
    return score


def _edge_weight(
    similarity: int,
    fresh: bool,
    tie_bonus: int,
    similarity_weight: int,
    fresh_weight: int,
) -> int:
    return (
        (1 if fresh else 0) * fresh_weight
        + similarity * similarity_weight
        + tie_bonus
    )


def build_pairing_plan(
    eligible_players: Iterable[Dict[str, Any]],
    assignment_history: Iterable[Dict[str, Any]],
    canonical_matches: Iterable[Dict[str, Any]],
    hard_blocks: Iterable[Dict[str, Any]],
    period_label: str,
    as_of: Any = None,
) -> Dict[str, Any]:
    """Build a lexicographically optimized pairing plan.

    NetworkX's Edmonds blossom implementation provides maximum-weight general
    graph matching, so this works for odd rosters and rosters well above the
    old 20-player exact-search limit. ``maxcardinality=True`` makes the hard
    first objective explicit; edge weights then maximize fresh pairings,
    performance similarity, and deterministic tie-breaking in that order.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - deployment misconfiguration
        raise RuntimeError("networkx is required for the pairing solver") from exc

    assignment_history = list(assignment_history or [])
    canonical_matches = list(canonical_matches or [])
    players = sorted(
        [dict(player) for player in eligible_players],
        key=lambda player: _stable_id(player.get("id")),
    )
    ratings = rebuild_ratings(canonical_matches, player_roster=players, as_of=as_of)
    players = _enrich_players(players, ratings)
    history_pairs = _history_pairs(assignment_history, canonical_matches)
    blocked = _hard_block_set(hard_blocks)

    graph = nx.Graph()
    graph.add_nodes_from(range(len(players)))
    edge_metadata: Dict[Tuple[int, int], Dict[str, Any]] = {}
    possible_edges = [
        (i, j)
        for i in range(len(players))
        for j in range(i + 1, len(players))
        if _pair_key(players[i]["id"], players[j]["id"]) not in blocked
    ]
    possible_edges.sort(
        key=lambda edge: (
            _stable_id(players[edge[0]]["id"]),
            _stable_id(players[edge[1]]["id"]),
        )
    )
    tie_count = len(possible_edges)
    # Make the deterministic tie component smaller than one total-similarity
    # point, while making one fresh edge more valuable than every possible
    # similarity point across a 100-player matching.
    tie_total = tie_count * (tie_count + 1) // 2
    similarity_weight = tie_total + 1
    fresh_weight = (
        max(1, len(players) // 2) * _MAX_SIMILARITY_SCORE * similarity_weight
        + tie_total
        + 1
    )

    for rank, (i, j) in enumerate(possible_edges):
        pair = _pair_key(players[i]["id"], players[j]["id"])
        fresh = pair not in history_pairs
        similarity = _similarity_score(players[i], players[j])
        tie_bonus = tie_count - rank
        graph.add_edge(
            i,
            j,
            weight=_edge_weight(
                similarity,
                fresh,
                tie_bonus,
                similarity_weight,
                fresh_weight,
            ),
        )
        edge_metadata[(i, j)] = {
            "fresh": fresh,
            "similarity": similarity,
            "pair": pair,
        }

    matching = nx.algorithms.matching.max_weight_matching(
        graph,
        maxcardinality=True,
        weight="weight",
    )

    pairings = []
    matched_nodes = set()
    forced_repeats = []
    for left, right in matching:
        i, j = sorted((left, right))
        p1 = players[i]
        p2 = players[j]
        metadata = edge_metadata[(i, j)]
        matched_nodes.update((i, j))
        if not metadata["fresh"]:
            forced_repeats.append(frozenset((p1["id"], p2["id"])))
        pairings.append(
            {
                "player1": p1,
                "player2": p2,
                "player1_availability": _availability_text(p1),
                "player2_availability": _availability_text(p2),
                "score": metadata["similarity"],
                "similarity_score": metadata["similarity"],
                "fresh": metadata["fresh"],
                "forced_repeat": not metadata["fresh"],
                "band": "new" if p1["is_new_player"] and p2["is_new_player"] else "rated",
            }
        )

    pairings.sort(
        key=lambda pair: (
            _stable_id(pair["player1"]["id"]),
            _stable_id(pair["player2"]["id"]),
        )
    )
    unpaired = [player for index, player in enumerate(players) if index not in matched_nodes]
    forced_repeats.sort(key=lambda pair: tuple(sorted(pair)))

    return {
        "period_label": period_label,
        "pairings": pairings,
        "unpaired": unpaired,
        "forced_repeats": forced_repeats,
        "ratings": ratings,
        "solver": "general-graph-max-weight-matching",
    }
