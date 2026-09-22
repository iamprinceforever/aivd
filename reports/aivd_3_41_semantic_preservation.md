# AIVD 3.41 — Semantic Preservation Specification (Design Only)

**Document type:** Semantic preservation (DOCS ONLY — **NOT IMPLEMENTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. Equivalence claim (binding)

For any fixed seed, plant_id, condition, and representation policy, a deterministic replay with `AIVD41_PLANNER_AUDIT` instrumentation **ON** must match instrumentation **OFF** on:

1. Proposal sequences (candidate_key order from `propose_atoms` / `propose_atom_candidates` after plan keep)
2. Rejection decisions and reasons (when both recorded)
3. Scores and score_components
4. Ranks
5. Selections / skips
6. Inventions (body_key set + order)
7. Budget trajectory (budget_before/after at each invent touch; BH remaining)
8. Final terminal_state / failure_class / stop_reason / occupancy / firewall_epoch

**STOP** on any mismatch: instrumentation is not behavior-preserving; do not accept results.

## 2. Strategy

1. **Append-only observers** at emission sites listed in `aivd_3_41_planner_ledger_spec.md` — no mutation of returned lists, scores, ranks, or control flow.
2. **Shadow ledger** written to side-channel artifacts (not consulted by planner).
3. **Twin runs:** every instrumented cell has an uninstrumented twin with identical seed/plant/condition/policy.
4. **Digest compare:** hash sequences of (candidate_key, action, score, rank, budget_after, body_key) across twin runs; require equality.
5. **No policy flags that alter planner math** under `AIVD41_PLANNER_AUDIT` — mode may only enable observers.

## 3. Explicit non-goals

- Not improving S discovery rate
- Not changing invent_cap / REDISCOVERY_FLOOR / BH
- Not altering rank_atoms / expected_verified_value formulas
- Not changing FILTER_BEHAVIORAL_DUP / R-A/R-C/R-D behavior

## 4. STOP

If instrumented ≠ uninstrumented on §1 sequences → **STOP** and revoke instrumentation acceptance.
