# AIVD 3.41 DESIGN CHARTER — Invention-Planner Audit / Causal Localization (Design Only)

**Document type:** AIVD 3.41 DESIGN CHARTER (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-22 12:35 IST  
**Baseline tip (authorized override):** `a380e3c` / `a380e3ce0be2bb1b456c38a0213cde12feef8f45`  
**Baseline branch:** `research/aivd-3.40-budget-representation-frontier`  
**Design branch:** `research/aivd-3.41-invention-planner-audit`  
**Parent of baseline tip:** `56dbc81` / `56dbc81f2712b610c852e03d87cd02eb706c2da1` (Stage-9 COMPLETE)  
**Authority priors (cite; do not weaken):** Stage-9 SUCCESS `56dbc81` / design `97f3804`; Stage-8 PARTIAL `a447649` / design `129a2e9`; Stage-7 `079d66f`; Stage-5 H5b FALSE_DUPLICATE; Stage-4 H2c / FILTER_BEHAVIORAL_DUP (CONTROLLED)  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Status:** **AIVD 3.41 DESIGN READY: IMPLEMENTATION REQUIRES SEPARATE AUTHORIZATION**

**Note on AIVD-v3.38.0 discrepancy:** Named branch `AIVD-v3.38.0` lacked Stage-9 lineage. User authorized baseline tip `a380e3c` on `research/aivd-3.40-budget-representation-frontier` (Stage-9 stamp). Design baseline is **aivd research tip** `a380e3c`; frozen remote `aivd-3.38.0-frozen` / worktree `origin` is **not** the design parent. Prefer push remote **`aivd`**.

Companion deliverables (this commit, `reports/` only):

1. `aivd_3_41_charter.md` — **this file**
2. `aivd_3_41_hypothesis_tree.md`
3. `aivd_3_41_matrix.json`
4. `aivd_3_41_preregistration.md`
5. `aivd_3_41_planner_ledger_spec.md`
6. `aivd_3_41_state_machine.md`
7. `aivd_3_41_semantic_preservation.md`
8. `aivd_3_41_rng_integrity.md`
9. `aivd_3_41_test_spec.md`
10. `aivd_3_41_execution_spec.md`

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Scope (this commit) | **DESIGN documents only** under `reports/` |
| No implementation | Do **not** implement planner ledger hooks, modes, or tests in production code in this phase |
| No production mutation | Do **not** edit `grow.py`, live `FILTER_BEHAVIORAL_DUP` path, `propose_atoms`, R-A/R-C/R-D, planner scoring/ranking/selection math, `invent_cap` / `INVENT_CAP`, firewall, novelty thresholds, TinyLlama, Sacred |
| No Sacred / plants | No discovery experiments; no live plant runs |
| No filter merge | Do **not** merge R-A/R-C/R-D; do **not** revive R-B |
| No S injection | Do **not** add S-specific or odd-stride heuristics; do **not** seed S-ATOM/S-CAT/S-DIAG into `propose_atoms` |
| No history rewrite | Do **not** modify Stage-7/8/9 results or baselines |
| Observation-only | Charter content is observational; future instrumentation must be **behavior-preserving** |
| Mode | `AIVD41_PLANNER_AUDIT` — observational; normal 3.40 behavior remains available when audit instrumentation is off/inert |
| STOP | Implementation / Sacred / instrumentation wiring requires **separate authorization** (see `aivd_3_41_execution_spec.md`) |

If a “design” proposal would inject S into `propose_atoms`, change ranking/selection math, raise BH/`INVENT_CAP`, lower firewall floor, merge controlled FALSE_DUPLICATE with autonomous invisibility, rewrite Stage-8/9, or define success as “S VERIFIED” → **STOP**.

---

## 1. Why 3.41 (post Stage-9)

### 1.1 Stage-8 / Stage-9 priors (immutable cite)

**Stage-8** (`a447649`): conditions S8-BASELINE/RA/RC/RD × seeds `[0,1,2,3,4,7,11]`; BH=48; invent_cap=48; REDISCOVERY_FLOOR=5; **28/28** `UNRESOLVED_INVISIBLE`; S verified **0/7**; **D=0**; no repair-induced trajectory divergence; axis-2/5 **PASS**; axis-3 **NULL**.

**Stage-9** (`56dbc81`): earliest disappearance waypoint = **INVENTION**; S-ATOM / S-CAT / S-DIAG **NOT_OBSERVED**; **H9a SUPPORTED**; **H9D AGAINST** scoped; **H9e INCONCLUSIVE**; controlled FALSE_DUPLICATE ≠ autonomous invisibility. Invent-attempt/reject ledger + rank/score/select ledger = **NOT_RECORDED**.

### 1.2 Primary scientific question (binding)

> **Why does the autonomous invention planner fail to produce the S behavioral direction? How does it propose / reject / score / rank / select / invent?**

Operationalized: in a future authorized phase, instrument the invention-planning path so each candidate’s lifecycle is ledgered without changing discovery semantics, then localize among H10a–H10h whether S-direction candidates are NEVER_PROPOSED, rejected, demoted by score/rank, not selected, skipped by budget/planning gates, or blocked by novelty/firewall — distinguishing **NEVER_PROPOSED** from **NOT_REACHED_BEFORE_BUDGET_EXHAUSTION**.

### 1.3 What 3.41 is NOT

- Not “make S pass” / not S VERIFIED as success criterion
- Not Stage-9 re-litigation that weakens H9a / H9D scoped AGAINST / H9e INCONCLUSIVE
- Not assumption that H10a (never proposed) follows from Stage-9 invention absence alone
- Not S seeding into `propose_atoms` / odd-stride heuristics
- Not live FILTER replacement or R-A/R-C/R-D merge
- Not Sacred / TinyLlama / plant execution under design authorization
- Not mutation of historical Stage-7/8/9 artifacts

---

## 2. Mode: `AIVD41_PLANNER_AUDIT`

| Property | Binding |
|----------|---------|
| Kind | Observational planner audit |
| Default discovery path | Unchanged 3.40 behavior when audit instrumentation is off / inert |
| Instrumentation | Behavior-preserving append-only ledger; **zero** experimental budget consumption; **no** planner RNG consumption |
| S-ATOM / S-CAT / S-DIAG | **Observational queries only** — never seed into `propose_atoms` |
| Controls | Preregistered rules for naturally successful candidates; no post-hoc favorable selection |

---

## 3. Planner path under inspection (read-only grounding)

Grounded in baseline `a380e3c` source (paths + symbols):

| Stage | Path | Symbol(s) |
|-------|------|-----------|
| Proposal generation | `aivd/science/atom_synth.py` | `propose_atoms`, `AtomSynthesizer.plan` |
| Representation wrapper | `aivd/science/representation.py` | `propose_atom_candidates`, `propose_growth_candidates` |
| Rejection (novelty / validation / duplicate) | `aivd/science/atom_synth.py` | `AtomSynthesizer.plan` (`atom_duplicate`, validation fails); `classify_atom` (`aivd/science/atom.py`) |
| Scoring | `aivd/science/lifecycle.py` | `expected_verified_value` |
| Ranking | `aivd/science/lifecycle.py` | `rank_atoms` |
| Selection / materialization order | `aivd/science/atom_synth.py` | `AtomSynthesizer.next_atom` (pop front of ranked `board.remaining`) |
| Invention orchestration | `aivd/science/designer.py` | `ScienceScienceDesigner._maybe_invent_atom` |
| Capacity gate | `aivd/science/methods.py` | `MethodInventor._register`, `INVENT_CAP` |
| Growth / compose selection | `aivd/science/grow.py` | `propose_growth`, `pick_compose_pair`, `pick_generation_action`, nested `_keep` |
| Budget / planning skip | `aivd/science/designer.py` | leftover `< 3` → `ATOM_INVENTION_SKIPPED_BY_PLANNING`; `REDISCOVERY_FLOOR` via `grow.py` |
| Firewall / provenance | `aivd/science/language.py` | `ExperimentExperimentLanguage.firewall`; `ScienceDesigner._maybe_firewall` |
| Behavioral identity | `aivd/science/grow.py` | `behavioral_equivalent`, `textual_identity` |
| Generation records (partial) | `aivd/science/generation_record.py` | `GenerationRecord` |
| Stage-8 capture (partial) | `aivd/experiments/aivd340/stage8_recorder.py` | invent keys; **no** invent-reject / rank-score-select ledger |

**Code fact (design-relevant, not a scored claim):** frozen `propose_atoms` 8-set **includes** odd-stride `MAPT(SLICE:1,2(TOK))` at `proposal_index=3` (same `char_stride` semantic_class as EVEN `MAPT(SLICE:0,2(TOK))` at index 1). Stage-8/9 show EVEN invented and odd **NOT_OBSERVED**. Therefore **do not assume H10a** from Stage-9 invention absence alone — ledger must distinguish proposal vs reject vs rank vs select vs invent vs budget skip.

---

## 4. Ledger field mandate

Required fields (emit `NOT_RECORDED` when unavailable; **never fabricate**):

candidate_key, candidate_family, candidate_origin, candidate_generation_method, proposal_index, proposal_epoch, proposal_state, rejection_state, rejection_reason, score, score_components, rank, selection_state, selection_reason, budget_before, budget_after, firewall_epoch, novelty_state, behavioral_identity, body_key, language_key, parent_key, provenance, seed, plant_id

**States:** PROPOSED, REJECTED, SCORED, RANKED, SELECTED, INVENTED, SKIPPED, NOT_RECORDED

**Budget distinction (binding):** `NEVER_PROPOSED` vs `NOT_REACHED_BEFORE_BUDGET_EXHAUSTION`.

Stage-9 gaps to close (cite): invent-attempt/reject ledger **NOT_RECORDED**; rank/score/select ledger **NOT_RECORDED**.

Full schema: `reports/aivd_3_41_planner_ledger_spec.md`.

---

## 5. Hypotheses

H10a–H10h + H10-REJECT — see `reports/aivd_3_41_hypothesis_tree.md`.  
**Binding:** Do **not** assume H10a from Stage-9 absence alone.

---

## 6. Semantic / RNG preservation

Instrumented vs uninstrumented deterministic replay must match sequences / scores / ranks / selections / inventions / budget / final state — **STOP** on mismatch.  
Instrumentation consumes **zero** experimental budget and **no** planner RNG / order / hashing / timing-dependent ordering changes.

See: `aivd_3_41_semantic_preservation.md`, `aivd_3_41_rng_integrity.md`.

---

## 7. Tests / execution

16-item test matrix in `aivd_3_41_test_spec.md` (deterministic replay through instrumentation-off regression). **Do not require S discovery.**  
Execution gate: `aivd_3_41_execution_spec.md` — **DESIGN-ONLY STOP**; implementation requires separate authorization text (quoted there).

---

## 8. Forbidden list (binding)

- S injection / odd-stride heuristics / seeding S into `propose_atoms`
- Filter merge / live `FILTER_BEHAVIORAL_DUP` replacement / R-A/R-C/R-D merge
- Sacred / TinyLlama / plant discovery in design phase
- `grow.py` / invent_cap / novelty threshold / firewall / planner score-rank-select math changes in this phase
- Rewriting Stage-7/8/9 historical results
- Fabricating `NOT_RECORDED` fields
- Post-hoc favorable selection of naturally successful candidates outside preregistered controls

---

## 9. STOP

Design documents only. Do not implement. Do not run Sacred.

**AIVD 3.41 DESIGN READY:**  
**IMPLEMENTATION REQUIRES SEPARATE AUTHORIZATION**
