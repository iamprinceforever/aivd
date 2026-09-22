# AIVD 3.43 — Precise Boundary

**Recorded:** 2026-09-22 13:06:36 IST  
**Sacred:** NO  

## Established

1. **First-window cut generalizes:** under recorded lazy n_mat=1, ALL board-position>0 candidates on the identical 10-slot board0 are skipped on the first invent window (9/9 keys × 28/28 cells); first SELECT is always board0[0]=EVEN.
2. **Permanent suppression is conditional:** lasting non-selection among scored/ranked pos>0 keys occurs when rank demotion keeps best_rank≥1 while n_mat=1 only materializes rank-0 — observed for ODD@1, POS6, POS7 (not only S).
3. **Escape path exists:** U@4, POS5, POS2 skip the first window but later attain rank-0 and are selected/invented 28/28 — board-position>0 is not an absolute barrier.
4. **Mechanism is not S/EVEN-specific:** same first-window skip and demotion×n_mat=1 pattern apply to non-S keys; H12d AGAINST; H12e SUPPORTED.
5. **Null control holds:** `MAPT(CAT(AT:-1|TOK))` rejected pre-select (novelty:ATOM_SEMANTIC_DUPLICATE) in 28/28; never on board0; never selected.
6. **H12 scoring:** H12a AGAINST; H12b SUPPORTED; H12c SUPPORTED; H12d AGAINST; H12e SUPPORTED; H12-REJECT AGAINST.

## Not established

1. **Board-pos1 positive control** — NOT_OBSERVED: no recorded cell places a non-ODD key at board0[1] that becomes selected; pos1 is always ODD and never selected.
2. **EVEN intrinsic pre-score** — still NOT_RECORDED (SELECTED pre-score); unchanged from 3.42.
3. **Why POS3 attains rank-0 but is never selected** — first rank0 occurs only after last invent (invent window closed); skip/early-return reasons inside `_maybe_invent_atom` after invent stop remain under-instrumented (NOT_RECORDED observe_skip rows).
4. **POS8/POS9 never scored** — observed fate; generative/board-drop internals not re-audited (out of selection-budget generalization scope).
5. **Whether changing n_mat / rank / board order would yield Sacred uplift** — FORBIDDEN; requires separate authorization.
6. **Alternate board compositions** — all 28 cells share one identical board0; generalization is across keys on that board, not across diverse propose-order regimes.
7. **No repair recommendation** — audit does not select or authorize any intervention.

## Phase 2

SKIPPED — Phase 1 sufficient (see counterfactual report).
