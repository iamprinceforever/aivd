# AIVD 3.40 Phase-1 EXECUTION CHARTER — Observational Instrumentation + Offline Counterfactual Replay

**Document type:** Phase-1 EXECUTION CHARTER (DOCS ONLY — **NOT EXECUTED**)  
**Recorded:** 2026-09-21 17:21 IST  
**Parent Stage-3 tip:** `146915b` (`research/aivd-3.40-budget-representation-frontier`)  
**Stage-2 results commit:** `dcae889`  
**R1b caveat commit:** `7a3457e`  
**Authorization:** `CHARTER_ONLY_NOT_EXECUTED`  
**Status:** **PHASE-1 EXECUTION CHARTER READY** (limitations explicit; trajectories 28/28 present)

---

## 0. Absolute mandate (read first)

| Rule | Binding |
|------|---------|
| Phase-1 scope | **Observational instrumentation** + **offline counterfactual replay** of **EXISTING** Stage-2 trajectories only |
| This commit | Docs under `reports/` **only** — charter, matrix JSON, replay schema, optional inventory |
| Do **NOT** execute Phase 1 now | No runners, no normalization jobs, no evaluator replay runs in this commit |
| Do **NOT** run Sacred | No BH Sacred, no mock Sacred, no Stage-2 re-run |
| Do **NOT** modify discovery / runtime / test code | No edits to `aivd/`, `aivd37/`, `tests/`, scripts that change behavior |
| Do **NOT** mutate Stage-2 artifacts | `reports/aivd_3_40_stage2/**` is **read-only** historical data |
| Scientific objective | Localize earliest S bottleneck vs U — **NOT** make S pass |
| Authority | All seven Stage-3 artifacts at `146915b` (charter, hypothesis tree, experimental matrix ± JSON, instrumentation spec, counterfactual replay spec, preregistration) — **do not weaken** |

This charter **authorizes the design** of future Phase-1 tooling. It does **not** authorize running that tooling, changing discovery, or opening Phase-2 Sacred/Rx/BHexplore.

---

## 1. Scope (Phase 1 ONLY)

Phase 1 = offline analysis of immutable Stage-2 Sacred trajectories:

1. **Observational instrumentation** — normalize existing Stage-2 run JSONs into the Phase-1 schema (map known fields; mark UNKNOWN honestly).  
2. **Offline counterfactual replay** — evaluator-only “If candidate X were selected / grown at an historical decision point, what would the evaluator report?”  

**Out of scope for Phase 1 (and for this charter commit):**

- Sacred / Rx / BHexplore  
- Budget change, representation change  
- `propose_atoms` / firewall / verification / `invent_cap` / `REDISCOVERY_FLOOR` changes  
- 3.38 / 3.39 baseline mods  
- Historical Stage-2 artifact mutation  
- Regenerating discovery / re-running episodes to “fill in” missing pool/score/rank fields  

---

## 2. Data contract (trajectory groups)

### 2.1 Four trajectory groups (exact globs)

| Group ID | Condition | Role | Glob (read-only) | n |
|----------|-----------|------|------------------|---|
| `AUD-S2-BHR1-S` | BH-R1 | S | `reports/aivd_3_40_stage2/runs/BH-R1_seed{0,1,2,3,4,7,11}_S.json` | 7 |
| `AUD-S2-BHR1-U` | BH-R1 | U | `reports/aivd_3_40_stage2/runs/BH-R1_seed{0,1,2,3,4,7,11}_U.json` | 7 |
| `AUD-S2-BHR1b-S` | BH-R1b | S | `reports/aivd_3_40_stage2/runs/BH-R1b_seed{0,1,2,3,4,7,11}_S.json` | 7 |
| `AUD-S2-BHR1b-U` | BH-R1b | U | `reports/aivd_3_40_stage2/runs/BH-R1b_seed{0,1,2,3,4,7,11}_U.json` | 7 |

**Total:** 28/28 present, **0 missing**. If any path were missing → **PHASE-1 BLOCKED**. Currently none missing.

### 2.2 Companion Stage-2 aggregates (read-only)

- Directory: `reports/aivd_3_40_stage2/` — `results.json`, `results.md`, `matrix_raw.json`, `generation_graph.json`, `independence.json`, `env_gate.json`, `freeze.json`, `reproducibility.json`, `run.log`  
- Aggregates: `reports/aivd_3_40_stage2_results.md` / `.json`, `aivd_3_40_stage2_generation_graph.md`, `aivd_3_40_stage2_independence.md`, `aivd_3_40_stage2_reproducibility.md`

### 2.3 Plants (Stage-2 immutable)

| Role | Plant ID | Content hash (from `results.json`) |
|------|----------|--------------------------------------|
| S | `AIVD340-S2-S` | `01f800b6008ece723cf405d17cc364cecd62f0f85a3257b9ec63930c2249fbc5` |
| U | `AIVD340-S2-U` | `82713ca768f9dc71b7443fc89ba691955a4ec656c1d6a8384db1aa39b01ec1e1` |

### 2.4 Immutability rule

**Do not regenerate / rerun discovery / alter these files.** Missing → BLOCKED. Present → read-only normalize + evaluator-only CF.

### 2.5 R1b integrity caveat (mandatory)

Commit `7a3457e` trimmed invent basis ≤3 geometric classes **after smoke / before Sacred**. Therefore **BH-R1b measured results are observational, not pure Commit-B prereg**. Preserve this caveat in every Phase-1 report. Never claim R1b Sacred was preregistered-unchanged.

### 2.6 U positive control (mandatory gate)

**BH-R1 × U** = F7 / I7 / V7 (firewall 7, independent-strict 7, verified 7) under Stage-2. Phase-1 instrumentation **must reconstruct this path first**. If it cannot → future execution **STOP** (do not interpret S).

---

## 3. Field coverage matrix

Sources: Stage-2 run envelope + `generation_records` + `methods_log` + `language.programs` (keyword scan of 28 runs: `pool=0`, `score=0`, `selected=0` files; `rank`/`reject` appear only as incidental `atom_rank` / `rejected_*` text — **not** full ranking tables or selection decision records).

### 3.1 Required Phase-1 fields → coverage class

| Required Phase-1 field (Stage-3 instrumentation) | Coverage | Source / note |
|--------------------------------------------------|----------|---------------|
| `generation_id` | **OBSERVED** | `generation_records[].generation_id` |
| `parent_id` / `parent_generation_id` | **OBSERVED** | `generation_records[].parent_generation_id` |
| `episode_id` (condition×target×seed) | **DERIVABLE_WITHOUT_RERUN** | from envelope `condition_id`+`role`+`seed` + filename |
| `condition_id` | **OBSERVED** | envelope |
| `target_role` | **OBSERVED** | envelope `role` |
| `seed` | **OBSERVED** | envelope |
| `firewall_epoch` | **OBSERVED** | envelope + per-record |
| `candidate_origin` | **OBSERVED** | `generation_records[].candidate_origin` |
| `representation_id` | **OBSERVED** | envelope `representation` (`R1` / `R1b`) |
| `features_used` | **UNKNOWN** | absent in all 28 runs (`features_used` keyword = 0) |
| `invented_atoms` | **DERIVABLE_WITHOUT_RERUN** | `kind/action=atom/invent` records + `methods_log` invent ops / `atom_materialize` |
| `composed_candidates` (grown/composed bodies) | **DERIVABLE_WITHOUT_RERUN** (partial) | bodies that **finished** into `generation_records` / `language.programs`; **not** full ephemeral compose pools |
| `candidate_scores` | **UNKNOWN** | keyword `score=0` across 28 files |
| `ranking` (ordered body list) | **UNKNOWN** | no ranking tables; incidental `atom_rank` ≠ ordered pool rank |
| `selected_candidate` (explicit decision record) | **UNKNOWN** | keyword `selected=0`; no explicit select decision objects |
| `verification_candidate` | **DERIVABLE_WITHOUT_RERUN** (weak) | infer from records with non-empty `verification_state` / terminal verify path — **not** a dedicated select→verify handoff log |
| `verification_result` | **DERIVABLE_WITHOUT_RERUN** (partial) | `verification_state`, envelope `pipeline_verified` / `terminal_state` / `failure_class` / `stop_reason` |
| `remaining_budget` / leftover | **OBSERVED** | `budget_before`, `leftover`, `leftover_after`, `leftover_at_firewall_decision` |
| `rejection_or_skip_reason` (full enum beyond envelope) | **UNKNOWN** (beyond partial) | have `stop_reason` / `failure_class` / `notes`; **not** systematic reject/skip enums per candidate |
| `event_kind` (`invent`\|`grow`\|`compose`\|`firewall`\|…) | **OBSERVED** | `generation_records[].kind` / `.action` |
| `record_label` | **DERIVABLE_WITHOUT_RERUN** | always `observed` for Stage-2 imports; CF rows added only by future replay |
| `terminal_state` | **OBSERVED** | envelope |
| `leakage_flag` / `provenance_leak` | **OBSERVED** | envelope |
| `body_key` / `candidate_id` / `candidate` | **OBSERVED** | generation_records |
| `semantic_class` / `proposal_origin` | **OBSERVED** | generation_records |
| `methods_log` invent ops lists | **OBSERVED** | methods_log |
| `strict_independence` | **OBSERVED** | envelope + independence_verdicts |
| `language.programs` | **OBSERVED** | envelope language |

### 3.2 Maximum valid claims given UNKNOWN fields

**Allowed (given OBSERVED / DERIVABLE):**

- Census of **produced** bodies that appear in `generation_records` / `language.programs` (invent / grow / compose / rediscover / firewall events).  
- Weaker production claim: “finished body **present in generation_records** vs **never appeared**.”  
- Timeline of `firewall_epoch`, leftover at firewall, terminal/verify outcomes.  
- Invent-ops / materialize evidence from `methods_log` (direction atoms attempted vs recorded).  
- Earliest-divergence among stages that do **not** require pool/score/rank/selected snapshots.  
- Evaluator-only CF: “if body B (known from history or legally grown offline) were submitted to evaluator, what result?” — labeled **COUNTERFACTUAL**, never as Sacred VERIFIED.

**Not allowed without new live instrumentation (FORBIDDEN silent fill):**

- Claims that a finished body was “in the live candidate pool with score X and rank Y but lost selection” (**H3 strong form**) — requires UNKNOWN pool/score/rank/selected.  
- Claims reconstructing full rejection-reason enums per skipped candidate.  
- Reconstructing `features_used` maps by regenerating discovery.  
- Treating incidental `atom_rank` / `rejected_classes` strings as full ranking tables.

**H3 status:** **may remain INCONCLUSIVE** unless weaker evidence from `methods_log` + `generation_records` supports only soft claims (e.g., finished body never appeared in records ⇒ bottleneck ≤ H2, not H3). No silent fill of pool/rank/selected.

---

## 4. Instrumentation (future impl — specify only)

**Observational only.** Future Phase-1 code may:

1. Read Stage-2 JSON **read-only**.  
2. Normalize each episode into Phase-1 schema rows with `record_label=observed`.  
3. Capture before/after firewall and generation boundaries from existing `firewall_epoch` / `kind`/`action` / methods_log `provenance_firewall`.  
4. Emit coverage tags per field: `OBSERVED` | `DERIVABLE_WITHOUT_RERUN` | `UNKNOWN`.  

**Must not:** add new candidate-generation behavior; call invent/grow/select live discovery loops to backfill UNKNOWN; edit GenerationRecord semantics; write into Stage-2 paths.

---

## 5. Offline counterfactual replay (future impl — specify only)

**Evaluator-only.** Future Phase-1 replay may ask:

> If candidate X were selected (or grown with a **generic** legal op) at historical decision point T, what would the evaluator report?

**MUST NOT:**

- Modify discovery / model state  
- Feed CF results back into discovery, caches, or Sacred tables  
- Generate new atoms/candidates via the live invent path as “fill-in”  
- Change the historical trajectory artifacts  

**MUST:**

- Label every output row `OBSERVED` vs `COUNTERFACTUAL`  
- Treat counterfactual ≠ observed discovery  
- Never present CF verify-accept as Sacred VERIFIED success  

Operators (from Stage-3 replay spec): `enumerate_produced_bodies`, `what_if_select`, `what_if_grow`, `path_prefix_check`.

---

## 6. Replay validation gate (before interpreting S)

**Positive control first:** BH-R1 × U.

1. For each BH-R1 U seed, reconstruct the historical selected/produced path from OBSERVED records.  
2. Replay must reproduce recorded evaluator / terminal outcomes **where deterministic** (`terminal_state`, `pipeline_verified`, independence/firewall bits consistent with Stage-2 table F7/I7/V7).  
3. If exact deterministic reproduction is impossible: document **why** + **maximum valid claim**; **never** silently swap evaluator config.  
4. **If U cannot be reconstructed → STOP** — do not interpret S; investigate harness / H6.

---

## 7. Earliest-divergence + S question ladder

### 7.1 Per S/U seed pair

For each seed ∈ `{0,1,2,3,4,7,11}` under BH-R1 (primary) and BH-R1b (observational):

- Compare matched S vs U trajectories.  
- Emit `earliest_divergence` ∈ `{H1, H2, H3, H4, H5, H6, INCONCLUSIVE}`.  
- Prefer earliest stage with positive evidence; if evidence for a stage is UNKNOWN → that stage may force **INCONCLUSIVE** rather than a guessed H.

### 7.2 S questions 1–8 (answer in order; UNKNOWN if artifact lacks evidence; no inference of missing stages)

| # | Question | Evidence dependency |
|---|----------|---------------------|
| Q1 | Did invent produce atoms from which an S-direction finished program is reachable? | invent records / methods_log |
| Q2 | Did grow/compose produce a finished S-direction body in OBSERVED records? | generation_records / language.programs |
| Q3 | Does any OBSERVED finished S-direction body appear in the produced-body census? | same as Q2 (pool snapshot UNKNOWN — do not claim live pool) |
| Q4 | Was that body explicitly ranked above competitors? | **UNKNOWN** unless only weak incidental `atom_rank` — default UNKNOWN |
| Q5 | Was that body explicitly selected for verification? | **UNKNOWN** (no selected records) — may answer only “verification_state path involves body B” if OBSERVED |
| Q6 | Did verification accept an S-direction body? | verification_state / terminal / pipeline_verified |
| Q7 | At failure, was leftover / remaining budget exhausted in a way that truncates a correct path? | leftover fields; H5 only with leftover evidence |
| Q8 | Do S and U share pipeline invariants under the same mode (H6 gate)? | mode flags, floor/cap, firewall arming, GenerationRecord origin rules vs U reconstruct |

**Rule:** If a question’s required artifact fields are UNKNOWN → answer **UNKNOWN**. Do **not** infer missing stages from silence.

---

## 8. Exit gates A–G (must prove in writing before Phase-1 *execution* is considered complete)

| Gate | Requirement | Charter posture now |
|------|-------------|---------------------|
| **A** | Trajectories sufficient (with UNKNOWN limitations explicit) | **PASS design** — 28/28 present; pool/score/rank/selected UNKNOWN documented |
| **B** | Instrumentation observational | **PASS design** — normalize-only; no new candidate generation |
| **C** | Replay evaluator-only | **PASS design** — CF labeled; no discovery feedback |
| **D** | Historical immutable | **PASS design** — Stage-2 JSON read-only; no mutation |
| **E** | U BH-R1 positive-control reconstruction | **REQUIRED at future execution** — if fail → STOP |
| **F** | S earliest-divergence classifiable **OR** INCONCLUSIVE | **PASS design** — INCONCLUSIVE allowed (esp. H3) |
| **G** | No new experimental condition | **PASS design** — no Sacred/Rx/BHexplore/budget/rep changes |

---

## 9. Future touch files (identify only — **DO NOT modify now**)

Future Phase-1 **execution** (separate authorization after this charter) would likely add **new** modules and read existing loaders **read-only**:

### 9.1 Likely new modules (create later; not in this commit)

- `aivd/experiments/aivd340/phase1_normalize.py` — Stage-2 JSON → Phase-1 schema  
- `aivd/experiments/aivd340/phase1_replay.py` — evaluator-only CF operators  
- `aivd/experiments/aivd340/phase1_report.py` — divergence / Q1–Q8 aggregation  
- `scripts/run_aivd_3_40_phase1_normalize.py`  
- `scripts/run_aivd_3_40_phase1_replay.py`  
- Output under `reports/aivd_3_40_phase1/` (future; not created now)

### 9.2 Existing paths (read-only use in future execution)

| Path | Role |
|------|------|
| `reports/aivd_3_40_stage2/runs/*.json` | Immutable trajectories |
| `aivd/science/generation_record.py` | Record schema reference |
| `aivd/science/designer.py` | Understanding historical decision boundaries (read-only) |
| `aivd/science/grow.py` | `REDISCOVERY_FLOOR` constant reference (do not change) |
| `aivd/science/atom_synth.py` / `propose_atoms` | Frozen 8-set reference (do not change) |
| `aivd/science/methods.py` | `INVENT_CAP` reference (do not change) |
| `aivd/science/representation.py` | R1/R1b mode reference (do not change) |
| `aivd/experiments/aivd340/condition.py` | Condition IDs / plant ID constants |
| `aivd/experiments/aivd340/runner.py` | Episode envelope shapes |
| `scripts/run_aivd_3_40_stage2_sacred.py` | Historical Sacred runner (do not re-run for Phase 1 fill) |
| `aivd37/unknowns/llama_340_stage2.py` | `LlamaS2STarget` / `LlamaS2UTarget` / `target_hash` (evaluator-only CF) |
| `aivd37/unknowns/pipeline.py` / `terminal.py` | Terminal/verify semantics reference |

**Emphasize:** read-only of Stage-2 JSON; **no edits** to `propose_atoms`, firewall, verification, invent_cap, REDISCOVERY_FLOOR, or GenerationRecord credit semantics.

---

## 10. Hard prohibitions (binding)

Phase-1 (charter and any future execution under it) **MUST NOT**:

1. Execute Phase 1 in this docs commit (charter-only).  
2. Run Sacred (any budget / representation / plant).  
3. Introduce Rx, R1c, or any new representation factor.  
4. Introduce BHexplore or any budget raise.  
5. Change budget, representation, `propose_atoms` (8-set), firewall, verification, `invent_cap`, or `REDISCOVERY_FLOOR`.  
6. Modify 3.38 / 3.39 baselines or Sacred artifacts.  
7. Mutate historical Stage-2 artifacts under `reports/aivd_3_40_stage2/`.  
8. Regenerate / rerun discovery to reconstruct UNKNOWN pool/score/rank/selected/`features_used`.  
9. Silently fill UNKNOWN fields or upgrade H3 to conclusive without pool/rank/selected evidence.  
10. Feed counterfactual outcomes back into discovery state, caches, or Sacred result tables.  
11. Present counterfactual verify-accept as observed Sacred VERIFIED.  
12. Encode S / ODDSTRIDE / odd-double / CAT-self GT / ROL1 / plant secrets into discovery features.  
13. Retune S or U independently / target-specific assists.  
14. Claim R1b Sacred was preregistered-unchanged (`7a3457e` caveat).  
15. Open Phase-2 Sacred without a further EXECUTION charter after Phase-1 localization completes or stops.  
16. Modify discovery / runtime / test code in this charter commit.

---

## 11. Authority lineage

| Artifact | Path | Tip |
|----------|------|-----|
| Stage-3 master charter | `reports/aivd_3_40_stage3_charter.md` | `146915b` |
| Hypothesis tree | `reports/aivd_3_40_stage3_hypothesis_tree.md` | `146915b` |
| Experimental matrix | `reports/aivd_3_40_stage3_experimental_matrix.md` (+ `.json`) | `146915b` |
| Instrumentation spec | `reports/aivd_3_40_stage3_instrumentation_spec.md` | `146915b` |
| Counterfactual replay spec | `reports/aivd_3_40_stage3_counterfactual_replay_spec.md` | `146915b` |
| Preregistration | `reports/aivd_3_40_stage3_preregistration.md` | `146915b` |
| Stage-2 results | `reports/aivd_3_40_stage2_results.*` + `reports/aivd_3_40_stage2/` | lineage incl. `dcae889` |

Companions in this commit:

- `reports/aivd_3_40_phase1_execution_matrix.json`  
- `reports/aivd_3_40_phase1_replay_schema.md`  
- `reports/aivd_3_40_phase1_artifact_inventory.md`

---

## 12. FINAL GATE STATEMENT

Trajectories **28/28 present**. Field coverage is honest: rich `generation_records` / `methods_log` support invent/grow/terminal/budget questions; **pool / score / rank / selected / features_used remain UNKNOWN**, so **H3 may stay INCONCLUSIVE** and must not be silently filled.

**PHASE-1 EXECUTION CHARTER READY**

(Not executed. No Sacred. No discovery/runtime/test code changes. Docs under `reports/` only.)
