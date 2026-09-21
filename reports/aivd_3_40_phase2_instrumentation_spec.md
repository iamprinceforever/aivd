# AIVD 3.40 Phase-2 — Instrumentation Specification (Observational)

**Document type:** Phase-2 instrumentation spec (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 17:37 IST  
**Parent charter:** `reports/aivd_3_40_phase2_charter.md`  
**Prereg:** `reports/aivd_3_40_phase2_preregistration.md`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Primary use:** Future live observational recording for H2/H3 localization (Mode A / Mode B). **No implementation in this commit.**

---

## 1. Purpose

Answer the Phase-2 primary question with pool/rank/select evidence Phase-1 could not recover:

> Once the relevant odd-stride atom is available, does AIVD place that candidate into its growth/composition candidate pool and how does the selector treat it?

Per generation, before selection is discarded, record complete pool + scores + ranks + selection + rejection + verification + budget.

---

## 2. Hard observational constraints (binding)

Instrumentation **MUST NOT**:

| Forbidden effect | Why |
|------------------|-----|
| Change selection algorithm | Confounds H3 |
| Reorder candidates | Confounds rank |
| Change scores or tie outcomes | Confounds H3 |
| Add / remove candidates (except Mode B availability hook, predeclared) | Confounds pool |
| Prioritize odd / S | Target injection |
| Alter `propose_atoms` | Invent factor |
| Alter verification / firewall semantics | H4 / independence |
| Feed plant GT / secrets into discovery features | Leakage |

**If enabling the recorder changes semantics → STOP.** Prefer fail-closed: disable credit / abort episode rather than silently alter behavior.

Mode B controlled availability is the **only** predeclared exception that adds an atom, and it must use non-autonomous provenance (see §6).

---

## 3. Timing

| Hook | When | Required |
|------|------|----------|
| `pre_selection_pool_snapshot` | After growth/compose candidates for the decision are assembled; **before** selector returns | YES — every generation with a selection decision |
| `post_selection_record` | Immediately after selector chooses (or skips) | YES |
| `post_verify_record` | After verify accept/reject/skip/not_called | YES when verify path reached |
| `terminal_record` | Episode end | YES |

Snapshots discarded without recording → integrity failure → outcome **6 INCONCLUSIVE** for that seed’s mechanism claim.

---

## 4. Minimum schema (per generation / decision)

### 4.1 Envelope

| Field | Type | Notes |
|-------|------|-------|
| `record_schema_version` | string | e.g. `aivd340-phase2-instr-1` |
| `pool_snapshot_id` | string | unique |
| `generation_id` | string | |
| `parent_id` | string\|null | |
| `episode_id` | string | condition×target×seed |
| `condition_id` | string | `P2-R1-INSTR` \| `P2-R1-MODEB-ODD` \| `P2-R1b-SACRED-AS-EXECUTED` |
| `mode` | `A` \| `B` | |
| `autonomous_discovery_credit` | bool | false if Mode B |
| `target_role` | `S` \| `U` | |
| `seed` | int | |
| `firewall_epoch` | int | |
| `representation_id` | string | `R1` or `R1b_sacred_as_executed` |
| `event_kind` | enum | `invent`\|`grow`\|`compose`\|`rank`\|`select`\|`verify`\|`firewall`\|`terminal`\|`mode_b_availability` |
| `snapshot_phase` | enum | `pre_selection`\|`post_selection`\|`post_verify`\|`terminal` |
| `remaining_budget` | number | leftover steps consistent with Stage-2 units |
| `leakage_flag` | bool | must be false for credit |
| `record_label` | `observed` | Phase-2 live = observed (CF replay is out of scope here) |

### 4.2 Candidate pool entry (`candidates[]`)

| Field | Type | Notes |
|-------|------|-------|
| `candidate_id` | string | stable within episode |
| `body_key` | string | representation/body key |
| `identity` | string | same as body_key or canonical form |
| `origin` | string | GenerationRecord origin / `controlled_availability_mode_b` |
| `parent_id` | string\|null | |
| `representation_id` | string | |
| `growth_or_composition_op` | string\|null | e.g. CAT_SELF, COMPOSE, INVENT, null |
| `score` | number\|null | baseline scalar |
| `score_components` | object\|null | only if baseline already computes; else null |
| `rank` | int\|null | 1 = best; null if pre-rank filtered |
| `rejection_category` | enum\|null | see prereg §5.6 |
| `rejection_reason` | string\|null | short machine+human |
| `selected` | bool | |
| `verification_candidate` | bool | whether submitted to verify |
| `verification_result` | enum\|null | `accept`\|`reject`\|`skip`\|`not_called` |

### 4.3 Selection block

| Field | Type |
|-------|------|
| `selected_candidate_id` | string\|null |
| `selected_body_key` | string\|null |
| `selection_rule_id` | string |
| `tie_break_rule_id` | string |
| `tie_break_inputs` | object |
| `ranking_ordered_body_keys` | string[] |
| `ties` | array of `{score, body_keys[]}` |

### 4.4 Verification block

| Field | Type |
|-------|------|
| `verification_candidate_id` | string\|null |
| `verification_body_key` | string\|null |
| `verification_result` | enum |
| `verification_reason_code` | string\|null |

---

## 5. Pipeline question mapping (H2 vs H3)

| Question | Positive pattern | Negative pattern |
|----------|------------------|------------------|
| Fail GROW (H2)? | Odd-stride available (Mode A invent or Mode B); finished/near-finished required body **absent** from `candidates[]` / pool | Required body ∈ pool |
| Fail SELECT pressure (H3 outcome 2)? | Required body in pool; consistently low `rank` across generations/seeds | Rank competitive |
| Fail SELECT tie/mechanism (outcome 3)? | High rank / tied best; `selected_body_key` ≠ required | Selected |
| Fail VERIFY (H4 outcome 4)? | Selected required body; verify ≠ accept | Verify accept or never selected |
| Post-select growth diverge (outcome 5)? | Selected earlier; later compose/grow path diverges from required finish | Stable path |
| INCONCLUSIVE (outcome 6)? | Missing snapshots / semantic drift / recorder failure | Clean snapshots |

**Earliest bottleneck** among invent→grow→select→verify; Mode B skips invent as autonomous claim.

---

## 6. Mode B availability hook (precise; non-masquerading)

### 6.1 Allowed injection

1. Source body key must be an **already-observed** odd-stride atom from Stage-2/Phase-1 BH-R1b×S invent census (cite historical body key).  
2. Inject into language/atom store with `origin = controlled_availability_mode_b`.  
3. Emit `event_kind = mode_b_availability` record.  
4. Set `autonomous_discovery_credit = false` for the episode’s invent claims.  
5. Do **not** set `independent_rediscovery` for the injected atom.  
6. After injection, growth/compose/rank/select/verify use **identical** baseline algorithms; recorder observational only.

### 6.2 Forbidden injections

- Finished odd CAT-self body as if invented  
- Odd-double / secret structure / plant GT  
- S-specific atoms beyond the single historically observed odd-stride atom class  
- Target-specific ranking features or forced selection of S-direction bodies  
- Labeling Mode B injection as Mode A invent success  

### 6.3 U under Mode B

Matched U cells must receive **no S-favoring** injection. If Mode B U also receives a controlled atom, it must be a predeclared U-irrelevant or U-matched control atom that does not privilege S; default design: Mode B availability applies the odd-stride atom on **S cells only**, while U cells run Mode B flag with **null injection** (same recorder path) to detect instrumentation side effects — document at EXECUTION freeze.

---

## 7. Controls for instrumentation-induced behavior change

1. Compare instrumented `P2-R1-INSTR` × U aggregates to Stage-2 BH-R1×U (F/I/V). Divergence beyond predeclared tolerance → STOP.  
2. Compare invent census presence/absence on instrumented `P2-R1-INSTR` × S to Stage-2 BH-R1×S (odd-stride absent expectation).  
3. Optional `P2-R1b-SACRED-AS-EXECUTED`: compare observationally to Stage-2 R1b; **never** claim Commit-B identity.  
4. Shadow-check: if feasible at EXECUTION, dual-run with recorder off vs on for one U seed — selection decisions and scores must match (design recommendation; authorize only in EXECUTION charter).

---

## 8. Aggregation outputs (future Phase-2 report expectations)

Per cell (condition × mode × target):

- Seed-level outcome class ∈ {1..6}  
- Pool presence rate of relevant candidate  
- Rank distribution when present  
- Selection rate when high-ranked  
- Verify outcomes when selected  
- Explicit Mode A vs Mode B claim labels  
- U positive-control pass/fail  
- Statement if S remains unresolved with bottleneck = {H2|H3|H4|ambiguous}

Do **not** combine S+U success. Do **not** classify from final success alone.

---

## 9. Compatibility / additive recorder

Future EXECUTION may add an observational recorder alongside existing `GenerationRecord` emission. **Forbidden without EXECUTION charter + semantic review:** changing GenerationRecord independence credit, firewall, verification, or selection semantics.

---

## 10. Privacy / Absolute Rules

- No plant secrets, evaluator GT, ODDSTRIDE/ROL1 tokens in discovery `features_used`.  
- Evaluator-only geometry labels belong in analysis reports, never as discovery credit.  
- Mode B provenance must remain visible forever in artifacts.

---

## 11. STOP

Instrumentation **spec** only. No recorder implementation in this commit.
