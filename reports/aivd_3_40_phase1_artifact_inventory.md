# AIVD 3.40 Phase-1 — Artifact Inventory (cell → run path + field coverage)

**Recorded:** 2026-09-21 17:21 IST  
**Parent:** `reports/aivd_3_40_phase1_execution_charter.md`  
**Authorization:** `CHARTER_ONLY_NOT_EXECUTED`  
**Inventory rule:** exact paths only; do not invent files.

---

## Summary

| Metric | Value |
|--------|-------|
| Expected trajectories | 28 |
| Present | 28 |
| Missing | 0 |
| Plants | `AIVD340-S2-S` / `AIVD340-S2-U` |
| Stage-2 tip lineage | results `dcae889`; docs parent `146915b` |
| R1b caveat | `7a3457e` — observational only |

## Field coverage (applies to every cell)

### OBSERVED

- `generation_id`
- `parent_generation_id`
- `firewall_epoch`
- `candidate_origin`
- `budget_before/after`
- `leftover(+_after,_at_firewall_decision)`
- `kind/action`
- `body_key`
- `candidate_id/candidate`
- `verification_state`
- `semantic_class`
- `proposal_origin`
- `methods_log invent ops`
- `terminal_state`
- `strict_independence`
- `language.programs`

### DERIVABLE_WITHOUT_RERUN (partial)

- episode_id from condition×role×seed
- invented_atoms / produced-body census from generation_records + methods_log
- weak verification path from verification_state + envelope terminals

### UNKNOWN (do not reconstruct by regenerating discovery)

- full candidate pool snapshots
- candidate scores
- candidate ranking tables
- explicit selected-candidate decision records
- rejection/skip reason enums beyond stop_reason/failure_class/notes
- features_used maps

**Keyword scan (28/28):** pool=0, score=0, selected=0; rank/reject incidental only.

**H3:** may remain INCONCLUSIVE; weaker claim allowed: finished body present in generation_records vs never appeared.

---

## Cells

### AUD-S2-BHR1-S

| Seed | Path | Present | plant_id | terminal_state | verified | strict_ind | firewall_epoch | n_gen | n_methods |
|------|------|---------|----------|----------------|----------|------------|----------------|-------|-----------|
| 0 | `reports/aivd_3_40_stage2/runs/BH-R1_seed0_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 1 | `reports/aivd_3_40_stage2/runs/BH-R1_seed1_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 2 | `reports/aivd_3_40_stage2/runs/BH-R1_seed2_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 3 | `reports/aivd_3_40_stage2/runs/BH-R1_seed3_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 4 | `reports/aivd_3_40_stage2/runs/BH-R1_seed4_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 7 | `reports/aivd_3_40_stage2/runs/BH-R1_seed7_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |
| 11 | `reports/aivd_3_40_stage2/runs/BH-R1_seed11_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 10 | 121 |

### AUD-S2-BHR1-U

| Seed | Path | Present | plant_id | terminal_state | verified | strict_ind | firewall_epoch | n_gen | n_methods |
|------|------|---------|----------|----------------|----------|------------|----------------|-------|-----------|
| 0 | `reports/aivd_3_40_stage2/runs/BH-R1_seed0_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 1 | `reports/aivd_3_40_stage2/runs/BH-R1_seed1_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 2 | `reports/aivd_3_40_stage2/runs/BH-R1_seed2_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 3 | `reports/aivd_3_40_stage2/runs/BH-R1_seed3_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 4 | `reports/aivd_3_40_stage2/runs/BH-R1_seed4_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 7 | `reports/aivd_3_40_stage2/runs/BH-R1_seed7_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |
| 11 | `reports/aivd_3_40_stage2/runs/BH-R1_seed11_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | True | 1 | 10 | 102 |

### AUD-S2-BHR1b-S

| Seed | Path | Present | plant_id | terminal_state | verified | strict_ind | firewall_epoch | n_gen | n_methods |
|------|------|---------|----------|----------------|----------|------------|----------------|-------|-----------|
| 0 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed0_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 1 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed1_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 2 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed2_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 3 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed3_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 4 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed4_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 7 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed7_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |
| 11 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed11_S.json` | YES | `AIVD340-S2-S` | `TerminalState.UNRESOLVED_INVISIBLE` | False | False | 1 | 9 | 109 |

### AUD-S2-BHR1b-U

| Seed | Path | Present | plant_id | terminal_state | verified | strict_ind | firewall_epoch | n_gen | n_methods |
|------|------|---------|----------|----------------|----------|------------|----------------|-------|-----------|
| 0 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed0_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 1 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed1_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 2 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed2_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 3 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed3_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 4 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed4_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 7 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed7_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |
| 11 | `reports/aivd_3_40_stage2/runs/BH-R1b_seed11_U.json` | YES | `AIVD340-S2-U` | `TerminalState.VERIFIED` | True | False | 0 | 3 | 65 |

---

## Companion Stage-2 directory files (also read-only)

- `reports/aivd_3_40_stage2/results.json`
- `reports/aivd_3_40_stage2/results.md`
- `reports/aivd_3_40_stage2/matrix_raw.json`
- `reports/aivd_3_40_stage2/generation_graph.json`
- `reports/aivd_3_40_stage2/independence.json`
- `reports/aivd_3_40_stage2/env_gate.json`
- `reports/aivd_3_40_stage2/freeze.json`
- `reports/aivd_3_40_stage2/reproducibility.json`
- `reports/aivd_3_40_stage2/run.log`

## STOP

Inventory only. No Phase-1 execution. No Sacred. No code changes.
