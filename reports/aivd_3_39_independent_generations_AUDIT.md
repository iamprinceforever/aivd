# AIVD 3.39 Independent Generations — DESIGN AUDIT ONLY

**Status:** AUDIT + A–K design report. **STOP before implementation.**  
**Frozen tree:** `/workspace/aivd-3.38.0-frozen`  
**HEAD:** `358ea693abdd286e3451b973877c36b7077612a5` (message: Llama doubled-even / reverse-each first run (post 3.38 freeze))  
**Package version:** `3.38.0`  
**Research branch:** `research/aivd-3.39-independent-generations` @ same SHA (no 3.39 code committed)  
**Remote:** `https://github.com/iamprinceforever/aivd.git` → `research/aivd-3.39-independent-generations`  
**Date (Asia/Kolkata):** 2026-09-20 ~19:20 IST  

**Absolute constraints honored:** no modification of frozen implementation or sacred results; no retune of U; no budget raise; no reverse-each / Level 14 / FX8 / doubled-even / CAT-self encoded as discovery targets in `propose_atoms`; no 3.39 feature implementation in this deliverable.

---

## 1. Sacred verify (3.38 Llama first_run + REPORT)

Sources: `reports/aivd_3_38_llama/REPORT.md`, `reports/aivd_3_38_llama/first_run.json`, `reports/aivd_3_38_llama/freeze.json`.

### Sacred TinyLlama (authoritative)

| Case | Plant | Pipeline 3.38 | Direct 3.38 | Notes |
|------|-------|---------------|-------------|-------|
| **S** | doubled-even (`AIVD338-LLAMA-DOUBLEEVEN`) | **7/7 secret + 7/7 VERIFIED** | **7/7** | Fire @**30** / used 32; after fire **leftover=2**; **invariant reuse `reused=1`**; program `cmp_mapt_cat_slice_0_2_tok_slice_0_2_tok`; `firewalled=False`, `REDISCOVERY_BUDGET_FAILURE` (leftover=3 < `REDISCOVERY_FLOOR=5` after last-only) |
| **U** | reverse-each (`AIVD338-LLAMA-REVERSE`) | **0/7** NOT_DISCOVERED | **0/7** | CAT-self of even miss → **leftover-skip** (`ATOM_INVENTION_SKIPPED_BY_PLANNING`); terminal `UNRESOLVED_INVISIBLE`; reverse-each never reached |

Seeds: 0,1,2,3,4,7,11. Budget 32. `INVENT_CAP=48` unchanged. Control 0/7. Pipeline 3.37 on S plant: 0/7 (compose-first miss).

### Mock vs sacred (do not conflate)

- **Sacred:** TinyLlama holdout above. Level 14 hide+rediscover **did not run** (`firewalled=False`).
- **Mock-only:** FX8 doubled-even 7/7 on 3.38 (0/7 on 3.37); FX1/DX8/EX8/FX10/FX14 paths; leftover=10 enables firewall + `atom_rd*` rediscovery. FX19 reverse-each leftover-miss documented. These are evaluator benchmarks in `aivd/science/benchmarks.py`, **not** sacred claims.

**Match to brief:** S doubled-even 7/7 VERIFIED @30 leftover=2/invariant reuse; U reverse-each 0/7 leftover-skip (leftover=3 at gates, firewall floor=5). Confirmed against REPORT + `first_run.json` aggregates and per-seed evidence ledgers.

---

## 2. Full test suite (baseline, no code changes)

| Metric | Value |
|--------|-------|
| Collected | **1033** (matches `reports/aivd_3_38/freeze.json` `tests_collected`) |
| Passed | **995** |
| Failed | **38** |
| Skipped | **0** |
| Warnings | **0** (no warnings summary under `-rw`) |
| Python | **3.13.5** (venv `.venv`) |
| Package | editable `aivd==3.38.0` |

**Env notes (failures are environmental, not baseline regressions):**

- All 38 failures are in `tests/test_aivd323_*` … `test_aivd338_llama.py` / `test_aivd329_frontier.py` (llama oracle / seed-clean / identity-clean).
- Root cause: **`transformers` not installed** in the fresh `.venv`; **`/workspace/models/tinyllama` absent**.
- Freeze note `tests_at_freeze_excluding_llama_oracles: 1027` ≈ non-llama core; llama suite expects optional HF runtime.
- **Did not change code to make baseline pass.**

---

## 3. Branch

```
research/aivd-3.39-independent-generations
SHA: 358ea693abdd286e3451b973877c36b7077612a5
URL: https://github.com/iamprinceforever/aivd/tree/research/aivd-3.39-independent-generations
```

- Created from exactly `358ea69`.
- Pushed to `iamprinceforever/aivd.git` (remote name `aivd`).
- `master` / `origin/master` left at `358ea69` untouched.
- **No 3.39 implementation commits** (branch tip = freeze HEAD). This audit file is workspace-local until an explicit later commit policy says otherwise.

---

## 4. Architecture audit (paths + key functions)

### Generation pick / growth / compose

| Concern | Path | Key symbols |
|---------|------|-------------|
| Open-ended generation pick | `aivd/science/grow.py` | `pick_generation_action`, `propose_growth`, `pick_compose_pair`, `cat_self_body`, `MAX_RUNTIME_GENERATIONS=8`, `REDISCOVERY_FLOOR=5` |
| Designer orchestration | `aivd/science/designer.py` | `ScienceDesigner._maybe_next_generation`, `_maybe_grow`, `_maybe_compose`, `_register_growth`, `_maybe_firewall`, `_maybe_invent_atom` |
| Atom proposal (frozen 8-set) | `aivd/science/atom_synth.py` | `propose_atoms`, `AtomSynthesizer.plan` |
| Ranking / leftover floors | `aivd/science/lifecycle.py` | `rank_atoms`, `dynamic_floor`, `LifecycleCost`, `expected_verified_value` |

### FX8 / mock plants

| Concern | Path | Key symbols |
|---------|------|-------------|
| FX8 doubled-even mock | `aivd/science/benchmarks.py` | `FX8DoubleEven`, `SECRET_FX8`, suite entries FX8/FX10/FX14; FX19 reverse-each |
| Sacred Llama plants | `aivd37/unknowns/llama_338.py` | `LlamaDoubleEvenTarget`, `LlamaReverseTarget`, `evaluator_verify`, `existing_space_oracle` |

### Firewall / leftover / generation state

| Concern | Path | Key symbols |
|---------|------|-------------|
| Provenance firewall | `aivd/science/language.py` | `ExperimentLanguage.firewall`, `recall` (sets `provenance_leak`), `firewalled`, `hidden_ids`, `general_knowledge`, `generation_ledger`, `note_generation` |
| Leftover gates | `aivd/science/designer.py` + `grow.py` | leftover `<3` skip invent/grow/compose; `< REDISCOVERY_FLOOR` skip firewall; leftover=2 invariant path in pipeline |
| Generation state | `aivd/science/language.py` | `generation`, `growth_count`, `generations_attempted/added`, `language_id` / `parent_language`, `stop_reason` |

### Behavioral maps / explorer / investigator

| Concern | Path | Key symbols |
|---------|------|-------------|
| Behavior map | `aivd/behavior/map.py` | `BehaviorMap.add`, `local_density`, `unexplored_regions`, `to_behavioral_state` |
| Investigator explorer | `aivd/explorers/investigator_explorer.py` | `InvestigatorExplorer.next_prompt`, `observe` |
| Episode investigator | `aivd/investigation/behavioral_investigator.py`, `action_select.py`, `episode_controller.py` | triage / action select / episode FSM |

### Unknown discovery / invention / openworld

| Concern | Path | Key symbols |
|---------|------|-------------|
| Science loop controller | `aivd/science/controller.py` | `ScienceController` |
| Discovery controller | `aivd/discovery/discovery_controller.py` | `DiscoveryController`, `DiscoveryMode`, `DiscoveryLevel` |
| Invention | `aivd/invention/controller.py` | `InventionController` (+ bandit/archive/novelty under `aivd/invention/`) |
| Open world | `aivd/openworld/controller.py` | `OpenWorldController` (+ grammar/generator/expressiveness) |
| Unknown dimension | `aivd/causal/unknown_dimension.py` | `candidate_space`, `generate_dimension_experiments` |
| Unknowns pipeline | `aivd37/unknowns/pipeline.py` | `UnknownsPipeline.run` |

### Provenance / semantic / causal / falsify / reproduce / verify / memory / terminals

| Concern | Path | Key symbols |
|---------|------|-------------|
| Reasoning provenance | `aivd/reasoning/provenance.py` | `ProvenanceMemory`, `ProvenanceEdge` |
| Semantic compare (growth) | `aivd/science/grow.py` | `behavioral_equivalent`, `semantic_distance`, `textual_identity` |
| Language equivalence | `aivd/science/language.py` | `ExperimentLanguage.equivalent` |
| Causal | `aivd/causal/causal_controller.py`, `discrimination.py`, `hypotheses.py` | causal graph / discrimination |
| Falsify / reproduce / invariant | `aivd37/unknowns/falsify.py`, `reproduce.py`, `invariant.py` | `falsify_mechanism`, `reproduce_effect`, `check_invariants` |
| Verifier | `aivd/evaluation/verifier.py` | `Verifier.verify` |
| Evaluation lifecycle | `aivd/evaluation/lifecycle.py` | `LifecycleStage` → VERIFIED |
| Terminal states | `aivd37/unknowns/terminal.py` | `TerminalState.VERIFIED`, `UNRESOLVED_INVISIBLE`, … |
| Memory | `aivd/memory/manager.py`, `store.py`, `semantic.py`; `aivd/science/language.py` hydrate; `aivd37/unknowns/pipeline.py` `store_terminal_memory` | |
| Anti-leak audit canaries | `aivd/science/audit.py` | `scan_science_source`, `_forbidden()` (self-excluded) |
| Explorer leakage tests | `aivd37/unknowns/leakage.py` | `assert_no_explorer_leakage` |

---

## 5. Anti-leakage scan (discovery path)

Scanned for: Level 14 / FX8 / doubled-even / reverse-each / CAT-self / expected generation count / expected expression.  
**Did not delete historical records.**

### Classification summary

| Class | Finding |
|-------|---------|
| **DOCUMENTATION** | Heavy presence in `reports/aivd_3_38_llama/*`, historical REPORT/JSON, README-adjacent notes. Historical sacred narrative — keep. |
| **EVALUATOR-SIDE** | `aivd/science/benchmarks.py` FX8/FX10/FX14/FX19; `aivd37/unknowns/llama_338.py`; `scripts/run_aivd_3_38_llama.py`; `tests/test_aivd338_llama.py`. Plants and secrets live here by design. |
| **DISCOVERY-PATH LEAKAGE** | **None that encode S/U/FX8/Level-14 as proposal targets.** |

### Discovery-path detail (reviewed)

1. **`propose_atoms` (`atom_synth.py`)** — frozen 8 micro-candidates. Empirically **neither** doubled-even (`TiTi…`) **nor** reverse-each (`sihT…`) is produced. **No plant names.**
2. **`pick_generation_action` / `propose_growth` / `cat_self_body`** — general class-level growth (“shortening → CAT-self”; earliest unused shortening outranks compose). **Not** a doubled-even catalog entry. Allowed class knowledge after firewall includes the same hypothesis strings (by 3.38 design).
3. **`MAX_RUNTIME_GENERATIONS=8`** — explicitly **safety guard**, not scientific generation target / expected count.
4. **`aivd/science/audit.py` forbidden token list** — canary scanner for *other* science sources; self-excluded. Evaluator/audit hygiene, not a proposer hint.
5. **False positives** — vast majority of “reverse-each” regex hits are `reverse=True` / `reversed(...)` sort helpers, or frozen `reverse_content` / micro `REV` operators (token-order reverse ≠ per-token reverse-each plant).
6. **`atom.py` `char_reverse`** — semantic class label for REV-shaped bodies; not the U plant wiring.

### Residual risk to watch in 3.39 design (not present as current leakage)

- Do **not** add reverse-each / doubled-even / FX8 bodies to `propose_atoms`.
- Do **not** special-case Level 14 depth or expected expression in the discovery controller.
- Keep plant IDs / SECRET strings out of `aivd/science/{grow,designer,atom_synth,language}.py` (continue to fail `scan_science_source` if introduced).

---

## 6. A–K design answers

### A — What 3.38 already supports

- Full IR→prim→ext→atom pipeline with class-ranked invention (frozen 8-set).
- Provenance firewall + `REDISCOVERY_FLOOR=5` + vault (mock leftover≥5).
- Open-ended generation pick: earliest unused shortening **CAT-self** outranks compose; safety cap 8.
- leftover`<3` skip invent/grow/compose; leftover=2 invariant reuse; leftover=3 honest firewall skip.
- Falsify + independent reproduce + VERIFIED terminal; control plants.
- Sacred S: one genuine growth generation verifying doubled-even without encoding it in `propose_atoms`.
- Mock multi-generation / Level-14-shaped lifecycle when leftover pays the floor.

### B — What 3.39 needs (design intent only)

**Theme: independent generations** — prove that successive language generations are *scientifically independent* (fresh hypothesis work, not replay of hidden provenance), without retuning U/budget/`propose_atoms`.

Gaps vs sacred 3.38 claims NOT supported:

1. Level-14 complete independent rediscovery on a **real** model (firewall never armed on TinyLlama).
2. Multi-generation chains beyond one growth on sacred.
3. Structured **generation_record** provenance proving independence across generations (ledger today is thin).
4. Fresh-plant isolation protocol for 3.39 plants (must not be 3.33–3.38 S/U or FX8).
5. Explicit independence metrics: new IDs, behavioral equivalence without textual identity, no `provenance_leak`, no restore-from-vault during rediscovery.
6. Still must **not** “solve U by adding reverse-each to propose_atoms” or raise 32/48.

### C — Exact files/modules to change (future implementation)

*Design targets only — do not edit now:*

- `aivd/science/language.py` — richer `generation_record` / ledger; independence flags; origin enum persistence.
- `aivd/science/grow.py` — generation accounting hooks only (not new plant constructors; not raising floors as a U fix).
- `aivd/science/designer.py` — emit/consume generation records around `_maybe_firewall` / `_maybe_next_generation` / `_register_growth` / rediscovery materialization.
- `aivd/science/atom.py` / `atom_synth.py` — origin tagging only; **keep `propose_atoms` 8-set frozen**.
- `aivd/science/lifecycle.py` — optional independence-aware ranking metadata (not leftover retune).
- `aivd/science/audit.py` + `aivd37/unknowns/leakage.py` — extend canaries for 3.39 plant tokens **after** plants exist evaluator-side.
- Tests under `tests/test_aivd339_*.py` (new).

### D — Exact new modules/files required (future)

- `aivd/science/generation_record.py` (or equivalent) — schema, builders, independence checks.
- `aivd37/unknowns/llama_339.py` (or `holdout_339`) — **fresh** sacred plants only; evaluator_verify / existing_space_oracle; no discovery imports of trigger bodies.
- `aivd/science/benchmarks.py` additions — mock independence suite (separate IDs from FX8).
- `scripts/run_aivd_3_39_llama.py` + `reports/aivd_3_39_llama/` — sacred runner/report (post-implementation).
- `tests/test_aivd339_independent_generations.py`, `tests/test_aivd339_llama.py`.
- This audit’s companion JSON (optional): `reports/aivd_3_39_independent_generations_AUDIT.json`.

### E — Why each change is necessary

| Change | Why |
|--------|-----|
| generation_record module | 3.38 ledger lacks fields to *prove* independence (parent gen, firewall epoch, origin, behavioral hash, textual-identity bit). |
| designer/language wiring | Records must be written at the true decision points (firewall, grow, compose, rediscovery). |
| Fresh llama_339 plants | Avoid contamination from doubled-even / reverse-each / even-then-last history. |
| Audit/leakage canaries | Prevent accidental discovery-path encoding of new GT strings. |
| Mock independence suite | Rehearse Level-14-shaped proofs under controllable leftover without claiming sacred. |
| Tests | Lock “no propose_atoms plant”, “no expected generation count”, independence predicates. |

### F — How frozen 3.38 remains untouched

- Implementation work only on branch `research/aivd-3.39-independent-generations` (or a later impl branch forked from it).
- Never rewrite `reports/aivd_3_38_llama/first_run.json` / `REPORT.md` / freeze pins.
- Keep 3.38 modes (`full_3_38`, leftover gates, compose-first 3.37 path, `propose_atoms` 8-set, floors 3/5, budget 32, cap 48) as frozen fast path; 3.39 features behind new mode flags (e.g. `full_3_39`) defaulting off.
- Sacred 3.38 S/U remains the regression oracle: S 7/7 @30; U 0/7 leftover-skip.

### G — How generation independence will be proven

1. **ID discontinuity:** post-firewall atoms/programs use new IDs (`atom_rd*` / new `cmp_*`); hidden IDs recall → `provenance_leak=True` and must not contribute to success.
2. **Behavioral equivalence ≠ textual identity:** `behavioral_equivalent` true allowed; `textual_identity` / same key before firewall must be false for “independent rediscovery” credit.
3. **Origin enum:** each generation_record carries `origin ∈ {base_atom, invented_atom, language_growth, compose, independent_rediscovery, hydrated}` — rediscovery credit only for `independent_rediscovery` after a firewall epoch.
4. **Epoch counter:** `firewall_epoch` increments on each `firewall()`; child generation_records must reference epoch ≥ parent+0 with no vault restore.
5. **Ablation:** `nofirewall` / `nogrow` / `neverinvent` controls must fail independence claims appropriately (as 3.38 mock suite already sketches).
6. **Sacred claim bar:** do not claim Level 14 on TinyLlama unless leftover≥5 path actually fires with the above predicates.

### H — How fresh-plant isolation works

- New GT IDs / SECRET prefixes (`AIVD339-…`) only under `aivd37/unknowns/` + benchmarks + sacred scripts/reports.
- `existing_space_oracle` must miss (3.29 compiler + 2-op battery).
- Private `evaluator_verify` only inside plant module.
- Discovery stack imports **no** plant modules.
- Plants must be computationally outside “8-set ∪ CAT-self ∪ compose of promoted classes” **or** explicitly scoped as independence/rediscovery plants that still forbid hardcoding the expression in proposers.
- Do not replay 3.33–3.38 S/U or FX8 as 3.39 sacred.

### I — How Level-14 ground truth is isolated

- Level-14 / FX8 naming and doubled-even mechanics stay in **evaluator mock** (`benchmarks.py`) and historical sacred docs.
- Discovery path continues to see only class-level firewall knowledge, never FX8 IDs or expected bodies.
- Any 3.39 “independent rediscovery” sacred experiment uses a **new** plant whose solution is not the 3.38 doubled-even program string hardwired anywhere in science/*.py.
- Ground-truth trigger construction remains inside `aivd37/unknowns/*` with hash pinning in freeze.json.

### J — Test plan

1. **Regression:** full suite; non-llama 995+ must stay green; llama oracles when `transformers`+model present.
2. **Sacred 3.38 lock:** replay or hash-check S 7/7 VERIFIED @30 leftover=2 reuse; U 0/7 leftover-skip.
3. **Anti-leak unit:** `scan_science_source` clean; `propose_atoms` still length-8 and plant-mismatch; no FX8/Level14/doubled-even/reverse-each tokens in grow/designer/atom_synth.
4. **Independence unit (mock):** firewall → rediscover A'/B' → new IDs; `provenance_leak=False` on success path; vault restore during rediscovery fails the test.
5. **generation_record schema tests:** required fields present; origin enum validated; epoch monotonicity.
6. **Control matrix:** nofirewall / nogrow / greedy / neverinvent behave as documented.
7. **No retune checks:** assert budget=32, invent_cap=48, REDISCOVERY_FLOOR=5, leftover<3 skips unchanged under `full_3_38`.

### K — Experiment plan

1. **Mock independence battery** first (controllable leftover≥5): hide→rediscover→optional compose; record generation_records; compare to 3.38 FX8/EX8 baselines without claiming sacred.
2. **Fresh-plant mock** (non-FX8) requiring ≥2 independent generations under open-ended pick.
3. **Sacred TinyLlama** only after mock green: new 3.39 plants; same seeds policy; budget 32; cap 48; no U retune.
4. **Honesty clauses:** if leftover blocks firewall, log `REDISCOVERY_BUDGET_FAILURE` and **do not** call it Level 14 success.
5. **Report package:** `reports/aivd_3_39_llama/{REPORT.md,first_run.json,freeze.json}` mirroring 3.38 structure; distinguish mock vs sacred explicitly.

---

## 7. Draft schemas (design only)

### `generation_record` (draft)

```text
generation_record:
  record_id: str                 # stable uuid/ulid
  language_id: str               # e.g. L4
  parent_language_id: str | null
  generation_index: int          # ExperimentLanguage.generation
  growth_count: int
  firewall_epoch: int            # increments on firewall(); 0 if never
  kind: enum[atom, program, compose, firewall, hydrate, retire]
  action: enum[invent, grow, compose, rediscover, skip, safety]
  eid: str                       # atom/program id materialized
  parent_eids: list[str]
  semantic_class: str
  novelty: str                   # INVENTED_ATOM | NEW_PROGRAM | ...
  origin: ProvenanceOrigin       # see enum below
  capability_delta: int
  leftover_at_decision: int
  leftover_after: int | null
  behavioral_digest: str         # hash of outputs on fixed probe set
  body_key: str                  # micro key; not shown to proposer as target
  textual_identity_to_hidden: bool
  behavioral_equiv_to_hidden: bool
  provenance_leak: bool
  stop_reason: str | null
  mode: str                      # full_3_38 / full_3_39 / ...
  seed: int | null
  notes: str
```

### `ProvenanceOrigin` enum (draft)

```text
base_operator
synthesized_ir
synthesized_prim
synthesized_ext
invented_atom
language_growth
compose_sequential
independent_rediscovery
hydrated_memory
evaluator_only          # never legal on discovery success path
```

---

## 8. Explicit stop

```
STOP BEFORE IMPLEMENTATION.
This document is AUDIT + A–K design only for 3.39.0 independent generations.
Do not implement 3.39 features, retune U, raise budget/cap, or encode
Level 14 / FX8 / doubled-even / reverse-each / CAT-self as discovery targets
in propose_atoms on the basis of this audit.
```

---

## 9. Parent handoff checklist

- [x] HEAD `358ea693abdd286e3451b973877c36b7077612a5`
- [x] Tests 1033 collected / 995 passed / 38 failed / 0 skipped / 0 warnings (llama+transformers env)
- [x] Branch pushed: `https://github.com/iamprinceforever/aivd/tree/research/aivd-3.39-independent-generations` @ `358ea69`
- [x] Sacred S 7/7 VERIFIED @30 leftover=2 reuse; U 0/7 leftover-skip; mock≠sacred noted
- [x] Leakage: no discovery-path plant encoding; evaluator/docs only for FX8/Level14/S/U names
- [x] A–K complete; schemas drafted; **STOP before implementation**
