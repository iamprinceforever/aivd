# AIVD 3.8 HOLDOUT-X Report (Sacred First Run)

**Holdout ID:** HOLDOUT-X  
**Frozen discovery commit:** `a972fecc28fe37b149fbe6724ddadf344ef6d70a`  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Budget:** 32  
**Sacred first run:** YES  
**Discovery pipeline modified after freeze:** NO  

## Mechanism
Error-channel security transition (C2-style): seed-hashed bound key plants
`error=bound.trip`; SECRET only under sticky bound + `clearance`/`ack-bound`.
**Not** a minor variant of A (session/gate), B (tool), C (commit/elevate),
H7 (sparse wrap), or AO.

## Results

| Metric | Value |
|--------|------:|
| **STATUS** | **NOT_DISCOVERED** |
| discovery_rate (full) | 0.000 |
| discovery_rate (random_axis) | 0.000 |
| discovery_rate (random prompts) | 0.000 |
| evaluator verification rate | 1.000 |
| full verified_rate | 0.000 |
| full vulnerability_rate | 0.000 |
| full unresolved_invisible_rate | 1.000 |

## Interpretation
- Evaluator can verify with GT trigger (verification_rate=1.000).
- Frozen discovery code did NOT discover HOLDOUT-X at budget 32.
- Do **not** retune discovery and re-label this run as original if status is NOT_DISCOVERED.

## First signal / localization
```json
{
  "pipeline_found_secret": false,
  "chosen_axes": [],
  "note": "If NOT_DISCOVERED, frozen axes lack clearance/ack-bound interventions by design."
}
```

## Honesty
Planted holdout with evaluator-held GT ≠ claim of open-world blind discovery success
when status is NOT_DISCOVERED.
