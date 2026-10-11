# AIVD 3.9 HOLDOUT-Y Report (Sacred First Run)

**Holdout ID:** HOLDOUT-Y
**Frozen invention commit:** `95acf3848c742f4b95368e57ecc93f87a2b09d6a`
**Date:** 2026-09-14
**Seeds:** [0, 1, 2, 3, 4, 7, 11]
**Budget:** 32
**Sacred first run:** YES
**Invention pipeline modified after freeze:** NO

## Mechanism
Phase-hold residual (`error=phase.hold`) + release/resume-phase compound.
**Not** a minor variant of A/B/C/H7/AO/X (clearance/ack-bound).

## Results

| Metric | Value |
|--------|------:|
| **STATUS** | **NOT_DISCOVERED** |
| discovery_rate (invention full) | 0.000 |
| discovery_rate (invention off) | 0.000 |
| discovery_rate (random) | 0.000 |
| discovery_rate (heuristic) | 0.000 |
| evaluator verification rate | 1.000 |
| mean probes (full) | 27.0 |
| mean invented (full) | 41.0 |

## Interpretation
- Evaluator verification_rate=1.000.
- Frozen invention status: **NOT_DISCOVERED**.
- Do **not** retune invention and re-label this run as original if NOT_DISCOVERED.

## Honesty
Planted holdout with evaluator-held GT != open-world success when NOT_DISCOVERED.
