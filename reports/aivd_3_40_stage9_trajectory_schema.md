# AIVD 3.40 Stage-9 — Trajectory Reconstruction Schema

**Document type:** Stage-9 trajectory schema (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Companions:** analysis_spec, metrics, data_availability  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 0. Purpose

Define the **vocabulary and field mapping** for reconstructing autonomous Stage-8 trajectories offline. Binding observation states prevent converting instrumentation gaps into causal claims.

---

## 1. Observation states (binding)

| State | Code | Meaning | Allowed causal use |
|-------|------|---------|-------------------|
| **OBSERVED** | `OBSERVED` | Explicit value present in Stage-8 recorded evidence | May support FOR / AGAINST |
| **NOT_OBSERVED** | `NOT_OBSERVED` | Instrument could see the event; record shows absence / false / zero | May support “did not occur” |
| **NOT_RECORDED** | `NOT_RECORDED` | Stage-8 recorder did not capture this field/stage | Must **not** be treated as failure; feeds H9i / INCONCLUSIVE |
| **NOT_APPLICABLE** | `NOT_APPLICABLE` | Downstream of earlier hard stop, or irrelevant under recorded fate | Skip in earliest-locus walk |

**Forbidden conversions:**

- `NOT_RECORDED` → failure  
- absence-from-report → “did not occur” (unless explicit NOT_OBSERVED)  
- Stage-4 controlled OBSERVED → Stage-8 autonomous OBSERVED  

---

## 2. Waypoint order (canonical)

```
W01 INVENTION
W02 LANGUAGE_GROWTH
W03 ATOM_BODY_IDENTITY
W04 COMPOSITION
W05 CANDIDATE_CREATION
W06 POOL_ENTRY
W07 EQUIVALENCE_DECISION
W08 SURVIVAL
W09 SELECTION
W10 VERIFICATION
W11 REDISCOVERY
W12 RECURSION
W13 STOPPING_STATE
```

Earliest-disappearance walk uses this order. Repair-divergence walk uses the same order.

---

## 3. Per-waypoint field mapping (Stage-8 artifacts)

Sources: `reports/aivd_3_40_stage8/runs/*.json` unless noted.

### W01 INVENTION

| Predicate | Typical Stage-8 source | If missing |
|-----------|------------------------|------------|
| Invent events occurred | `generation_record_summaries` with `origin=invented_atom` | NOT_RECORDED if summaries absent |
| S-direction atom invented | body_key ∈ summaries matching odd-stride key | NOT_OBSERVED if summaries present and key absent; else NOT_RECORDED |
| Planning skip class | `failure_class` (e.g. `ATOM_INVENTION_SKIPPED_BY_PLANNING`) | NOT_RECORDED if field absent |
| Invent-attempt rejects ledger | *(often absent)* | **NOT_RECORDED** (do not infer) |

### W02 LANGUAGE_GROWTH

| Predicate | Source | If missing |
|-----------|--------|------------|
| Occupancy / language size | `occupancy` | NOT_RECORDED if absent |
| Growth edge lineage | parent links in generation summaries | NOT_RECORDED if parents null/absent without schema |
| Per-step language diffs | *(typically absent)* | **NOT_RECORDED** |

### W03 ATOM_BODY_IDENTITY

| Predicate | Source | If missing |
|-----------|--------|------------|
| Body keys present | `generation_record_summaries[].body_key`, `mechanism.fates` keys | NOT_RECORDED if both absent |
| Odd CAT-self in records | `s_diagnostic.odd_cat_self_in_records` | If boolean present → OBSERVED true/false ⇒ OBSERVED / NOT_OBSERVED |
| Identity vs U known-good | compare keys to `MAPT(AT:-1)` / U CAT-self | OBSERVED comparison only on present keys |

### W04 COMPOSITION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Composed bodies in records | CAT-shaped keys in summaries / fates | Presence OBSERVED; attempts ledger often **NOT_RECORDED** |
| S-direction composition success | odd CAT-self key present | NOT_OBSERVED if instrumented absence; else NOT_RECORDED for attempts |
| Compose operator IDs | *(may be absent)* | **NOT_RECORDED** |

### W05 CANDIDATE_CREATION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Candidates created | implied by pool / equiv decision inputs | NOT_RECORDED if only aggregates |
| Candidate list | `mechanism.equiv_decisions[].candidate_key` | OBSERVED for keys that reached equiv |

### W06 POOL_ENTRY

| Predicate | Source | If missing |
|-----------|--------|------------|
| `n_pool_entered` | `mechanism.n_pool_entered` | NOT_RECORDED if absent |
| Body entered pool | candidate in equiv_decisions or fate not A/B/C | OBSERVED when listed |
| Fate C | primary fate C in `mechanism.fates` | OBSERVED if labeled; absence of label ≠ NOT_OBSERVED without schema coverage |

### W07 EQUIVALENCE_DECISION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Decision events | `mechanism.equiv_decisions[]` | NOT_RECORDED if absent |
| Duplicate removals | `action/label`, `n_pool_removed_D`, M8 `equiv_decision_counts` | OBSERVED zeros are **NOT_OBSERVED removals** (instrument saw keep/duplicate) |
| Family | `mechanism.family` / condition map | OBSERVED |

### W08 SURVIVAL

| Predicate | Source | If missing |
|-----------|--------|------------|
| Survived equiv | `n_pool_survived`, fate not D | OBSERVED |
| Fate E/H/… after survive | `mechanism.fates` | OBSERVED |

### W09 SELECTION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Selected count | `mechanism.n_selected` | OBSERVED if present |
| Rank / score / policy | *(Stage-8 runs: typically absent)* | **NOT_RECORDED** → H9e INCONCLUSIVE |
| “Not selected” as outcome | fate **E** with n_selected=0 | Outcome OBSERVED; **reason** NOT_RECORDED |

### W10 VERIFICATION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Verified | `pipeline_verified`, `s_diagnostic.verified`, D8 | OBSERVED |
| Verify failure reasons | *(may be absent when never selected)* | NOT_APPLICABLE if n_selected=0; else NOT_RECORDED if selected without reason |

### W11 REDISCOVERY

| Predicate | Source | If missing |
|-----------|--------|------------|
| Rediscovery origins | summaries `origin=independent_rediscovery`; RD8 | OBSERVED |
| Independence / leak | `n_independent`, `provenance_leak`, `strict_independence` | OBSERVED |
| Firewall | `firewall_epoch`, `firewalled`, floor | OBSERVED |

### W12 RECURSION

| Predicate | Source | If missing |
|-----------|--------|------------|
| Recursive bodies | `mechanism.n_recursive`, `recursive_edges`, RC8 | OBSERVED |
| Fate I | fates / I counts | OBSERVED |

### W13 STOPPING_STATE

| Predicate | Source | If missing |
|-----------|--------|------------|
| Terminal | `terminal_state` | OBSERVED |
| Stop reason | `stop_reason` | OBSERVED |
| Failure class | `failure_class` | OBSERVED |
| Budget | `budget_used`, `BH`, `budget_remaining` | OBSERVED |

---

## 4. S-direction predicates (prereg)

| ID | Predicate |
|----|-----------|
| S-ATOM | body_key == `MAPT(SLICE:1,2(TOK))` appears in invent/generation records |
| S-CAT | body_key == `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` appears |
| S-DIAG | `s_diagnostic.odd_cat_self_in_records == true` |
| S-VER | `s_diagnostic.verified == true` OR pipeline_verified with S body |

Historical S behavioral direction = progress satisfying S-ATOM → S-CAT → pool → … → S-VER as in prior controlled/reference trajectories. Stage-9 asks where autonomous Stage-8 ceases that direction.

---

## 5. Fate label continuity (A–I)

Unchanged from Stage-8:

| Code | Meaning |
|------|---------|
| A | Never invented |
| B | Invented but composition failed |
| C | Composed but absent from pool |
| D | Entered pool but removed by equivalence |
| E | Survived equiv but not selected |
| F | Selected but failed verification |
| G | Verified |
| H | Independently rediscovered |
| I | Produced another generation |

Primary fate per tracked body from `mechanism.fates`. Missing body of interest → do not invent a fate; mark S-predicates NOT_OBSERVED / NOT_RECORDED per §3.

---

## 6. Cell trajectory record (output schema for EXECUTION)

```json
{
  "condition_id": "S8-BASELINE",
  "seed": 0,
  "plant_id": "AIVD340-S8-BASELINE",
  "waypoints": {
    "INVENTION": {"state": "OBSERVED|NOT_OBSERVED|NOT_RECORDED|NOT_APPLICABLE", "evidence_refs": [], "notes": ""},
    "LANGUAGE_GROWTH": {},
    "ATOM_BODY_IDENTITY": {},
    "COMPOSITION": {},
    "CANDIDATE_CREATION": {},
    "POOL_ENTRY": {},
    "EQUIVALENCE_DECISION": {},
    "SURVIVAL": {},
    "SELECTION": {},
    "VERIFICATION": {},
    "REDISCOVERY": {},
    "RECURSION": {},
    "STOPPING_STATE": {}
  },
  "s_predicates": {
    "S-ATOM": "OBSERVED|NOT_OBSERVED|NOT_RECORDED|NOT_APPLICABLE",
    "S-CAT": "",
    "S-DIAG": "",
    "S-VER": ""
  },
  "fate_counts": {},
  "earliest_s_disappearance_waypoint": null,
  "earliest_s_disappearance_confidence": "SUPPORTED|WEAKLY SUPPORTED|INCONCLUSIVE|AGAINST|null"
}
```

---

## 7. Repair-divergence record

```json
{
  "seed": 0,
  "baseline_vs": {
    "S8-RA": {"earliest_diff_waypoint": null, "diff_kind": "none|state|s_predicate|fate|ledger_only", "notes": ""},
    "S8-RC": {},
    "S8-RD": {}
  },
  "null_label_if_none": "NO OBSERVED REPAIR-INDUCED TRAJECTORY DIVERGENCE"
}
```

`ledger_only` = differences confined to `repair_calls_total` / family identity without S-trajectory change — **does not** count as S-trajectory divergence.

---

## 8. Honesty examples

| Situation | Correct tagging |
|-----------|-----------------|
| `odd_cat_self_in_records: false` | S-CAT / S-DIAG → **NOT_OBSERVED** |
| No invent-attempt reject list in JSON | invent-reject reasons → **NOT_RECORDED** |
| fate E and `n_selected: 0`, no scores | selection outcome NOT selected **OBSERVED**; selection reason **NOT_RECORDED** |
| `n_pool_removed_D: 0` with equiv_decisions keep | D removals **NOT_OBSERVED** (instrument saw decisions) |
| Comparing to Stage-4 solo odd pool 7/7 | Stage-4 remains CONTROLLED_FILTER cite — **not** copied into Stage-8 cell as OBSERVED autonomous composition |

---

## 9. STOP

Schema only. Do not populate result tables in this design commit.
