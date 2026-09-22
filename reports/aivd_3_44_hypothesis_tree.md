# AIVD 3.44 — Hypothesis Tree

**Recorded:** 2026-09-22 13:20:03 IST  
**Sacred:** NO  

## Root

**H13:** What exploration/efficiency tradeoff does n_mat=1 produce when candidates beyond position 0 compete for materialization?

## Leaves

| Leaf | Claim | Classification |
|------|-------|----------------|
| H13a | n_mat=1 is primarily a cost-control policy | **SUPPORTED** |
| H13b | n_mat=1 materially reduces behavioral diversity | **SUPPORTED** |
| H13c | n_mat=1 primarily affects breadth, not eventual discovery | **PARTIAL** |
| H13d | rank demotion converts temporary skips into persistent suppression | **SUPPORTED** |
| H13e | increasing materialization breadth produces additional behavioral directions but at measurable budget cost | **PARTIAL** |
| H13f | the observed tradeoff is negligible outside the S-family | **AGAINST** |
| H13-REJECT | existing data cannot establish the allocation tradeoff | **AGAINST** |

## Evidence detail

### H13a — SUPPORTED

**Claim:** n_mat=1 is primarily a cost-control policy

**Evidence:** Observed lazy n_mat=1 in 28/28 cells (exactly 1 SELECT before any RANK). First-window materialization capped at 1/10 board slots. Code path (read-only, 3.42): designer._maybe_invent_atom uses n_mat=1 if allow_atom_lazy else 4. Invent attempts stay finite (mode 7/cell); all cells hit BUDGET_EXHAUSTED. Primary first-window role is slot-cost control; secondary effects on diversity/suppression also present (H13b/d).

### H13b — SUPPORTED

**Claim:** n_mat=1 materially reduces behavioral diversity

**Evidence:** First-window diversity under n_mat=1: 1 key / 1 family vs board0 of 10 keys. Eventual unique invented keys = 4/cell spanning 3 families; 9 pos>0 keys skipped every cell. CF n_mat=2 would add board0[1]=ODD in first window (28/28). Material first-window diversity reduction established; eventual diversity partially recovered via later rank-0 escapes.

### H13c — PARTIAL

**Claim:** n_mat=1 primarily affects breadth, not eventual discovery

**Evidence:** For escapees POS2/U/POS5: first-window skip is temporary; they attain rank-0 and are invented 28/28 — breadth/timing effect only. For ODD/POS6/POS7: demotion×n_mat=1 yields persistent non-selection (0/28 invented) — eventual discovery IS blocked for that set. POS3 attains rank-0 only after invent stops (never selected). POS8/POS9 never scored after skip. Therefore 'breadth only' is false as a universal claim; true for escapees, false for suppressed.

### H13d — SUPPORTED

**Claim:** rank demotion converts temporary skips into persistent suppression

**Evidence:** All 9 pos>0 keys are FIRST-WINDOW-SKIPPED. Of scored/ranked pos>0 keys that never attain rank-0 (ODD best_rank=1, POS6 best_rank=2, POS7 best_rank=3), all remain unselected 0/28 — persistent suppression. Keys that later reach rank-0 during invent windows escape (POS2/U/POS5). Same first-window skip; divergent permanent fate via demotion gate.

### H13e — PARTIAL

**Claim:** increasing materialization breadth produces additional behavioral directions but at measurable budget cost

**Evidence:** Directions: CF n_mat=2 first-window adds ODD; CF n_mat=3 adds ODD+POS2; coverage 0.20/0.30. Budget cost: marginal first-window invent slots = n_mat-1 are countable; ledger invent budget_delta is 0 on all 196 invent events (before==after), so unit invent cost NOT_RECORDED. CF remaining-budget under wider n_mat NOT_RECORDED. Directions SUPPORTED; measurable budget cost only at slot-count proxy level.

### H13f — AGAINST

**Claim:** the observed tradeoff is negligible outside the S-family

**Evidence:** First-window n_mat=1 skip hits ALL 9 pos>0 keys (not only ODD). Persistent demotion×n_mat=1 suppression also hits non-S POS6 and POS7 (0/28 selected). Escape pattern hits non-S POS2/POS5 and U. Mechanism and tradeoff are generic on this board — not S-family-local.

### H13-REJECT — AGAINST

**Claim:** existing data cannot establish the allocation tradeoff

**Evidence:** 28/28 identical board0 trajectories establish first-window skip rate 9/9 pos>0, persistent suppression set {ODD,POS6,POS7}, escape set {POS2,U,POS5}, and honest CF first-window materialization under n_mat=2..10 from recorded board0. Residual NOT_RECORDED items do not justify H13-REJECT; they bound intervention claims.

