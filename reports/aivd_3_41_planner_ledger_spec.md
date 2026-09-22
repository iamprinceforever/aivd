# AIVD 3.41 — Planner Ledger Specification (Design Only)

**Document type:** Planner ledger schema (DOCS ONLY — **NOT IMPLEMENTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Parent charter:** `reports/aivd_3_41_charter.md`  
**Baseline tip:** `a380e3c`  
**Mode:** `AIVD41_PLANNER_AUDIT`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

---

## 1. Purpose

Specify a **behavior-preserving** invent-attempt / reject / score / rank / select ledger that closes Stage-9 gaps without changing discovery semantics, budget, or planner RNG.

Stage-9 cited gaps (immutable):
- invent-attempt / reject ledger = **NOT_RECORDED**
- rank / score / select ledger = **NOT_RECORDED**

## 2. Emission sites (design targets; not implemented here)

| Transition | Primary site | Symbol |
|------------|--------------|--------|
| Candidate created / proposed | `aivd/science/atom_synth.py` | `propose_atoms`, `AtomSynthesizer.plan` |
| Representation policy apply | `aivd/science/representation.py` | `propose_atom_candidates` |
| Rejected (validation/novelty/duplicate) | `aivd/science/atom_synth.py` | `AtomSynthesizer.plan` |
| Scored | `aivd/science/lifecycle.py` | `expected_verified_value` |
| Ranked | `aivd/science/lifecycle.py` | `rank_atoms` |
| Selected / next materialization | `aivd/science/atom_synth.py` | `AtomSynthesizer.next_atom` |
| Invent orchestration / skip | `aivd/science/designer.py` | `ScienceDesigner._maybe_invent_atom` |
| Capacity block | `aivd/science/methods.py` | `MethodInventor._register`, `INVENT_CAP` |
| Growth/compose keep | `aivd/science/grow.py` | `propose_growth` nested `_keep` |
| Firewall | `aivd/science/language.py` | `ExperimentLanguage.firewall` |
| Behavioral identity | `aivd/science/grow.py` | `behavioral_equivalent`, `textual_identity` |

**Constraint:** hooks must be append-only observers. No mutation of return values, ordering, scores, ranks, selections, inventions, budget, or RNG streams.

## 3. Required fields

| Field | Availability at Stage-8/9 | Design requirement |
|-------|---------------------------|--------------------|
| `candidate_key` | PARTIAL — available as body_key after invent in generation_record_summaries; NOT for rejected/unmaterialized | Emit value or `NOT_RECORDED` |
| `candidate_family` | PARTIAL — semantic_class on in-memory InventedAtom / occasional methods_log; NOT in Stage-8 summary schema | Emit value or `NOT_RECORDED` |
| `candidate_origin` | ALREADY_AVAILABLE — generation_record_summaries.origin for invented bodies | Emit value or `NOT_RECORDED` |
| `candidate_generation_method` | NOT_RECORDED as explicit ledger field | Emit value or `NOT_RECORDED` |
| `proposal_index` | NOT_RECORDED in Stage-8 artifacts (InventedAtom.proposal_index exists in-memory only) | Emit value or `NOT_RECORDED` |
| `proposal_epoch` | NOT_RECORDED | Emit value or `NOT_RECORDED` |
| `proposal_state` | NOT_RECORDED — invent-attempt ledger missing (Stage-9 gap) | Emit value or `NOT_RECORDED` |
| `rejection_state` | NOT_RECORDED — invent-reject ledger missing (Stage-9 gap) | Emit value or `NOT_RECORDED` |
| `rejection_reason` | NOT_RECORDED on invent path; FILTER_BEHAVIORAL_DUP is Stage-4/5 CONTROLLED category, not Stage-8 invent ledger | Emit value or `NOT_RECORDED` |
| `score` | NOT_RECORDED — rank/score/select ledger missing (Stage-9 H9e INCONCLUSIVE) | Emit value or `NOT_RECORDED` |
| `score_components` | NOT_RECORDED | Emit value or `NOT_RECORDED` |
| `rank` | NOT_RECORDED in Stage-8 run JSON (methods_log atom_rank before/after truncated, not exported) | Emit value or `NOT_RECORDED` |
| `selection_state` | PARTIAL — n_selected / fate E OBSERVED for non-S pool survivors; reason NOT_RECORDED; S N/A at invent | Emit value or `NOT_RECORDED` |
| `selection_reason` | NOT_RECORDED | Emit value or `NOT_RECORDED` |
| `budget_before` | PARTIAL — budget_used / leftover_at_firewall_decision AVAILABLE; per-candidate budget_before NOT_RECORDED | Emit value or `NOT_RECORDED` |
| `budget_after` | PARTIAL — same | Emit value or `NOT_RECORDED` |
| `firewall_epoch` | ALREADY_AVAILABLE — Stage-8 firewall_epoch / firewalled | Emit value or `NOT_RECORDED` |
| `novelty_state` | NOT_RECORDED in Stage-8 summaries | Emit value or `NOT_RECORDED` |
| `behavioral_identity` | NOT_RECORDED at invent ledger; Stage-8 equiv_decisions are post-pool only | Emit value or `NOT_RECORDED` |
| `body_key` | ALREADY_AVAILABLE — generation_record_summaries.body_key for invented | Emit value or `NOT_RECORDED` |
| `language_key` | NOT_RECORDED | Emit value or `NOT_RECORDED` |
| `parent_key` | PARTIAL — generation_record_summaries.parent (often null) | Emit value or `NOT_RECORDED` |
| `provenance` | NOT_RECORDED in Stage-8 summaries | Emit value or `NOT_RECORDED` |
| `seed` | ALREADY_AVAILABLE | Emit value or `NOT_RECORDED` |
| `plant_id` | ALREADY_AVAILABLE | Emit value or `NOT_RECORDED` |

## 4. States

Allowed `proposal_state` / lifecycle tags: `PROPOSED`, `REJECTED`, `SCORED`, `RANKED`, `SELECTED`, `INVENTED`, `SKIPPED`, `NOT_RECORDED`.

Interpretation rules:
- `PROPOSED` — entered proposal set after `propose_atoms` / `propose_atom_candidates` + plan keep
- `REJECTED` — failed validation/novelty/duplicate before score
- `SCORED` / `RANKED` — passed through `expected_verified_value` / `rank_atoms`
- `SELECTED` — chosen by `next_atom` / invent orchestration for materialization
- `INVENTED` — successfully registered / generation record emitted
- `SKIPPED` — planning gate / budget / capacity skip without invent
- `NOT_RECORDED` — instrumentation absent for that transition (Stage-8/9 default for invent-reject and rank/score/select)

## 5. Budget distinction (binding)

| Label | Meaning |
|-------|---------|
| `NEVER_PROPOSED` | No proposal event for the candidate key in the episode |
| `NOT_REACHED_BEFORE_BUDGET_EXHAUSTION` | Proposal (or reachable proposal) existed, but leftover / BH / invent path exhausted before materialization |

Do not collapse these labels. Stage-8 failure_class `ATOM_INVENTION_SKIPPED_BY_PLANNING` is compatible with either until ledger separates them.

## 6. S observational queries (non-seeding)

Ledger consumers may query whether body keys matching historical S-ATOM / S-CAT / S-DIAG appear in PROPOSED/REJECTED/SCORED/RANKED/SELECTED/INVENTED/SKIPPED rows.  
**Forbidden:** writing S keys into `propose_atoms`, biasing rank/score, or adding odd-stride heuristics.

## 7. Zero-cost / zero-RNG mandate

- Instrumentation must not decrement experimental budget.
- Instrumentation must not call planner RNG / must not reorder RNG consumers.
- Instrumentation must not change hash/identity keys used for selection.

## 8. STOP

Schema only. Do not implement hooks in this phase.
