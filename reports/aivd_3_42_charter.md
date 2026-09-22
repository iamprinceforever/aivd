# AIVD 3.42 — Planner Selection Causal Audit Charter

**Recorded:** 2026-09-22 13:00:57 IST  
**Baseline tip:** `0f42dc01dd0feac3b18e1dbe835282c8226bc821` (`0f42dc0`) — AIVD 3.41 audit COMPLETE  
**Branch:** `research/aivd-3.42-selection-causal-audit` (from 0f42dc0)  
**Mode:** OFFLINE REPLAY ONLY  
**Sacred:** NO  
**Planner changed:** NO  

## Primary question

Why does the already-proposed odd-stride candidate `MAPT(SLICE:1,2(TOK))` never reach SELECTED/INVENTED?

## Scope gate

| Allowed | Forbidden |
|---------|-----------|
| Offline replay of immutable 3.41 ledgers | Change planner / score / rank / n_mat / propose atoms / invent_cap / budget / firewall / novelty / grow.py / FILTER |
| Pure offline counterfactual on recorded rows | Select a planner repair / declare repair winner |
| Read-only analyzer under `aivd/experiments/aivd342/` | New model calls / Sacred / production behavior change |
| NOT_RECORDED for missing fields | Infer missing values; provenance leakage |

## Source artifacts (immutable)

- `reports/aivd_3_41_audit_ledger.json`
- `reports/aivd_3_41_audit_candidate_fate.json`
- `reports/aivd_3_41_audit_causal_localization.md`
- related 3.41 audit reports

## Phases

1. **REQUIRED** — Offline reconstruct trajectories; compare ODD vs naturally selected EVEN; controls U / null.
2. **Conditional** — Offline what-if on recorded rows only if Phase 1 sufficient; else SKIP.

## Stop line

```
AIVD 3.42 CAUSAL AUDIT COMPLETE:
INTERVENTION REQUIRES SEPARATE AUTHORIZATION
```
