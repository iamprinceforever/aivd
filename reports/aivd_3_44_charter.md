# AIVD 3.44 — Charter (Exploration Allocation Audit)

**Recorded:** 2026-09-22 13:20:03 IST  
**Baseline tip:** `9810aea5efe14fe4b8786eedc94a7710ecdbbe0e`  
**Branch:** `research/aivd-3.44-exploration-allocation`  
**Parent:** `research/aivd-3.43-selection-budget-generalization` @ 9810aea  
**Mode:** OFFLINE ONLY — recorded trajectories + counterfactual replay  
**Sacred:** NO  
**Planner changed:** NO  
**Live n_mat changed:** NO  

## Primary question

What exploration/efficiency tradeoff is produced by n_mat=1 when candidates beyond position 0 compete for materialization?

## Method

1. Reconstruct 28 ON-cell trajectories from immutable `reports/aivd_3_41_audit_ledger.json`.
2. Cross-check fate tags against 3.42/3.43 offline artifacts.
3. Compare n_mat=1 (observed) vs n_mat=2,3,… **only** as offline first-window counterfactuals on recorded board0 order.
4. Separate FIRST-WINDOW SKIP from PERSISTENT SUPPRESSION.
5. Mark all downstream CF claims beyond first-window SELECT/INVENT as NOT_RECORDED.

## Forbidden (honored)

planner modification; live n_mat modification; Sacred; S injection; proposal/scoring/ranking/novelty/firewall changes; new model calls; selecting a repair; calling skipped keys undiscoverable; calling CF keys discoverable beyond recorded-order first-window materialization.

## Controls

| Control | Role | Observed fate |
|---------|------|---------------|
| S/ODD | suppressed | board@1; first-window skip; persistent demotion×n_mat=1 |
| U | successful | board@4; skip then escape via rank-0; invented 28/28 |
| POS2 | escape | board@2; skip then escape |
| POS5 | escape | board@5; skip then escape |
| POS6/POS7 | suppressed siblings | demotion×n_mat=1; never selected |
| NULL | rejected | novelty:ATOM_SEMANTIC_DUPLICATE pre-select; not on board0 |

## Authorization boundary

This audit does **not** authorize any intervention. Changing n_mat, rank, or board order requires separate authorization.
