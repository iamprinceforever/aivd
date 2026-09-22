# AIVD 3.42 — Phase 1 Offline Replay

**Recorded:** 2026-09-22 13:00:57 IST  
**Source ledger:** `reports/aivd_3_41_audit_ledger.json` (recorded 2026-09-22 12:57:05 IST)  
**Sacred:** NO  
**Mode:** deterministic offline reconstruction from recorded `ledger_events` only  

## Controls

| Role | Key |
|------|-----|
| S odd-stride | `MAPT(SLICE:1,2(TOK))` @ proposal_index=3 |
| Naturally selected even-stride | `MAPT(SLICE:0,2(TOK))` @ proposal_index=1 |
| U successful | `MAPT(CAT(TOK|AT:-1))` |
| Null/control | `MAPT(CAT(AT:-1|TOK))` (rejected pre-select) |

## Aggregate (28 ON cells)

| Metric | Value |
|--------|-------|
| first_select_always_even | True |
| even_board_pos | {'0': 28} |
| odd_board_pos | {'1': 28} |
| n_mat_inferred_pre_rank | {'1': 28} |
| odd_best_rank | {'1': 28} |
| odd_selected / invented | 0 / 0 |
| even_invented_cells | 28 |
| u_invented_cells | 28 |
| odd_ever_rank0 | 0 |
| scores_before_first_select always 0 | True |
| ranks_before_first_select always 0 | True |
| even score recorded cells | 0 |
| null rejected pre-select | 28/28 |

## Exemplar trajectory (S8-BASELINE seed=0)

- **board0 head:** `['MAPT(SLICE:0,2(TOK))', 'MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(AT:-1|SLICE:0,1(TOK)))', 'MAPT(CAT(TOK|AT:-1))']`
- **odd_board_pos / even_board_pos:** 1 / 0
- **first_selected:** `MAPT(SLICE:0,2(TOK))` (proposal_index=1)
- **n_mat_inferred_pre_rank:** 1
- **invent_order:** `['MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(SLICE:0,2(TOK))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(SLICE:1,1(TOK)|AT:0))']`
- **remaining_budget_at_first_invent:** 29
- **odd scores / best_rank / selected / invented:** [0.038148] / 1 / False / False
- **even scores / selected / invented:** ['NOT_RECORDED'] / True / True
- **U best_rank / invented:** 0 / True
- **null rejected_pre_first_select:** True
- **first rank block rejected_classes:** ['char_stride']
- **first rank block ordered_keys head:** ['MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']

## Integrity

- Twin equality / RNG integrity inherited from 3.41 ledger PASS flags (not re-executed).
- No new model calls; no production changes; missing fields left as NOT_RECORDED.

## Machine-readable

See `reports/aivd_3_42_phase1_replay.json`.
