# AIVD 3.40 Stage-4 — Instrumentation Specification (Observational Growth Audit)

**Document type:** Stage-4 instrumentation spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 18:45 IST  
**Parent charter:** `reports/aivd_3_40_stage4_charter.md`  
**Prereg:** `reports/aivd_3_40_stage4_preregistration.md`  
**Hypothesis tree:** `reports/aivd_3_40_stage4_hypothesis_tree.md`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Primary use:** Future observational recording of the growth path  
`controlled atom → admissibility → compatibility → operators → compositions → structural filters → pool → score/rank → select`  
**No implementation in this commit.** First experiment must remain observational (no growth-algorithm change).

---

## 1. Purpose

Answer the Stage-4 primary question with **per-transition evidence** Phase-2 Outcome 1 could not supply:

> WHY does the controlled odd-stride atom fail to enter the growth/composition candidate pool?

Phase-2 established absence of `ODD_CAT_SELF_BODY_KEY` from growth pools under Mode B. Stage-4 must locate the **earliest stop** among H2a–H2f (or reopen post-pool H3-class if pool membership appears).

---

## 2. Hard observational constraints (binding)

Instrumentation **MUST NOT**:

| Forbidden effect | Why |
|------------------|-----|
| Change growth algorithm / operators | Confounds H2b |
| Add odd/S/target-specific operators | Target assistance |
| Change ordering, scores, ties, filtering, compatibility | Confounds H2c/H2d |
| Change selection / verification / firewall | Confounds post-pool / H4 |
| Alter `propose_atoms` / invent_cap / REDISCOVERY_FLOOR / BH48 | Factor contamination |
| Insert intermediate atoms into autonomous discovery | Breaks H2e discipline |
| Feed plant GT / secrets into discovery features | Leakage |
| Merge CONTROLLED into AUTONOMOUS metrics | Claim firewall |

**If enabling the recorder changes semantics → STOP.**

Allowed predeclared CONTROLLED hooks (evaluator-only): CONTROL A/B/C availability as frozen in matrix/prereg — same Mode B discipline as Phase-2 (`origin=controlled_availability_mode_b`, `autonomous_discovery_credit=false`).

---

## 3. Code anchors (read-only map at tip `f4d7a2b`)

| Stage | Module / symbol |
|-------|-----------------|
| Controlled inject | `aivd.experiments.aivd340.phase2_mode_b.inject_odd_stride_controlled`, `build_odd_stride_atom` |
| Language store | `aivd.science.language.ExperimentLanguage.add_atom`, `promote`, `compose`, `add_program` |
| Growth propose | `aivd.science.grow.propose_growth`, `cat_self_body`, `tokens_shorter`, `_keep` (nested) |
| Representation wrapper | `aivd.science.representation.propose_growth_candidates` |
| Compose pair | `aivd.science.grow.pick_compose_pair`, `propose_sequential` |
| Action pick | `aivd.science.grow.pick_generation_action` (`parent_rank`) |
| Designer orchestration | `aivd.science.designer.ScienceDesigner._maybe_grow`, `_maybe_next_generation`, `_register_growth` |
| Phase-2 prior hooks (extend, do not silently alter) | `aivd.experiments.aivd340.phase2_hooks` wrapping `pick_generation_action` / `propose_growth_candidates` |
| Frozen keys | `aivd.experiments.aivd340.phase2_constants.ODD_STRIDE_BODY_KEY`, `ODD_CAT_SELF_BODY_KEY` |

Future EXECUTION may add an **additive** Stage-4 recorder schema version (e.g. `aivd340-stage4-growth-audit-1`) alongside Phase-2 records. **Forbidden without EXECUTION charter:** changing growth/selection semantics when recording is enabled.

---

## 4. Timing hooks

| Hook | When | Required |
|------|------|----------|
| `controlled_atom_presence` | After CONTROL A/B/C inject or null decision | YES |
| `admissibility_check` | Before `propose_growth` considers parent | YES |
| `compatibility_check` | Per named gate for controlled parent | YES |
| `operator_applicability` | After compatibility; before/at propose | YES |
| `composition_attempt` | Each CAT_SELF / COMPOSE attempt involving controlled lineage | YES |
| `structural_filter` | Inside / parallel to `_keep` rejects | YES — emit even when Phase-2 pool snapshot would miss them |
| `pre_selection_pool_snapshot` | After `growth_cands` (+ compose marker) assembled; before `pick_generation_action` returns | YES (continuity with Phase-2) |
| `post_selection_record` | After action choose/skip | YES |
| `offline_ir_path` | Offline intermediate-representation test only | YES for `OFFLINE_IR` cells |
| `terminal_record` | Episode end | YES |

Missing required online hooks → integrity failure → mechanism claim **INCONCLUSIVE** for that seed.

---

## 5. Minimum schema

### 5.1 Envelope

| Field | Type | Notes |
|-------|------|-------|
| `record_schema_version` | string | e.g. `aivd340-stage4-growth-audit-1` |
| `audit_id` | string | unique |
| `episode_id` | string | condition × control × target × seed |
| `condition_id` | string | Stage-4 condition ids from matrix |
| `control_id` | `A` \| `B` \| `C` | |
| `mode_namespace` | `AUTONOMOUS` \| `CONTROLLED_INPUT` | CONTROLLED for A/B/C inject cells as applicable |
| `autonomous_discovery_credit` | bool | **false** for controlled cells |
| `target_role` | `S` \| `U` | |
| `seed` | int | |
| `audit_mode` | `OBS_ONLINE` \| `OFFLINE_IR` | |
| `representation_id` | string | primary `R1` |
| `firewall_epoch` | int | |
| `remaining_budget` | number | leftover steps |
| `snapshot_phase` | enum | see hooks |
| `event_kind` | enum | `controlled_presence`\|`admissibility`\|`compatibility`\|`operator`\|`compose_attempt`\|`structural_filter`\|`pool`\|`rank`\|`select`\|`offline_ir`\|`terminal`\|`unknown` |
| `claim_label` | `OBSERVED` \| `CONTROLLED` \| `OFFLINE_IR` \| `UNKNOWN` | |
| `leakage_flag` | bool | must be false for credit |

### 5.2 Controlled atom trail (per charter mandate)

| Field | Type | Notes |
|-------|------|-------|
| `atom_id` | string\|null | |
| `origin` | string | `CONTROLLED_INPUT` / `controlled_availability_mode_b` / null for CONTROL C |
| `generation` | int\|string\|null | growth_count / generation_id |
| `parent` | string\|list\|null | |
| `body_key` | string | e.g. `MAPT(SLICE:1,2(TOK))` |
| `representation` | string | |
| `admissible` | bool\|`UNKNOWN` | |
| `admissibility_reason` | string\|null | |
| `compatibility_tests` | array of `{gate_id, passed, detail}` | gates below |
| `applicable_operators` | string[] | e.g. `CAT_SELF`, `COMPOSE`, `NONE` |
| `compositions` | array of attempt objects (§5.3) | |
| `structural_filter_results` | array | |
| `in_candidate_pool` | bool\|`UNKNOWN` | |
| `score` | number\|null\|`UNKNOWN` | |
| `rank` | int\|null\|`UNKNOWN` | |
| `selected` | bool\|`UNKNOWN` | |
| `stop_stage` | enum\|null | earliest failed stage id |
| `h2_leaf_hint` | `H2a`…`H2f`\|`POST_POOL`\|`INCONCLUSIVE`\|null | analysis-time; not discovery feature |

**UNKNOWN mandatory** when historical Phase-2 artifacts lack the field — do not fabricate.

### 5.3 Composition attempt object

| Field | Type |
|-------|------|
| `op` | `CAT_SELF` \| `COMPOSE` \| other frozen name |
| `parent_body_keys` | string[] |
| `result_body_key` | string\|null |
| `status` | `attempted` \| `constructed` \| `rejected` \| `UNKNOWN` |
| `rejection_reason` | string\|null |
| `rejection_category` | enum (§5.5) |

### 5.4 Compatibility gates (frozen names)

| `gate_id` | Meaning (maps to code) |
|-----------|------------------------|
| `PROMOTED_STATE` | `language.state_of(name)==PROMOTED` |
| `LEFTOVER_GE_3` | leftover ≥ 3 at growth entry |
| `TOKENS_SHORTER` | `tokens_shorter(identity, apply_micro(identity, body))` |
| `CAT_SELF_SHAPE` | `cat_self_body(body) is not None` (MAPT unary) |
| `SEMANTIC_CLASS_ELIGIBLE` | class loop eligibility under `any_class` / char_project preference |
| `COMPOSE_DISTINCT_CLASS` | pairable under `pick_compose_pair` rules |
| `UNKNOWN_GATE` | exposed but unnamed historically |

Each gate: `{gate_id, passed: bool|UNKNOWN, detail: string|null}`.

### 5.5 Rejection / filter categories (Stage-4 enum; additive to Phase-2)

| Code | Meaning | Typical leaf |
|------|---------|--------------|
| `NOT_ADMISSIBLE` | Failed promoted/budget admissibility | H2a/H2f |
| `COMPAT_FAIL` | Named compatibility gate failed | H2a |
| `NO_APPLICABLE_OPERATOR` | Operator census empty for parent | H2b |
| `NOT_GENERATED` | No construction attempt observed | H2b/H2d/H2e/H2f |
| `FILTER_KNOWN_KEY` | `_keep` known_keys | H2c |
| `FILTER_VALIDATE_MICRO` | `validate_micro` reject | H2c |
| `FILTER_IDENTITY_NOOP` | got == identity / empty | H2c |
| `FILTER_BEHAVIORAL_DUP` | got in behaviors.values() | H2c |
| `FILTER_OTHER` | other pre-pool drop | H2c |
| `ABSENT_FROM_POOL` | not in growth_cands | Outcome-1 continuity |
| `IN_POOL_LOW_RANK` | present; low rank | POST_POOL |
| `IN_POOL_NOT_SELECTED` | present; not selected | POST_POOL |
| `BUDGET_GATE` | leftover/safety skipped growth | H2f |
| `OFFLINE_NO_PATH` | offline IR: no path | H2b/H2e |
| `OFFLINE_PATH_EXISTS` | offline IR: path exists | rules out pure H2b |
| `MODE_B_NONCREDIT` | controlled provenance | claim firewall |
| `UNKNOWN_INCONCLUSIVE` | recorder integrity | INCONCLUSIVE |

### 5.6 Pool / rank / select block (Phase-2 continuity)

Retain Phase-2 fields where applicable:

- `candidates[]` with `candidate_id`, `body_key`, `origin`, `parent_id`, `growth_or_composition_op`, `score`, `rank`, `selected`, …
- `ranking_ordered_body_keys`, `ties`, `selection_rule_id`, `tie_break_rule_id`
- Relevant-body detector continuity: `ODD_CAT_SELF_BODY_KEY` / CAT+SLICE:1,2 heuristic from `phase2_analyze._is_relevant_growth_cand` — **analysis only**, not a discovery feature

---

## 6. Offline intermediate-representation test schema

| Field | Type | Notes |
|-------|------|-------|
| `start_body_key` | string | controlled odd-stride |
| `target_body_key` | string | `ODD_CAT_SELF_BODY_KEY` |
| `operators_allowed` | string[] | existing only (`cat_self_body`, compose, …) |
| `path_found` | bool\|`UNKNOWN` | |
| `path_steps` | array of `{op, input_keys, output_key}` | empty if none |
| `single_step_cat_self` | bool\|`UNKNOWN` | whether `cat_self_body(start)` equals target |
| `inserted_into_autonomous` | bool | **must be false** |
| `claim_label` | `OFFLINE_IR` | |

Interpretation binding: charter §5 / hypothesis tree H2e/H2b.

---

## 7. Pipeline → leaf mapping

| Earliest observed stop | Prefer |
|------------------------|--------|
| Compatibility gate fail | H2a |
| No applicable operator / offline no path | H2b |
| Constructed then structural filter | H2c |
| Compatible + offline path; online never attempts (utility/schedule) | H2d |
| Offline needs intermediate; online never builds it | H2e |
| Budget/safety gate only | H2f |
| `in_candidate_pool=true` | POST_POOL (revise H2 scope) |
| Cannot distinguish H2a vs H2b | INCONCLUSIVE (valid) |

Do **not** classify from Sacred success alone. Do **not** require positive S.

---

## 8. Controls for instrumentation-induced behavior change

1. CONTROL A (U known-good): growth accept/compose path must remain class-consistent with Phase-2 Mode A × U F/I/V expectations when audit mode is observational on U. Collapse → **STOP**.  
2. CONTROL C (null): detect recorder side effects.  
3. Shadow recommendation (EXECUTION only): recorder off vs on for one U seed — decisions/scores must match.  
4. Never present CONTROLLED pool presence as AUTONOMOUS invent.

---

## 9. Aggregation outputs (future Stage-4 report expectations)

Per control × target × audit_mode:

- Seed-level earliest `stop_stage` + `h2_leaf_hint`
- Rates: admissible, compat pass, operator applicable, constructed, filtered, in_pool, selected
- Offline IR: path_found rate; single_step rate
- Explicit statement if H2a/H2b indistinguishable
- Explicit statement if pool membership reopens H3-class
- Separate AUTONOMOUS vs CONTROLLED tables — **never merge**

---

## 10. Privacy / Absolute Rules

- No plant secrets, evaluator GT, ODDSTRIDE/ROL1 tokens in discovery `features_used`
- Evaluator-only geometry labels stay in analysis / OFFLINE_IR reports
- CONTROLLED provenance must remain visible forever

---

## 11. STOP

Instrumentation **spec** only. No recorder implementation in this commit.
