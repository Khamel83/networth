---
status: accepted
---

# Two-Set Match Format Is Canonical

The current Net Worth league rules define matches as two sets, and rankings use total games won. The adaptive Rating therefore uses the two recorded set scores and their game totals; it must not require a third set or treat a winner-only value as the complete result.

The score-entry schema contains optional `set3` fields for compatibility with existing records or a future rule change. Those fields are not part of the current rating contract and must not affect Ratings unless the league format is explicitly changed and the model is versioned accordingly.
