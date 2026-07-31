---
status: accepted
---

# Uncertainty-Aware Player Ratings

The matcher will replace its current rolling RMS signal with an uncertainty-aware Elo-style Rating derived from the existing monthly two-set match scores. New players start at a neutral Rating with high Rating uncertainty; valid logged results update the Rating and uncertainty over time. Self-reported skill levels remain descriptive inputs, not the source of the pairing Rating, and no new raw data collection is required.
