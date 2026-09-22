# AIVD 3.41 — Implementation Report (Behavior-Preserving Planner Ledger)

**Document type:** Implementation report  
**Recorded:** 2026-09-22 (Asia/Calcutta)  
**Design parent:** `4ae940b` / `4ae940b34697bdeb66bc594206155d4f2ccbfb0d`  
**Research baseline:** `a380e3c` / `a380e3ce0be2bb1b456c38a0213cde12feef8f45`  
**Branch:** `research/aivd-3.41-invention-planner-audit`  
**Mode gate:** `AIVD41_PLANNER_AUDIT` (env; also `enable_audit()` for tests)  
**Sacred:** **NO**  
**Status:** IMPLEMENTATION READY — EXECUTION REQUIRES SEPARATE AUTHORIZATION

---

## 1. Design commit verified

- HEAD at start of implementation: `4ae940b` (design READY docs).
- Parent of design: `a380e3c` (Stage-9 stamp).

## 2. What was implemented

Append-only observational planner ledger under `aivd/science/planner_audit_ledger.py`.

- Gate OFF (default): every observer is a no-op (zero budget, zero planner RNG, zero decision-path mutation).
- Gate ON: side-channel rows for propose / reject / score / rank / select / invent / skip / firewall.
- Missing honest fields emit `NOT_RECORDED` (never fabricated).
- Stage-8 invent-gap completion via `Stage8Recorder.ingest_planner_audit_ledger`.

## 3. Mode gate

| Property | Value |
|----------|-------|
| Env name | `AIVD41_PLANNER_AUDIT` |
| Enable | `1` / `true` / `yes` / `on` / `audit` |
| Default | OFF |
| Test force | `enable_audit()` / `disable_audit()` (thread-local) |

## 4. Hook sites (path:symbol)

- `aivd/science/atom_synth.py:AtomSynthesizer.plan (observe_propose / observe_reject)`
- `aivd/science/atom_synth.py:AtomSynthesizer.next_atom (observe_select)`
- `aivd/science/designer.py:ScienceDesigner._maybe_invent_atom (observe_score / observe_rank / observe_skip / observe_invent)`
- `aivd/science/designer.py:ScienceDesigner._maybe_firewall (observe_firewall)`
- `aivd/experiments/aivd340/stage8_recorder.py:ingest_planner_audit_ledger (Stage-8 invent-gap completion)`

**Frozen (unchanged vs `a380e3c`):** `grow.py`, `lifecycle.py`, `methods.py`, `language.py`.  
**`propose_atoms` / `rank_atoms` / `expected_verified_value` function bodies:** unchanged (verified by `inspect.getsource` ⊆ baseline blob).

## 5. Newly OBSERVABLE fields

- `candidate_key`
- `candidate_family`
- `candidate_origin`
- `candidate_generation_method`
- `proposal_index`
- `proposal_epoch`
- `proposal_state`
- `rejection_state`
- `rejection_reason`
- `score`
- `score_components`
- `rank`
- `selection_state`
- `selection_reason`
- `budget_before`
- `budget_after`
- `firewall_epoch`
- `novelty_state`
- `body_key`
- `parent_key`
- `provenance`
- `seed`
- `plant_id`

## 6. Still NOT_RECORDED

- behavioral_identity (grow._keep / FILTER path frozen — honesty marker via observe_not_recorded)
- language_key (not available at invent hook without language mutation)
- grow nested _keep reject reasons (grow.py frozen per T15)

## 7. T01–T16 results

| ID | Result |
|----|--------|
| T01 | PASS |
| T02 | PASS |
| T03 | PASS |
| T04 | PASS |
| T05 | PASS |
| T06 | PASS |
| T07 | PASS |
| T08 | PASS |
| T09 | PASS |
| T10 | PASS |
| T11 | PASS |
| T12 | PASS |
| T13 | PASS |
| T14 | PASS |
| T15 | PASS |
| T16 | PASS |
| odd_stride_index3 | PASS |

Command: `.venv/bin/pytest tests/test_aivd341_planner_audit.py -q` → **17 passed**.

## 8. Twin ON/OFF equality

**PASS** (T03, T04, T16). Sequences / board counters / selections match with audit ON vs OFF.

## 9. RNG integrity

**PASS** (T05). Observer path consumes no `random` draws; ON/OFF streams equal under fixed seed.

## 10. STOP conditions checked

| # | Condition | Result |
|---|-----------|--------|
| 1 | AUDIT=ON changes candidate sequence | NOT HIT (T03) |
| 2 | AUDIT=ON changes ordering | NOT HIT (T03/T09) |
| 3 | AUDIT=ON changes score/rank/selection | NOT HIT (T03/T08–T10) |
| 4 | AUDIT=ON changes invention outcome | NOT HIT (T03/T11) |
| 5 | AUDIT=ON changes budget consumption | NOT HIT (T04) |
| 6 | AUDIT=ON changes firewall behavior | NOT HIT (observe-only) |
| 7 | AUDIT=ON changes RNG state/consumption | NOT HIT (T05) |
| 8 | AUDIT=ON changes final state | NOT HIT (T03/T16) |
| 9 | Instrumentation requires altering planner decision logic | NOT HIT |
| 10 | Any T01–T16 gate fails | NOT HIT |

## 11. Odd-stride proposal_index=3

- Key `MAPT(SLICE:1,2(TOK))` observed at `proposal_index=3` in ledger tests.
- **Never special-cased** in ledger module (no SLICE:1,2 / ODDSTRIDE tokens in `planner_audit_ledger.py`).
- Distinguishes NEVER_PROPOSED vs NOT_REACHED_BEFORE_BUDGET_EXHAUSTION (T12).

## 12. Sacred

**NO** Sacred / TinyLlama / plant discovery runs.

## 13. Files changed

- `aivd/science/planner_audit_ledger.py`
- `aivd/science/atom_synth.py`
- `aivd/science/designer.py`
- `aivd/experiments/aivd340/stage8_recorder.py`
- `tests/test_aivd341_planner_audit.py`
- `reports/aivd_3_41_implementation.md`
- `reports/aivd_3_41_implementation.json`

## 14. Next authorization (exact)

```
AIVD 3.41 AUDIT EXECUTION AUTHORIZATION — INSTRUMENTED OBSERVATIONAL RUNS ONLY
(behavior-preserving ledger ON; twin OFF runs required; no Sacred plants beyond
preregistered observational matrix; no S injection; STOP on semantic/RNG mismatch)
```

Sacred / discovery uplift / filter replacement each require additional distinct authorizations.

---

**AIVD 3.41 IMPLEMENTATION READY:**  
**EXECUTION REQUIRES SEPARATE AUTHORIZATION**
