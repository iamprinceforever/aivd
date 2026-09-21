# AIVD 3.40 PREFLIGHT AUDIT ONLY — Budget × Representation Frontier

**Status:** PREFLIGHT / Step-0 AUDIT. **STOP BEFORE IMPLEMENTATION.**  
**Date (Asia/Kolkata):** 2026-09-21 ~10:09 IST  
**Frozen tree:** `/workspace/aivd-3.38.0-frozen`  
**Parent tip (Sacred 3.39 completion):** `9e1ad91f6a8d0dffa215dad033e7fc2445d265e6`  
**Research branch:** `research/aivd-3.40-budget-representation-frontier` (created from `9e1ad91`; docs-only tip)  
**Remote target:** `iamprinceforever/aivd.git` (remote name `aivd`)  
**Package at tip:** `3.39.0` (no 3.40 algorithm package yet)

**This deliverable does NOT implement** experiment matrix, discovery algorithm changes, `propose_atoms` changes, budget/floor retunes, force-firewall, or odd-double/rotate encoding into proposal targets.

---

## Step-0 checklist (required fields)

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Audit Sacred 3.39 stop conditions; map architecture symbols; separate evidence for budget vs representation limits; charter (design-only) a preregistered B×R factorial — without implementing it. |
| **HYPOTHESIS (preflight)** | Sacred 3.39 stop is jointly consistent with (a) leftover / `REDISCOVERY_FLOOR` budget wall pre-firewall and (b) a representation gap (grown even CAT-self vs odd-double / rotate plants). Neither factor alone is isolated by Sacred evidence. |
| **METHOD** | Verify immutable SHAs; `git log`/`status`/blob identity; inspect paths+symbols; reconstruct stop from `reports/aivd_3_39_llama/*` + `reports/aivd339_budget_frontier.md`; answer Y/N/partial with citations only; branch + write this report; no algorithm commits. |
| **RESULT** | Identifiers verified; sacred 3.38/3.39 artifacts unchanged; stop reconstructed; budget **YES**, representation **YES** (for these plants); invent_cap **not** binding; independence post-firewall **untested** on Sacred; factorial design preview only (**NOT EXECUTED**). |
| **ARTIFACTS** | `reports/aivd_3_40_preflight.md`, `reports/aivd_3_40_preflight.json` |
| **DECISION** | **STOP BEFORE IMPLEMENTATION.** Do not start 3.40 experiment matrix until parent re-charters execution. |

---

## 1. Identifier / immutability verify

| Identifier | Role | Observed |
|------------|------|----------|
| `9e1ad91f6a8d0dffa215dad033e7fc2445d265e6` | Sacred 3.39 completion HEAD | **MATCH** — was tip of `research/aivd-3.39-independent-generations`; branch base for 3.40 |
| `34bc665233a32a8a6f3b1f760fd65e99a37c232b` | 3.38 frozen implementation | Present; message *independent rediscovery + open-ended language growth freeze* |
| `6547502c4895ac0ab879359a14350cb077b28676` | 3.38 freeze pin | Present |
| `358ea693abdd286e3451b973877c36b7077612a5` | 3.38 sacred first_run commit | Present; blob `reports/aivd_3_38_llama/first_run.json` identical at HEAD (`ffaee90d…`) |
| `f86ebdf19403554be30e3545ee3c402dec04bb04` | 3.39 implementation freeze (Sacred runner pin) | Recorded in `freeze.json` / REPORT |
| `b07b58920b42140ea1d2cecb137b29cdad7e1c8f` | 3.39 freeze pin | Recorded in `env_gate.json` / `freeze.json` |

### Sacred artifacts unchanged (working tree clean at audit start)

| Artifact | Status |
|----------|--------|
| `reports/aivd_3_38_llama/{first_run.json,REPORT.md,freeze.json,run.log}` | Unchanged vs `358ea69` tip blob for `first_run.json` |
| `reports/aivd_3_39_llama/{REPORT.md,first_run.json,freeze.json,env_gate.json,generation_ledgers*.json,run.log}` | Tip = `9e1ad91`; **not rewritten** this audit |
| `reports/aivd339_budget_frontier.md` | Tip = `9e1ad91`; **not rewritten** this audit |
| `aivd/science/atom_synth.py` `propose_atoms` | **0-line diff** vs `34bc665` (frozen 8-set intact) |
| `REDISCOVERY_FLOOR=5`, leftover&lt;3 invent/grow/compose, `INVENT_CAP=48`, sacred budget=32 | Unchanged; **not retuned** this audit |

**Absolute constraints honored this audit:** no odd-double/rotate into `propose_atoms`; no force firewall; no lower `REDISCOVERY_FLOOR`; no raise sacred budget; no 3.39 REPORT/first_run rewrite; no discovery algorithm commits.

---

## 2. Architecture map (paths + key symbols)

### Generation records / origins

| Concern | Path | Key symbols |
|---------|------|-------------|
| Generation schema | `aivd/science/generation_record.py` | `GenerationRecord`, `CandidateOrigin`, `normalize_origin`, `build_record`, `assign_discovery_origin`, `independence_verdict`, `_INDEPENDENT_CREDIT` |
| Origins (discovery-path) | same | `independent_rediscovery`, `model_generated`, `invented_atom`, `language_growth`, `compose_sequential`, `evaluator_derived` / `fixture_derived` / `human_supplied` (non-credit) |

### Firewall / leftover / language growth

| Concern | Path | Key symbols |
|---------|------|-------------|
| Provenance firewall | `aivd/science/language.py` | `ExperimentLanguage.firewall`, `firewall_epoch`, `firewalled`, `hidden_ids`, `general_knowledge`, `emit_generation_record`, `note_generation` |
| Firewall gate | `aivd/science/designer.py` | `ScienceDesigner._maybe_firewall` — skip if `leftover < REDISCOVERY_FLOOR`; emit `REDISCOVERY_BUDGET_FAILURE` |
| Leftover floors | `aivd/science/designer.py`, `aivd/science/grow.py`, `aivd/science/lifecycle.py` | invent/grow/compose skip if leftover&lt;3; `REDISCOVERY_FLOOR=5`; `RECURSIVE_BUDGET_FAILURE` |
| Open-ended growth | `aivd/science/grow.py` | `propose_growth`, `pick_generation_action`, `pick_compose_pair`, `cat_self_body`, `MAX_RUNTIME_GENERATIONS=8`, `REDISCOVERY_FLOOR=5` |
| Failure classes | `aivd/science/failures.py` | `REDISCOVERY_BUDGET_FAILURE`, `RECURSIVE_BUDGET_FAILURE`, `ATOM_INVENTION_SKIPPED_BY_PLANNING`, … |

### propose_atoms / discovery / budget

| Concern | Path | Key symbols |
|---------|------|-------------|
| Frozen atom proposals | `aivd/science/atom_synth.py` | `propose_atoms` (deterministic **8** micros), `AtomSynthesizer.plan` |
| Invent occupancy cap | `aivd/science/methods.py` | `INVENT_CAP = 48` |
| Designer orchestration | `aivd/science/designer.py` | `_maybe_invent_atom`, `_maybe_grow`, `_maybe_compose`, `_maybe_firewall`, `_emit_gen_record`, `full_3_39` / `allow_gen_record` |
| Science / discovery controllers | `aivd/science/controller.py`, `aivd/discovery/discovery_controller.py`, `aivd/invention/controller.py` | mode recognition; invention bandit/archive under `aivd/invention/` |
| Budget accounting | `aivd/invention/budget.py`, episode `remaining_steps` / `interaction_used` | Sacred episodes use full **32** probes |

### Evaluator isolation / fresh plants

| Concern | Path | Key symbols |
|---------|------|-------------|
| Sacred 3.39 plants (evaluator-only) | `aivd37/unknowns/llama_339.py` | `fire_odd_double`, `fire_rotate_left`, `LlamaOddDoubleTarget` (`AIVD339-LLAMA-ODDDOUBLE`), `LlamaRotateTarget` (`AIVD339-LLAMA-ROTATE`), `evaluator_verify`, `existing_space_oracle` |
| Sacred runner | `scripts/run_aivd_3_39_llama.py` | imports `llama_339` for evaluator wiring only |
| Isolation | Discovery packages under `aivd/science/`, `aivd/discovery/`, `aivd/invention/` do **not** import `llama_339` | Leak canaries / plant tokens in `aivd/science/audit.py` (`scan_discovery_target_leakage`) |
| Mock independence plants | `aivd/science/benchmarks.py` | `GX8OddDouble`, `GX14…` (`AIVD339-GX*`) — mock/evaluator, not Sacred credit |
| Prior sacred plants | `aivd37/unknowns/llama_338.py` | doubled-even / reverse-each — **not reused** in 3.39 Sacred |

### Tests

| Suite | Path | Role |
|-------|------|------|
| 3.39 independence (mock) | `tests/test_aivd339_independent_generations.py` | records, origins, firewall epoch, leakage canary |
| 3.39 llama (env-gated) | `tests/test_aivd339_llama.py` | plant integrity when transformers+model present |
| 3.38 lang / llama | `tests/test_aivd338_lang.py`, `tests/test_aivd338_llama.py` | freeze regressions |

---

## 3. Sacred 3.39 stop reconstruction

**Sources (authoritative, immutable this audit):**

- `reports/aivd_3_39_llama/REPORT.md`
- `reports/aivd_3_39_llama/first_run.json`
- `reports/aivd_3_39_llama/freeze.json` / `env_gate.json`
- `reports/aivd_3_39_llama/generation_ledgers.json` (+ `_S` / `_U`)
- `reports/aivd_3_39_llama/run.log`
- `reports/aivd339_budget_frontier.md`

### Params

| Param | Value |
|-------|-------|
| Mode | `full_3_39` |
| Budget | **32** |
| invent_cap | **48** |
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` (7 × S + 7 × U = 14 pipeline seeds) |
| Plants | S=`AIVD339-LLAMA-ODDDOUBLE` (odd-double), U=`AIVD339-LLAMA-ROTATE` |
| Model | TinyLlama-1.1B-Chat-v1.0, greedy fp16 CPU |
| Env gate | **PASS** |
| Sacred status | **RUN** (recorded 2026-09-20 ~20:50–20:51 IST) |

### Outcomes

| Case | Pipeline verified | Secret | Direct secret | Control secret | Status |
|------|-------------------|--------|---------------|----------------|--------|
| S odd-double | **0/7** | 0/7 | 0/7 | 0/7 | `NOT_DISCOVERED` |
| U rotate | **0/7** | 0/7 | 0/7 | 0/7 | `NOT_DISCOVERED` |

Plant integrity (evaluator-side, **not** discovery credit) per budget frontier / REPORT Stage 5: `evaluator_verify` S/U **True**; `existing_space_oracle` S/U **True** (frozen operator space misses plants).

### Budget consumed / leftover / invent_cap

Typical chain (identical structure all 14 pipeline seeds; exemplified by S seed=0 `methods_log` + `generation_records`):

1. Escalate → atom invention at leftover **6 → 5 → 4**:  
   `atom_mapt_cat_tok_at_-1`, `atom_mapt_slice_0_2_tok`, `atom_mapt_at_-1` (origins `invented_atom`).
2. At leftover=**3**: **`REDISCOVERY_BUDGET_FAILURE`** — firewall skipped (`leftover=3 < REDISCOVERY_FLOOR=5`); `firewall_epoch` stays **0**; `firewalled=False`.
3. Open-ended grow at leftover=3: **`cmp_mapt_cat_slice_0_2_tok_slice_0_2_tok`** (even-stride CAT-self; origin `language_growth`) — same family that verified 3.38 S doubled-even; **not** odd-double; **not** rotate.
4. leftover→**2**: **`RECURSIVE_BUDGET_FAILURE`** + **`ATOM_INVENTION_SKIPPED_BY_PLANNING`** (leftover=2, floor=5).
5. Terminal: `stop_reason=BUDGET_EXHAUSTED`, `generation=4`, `interaction_used=32`, `failure_class=ATOM_INVENTION_SKIPPED_BY_PLANNING`, `terminal_state=UNRESOLVED_INVISIBLE`.

| Meter | Sacred measurement |
|-------|-------------------|
| Probes / budget | **32/32** used every pipeline seed |
| invent_cap | **48 not reached** (3 invented atoms + 1 grown program; occupancy ≪ 48) |
| Leftover at firewall decision | **3** (&lt; floor **5**) |
| Leftover at final invent skip | **2** |
| `firewall_epoch` | **0** all Sacred pipeline seeds |
| Generation records | **4/seed** pipeline (3×`invented_atom` + 1×`language_growth`); ledgers: 56 pipeline records/label (42 invent + 14 growth) |
| `independence_verdict` | `exists=True`, `independently_discovered=False` (origin not independent; epoch=0) |
| Provenance leak | **False** |

### Why epoch stayed 0

`_maybe_firewall` requires ≥2 promoted non-`cmp_` classes, no untried atom classes, **and** `leftover >= REDISCOVERY_FLOOR` (5). Sacred hit the promoted-class / exhaustion path with leftover already **3**, so firewall never armed. Evidence event:  
`REDISCOVERY_BUDGET_FAILURE` / `why=firewall skipped; leftover below independent rediscovery floor` / `leftover=3` / `floor=5`.

### Representations grown vs plants

| Grown (discovery) | Plant need |
|-------------------|------------|
| Even-index CAT-self `MAPT(CAT(SLICE:0,2(TOK)\|SLICE:0,2(TOK)))` | S: **odd**-index CAT-self (`t[1::2]+t[1::2]`); U: rotate-left per token |
| In `propose_atoms` 8-set: even slice `SLICE:0,2` present as atom; **finished odd-double / rotate programs absent** | By construction plants miss existing space (`existing_space_oracle=True`) |

### Termination reasons (observed)

- Dominant failure class logged: `ATOM_INVENTION_SKIPPED_BY_PLANNING`
- Preceding budget events: `REDISCOVERY_BUDGET_FAILURE`, `RECURSIVE_BUDGET_FAILURE`
- Language `stop_reason`: `BUDGET_EXHAUSTED`
- Offline Level-14 class (evaluator-side only): **`LEFTOVER_WALL_PRE_FIREWALL`**
- Stage 7+ decision in Sacred docs: **STOP**

---

## 4. Evidence-supported limit answers

### Consistent with budget limitation?

**YES** — primary binding constraint for firewall / independence path.

Evidence:

1. Every pipeline seed: `interaction_used=32` (full sacred budget).
2. Explicit `REDISCOVERY_BUDGET_FAILURE` at leftover=3 &lt; `REDISCOVERY_FLOOR=5` → no firewall epoch.
3. Post-grow leftover=2 → `RECURSIVE_BUDGET_FAILURE` + invent skip.
4. invent_cap=48 **not** binding (frontier table + occupancy).
5. Offline class name: `LEFTOVER_WALL_PRE_FIREWALL`.

### Consistent with representation limitation?

**YES** — for these plants (joint with budget; not isolated).

Evidence:

1. Grown program is even-stride CAT-self; S plant requires odd-stride CAT-self; U requires rotate-left (`llama_339.py` fire functions vs grown `body_key`).
2. `existing_space_oracle` True (plants miss frozen operator space).
3. `propose_atoms` frozen 8-set unchanged since `34bc665`; does not emit finished odd-double or rotate programs (constraint).
4. Budget frontier Stage 6 table: representation **YES — for these plants**.

### What remains experimentally unresolved

Cannot claim from Sacred 3.39 alone:

1. **That TinyLlama “can't” discover odd-double / rotate** — model triggers succeed evaluator-side; failure is pre-firewall leftover + wrong grown manifold, not demonstrated refusal once a correct prompt exists.
2. **That Level-14 / independent rediscovery is impossible** — Sacred never entered `firewall_epoch≥1`; independence success path is **untested**, not falsified (mock gate previously showed machinery can credit rediscovery under fixtures).
3. **That raising budget alone would verify these plants** — representation gap remains; even with more leftover, proposal/growth may still prefer even CAT-self unless representation policy changes (forbidden without new charter) or factorial isolates it.
4. **That representation change alone would verify under budget 32** — leftover floor may still block firewall/rediscovery chain before plant hit.
5. **Which factor is sufficient vs necessary** — Sacred conflates both; requires a **preregistered factorial** (below) to separate.
6. **Algorithm bug in 3.39 independence machinery** — not supported; gate behaved as designed when leftover&lt;floor.

---

## 5. Branch

```
research/aivd-3.40-budget-representation-frontier
base: 9e1ad91f6a8d0dffa215dad033e7fc2445d265e6
URL (after push): https://github.com/iamprinceforever/aivd/tree/research/aivd-3.40-budget-representation-frontier
```

- Created from exactly Sacred 3.39 completion SHA.
- **No algorithm / discovery / propose_atoms / floor / budget commits** in this preflight.
- Prior branch `research/aivd-3.39-independent-generations` and sacred REPORT/first_run left untouched.

---

## 6. DESIGN PREVIEW — preregistered B32×R0/R1 × BH×R0/R1 factorial

> **NOT EXECUTED. Design-only. Not an authorization to implement, retune Absolute floors, or rewrite sacred artifacts.**

### Motivation

Sacred 3.39 stopped with **both** leftover wall and representation gap active. A single-cell rerun cannot attribute credit. A small factorial separates:

- **B** — budget/leftover regime (whether firewall can open under the same Absolute floor semantics, or a *separately chartered* high-leftover cell).
- **R** — representation regime (whether proposal/growth can express odd-double / rotate-class programs without encoding plant secrets as discovery instructions).

### Sketch (cells)

| Factor | Level 0 (baseline / Sacred-like) | Level 1 (contrast) |
|--------|----------------------------------|--------------------|
| **B** (budget / leftover headroom) | **B32**: sacred budget=32, floors unchanged (`REDISCOVERY_FLOOR=5`, leftover&lt;3 skips) | **BH**: *chartered* higher leftover headroom at firewall decision (e.g. larger episode budget **or** equivalent leftover-preserving schedule) so `leftover ≥ 5` is reachable **without** lowering the floor and **without** force-firewall |
| **R** (representation) | **R0**: frozen `propose_atoms` 8-set + current growth priors (even CAT-self preferential) | **R1**: representation expansion that can *name* odd-stride CAT-self / rotate-class micros as ordinary geometric candidates — **not** plant GT strings, **not** Level-14 instructions, still leakage-canaried |

Full factorial: **B32×R0**, **B32×R1**, **BH×R0**, **BH×R1** (plus locked seeds/plants/model pin).

### Why this separates budget vs representation

| Cell | If verifies | Interpretation |
|------|-------------|----------------|
| B32×R0 (Sacred replicate) | — | Baseline; expect 0/7 as measured |
| B32×R1 | Plants verify under budget 32 | **Representation was binding**; budget alone insufficient explanation for miss |
| B32×R1 | Still 0/7 with leftover wall | Budget still blocks even with richer reps |
| BH×R0 | Plants verify with frozen reps | **Budget/leftover was binding**; even-CAT-self prior may still win unless R helps |
| BH×R0 | Firewall opens but plants still miss | Independence path exercised; representation still missing |
| BH×R1 | Strongest enablement | Joint sufficiency; still does not prove necessity of either alone without the cross cells |

Pre-register success metrics before run: pipeline verified rate, `firewall_epoch`, origins (`independent_rediscovery` vs `invented_atom`/`language_growth`), leftover at firewall decision, grown `body_key` class, invent_cap occupancy, leakage canary clean.

### Explicit non-goals of this preview

- Do **not** lower `REDISCOVERY_FLOOR`.
- Do **not** force-firewall.
- Do **not** inject odd-double/rotate / Level-14 / FX8 / CAT-self as secret discovery targets into `propose_atoms`.
- Do **not** raise sacred budget on the immutable 3.39 RECORD; BH is a **new experiment cell** under a future charter.
- Do **not** rewrite 3.38/3.39 sacred first_run/REPORT.

---

## 7. STOP BEFORE IMPLEMENTATION

**STOP.**

This preflight is complete. Do **not**:

1. Implement the B×R factorial or any 3.40 experiment matrix.
2. Change discovery algorithms, `propose_atoms`, growth priors, firewall forcing, or leftover floors.
3. Raise sacred budget or invent_cap on frozen runners as a “make it pass” move.
4. Rewrite `reports/aivd_3_38_llama/*` or `reports/aivd_3_39_llama/*` sacred results.
5. Claim TinyLlama incapability, Level-14 impossibility, or VERIFIED discovery from this audit.

Next action requires an explicit parent charter to execute experiments under Absolute constraints restated at that time.

---

## Appendix A — Quick cite map

| Claim | Cite |
|-------|------|
| 0/7 S and U | `REPORT.md` pipeline table; `first_run.json` `pipeline_verified` |
| leftover=3 &lt; floor=5 | `first_run.json` methods_log `REDISCOVERY_BUDGET_FAILURE`; frontier §Measured |
| epoch=0 | REPORT Independence summary; run.log `epoch=0`; ledgers `generation_epoch=0` |
| even CAT-self grown | REPORT “Grown program”; language `programs`; grow `body_key` |
| invent_cap not binding | frontier Limit decomposition; INVENT_CAP=48 vs 3 atoms |
| plants miss space | frontier plant integrity; `llama_339` + `existing_space_oracle` |
| Stage 7+ STOP | REPORT Budget frontier; `aivd339_budget_frontier.md` Stage 7+ |

## Appendix B — Confirmation

| Item | Status |
|------|--------|
| Discovery / propose_atoms / floor / budget code changed this audit? | **NO** |
| Sacred 3.38 / 3.39 results rewritten? | **NO** |
| Experiment matrix implemented? | **NO** |
| Docs committed on 3.40 branch only? | **YES** (this preflight + JSON) |
