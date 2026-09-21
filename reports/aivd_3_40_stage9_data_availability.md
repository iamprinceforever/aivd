# AIVD 3.40 Stage-9 — Data Availability Specification (Optional Companion)

**Document type:** Stage-9 data-availability inventory (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Purpose:** Freeze which Stage-8 fields are **AVAILABLE** for offline audit vs **MISSING** (`NOT_RECORDED`), so EXECUTION cannot “discover” new fields mid-analysis.  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Mandate

Inventory is based on Stage-8 COMPLETE artifacts at tip `a447649` (design inspection for schema freeze). This is **not** an executed localization result. If EXECUTION finds a field listed MISSING that is actually present, amend via design revision — do not silently reclassify mid-flight without note.

---

## 1. Aggregate evidence files (AVAILABLE)

| File | Status |
|------|--------|
| `reports/aivd_3_40_stage8_results.md` | AVAILABLE |
| `reports/aivd_3_40_stage8_results.json` | AVAILABLE |
| `reports/aivd_3_40_stage8_mechanism_evidence.json` | AVAILABLE |
| `reports/aivd_3_40_stage8_discovery_evidence.json` | AVAILABLE |
| `reports/aivd_3_40_stage8_rediscovery_evidence.json` | AVAILABLE |
| `reports/aivd_3_40_stage8_recursion_evidence.json` | AVAILABLE |
| `reports/aivd_3_40_stage8_fresh_plant_isolation.json` | AVAILABLE |
| `reports/aivd_3_40_stage8/runs/S8-*_seed*.json` (28) | AVAILABLE |

Cite-only (not Stage-9 primary): Stage-4/5/2/Phase-1/Phase-2/3.38 docs — AVAILABLE as HISTORICAL_REFERENCE / CONTROLLED_FILTER.

---

## 2. Per-run top-level fields (Stage-8 runs)

| Field | Availability | Notes |
|-------|--------------|-------|
| `condition_id`, `family`, `plant_id`, `seed` | AVAILABLE | |
| `terminal_state` | AVAILABLE | expect `UNRESOLVED_INVISIBLE` |
| `discovered`, `pipeline_verified`, `secret_found` | AVAILABLE | |
| `budget_used`, `BH`, `INVENT_CAP`, `REDISCOVERY_FLOOR` | AVAILABLE | |
| `firewall_epoch`, `firewalled`, `provenance_leak` | AVAILABLE | |
| `failure_class` | AVAILABLE | Stage-8 matrix shows planning-skip class |
| `stop_reason` | AVAILABLE | Stage-8 matrix shows budget exhausted |
| `occupancy` | AVAILABLE | |
| `generation_record_summaries` | AVAILABLE | body_key, origin, parent (often null) |
| `s_diagnostic` | AVAILABLE | includes `odd_cat_self_in_records`, `verified` |
| `mechanism` | AVAILABLE | see §3 |
| `rank` / `score` / selection policy ledger | **MISSING** | → selection **reason** NOT_RECORDED |
| Per-invent reject ledger | **MISSING** | → invent-attempt detail NOT_RECORDED |
| Per-compose attempt ledger | **MISSING** | → compose-attempt detail NOT_RECORDED |
| Per-step language-store diffs | **MISSING** | → H9b detail often NOT_RECORDED |

---

## 3. `mechanism` subfields

| Field | Availability | Notes |
|-------|--------------|-------|
| `n_equiv_decisions`, `equiv_decisions[]` | AVAILABLE | candidate_key, label, action, apply_micro_calls |
| `n_pool_entered`, `n_pool_removed_D`, `n_pool_survived` | AVAILABLE | Stage-8 D=0 |
| `n_selected`, `n_verified_keys` | AVAILABLE | |
| `n_rediscovered`, `n_recursive`, `recursive_edges` | AVAILABLE | |
| `D_rate`, `surv_rate` | AVAILABLE | |
| `fate_counts`, `fates` | AVAILABLE | E/H dominant in Stage-8 priors |
| `unobserved_reasons` | AVAILABLE | may be empty object |
| `repair_calls_total` | AVAILABLE | |
| Ranked candidate lists | **MISSING** | |
| Score vectors | **MISSING** | |

---

## 4. Waypoint availability matrix (design freeze)

| Waypoint | Primary status | Blocking gaps |
|----------|----------------|---------------|
| INVENTION | PARTIAL | summaries AVAILABLE; reject ledger MISSING |
| LANGUAGE_GROWTH | PARTIAL | occupancy AVAILABLE; diffs MISSING |
| ATOM_BODY_IDENTITY | AVAILABLE | keys + s_diagnostic |
| COMPOSITION | PARTIAL | composed keys AVAILABLE; attempt ledger MISSING |
| CANDIDATE_CREATION | PARTIAL | equiv candidate_keys AVAILABLE |
| POOL_ENTRY | AVAILABLE | n_pool_* + fates |
| EQUIVALENCE_DECISION | AVAILABLE | equiv_decisions + D counts |
| SURVIVAL | AVAILABLE | |
| SELECTION | PARTIAL | n_selected / fate E AVAILABLE; **reason MISSING** |
| VERIFICATION | AVAILABLE | verified flags; failure reasons often N/A if never selected |
| REDISCOVERY | AVAILABLE | |
| RECURSION | AVAILABLE | |
| STOPPING_STATE | AVAILABLE | |

---

## 5. Implications for hypothesis leaves (pre-registered)

| Leaf | Likely data posture (design expectation — not result) |
|------|--------------------------------------------------------|
| H9a | PARTIAL — may be WEAKLY SUPPORTED / SUPPORTED via s_diagnostic + failure_class + missing S keys; invent-reject detail NOT_RECORDED |
| H9b | Often INCONCLUSIVE without language diffs |
| H9c | PARTIAL — composed non-S keys OBSERVED; S compose attempts NOT_RECORDED |
| H9d | Score if pool-entry of S body NOT_OBSERVED after composition OBSERVED; else N/A |
| H9D | D aggregates AVAILABLE → scoped AGAINST expected if D=0 confirmed |
| H9e | **INCONCLUSIVE** while rank/score MISSING (even if E dominates) |
| H9f | Likely NOT_APPLICABLE / AGAINST as earliest if n_selected=0 |
| H9g | Rediscovery fields AVAILABLE for non-S bodies; S-specific may be N/A |
| H9h | stop/budget AVAILABLE; earliest-locus claim requires care |
| H9i | WEAKLY SUPPORTED / SUPPORTED if gaps block H9a–H9e separation |
| H9-REJECT | not_supported unless protocol broken |

---

## 6. Missing-data handling (binding pointer)

Follow preregistration §6 and analysis_spec P0:

1. Tag NOT_RECORDED — do not fill.  
2. Score affected leaves INCONCLUSIVE.  
3. Report gaps in Stage-9 results (when authorized).  
4. **Do not** propose or run a new Sacred / instrumentation experiment inside Stage-9 EXECUTION authorization.

Future instrumentation (post Stage-9) would require a **separate design** — out of Stage-9 scope.

---

## 7. STOP

Inventory only. Do not execute audit. Do not modify Stage-8 artifacts.
