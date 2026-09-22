# AIVD 3.43 — Hypothesis Tree (H12a–H12e + H12-REJECT)

**Recorded:** 2026-09-22 13:06:36 IST  
**Sacred:** NO  
**Scoring rule:** score independently; ties allowed; do not force singular repair winner.

| Leaf | Claim | Classification |
|------|-------|----------------|
| H12a | n_mat=1 generally sufficient to suppress board-position >0 candidates | **AGAINST** |
| H12b | suppression only when rank demotion interacts with n_mat=1 | **SUPPORTED** |
| H12c | plan-board ordering is the dominant prerequisite | **SUPPORTED** |
| H12d | mechanism specific to S/EVEN — does not generalize | **AGAINST** |
| H12e | mechanism broader than S — generic exploration/materialization tradeoff | **SUPPORTED** |
| H12-REJECT | existing evidence insufficient for generalization | **AGAINST** |

## Evidence summaries

### H12a — AGAINST

n_mat=1 skips all pos>0 on the FIRST window (9/9 keys × 28 cells), but is NOT generally sufficient for permanent suppression: 3 keys ESCAPE via later rank-0 (['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']) including U@4.

### H12b — SUPPORTED

Permanent non-selection among scored/ranked pos>0 keys that stay best_rank>=1 under demotion: 3 keys (['MAPT(SLICE:1,2(TOK))', 'MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']) including S/ODD. Keys that attain rank-0 during active invent windows escape (['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']). Therefore lasting suppression requires demotion×n_mat=1, not n_mat=1 alone.

### H12c — SUPPORTED

first_select_always_board0_pos0=True; board0 identical True; board order is the prerequisite for which key occupies the single n_mat=1 first-window slot. Alone it does not determine permanent fate (escape via re-rank).

### H12d — AGAINST

First-window n_mat=1 skip applies to ALL 9 pos>0 keys, not only ODD. Demotion×n_mat=1 permanent suppress also hits non-S keys ['MAPT(CAT(TOK|AT:0))', 'MAPT(CAT(AT:0|AT:-1))']. Escape pattern hits non-S keys ['MAPT(CAT(SLICE:1,1(TOK)|AT:0))', 'MAPT(CAT(TOK|AT:-1))', 'MAPT(AT:-1)']. Mechanism is not S/EVEN-specific.

### H12e — SUPPORTED

Observed generic pattern under lazy n_mat=1: (1) board-order first cut; (2) class demotion after invent updates rejected_classes; (3) only current rank-0 materializes on later windows; (4) non-rank-0 remain unmaterialized — applies to ODD plus POS6/POS7; escapees U/POS5/POS2 confirm the rank-0 gate is the materialization valve.

### H12-REJECT — AGAINST

Deterministic 28/28 ON cells with identical board0 provide multi-key contrast (S suppress, U/POS2/POS5 escape, POS6/POS7 demotion suppress, null reject, POS3 post-window rank0). Sufficient to score H12a–H12e; residual: board-pos1 positive control never observed (pos1_selected=0/28).

## Parent localization (3.42 H11 / E)

3.42 localized ODD disappearance to board-order × rank demotion × n_mat=1 (E SUPPORTED).
3.43 asks whether that mechanism generalizes beyond the S odd/even pair.
