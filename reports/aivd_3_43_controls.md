# AIVD 3.43 — Controls

**Recorded:** 2026-09-22 13:06:36 IST  
**Sacred:** NO  

## 1. S — EVEN@0 / ODD@1

| Key | Board pos | Selected | Invented | Role |
|-----|-----------|----------|----------|------|
| EVEN `MAPT(SLICE:0,2(TOK))` | 0 | 28/28 | 28/28 | first-window materialization under board0@0 + n_mat=1 |
| ODD `MAPT(SLICE:1,2(TOK))` | 1 | 0/28 | 0/28 | S suppressed: skipped first window + demotion keeps best_rank>=1 |

ODD best_rank_counter: `{'1': 28}`

## 2. U — naturally successful

- key: `MAPT(CAT(TOK|AT:-1))`
- board_position: **4**
- selected/invented: **28/28** / **28/28**
- ever_rank0: **28/28**
- scores: `[0.2781625]`
- role: naturally successful: skipped first window but ESCAPES via later rank-0

## 3. Positive control — board position 1 selected?

- **Definition:** A case where the candidate at board position 1 is known to become selected/materialized under existing machinery
- board_pos1 identity (always): `MAPT(SLICE:1,2(TOK))`
- board_pos1 selected cells: **0/28**
- **Finding: NOT_OBSERVED**
- Note: In all 28 recorded cells board0[1]==ODD and is never selected. No alternate configuration places a different key at pos1.

### Broader positive control (pos>0 escape) — OBSERVED

Exemplars that start at board_position>0 and become selected/invented:

- `MAPT(CAT(SLICE:1,1(TOK)|AT:0))` @ pos 2 selected 28/28
- `MAPT(CAT(TOK|AT:-1))` @ pos 4 selected 28/28
- `MAPT(AT:-1)` @ pos 5 selected 28/28

Implication: Board-position >0 is not an absolute barrier; escape requires attaining rank-0 under n_mat=1 on a later invent window.

## 4. Null control — no valid second candidate

- key: `MAPT(CAT(AT:-1|TOK))`
- NULL rejected pre-first-select in 28/28 cells (reason={'novelty:ATOM_SEMANTIC_DUPLICATE': 28}); never on board0; never selected/invented.
- reject_reason_counter: `{'novelty:ATOM_SEMANTIC_DUPLICATE': 28}`

See `reports/aivd_3_43_controls.json`.
