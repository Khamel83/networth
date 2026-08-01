# Adaptive Monthly Pairing System

Status: implemented on `codex/redesign`; pending deployment-branch merge and database migration verification
Target branch: `codex/redesign`
Deployment branch: unchanged; this work must not touch `main`/`master`.

## Objective

Replace the current size-limited RMS/greedy matcher with an uncertainty-aware Elo-style rating system and a scalable monthly pairing solver. The system must use only the match scores and roster information the league already collects, work as Players join and leave, and preserve the league's hard rules.

This is a background pairing change. It does not require a player-facing rating screen, new questionnaires, USTA/NTRP integration, or production shadow mode.

## Decisions already resolved

1. Hard exclusions are authoritative.
2. The normal odd-roster case uses the Natalie/Ashley admin-flex rotation.
3. Maximize the number of Players assigned.
4. Maximize fresh pairings whenever a complete fresh assignment is possible.
5. Prefer performance-similar pairings after the previous priorities.
6. New players start neutral with high Rating uncertainty and prefer other New players when feasible.
7. Only completed, complete, valid scores update Ratings.
8. Ratings are rebuilt deterministically from Canonical match records; corrections do not apply a second adjustment.
9. Returning players retain historical Ratings, with increased uncertainty after inactivity.
10. The Rating uses the two-set score and capped game margin; a third set is not required by the current league format.

## Current implementation facts

The current matcher already calculates a rolling average of games won, assigns performance bands, and uses prior pairings and feedback. However:

- The exact matching search stops at 20 Players.
- At 21 or more Players it uses a greedy fallback, so it cannot guarantee the best global fresh pairing.
- The public rules define matches as two sets. The score record contains optional `set3` fields for compatibility, but those fields are not part of the current Rating contract.
- The current pairing run reads a global limit of 500 match rows rather than expressing the Rating source as a canonical, deterministic history.

The new implementation must remove those limitations rather than add another fallback on top of them.

## Raw information and derived information

No new raw data is required. The implementation uses:

- the current eligible roster, active status, availability, membership, and admin-flex identities;
- formal match-assignment history;
- logged two-set match scores and total games;
- explicit “would not play again” feedback.

The new Rating, Rating uncertainty, valid-result count, inactivity state, and pairing-quality score are derived information. Raw match records remain authoritative.

## Rating model

Use one internal Rating module with a small interface:

```text
rebuild_ratings(canonical_matches, player_roster, as_of) -> rating_snapshot
```

The implementation should be an uncertainty-aware Elo-style model, Glicko-like in behavior:

- neutral starting Rating for a New player;
- high starting uncertainty;
- result update from the two-set result and total games won;
- capped margin-of-victory adjustment from the existing score;
- uncertainty decreases as valid results accumulate;
- uncertainty widens during long inactivity;
- invalid, pending, incomplete, or unplayed records are ignored;
- optional legacy `set3` fields are not required and do not affect Ratings;
- a corrected canonical score changes the rebuild result rather than adding a second delta.

The model is not a machine-learning system and does not need to infer from self-reported skill. Its contract is to make future pair quality more informed as valid monthly results accumulate.

### Rating persistence

The raw `matches` table remains the source of truth. A Supabase-backed derived snapshot may store:

- `player_id`;
- current Rating;
- current Rating uncertainty;
- valid-result count;
- last valid-result timestamp;
- model version;
- rebuild timestamp.

The snapshot is a cache and explanation surface, not an authority. Rebuilding from canonical matches must be able to repair it.

## Pairing module

Create one deep pairing module behind a small interface:

```text
build_pairing_plan(
    eligible_players,
    assignment_history,
    canonical_matches,
    hard_blocks,
    period_label,
) -> pairing_plan
```

The plan should contain pairings, unpaired Players, forced repeats, Rating diagnostics, and a deterministic explanation of why any fallback occurred. It must not send email or write assignments itself.

### Matching algorithm

Build a general graph for the current roster. Each allowable Player pair is an edge; hard exclusions remove edges. The matching objective is lexicographic:

1. maximize cardinality;
2. maximize fresh edges / minimize repeats;
3. maximize performance similarity using the Ratings and uncertainty;
4. apply deterministic ID-based tie-breaking.

Use a standard general-graph maximum-weight matching implementation that works beyond 20 Players, targeting rosters from 2 through 100 without a special-size fallback. A pure-Python dependency is acceptable only after verifying its Vercel bundle, cold-start, and runtime behavior; otherwise the algorithm belongs behind the same internal module seam.

### New and returning Players

- New Players have neutral Rating and high uncertainty.
- New-to-new edges receive a preference when feasible, but New status is not a hard exclusion.
- A Returning player keeps historical Rating evidence while uncertainty increases with time away.
- A Player leaving the roster is absent from the current graph but retains raw history and derived state.

### Hard-rule behavior

- “Would not play again” is never overridden.
- Inactive, unavailable, and excluded membership states are never inserted into the graph.
- Natalie/Ashley rotation handles the normal odd roster.
- If the admin-flex rule cannot resolve an odd roster, leave one Player unpaired deterministically and report it; never silently remove an arbitrary Player.
- If no complete fresh assignment exists, use the best maximum-cardinality plan and explicitly label forced repeats.
- No pair may contain the same Player twice.

## Failure-mode review

The following are required invariants and tests:

| Scenario | Required behavior |
| --- | --- |
| 21, 50, or 100 eligible Players | Same general solver; no greedy size fallback |
| Player joins | Enters as neutral/high-uncertainty New Player |
| Player leaves | Removed from current graph; history retained |
| Player returns | Historical Rating retained; uncertainty widened |
| Odd roster | Admin flex first; deterministic reported fallback only if unavailable |
| Hard-blocked graph | Never use a blocked edge |
| No fresh perfect matching | Maximize fresh pairs, then report forced repeats |
| Missing/incomplete score | No Rating update |
| Duplicate score submission | Canonical uniqueness prevents a second result |
| Corrected score | Rebuild replaces its prior influence |
| Partial history query or DB error | Abort before assignment writes or email |
| Solver exception or time budget breach | Abort safely; preserve prior assignments |
| Equal-quality candidates | Stable deterministic tie-break |
| Repeated monthly run | Same inputs produce the same pairing plan |

## Vercel/Supabase shape

- Keep the Rating and pairing calculations in pure Python modules with injected data, so they can be tested without Vercel or Supabase.
- Keep the Vercel handler responsible for authorization, snapshot reads, validation, persistence, and existing no-email delivery gates.
- Use a Supabase migration for any derived snapshot table and constraints.
- Acquire the existing automation run lock before reading the pairing snapshot.
- Read the roster, assignment history, feedback, and canonical scores as one run snapshot.
- Validate the complete plan before writing assignments or invoking any email path.
- Do not dispatch a GitHub workflow or send a test email during implementation.

## Acceptance criteria / implementation check

Implementation is complete only when:

- the 20-Player limit and greedy fallback are gone;
- the same hard rules pass for dynamic rosters through at least 100 Players;
- Rating rebuilds are deterministic and correction-safe;
- two-set score and capped game margin are handled consistently; optional legacy `set3` fields are explicitly excluded from the Rating contract;
- tests cover new, returning, inactive, odd, blocked, duplicate, corrected, and large-roster cases;
- Vercel/Supabase integration is verified without email delivery;
- the working tree remains on `codex/redesign` and `main`/`master` is untouched.
