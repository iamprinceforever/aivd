# AIVD 3.40 Phase-1 — Replay Schema (OBSERVED vs COUNTERFACTUAL)

**Recorded:** 2026-09-21 17:21 IST  
**Parent:** `reports/aivd_3_40_phase1_execution_charter.md`  
**Authority:** Stage-3 instrumentation + counterfactual replay specs at `146915b`  
**Authorization:** `CHARTER_ONLY_NOT_EXECUTED` — schema only; no runner in this commit

---

## 1. Purpose

Define machine-readable records for:

1. **OBSERVED** — normalized facts imported from immutable Stage-2 run JSONs.  
2. **COUNTERFACTUAL** — evaluator-only hypotheticals at historical decision points.  

Counterfactual ≠ observed discovery. Never write CF accepts into Sacred VERIFIED tables.

---

## 2. Common envelope (every row)

```json
{
  "schema_version": "aivd340.phase1.replay.v1",
  "record_label": "observed | counterfactual",
  "audit_cell_id": "AUD-S2-BHR1-S | AUD-S2-BHR1-U | AUD-S2-BHR1b-S | AUD-S2-BHR1b-U",
  "condition_id": "BH-R1 | BH-R1b",
  "target_role": "S | U",
  "seed": 0,
  "plant_id": "AIVD340-S2-S | AIVD340-S2-U",
  "source_artifact_path": "reports/aivd_3_40_stage2/runs/BH-R1_seed0_S.json",
  "source_generation_id": "string | null",
  "firewall_epoch": 0,
  "field_coverage_notes": {
    "pool": "UNKNOWN",
    "score": "UNKNOWN",
    "ranking": "UNKNOWN",
    "selected": "UNKNOWN",
    "features_used": "UNKNOWN"
  }
}
```

---

## 3. OBSERVED record schema

Imported from Stage-2 `generation_records` + envelope + selective `methods_log` projection.

```json
{
  "record_label": "observed",
  "event_kind": "invent | grow | compose | rediscover | firewall | terminal | other",
  "generation_id": "string",
  "parent_generation_id": "string | null",
  "candidate_origin": "string",
  "proposal_origin": "string | null",
  "body_key": "string | null",
  "candidate_id": "string | null",
  "candidate": "any | null",
  "semantic_class": "string | null",
  "verification_state": "string | null",
  "budget_before": "number | null",
  "budget_after": "number | null",
  "leftover": "number | null",
  "leftover_after": "number | null",
  "kind": "string | null",
  "action": "string | null",
  "terminal_state": "string | null",
  "strict_independence": "boolean | null",
  "leftover_at_firewall_decision": "number | null",
  "language_programs": ["string"],
  "methods_log_excerpt": [
    {"event": "string", "ops": "string | null"}
  ],
  "derived": {
    "produced_body_in_generation_records": true,
    "invent_ops_list": ["string"]
  },
  "unknown_fields_explicit": [
    "full_candidate_pool_snapshots",
    "candidate_scores",
    "candidate_ranking_tables",
    "explicit_selected_candidate_decision_records",
    "features_used_maps"
  ]
}
```

**Import rules:**

- Copy OBSERVED values verbatim where present.  
- Mark absent Stage-3 fields as `null` + list in `unknown_fields_explicit`.  
- Do **not** regenerate discovery to populate UNKNOWN.  
- `record_label` for all Stage-2 imports = `observed`.

---

## 4. COUNTERFACTUAL record schema

```json
{
  "record_label": "counterfactual",
  "counterfactual_op": "what_if_select | what_if_grow | enumerate_produced_bodies | path_prefix_check",
  "counterfactual_of_generation_id": "string | null",
  "decision_point_ref": {
    "source_artifact_path": "string",
    "generation_id": "string | null",
    "firewall_epoch": 0,
    "note": "historical anchor only; trajectory not mutated"
  },
  "hypothesis_input": {
    "body_key": "string | null",
    "parent_atom_body_key": "string | null",
    "grow_op": "string | null",
    "grow_op_must_be_generic_legal": true
  },
  "evaluator_result": {
    "would_accept": "boolean | null",
    "would_trigger_plant": "boolean | null",
    "terminal_class_hypothetical": "string | null",
    "reason": "string | null",
    "deterministic": true
  },
  "discovery_feedback": false,
  "sacred_credit": false,
  "notes": "CF must not modify discovery/model state or Stage-2 artifacts"
}
```

**Hard constraints:**

| Field / rule | Binding |
|--------------|---------|
| `discovery_feedback` | Always `false` |
| `sacred_credit` | Always `false` |
| Grow ops | Generic legal vocabulary only — no plant-named ops |
| GT use | Evaluator-side scoring only; never rewrite invent features |
| R1b rows | Tag `r1b_observational_only: true` |

---

## 5. Divergence report schema (per seed × condition)

```json
{
  "schema_version": "aivd340.phase1.divergence.v1",
  "condition_id": "BH-R1",
  "seed": 0,
  "s_artifact": "reports/aivd_3_40_stage2/runs/BH-R1_seed0_S.json",
  "u_artifact": "reports/aivd_3_40_stage2/runs/BH-R1_seed0_U.json",
  "u_positive_control_reconstructed": "pass | fail | not_run",
  "earliest_divergence": "H1 | H2 | H3 | H4 | H5 | H6 | INCONCLUSIVE",
  "s_questions": {
    "Q1": "yes | no | UNKNOWN",
    "Q2": "yes | no | UNKNOWN",
    "Q3": "yes | no | UNKNOWN",
    "Q4": "yes | no | UNKNOWN",
    "Q5": "yes | no | UNKNOWN",
    "Q6": "yes | no | UNKNOWN",
    "Q7": "yes | no | UNKNOWN",
    "Q8": "yes | no | UNKNOWN"
  },
  "evidence_refs": {
    "generation_ids": ["string"],
    "observed_record_ids": ["string"],
    "counterfactual_record_ids": ["string"]
  },
  "h3_note": "May remain INCONCLUSIVE: pool/score/rank/selected UNKNOWN",
  "s_unresolved_preserved": true,
  "r1b_caveat_applies": false,
  "max_valid_claim": "string",
  "stop_if_u_fail": true
}
```

**Ordering rule:** Answer Q1→Q8 in order. If evidence absent → `UNKNOWN`. No inference of missing stages.

---

## 6. Validation tests (description only — not executed here)

### 6.1 U BH-R1 positive-control reconstruction (Gate E)

For each seed in `{0,1,2,3,4,7,11}` on `AUD-S2-BHR1-U`:

1. Load OBSERVED trajectory.  
2. Reconstruct produced path relevant to historical verify.  
3. Assert consistency with Stage-2 recorded `terminal_state` / `pipeline_verified` / independence / firewall expectations (**F7/I7/V7** aggregate).  
4. Where evaluator replay is deterministic, offline evaluate historical body → must match recorded accept class.  
5. **If fail → STOP**; do not interpret S. Document nondeterminism causes explicitly (no silent evaluator config swap).

### 6.2 Label integrity

- Every Stage-2 import row has `record_label=observed`.  
- Every CF row has `record_label=counterfactual` and `sacred_credit=false`.  
- Mixed unlabeled rows → fail validation.

### 6.3 Immutability

- SHA-256 (or byte identity) of source Stage-2 JSON unchanged before/after Phase-1 tooling.  
- No writes under `reports/aivd_3_40_stage2/`.

### 6.4 UNKNOWN honesty

- Rows must not invent pool/score/rank/selected/`features_used` values.  
- Strong H3 accept criteria cannot pass validation if those fields remain UNKNOWN.

### 6.5 R1b caveat flag

- All BH-R1b divergence reports set `r1b_caveat_applies=true` and refuse “pure prereg” wording.

---

## 7. Aggregate Phase-1 outputs (future paths; not created now)

| Artifact | Intent |
|----------|--------|
| `reports/aivd_3_40_phase1/observed_events.jsonl` | Normalized OBSERVED stream |
| `reports/aivd_3_40_phase1/counterfactual_events.jsonl` | CF stream |
| `reports/aivd_3_40_phase1/divergence_by_seed.json` | Per-seed divergence reports |
| `reports/aivd_3_40_phase1/results.md` | Human summary; unresolved S preserved |

---

## 8. STOP

Replay **schema** only. No Phase-1 runner, no Sacred, no discovery edits in this commit.
