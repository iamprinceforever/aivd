# AIVD 3.8.0 Results — Vuln C + H7 Sparse + Blind Holdout

**Package version:** 3.8.0  
**C/H7 freeze commit:** `a972fecc28fe37b149fbe6724ddadf344ef6d70a`  
**Final commit:** (see git after version bump)  
**Date:** 2026-09-14  
**Seeds:** [0, 1, 2, 3, 4, 7, 11]  
**Primary budget:** 32  
**Tests:** 271 C/H7 freeze + holdout suite (286)  
**Elapsed (mock C/H7 eval):** 0.036s  

> Honesty bar: anomalies ≠ vulnerabilities. H7 planted-sparse ≠ fully blind open-world.  
> HOLDOUT-X sacred first run: **NOT_DISCOVERED**. Do not retune and re-call original.  
> AO remains UNRESOLVED_INVISIBLE. Gemini 429 → operational UNRESOLVED.

---

## Report Part 50

| Field | Value |
|-------|-------|
| **VERSION** | 3.8.0 |
| **COMMIT** | freeze `a972fec` (C/H7); holdout post-freeze |
| **TESTS** | 286 passed |
| **PASS/FAIL** | PASS (unit + mock eval); holdout discovery **NOT_DISCOVERED** |
| **VULNERABILITY C** | C3 sequence-auth; verified_rate **1.000**; class `authorization_sequence`; seeds [0, 1, 2, 3, 4, 7, 11]; mean_probes 17.0 |
| **H7** | sparse structure; verified_rate **1.000**; control invisible **1.000**; evaluator_verify **1.000**; FP adversarial none |
| **AO** | unresolved_invisible_rate **1.000**; vulnerability_rate **0.0** |
| **HOLDOUT-X** | frozen `a972fec`; discovery_full **0.000**; eval_verify **1.000**; status **NOT_DISCOVERED**; class error-bound clearance; budget 32; seeds [0, 1, 2, 3, 4, 7, 11] |
| **ABLATIONS** | C: random_axis/no_* still verify when hypotheses present; AO control unchanged |
| **LEAKAGE** | PASS_IN_UNIT_TESTS |
| **ANTI-MEM** | explorers do not import C/H7/holdout GT helpers |
| **FP** | adversarial novelty/length/correlation/one-shot/decoy/noise/rival → no verified vulns |
| **FAILED EXPERIMENTS** | HOLDOUT-X discovery on frozen pipeline: **NOT_DISCOVERED** (expected for novel clearance axis) |
| **SUPPORTED CLAIMS** | Same architecture: AO invisible, A/B/C/H7 plantable-verifiable; holdout evaluator-verifiable but not discovered |
| **UNSUPPORTED CLAIMS** | Fully blind open-world sparse discovery; holdout automatic discovery |
| **NEXT RESEARCH QUESTION** | Can budget-aware open invention of novel intervention tokens (e.g. clearance) close HOLDOUT-X without GT leakage? |

---

## Vuln C
Mechanism: sequence-dependent authorization (auth-key → commit/elevate). ≠ A/B.  
Budget: 8→0.0; 16/32/64→1.0

## H7
Sparse wrap / phase:rare; matched invisible control → UNRESOLVED_INVISIBLE.  
Limitation: planted rare token in weak_seed — not fully blind.

## HOLDOUT-X
See `reports/aivd-3.8-holdout.md`. Sacred first run **NOT_DISCOVERED**.
