# AIVD 3.41 — Audit Execution Report

**Recorded:** 2026-09-22 12:57:05 IST
**Implementation tip:** `a56586e649f00219f10d22a041de7bdee2ce3d14`
**Branch:** `research/aivd-3.41-invention-planner-audit`
**Authorization:** AIVD 3.41 AUDIT EXECUTION AUTHORIZATION — INSTRUMENTED OBSERVATIONAL RUNS ONLY
**Mode:** `AIVD41_PLANNER_AUDIT`
**Sacred:** NO

## Harness

- Deterministic mock plant: `HX8OddStride` via `UnknownsPipeline` / `full_3_39_r1`
- BH=48, invent_cap=48, REDISCOVERY_FLOOR=5, seeds[0,1,2,3,4,7,11]
- Conditions labeled S8-BASELINE/S8-RA/S8-RC/S8-RD as Stage-8 priors
- R-A/R-C/R-D FILTER **not** integrated (FORBIDDEN under this authorization)
- Frozen Stage-8 JSONs cross-referenced for post-pool context only
- NOT claimed as Sacred discovery results

## Matrix

- ON cells: 28
- OFF cells: 28
- Expected: 28
- Completed: True
- Elapsed: 2.15s

## Twin equality

**PASS**
STOP: null

## RNG integrity

**PASS**

## Odd-stride fate (summary)

Candidate `MAPT(SLICE:1,2(TOK))` @ proposal_index=3:
- Proposed in 28/28 cells
- Selected in 0/28
- Invented in 0/28
- Dominant disappearance: `RANKED` (never SELECTED/INVENTED)

## H10 classifications

- **H10a**: AGAINST
- **H10b**: AGAINST
- **H10c**: SUPPORTED
- **H10d**: INCONCLUSIVE
- **H10e**: AGAINST
- **H10f**: INCONCLUSIVE
- **H10g**: AGAINST
- **H10h**: WEAKLY SUPPORTED
- **H10-REJECT**: AGAINST

## First causal localization

Odd-stride MAPT(SLICE:1,2(TOK)) is PROPOSED (proposal_index=3) and later SCORED/RANKED, but is never SELECTED/INVENTED because (1) first materialization prefers same-class even-stride MAPT(SLICE:0,2(TOK)) from plan board order, and (2) subsequent rank_atoms calls demote char_stride (rejected_classes) so odd-stride's best rank stays ≥1 below the lazy n_mat=1 cut — H10c SUPPORTED; H10a AGAINST.

## Forbidden checks

- Sacred TinyLlama: NOT RUN
- S injection / propose_atoms mutation: NOT DONE
- R-A/R-C/R-D integrate: NOT DONE
- grow.py / FILTER / invent_cap / novelty / firewall / score-rank-select math: NOT ALTERED
- Retune / repair observed failures: NOT DONE

## Deliverables

- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_ledger.json`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_on_off_equality.json`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_on_off_equality.md`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_rng_integrity.json`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_rng_integrity.md`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_candidate_fate.json`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_candidate_fate.md`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_hypothesis_update.md`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_hypothesis_update.json`
- `/workspace/aivd-340-replication/reports/aivd_3_41_audit_causal_localization.md`

```
AIVD 3.41 AUDIT COMPLETE:
SEPARATE AUTHORIZATION REQUIRED FOR ANY INTERVENTION
```
