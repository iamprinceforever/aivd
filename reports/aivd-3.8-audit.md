# AIVD 3.8.0 Audit — Vuln C + H7 Sparse + Blind Holdout

**Base:** 3.7.0 @ `98ad5a2` / `94b4903` (231 tests)  
**Date:** 2026-09-14  
**Constraint:** Incremental; preserve 3.4–3.7; do not weaken verification; AO stays UNRESOLVED_INVISIBLE.

## Starting state
- Package `aivd37/unknowns/`: residual sweep → open axes → falsify/reproduce/invariant → classify LAST
- AO hard control: invisible; Vuln A delayed-state; Vuln B tool-channel
- H7: NOT DEMONSTRATED in 3.7
- Config `unknowns_mode` default **off**
- Explorer hygiene: no orchid-lattice / PV-RARE-CANARY / SECRET_A/B in explorers/pipeline

## 3.8 plan (protocol order)
1. **Vuln C (C3):** sequence-dependent authorization state — ordered auth→commit/elevate; qualitatively ≠ A/B; target `mock://aivd37-vuln-c`; blind to explorer
2. **H7:** sparse / low-frequency / minimal footprint; no echo_stem; no proximity gradient; matched invisible control → UNRESOLVED_INVISIBLE; honest failure OK
3. Extend residual/open-axes only as budget-aware sparse hypotheses (no C/H7 names in explorer path)
4. Tests + multi-seed/budget/ablation evals → interim metrics
5. **FREEZE** (`freeze.json` + commit) before any holdout
6. **HOLDOUT-X** evaluator-only, different mechanism; sacred first run; separate report
7. Version 3.8.0; push via `/workspace/git_push_aivd.sh`

## Non-goals
- Do not make AO pass as vuln
- Do not retune discovery after seeing holdout and re-call it original
- Do not claim blind open sparse if H7 fails
