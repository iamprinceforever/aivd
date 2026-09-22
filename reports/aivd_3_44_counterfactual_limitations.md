# AIVD 3.44 — Counterfactual Limitations

**Recorded:** 2026-09-22 13:20:03 IST  
**Mode:** OFFLINE_COUNTERFACTUAL_ON_RECORDED_ROWS_ONLY  
**Sacred:** NO  

## Honest CF scope

Counterfactual n_mat=k is limited to: if the first invent call materialized board0[:k] in recorded order, those k keys would be SELECTED/INVENTED in the first window. Nothing beyond that window is asserted.

## Hard limits

1. Downstream trajectory after CF first-window invent of board0[1:] is NOT_RECORDED (would diverge via rejected_classes / rank updates).
2. Invent ledger budget_delta is 0 on all invent events — unit invent cost NOT_RECORDED.
3. CF remaining budget / stop_reason under n_mat>=2 NOT_RECORDED.
4. Verification and recursive-growth outcomes under CF NOT_RECORDED (observed verified=False all cells).
5. behavioral_identity field on invent events is NOT_RECORDED — family used as direction proxy.
6. All 28 cells share one identical board0 — no alternate propose-order regimes.
7. Board-pos1 positive control (non-ODD at pos1 selected) NOT_OBSERVED.
8. POS8/POS9 generative drop / never-scored internals not re-audited.
9. No claim that CF materialization implies Sacred success or discoverability beyond SELECT/INVENT first-window.
10. FORBIDDEN actions not taken: planner mod, live n_mat change, Sacred, S injection, scoring/ranking/novelty/firewall changes, new model calls, selecting a repair.

## Precise boundary

- **Established offline:** first-window skip rate; persistent vs escape partition; CF first-window materialization set for each n_mat from recorded board0; slot-count cost proxy.
- **Not established:** post-window CF discovery, verification, recursive growth, Sacred uplift, true invent unit cost, alternate board compositions.
- **Intervention:** NOT authorized by this audit.
