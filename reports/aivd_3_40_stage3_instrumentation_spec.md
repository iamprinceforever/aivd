# AIVD 3.40 Stage-3 — Instrumentation Specification

**Recorded:** 2026-09-21 17:04 IST  
**Parent charter:** `reports/aivd_3_40_stage3_charter.md`  
**Authorization:** Spec only. Emitting these fields in code requires EXECUTION charter.  
**Primary use:** Phase-1 offline normalization of Stage-2 trajectories; later live Sacred only if authorized.

---

## Purpose

Per-generation (and per-decision) records must answer, for each seed × target × condition:

1. Did S fail to **INVENT** the required direction?  
2. Invent but fail to **GROW** / compose a finished program?  
3. Grow but fail to **SELECT** for verification?  
4. Select but fail to **VERIFY**?

Also support H5 (remaining budget at failure) and H6 (invariant / mode consistency checks vs U).

---

## Required fields (minimum schema)

Every recorded generation / decision event SHOULD include:

| Field | Type / notes | Answers |
|-------|--------------|---------|
| `generation_id` | stable unique id | identity |
| `parent_id` | nullable id | lineage |
| `episode_id` | run id (condition×target×seed) | grouping |
| `condition_id` | e.g. `BH-R1`, `BH-R1b` | factor |
| `target_role` | `S` \| `U` | factor |
| `seed` | int | factor |
| `firewall_epoch` | int ≥ 0 | independence / stage |
| `candidate_origin` | GenerationRecord origin enum / string | provenance |
| `representation_id` | `R0` \| `R1` \| `R1b` \| future `Rx` | H1 |
| `features_used` | list/map of generic feature keys actually consulted (no secrets) | H1 |
| `invented_atoms` | list of body keys / atom ids invented at this step (may be empty) | H1 |
| `composed_candidates` | list of grown/composed body keys considered | H2 |
| `candidate_scores` | map body_key → score components | H3 |
| `ranking` | ordered list of body keys after rank | H3 |
| `selected_candidate` | body key or null | H3 |
| `verification_candidate` | body key submitted to verify (may differ if retarget — must record) | H4 |
| `verification_result` | enum: `accept` \| `reject` \| `skip` \| `not_called` + reason code | H4 |
| `remaining_budget` | leftover steps / invent remaining as applicable (define units consistently with Stage-2) | H5 |
| `rejection_or_skip_reason` | machine code + short string | all |
| `event_kind` | `invent` \| `grow` \| `compose` \| `rank` \| `select` \| `verify` \| `firewall` \| `terminal` | staging |
| `record_label` | `observed` \| `counterfactual` | replay integrity |
| `terminal_state` | if terminal event | outcome |
| `leakage_flag` | bool (must be false for credit) | integrity |

### Optional but recommended

| Field | Why |
|-------|-----|
| `semantic_class` / `coverage_key` | Diagnose class-collapse vs geometry coverage |
| `promoted_classes_so_far` | Invent scheduling |
| `max_cands` / growth knobs in effect | H2 mechanism |
| `independently_discovered` bit | Strict bar audit |
| `plant_triggered` | Evaluator-side only in separate channel — **never** feed into discovery features |

---

## Pipeline question mapping

| Question | Positive evidence pattern | Negative evidence pattern |
|----------|---------------------------|---------------------------|
| Fail INVENT? | Across episode, `invented_atoms` never contains direction atoms from which finished S-program is reachable | Direction atoms present in `invented_atoms` |
| Fail GROW? | Direction atoms present; `composed_candidates` lacks finished body | Finished body ∈ `composed_candidates` |
| Fail SELECT? | Finished body in pool/`ranking`; `selected_candidate` ≠ that body | `selected_candidate` is finished S-direction body |
| Fail VERIFY? | `verification_candidate` correct; `verification_result` ≠ accept | Verify accept, or verify never reached because earlier fail |

**Earliest bottleneck** = first failed stage in invent → grow → select → verify order.

---

## Aggregation outputs (Phase-1 report expectations)

Per audit cell (`AUD-S2-BHR1-S`, etc.):

- Counts of seeds in each earliest-bottleneck class  
- Example `generation_id` chains (1–2 exemplars) for the modal class  
- U positive-control reconstruction checklist pass/fail  
- H6 invariant checklist pass/fail  
- Explicit statement if S remains unresolved with bottleneck = X

Do **not** aggregate S+U into one success rate.

---

## Compatibility with existing GenerationRecord

Stage-2 / 3.39 `GenerationRecord` already carries origin, independence, and body keys for many events. Phase-1 may:

- Map existing JSON run artifacts → this schema (preferred first), and/or  
- Specify additive recorder fields under a future EXECUTION charter  

**Forbidden without EXECUTION charter:** changing GenerationRecord *semantics*, independence credit rules, or discovery behavior when recording is enabled.

---

## Privacy / Absolute Rules

- No plant secrets, evaluator GT, or ODDSTRIDE/ROL1 tokens may appear in `features_used` fed to discovery.  
- Evaluator-only annotations (e.g., “this body would match S geometry”) belong in **counterfactual replay reports**, labeled evaluator-derived, never as discovery `candidate_origin` credit.

---

## STOP

Instrumentation **spec** only. No recorder implementation in this commit.
