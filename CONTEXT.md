# Net Worth Tennis Matching

This context defines the language and invariants for assigning monthly matches in a small, dynamic women's tennis league.

## Pairing rules

**Eligible player**:
A currently active Player who is participating in the monthly ladder and is available for assignment.
_Avoid_: roster member, user, account

**Hard exclusion**:
A condition that makes a pairing invalid, such as unavailable status or a player's explicit “would not play again” feedback about the other player.
_Avoid_: preference, penalty

**Fresh pairing**:
A pairing between two Players who have not previously played each other in a formal assignment or logged extra match.
_Avoid_: new match, unused pairing

**Repeat pairing**:
A pairing between two Players who have already played each other.
_Avoid_: duplicate match

**Performance similarity**:
How close two Players' observed recent match results are; it is a pairing preference, not a hard exclusion.
_Avoid_: exact skill, guaranteed competitiveness

**Rating**:
A derived estimate of a Player's competitive ability based on logged Net Worth match results, not a self-reported USTA/NTRP level.
_Avoid_: skill level, rank, certainty

**Rating uncertainty**:
The system's measure of how much confidence it has in a Player's Rating; it is highest for New players and decreases as valid results accumulate.
_Avoid_: error, inexperience

**Valid rating result**:
A completed Net Worth two-set match with a complete, valid score that is eligible to influence Ratings. The league's official ranking signal is total games won, not a separate match-win table.
_Avoid_: scheduled match, submitted form, reported attempt

**Two-set match**:
The current league match format: two recorded sets, with the score and total games won providing the result data. Optional `set3` storage fields are compatibility fields, not a required part of the current format.
_Avoid_: three-set requirement, winner-only result

**Canonical match record**:
The single authoritative record of a Player pair's completed result for a pairing period; corrections replace its score rather than create a second result.
_Avoid_: submission, attempt, duplicate result

**Rating rebuild**:
A deterministic recalculation of Ratings from the current set of Canonical match records.
_Avoid_: rating retry, rating patch

**New player**:
An Eligible player with no completed Net Worth match results available when a pairing cycle is calculated.
_Avoid_: unskilled player, unranked player

**Returning player**:
A Player with prior valid results who re-enters the eligible roster after an absence.
_Avoid_: new player, inactive player

**Admin flex**:
Natalie or Ashley, who voluntarily sits out according to the league's rotation rule when the eligible roster is odd so the remaining Players can be paired.
_Avoid_: skipped player, exception player
<!-- janitor:begin:recent -->
- `d05eefbcf86ae9243a9f76e6da20c494eb68b1aa`: merged pull request #22.
- `e9305e6f7e95fd2672ed901b5664e8ded8fb2690`: updated the watchdog to require an accepted match email for every actual pairing.
- `ebf6d2ea023de5aafc38a8a9a915218cc886739e`: documented that the repository should remain public and that the watchdog covers GitHub's 60-day schedule shutoff.
- `e4862c38b99a7d40b28047a46d7c2b9a7b7d0d49`: changed watchdog recovery so a failure is fixed only by a success that started after it.
- `94844a6b3c55492a252c74347a1575f0a2ce393d`: updated watchdog handling for late 27th jobs, duplicate pairing counts, and alert-send failures.
- `aab591fdcd36908a3963b75900a3f5a19438039b`: added an independent daily watchdog that emails the owner via Resend.
<!-- janitor:end:recent -->
