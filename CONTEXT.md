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
- 260e28489fdc39ced90091167f1a297e96a68ae1: Merge pull request #18 from Khamel83/claude/logo-admin-scores-qqfb3p
- ccd1f8c39c344b5704c7a547fd3df7ffdfed905d: Email the monthly report to Natalie and Ashley
- b9af2b83ea6405a9cb8155f9b8a8911ade36b797: Merge pull request #17 from Khamel83/claude/logo-admin-scores-qqfb3p
- 03de7a81555041243c3ef0e876169c1984744e4c: Don't fail closing a pairing on older schema; skip reminders for recorded scores
- d90b2e307b829a3102165fb5eb1fc6b72bfd6449: Close pairings atomically with the match insert; self-heal dashboard
- 0354f370920e6bfc6779d0577d404228133a66a4: Reset I-paid on rejoin; only fall back on a confirmed missing column
- 44a8f0931cff0ab2208b318fe63fb18df800cf41: Limit player-reported months and neutralize CSV formulas
- 539d49a77940ffba65e265ad0343297dc2121657: Require the atomic DB function for score corrections
- 0659d346c35724741605ba0b77050c8abbc84bf9: Show pairing scores in the pairing's player order
- 05387696d2b1859d8df6c9a4afb5c443ee5e1165: Atomic score correction via DB function; remove names from inline handlers
- e2e78395606196790b991b43c40e84e6964a9bfc: Validate pairing before saving a score and heal half-finished saves
- 84705773fd026bb98df86f41002d705fc53341e3: Animated logo and saved "I paid" checkbox
- a8afb0efa45fe6c2120382304ec1482b6f69d7d9: Harden admin score edits and scope monthly report standings
- 17129e7a32dd702a1ed749a79e5efebdff585a11: Add new logo, admin score entry, monthly report, and Venmo pay step
- 90dbee9385895ad54178881cca8521ac442bfe75: fix: accept pairing delivery outcome in workflow
- 40b45d906df9a6ceae7dc28c220c552008b426e1: fix: fail pairing health checks on empty months
- 555490c2c1805ca55e17c72baef210a09b058ce0: fix: make monthly pairing delivery fail loudly
- 83c69bf5746dfc58ccafb107e8118e380d137342: docs: align Venmo link plan copy
- 6ecc65931f53617bafad3b9eb3d4266f123913e3: feat: add prefilled Venmo links to join page
- 2883cf7d8db91620541251a9d39e9a12551cca01: test: define join page Venmo payment links
<!-- janitor:end:recent -->
