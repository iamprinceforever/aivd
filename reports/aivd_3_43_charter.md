# AIVD 3.43 — Selection-Budget Generalization Audit Charter

**Recorded:** 2026-09-22 13:06:36 IST  
**Baseline tip:** `3a07abe1e370f3328be33a3ad93e5fb7972a65eb` (`3a07abe`) — AIVD 3.42 causal audit COMPLETE  
**Branch:** `research/aivd-3.43-selection-budget-generalization` (from 3a07abe)  
**Mode:** OFFLINE REPLAY ONLY  
**Sacred:** NO  
**Planner changed:** NO  
**n_mat changed:** NO  

## Primary question

Does plan-board order + rank demotion + lazy n_mat=1 systematically suppress valid lower-position candidates?

Test the **mechanism**, not S specifically.

## Required controls

1. **S:** EVEN@0 / ODD@1 (from 3.41/3.42)
2. **U:** naturally successful candidate configuration
3. **Positive control:** candidate at board position 1 known to become selected/materialized under existing machinery
4. **Null control:** no valid second candidate

## Scope gate

| Allowed | Forbidden |
|---------|-----------|
| Offline replay of immutable 3.41/3.42 artifacts | Modify planner / rank_atoms / score / board / n_mat / propose / invent_cap / budget / firewall / novelty / grow.py / FILTER |
| Read-only analyzer under `aivd/experiments/aivd343/` | Sacred / production selection change / S injection / planner repair |
| NOT_RECORDED for missing fields | Infer missing values; select a repair / declare repair winners |

## Phases

1. **REQUIRED** — Offline replay of existing 3.41/3.42 observations; multi-key generalization matrix.
2. **Conditional** — Preregistered controlled offline CF only if Phase 1 insufficient; else SKIPPED.

## Stop line

```
AIVD 3.43 GENERALIZATION AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```
