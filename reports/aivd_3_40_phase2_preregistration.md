# AIVD 3.40 Phase-2 — Preregistration Freeze Protocol

**Document type:** Phase-2 preregistration (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 17:37 IST  
**Parent charter:** `reports/aivd_3_40_phase2_charter.md`  
**Start tip:** `a2ab0cc`  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`  
**Anti-pattern callout:** Commit `7a3457e` (Stage-2 R1b invent-basis trim **after smoke / before Sacred**). Do not repeat.

---

## 1. Purpose

Freeze schemas, locks, Mode A/B claim firewall, R1b decision, seeds, budget, and interpretation rules **before** any Phase-2 EXECUTION. No fields may be defined after inspecting Sacred outcomes.

---

## 2. Authority priors (immutable cite)

| Prior | Binding |
|-------|---------|
| Phase-1 COMPLETE `a2ab0cc` / exec `26ec383` | H1×7 (R1×S); H2 observational×7 (R1b×S); H3 unresolved; U F7/I7/V7; H5 weakened; H6 weakened not eliminated |
| Stage-3 `146915b` | Localize bottleneck; not make S pass |
| Stage-2 `dcae889` | Immutable Sacred aggregates |
| R1b caveat `7a3457e` | Sacred R1b not pure Commit-B prereg |
| Phase-1 charter `57c88f9` | Observational-first discipline |

---

## 3. R1b decision (frozen)

**Enum:** `NEW_PREREGISTERED_CONDITION` — choice **(b)**

| Allowed Phase-2 condition IDs | Notes |
|-------------------------------|-------|
| `P2-R1-INSTR` | Mode A; frozen R1 + observational instrumentation |
| `P2-R1-MODEB-ODD` | Mode B; controlled availability of already-observed odd-stride atom; **not** autonomous invent |
| `P2-R1b-SACRED-AS-EXECUTED` | Optional Mode A continuity; exact post-`7a3457e` Sacred R1b; labeled historical-replication; **not** Commit-B identity |

**Forbidden:** Presenting any Phase-2 cell as identical to Commit-B preregistered `BH-R1b` / “preregistered-unchanged R1b”.

---

## 4. Frozen locks (no change without revision §8)

| Lock | Value |
|------|-------|
| Episode budget | **BH48** (48) |
| `REDISCOVERY_FLOOR` | unchanged from Stage-2 BH-R1 baseline |
| `invent_cap` | unchanged |
| `propose_atoms` 8-set | IMMUTABLE |
| Firewall / verification / GenerationRecord **semantics** | IMMUTABLE (recorder additive only) |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Model | TinyLlama-1.1B-Chat-v1.0 (same Stage-2 pin / env gate discipline) |
| Plants (when EXECUTION authorized) | **Fresh Phase-2 plant IDs** (not Stage-2 `AIVD340-S2-*` for new Sacred claims); hashes recorded at EXECUTION freeze |
| Positive control | Every live matrix includes `P2-R1-INSTR` × U |
| Mode B claim | `autonomous_discovery_credit=false` always |

**No budget raise.** Phase-2 question is H2 vs H3.

---

## 5. Schemas frozen before any future exec

All schemas are fully specified in `reports/aivd_3_40_phase2_instrumentation_spec.md`. Summary freeze list:

### 5.1 Candidate-pool schema

Per generation decision snapshot:

- `pool_snapshot_id`, `generation_id`, `episode_id`, `condition_id`, `mode` (`A`|`B`), `target_role`, `seed`
- `candidates[]`: each `{candidate_id, body_key, origin, parent_id, representation_id, growth_or_composition_op, score, score_components, rank, in_pool=true}`
- `pool_size`, `snapshot_phase` = `pre_selection` (mandatory timing)

### 5.2 Ranking schema

- `ranking_ordered_body_keys`: list high→low  
- `rank_method_id`: frozen string naming the **unchanged** baseline ranker  
- `ties[]`: groups of body keys with equal score under frozen tie definition  
- **No** reordering for instrumentation; ranks must match live selector inputs

### 5.3 Selection schema

- `selected_candidate_id` / `selected_body_key` / `null`  
- `selection_rule_id`: frozen baseline selector name  
- `tie_break_rule_id` + `tie_break_inputs` (must match production)  
- `rejected_candidates[]` with `rejection_category` (enum below)

### 5.4 Score interpretation (frozen)

- Scores are whatever the **baseline** scorer already emits; instrumentation records them verbatim.  
- Phase-2 does **not** introduce new score features, S-specific weights, odd-stride bonuses, or plant-derived features.  
- `score_components` may mirror existing internal breakdown if already computed; otherwise record scalar `score` only — **do not invent components post-hoc after Sacred**.

### 5.5 Tie handling (frozen)

- Ties defined by exact equality of the baseline scalar score (or the baseline’s existing tie predicate — pin the predicate name at EXECUTION freeze).  
- Tie-break must be the **existing** production tie-break; instrumentation logs which candidate won and why.  
- Forbidden: deterministic “prefer odd / prefer S-direction” tie-breaks.

### 5.6 Rejection categories (frozen enum)

| Code | Meaning |
|------|---------|
| `NOT_IN_POOL` | Candidate never entered pool |
| `LOW_RANK` | In pool; rank below selection cutoff |
| `TIE_LOST` | Tied on score; lost tie-break |
| `FILTERED_PRE_RANK` | Removed by pre-rank filter (record filter id) |
| `NOT_SELECTED_OTHER` | In pool / eligible but selector chose another (non-tie) |
| `SELECTED_VERIFY_REJECT` | Selected; verify rejected |
| `SELECTED_VERIFY_SKIP` | Selected; verify skipped |
| `BUDGET_EXHAUSTED` | Leftover prevented further action (secondary; H5 already weakened) |
| `MODE_B_NONCREDIT` | Mode B provenance excluded from invent/independence credit |
| `UNKNOWN_INCONCLUSIVE` | Recorder integrity failure → outcome 6 |

### 5.7 Stopping rules (frozen)

1. Env gate FAIL → do not Sacred.  
2. Instrumented `P2-R1-INSTR` × U fails positive-control class (F/I/V collapse vs Stage-2 expectation) → **STOP**; do not interpret S.  
3. Recorder changes selection/scores/ties/propose_atoms/verify/firewall semantics → **STOP**.  
4. Mode B injects finished odd CAT-self / odd-double / S-specific ranking / secrets → **STOP** (protocol violation).  
5. Smoke reveals need to trim invent basis / change ranking → **STOP** → revision (§8); do **not** patch into Sacred (`7a3457e` anti-pattern).  
6. Per-seed mechanism classification uses outcomes 1–6; matrix may stop early for reporting only if predeclared — default is full seed set.

### 5.8 Success / failure / mechanism criteria (frozen)

**Episode pipeline success** (independence bar; same spirit as Stage-2):

1. `pipeline_verified == True`  
2. `firewall_epoch >= 1`  
3. `independently_discovered == True` (fail-closed)  
4. Discovery-path origin includes `independent_rediscovery` where required  
5. `provenance_leak == False`  
6. Leakage canaries PASS  

**Mode B episodes:** may report pipeline verify for engineering continuity, but **must not** count Mode B invent/injection toward autonomous discovery success. Mechanism claims use outcomes 1–6.

**Mechanism classification:** outcomes 1–6 from charter §6; **do not** use final success alone.

---

## 6. Mode A / Mode B claim freeze

| Mode | Autonomous invent credit | Allowed scientific use |
|------|--------------------------|------------------------|
| A | Yes (for that condition’s invent path) | Baseline behavior + pool/rank/select observation |
| B | **No** | Conditional H2/H3 given availability |

Every Mode B artifact must carry:

```
mode=B
autonomous_discovery_credit=false
controlled_availability=true
availability_source=historical_observed_odd_stride_atom
```

---

## 7. Freeze protocol (before Phase-2 EXECUTION)

1. Land separate **EXECUTION** charter citing this prereg + instrumentation spec + matrix.  
2. Record `freeze_commit = git rev-parse HEAD` in a Phase-2 freeze JSON under `reports/`.  
3. Pin invent-basis / ranker / selector / tie-break identifiers and hashes.  
4. Env gate PASS.  
5. Smoke may validate wiring/recorder emission only — **no** invent-basis trim, ranking change, or S-specialization.  
6. Sacred only after freeze; fresh plant IDs; full seed set unless stop rule fires.

---

## 8. Revision policy

Allowed only via **new docs commit** that:

1. States what changed and why  
2. Explicitly invalidates prior freeze_commit for new Sacred claims  
3. Re-freezes schemas **before** any new smoke toward Sacred  
4. Preserves `7a3457e` caveat and Mode A/B separation  

Forbidden silent mid-flight patches (especially invent-basis / selection / ranking between smoke and Sacred).

---

## 9. Interpretation outcomes (re-freeze)

1 absent from pool → H2/earlier growth  
2 present but consistently low-ranked → H3 selection pressure  
3 high-ranked not selected → tie-break/selection mechanism  
4 selected but verify fails → H4  
5 present+selected but later growth diverges → H2 post-selection composition  
6 cannot establish → INCONCLUSIVE  

---

## 10. Final gate (design)

```
PHASE-2 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Phase-2 EXECUTION is authorized by this document alone.
