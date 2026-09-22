# AIVD 3.42 — n_mat Analysis

**Recorded:** 2026-09-22 13:00:57 IST  
**Sacred:** NO  
**Planner mutated:** NO  

## Headline

Inferred lazy n_mat=1 from recorded events: exactly one SELECT before any RANK in every cell (counter={1: 28}). Code path (read-only confirmation): designer._maybe_invent_atom uses n_mat=1 if allow_atom_lazy else 4 — not modified.

## Aggregate

| Metric | Value |
|--------|-------|
| n_mat_inferred_pre_rank | {'1': 28} |
| H11e | **SUPPORTED** |
| H11f | **SUPPORTED** |

## Interpretation

- **Pre-rank window:** exactly one SELECT (=EVEN) before any RANK → lazy single-slot cut.
- **Post-rank window:** ODD best_rank stays ≥1; with n_mat=1 only rank-0 materializes → ODD never SELECTED.
- Offline CF1: if recorded board0 were consumed with n_mat≥2, board0[1]==ODD would be next SELECT in 28/28.

See `reports/aivd_3_42_n_mat_analysis.json`.
