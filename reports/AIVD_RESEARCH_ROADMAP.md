# AIVD Research Roadmap — 3.39 Independent Generations → 3.40 Budget×Representation

**Branch:** `research/aivd-3.39-independent-generations`  
**Base pin:** `f86ebdf` (implementation freeze for Sacred)  
**Package:** `3.39.0`  
**Timezone:** Asia/Kolkata (IST)

Absolute constraints for all stages: no U retune; no budget/cap raise; no `propose_atoms` rewrite; no rewrite of 3.38 sacred first_run; no discovery instruction for Level-14 / FX8 / doubled-even / CAT-self / generation counts; no fabricated Sacred results if gate fails.

---

## Stage 1 — Environment fingerprint

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Record a reproducible TinyLlama + transformers + AIVD commit fingerprint for Sacred 3.39. |
| **HYPOTHESIS** | A machine-readable env document plus hashes is sufficient for another box to match greedy fp16 CPU inference. |
| **METHOD** | Collect Python/OS/torch/transformers versions; model id/revision/path; sha256 of key files; `llama_infer.runtime_info()`; AIVD commit/branch; gate criteria. |
| **RESULT** | `configs/aivd339_tinyllama_environment.json` written. Gate status recorded as **PASS** (transformers 5.17.0; model.safetensors sha256 `6e6001da…f14933`; `llama_infer.available()==True`). |
| **ARTIFACTS** | `configs/aivd339_tinyllama_environment.json` |
| **DECISION** | Proceed to Stage 2 reproduction doc and Stage 3 Sacred only after PASS (confirmed). |

---

## Stage 2 — Reproduction + gate instrumentation

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Document how to recreate the env on another machine; persist an executable gate result under `reports/aivd_3_39_llama/`. |
| **HYPOTHESIS** | Explicit checkout → pip → snapshot_download(revision pin) → `available()` checklist prevents silent drift. |
| **METHOD** | Write reproduction markdown; extend `scripts/run_aivd_3_39_llama.py` env gate to require transformers + model weights + `llama_infer.available()`; write `env_gate.json`. |
| **RESULT** | `docs/aivd339_tinyllama_reproduction.md` created. Env gate **PASS**. Sacred runner ready (`full_3_39`, budget 32, invent_cap 48, seeds 0/1/2/3/4/7/11, plants AIVD339-* only). |
| **ARTIFACTS** | `docs/aivd339_tinyllama_reproduction.md`, `reports/aivd_3_39_llama/env_gate.json`, `scripts/run_aivd_3_39_llama.py` |
| **DECISION** | Stage 3 Sacred authorized. |

---

## Stage 3 — Sacred TinyLlama first run

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Fresh Sacred measurement of 3.39 independent-generations mode on TinyLlama with AIVD339 plants only. |
| **HYPOTHESIS** | With recording on and no depth target, generation records will show whether independence machinery fires under budget 32 without retuning U. |
| **METHOD** | `python scripts/run_aivd_3_39_llama.py` — pipeline + direct + control; no 3.38 state reuse; write first_run / REPORT / freeze / ledgers. |
| **RESULT** | **RUN.** S verified **0/7**, U verified **0/7**. Failure `ATOM_INVENTION_SKIPPED_BY_PLANNING` / `REDISCOVERY_BUDGET_FAILURE` (leftover=3 < floor=5) then grow even-CAT-self; `firewall_epoch=0`. Direct/control secrets 0/7. |
| **ARTIFACTS** | `reports/aivd_3_39_llama/{first_run.json,REPORT.md,freeze.json,env_gate.json,generation_ledgers.json,generation_ledgers_S.json,generation_ledgers_U.json,run.log}` |
| **DECISION** | Proceed to Stage 4–6 analysis only (no retune). |

---

## Stage 4 — Independence analysis

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Classify independence from generation records only (discovery-path origins; no evaluator retro-label credit). |
| **HYPOTHESIS** | Records distinguish exists vs independently_discovered under firewall epoch rules. |
| **RESULT** | Records **exist** (4/seed). **Zero** `independently_discovered=True`. Origins=`invented_atom`/`language_growth`; epoch=0. |
| **DECISION** | Independence success path not reached on Sacred; machinery recorded honestly. |

---

## Stage 5 — Offline Level-14 evaluation (evaluator-side only)

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Offline, evaluator-side assessment of whether deeper generation depth is *representable* — **not** a discovery instruction and **not** a VERIFIED claim without evidence ladder. |
| **HYPOTHESIS** | Budget/leftover floors may preclude deep independent rediscovery on TinyLlama without implying algorithm falsehood. |
| **RESULT** | Offline class **`LEFTOVER_WALL_PRE_FIREWALL`**. Plants verify evaluator-side; Sacred never enters firewall epoch. **Not VERIFIED.** |
| **DECISION** | Do not claim VERIFIED. Do not instruct discovery toward Level-14. |

---

## Stage 6 — Budget frontier

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Separate algorithm vs budget vs model vs representation limits in `reports/aivd339_budget_frontier.md`. |
| **HYPOTHESIS** | Conservative measurement will show leftover/REDISCOVERY_FLOOR as the binding constraint for U-class plants (as in 3.38), not invent_cap. |
| **RESULT** | Confirmed: leftover wall primary; representation gap (even program vs odd/rotate plants); invent_cap not binding; model unlikely primary. Algorithm independence path untested post-firewall, not falsified. |
| **DECISION** | **STOP Stage 7+.** Evidence does not justify deeper gens under Absolute constraints. |

---

# AIVD 3.40 — Budget × Representation Frontier (Step 1+)

**Branch:** `research/aivd-3.40-budget-representation-frontier`  
**Preflight:** `35363d6`  
**Timezone:** Asia/Kolkata (IST)

Absolute constraints: 3.38/3.39 sacred IMMUTABLE; no propose_atoms rewrite; no force-firewall; no lower REDISCOVERY_FLOOR; no raise Absolute B32 sacred semantics; no evaluator imports into discovery; no Sacred TinyLlama 3.40 matrix this stage.

---

## Step 0 — Preflight audit

| Field | Content |
|-------|---------|
| **RESULT** | Budget YES + representation YES (joint); invent_cap not binding; factorial design preview only |
| **ARTIFACTS** | `reports/aivd_3_40_preflight.md` / `.json` |
| **DECISION** | STOP before implementation (completed); parent re-chartered Step 1+ |

---

## Step 1+ — Experiment design + matrix framework + mocks + tests

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Preregister B×R factorial; ship condition/manifest/runner; R0/R1 abstraction; budget docs/tests; AIVD340 plants + leakage; mock matrix + controls; regression locks. **No Sacred TinyLlama matrix.** |
| **BH** | **48** — leftover-wall justification: Sacred 3.39 leftover=3 at firewall; need ≥5 without lowering floor; BH=48 ⇒ expected leftover≈19 |
| **R1** | Generic parity/position/stride/order augmentation via `representation.py`; R0 bit-identical to frozen propose_atoms/growth |
| **RESULT** | Framework + mocks + unit/leakage/regression tests green; Sacred TinyLlama **NOT RUN** |
| **ARTIFACTS** | `reports/aivd_3_40_experiment_design.{md,json}`, `condition_manifest.json`, `representation_spec.md`, `budget_semantics.md`, `leakage_audit.md`, `reports/aivd_3_40_mock/*`, `aivd/experiments/aivd340/*` |
| **DECISION** | **STOP** before Sacred TinyLlama 3.40 factorial. Remaining blockers listed in Step 1+ closeout. |

### Factorial (preregistered, not sacred-run)

`B32-R0`, `B32-R1`, `BH-R0`, `BH-R1`

### Controls proven offline

NORMAL-R0/R1, NO-FIREWALL, NO-LANGUAGE-GROWTH, NO-OPEN-SELECTION, LEAKAGE-CANARY, BEHAVIORAL-EQUIVALENCE, TEXTUAL-DIFFERENCE

---

# AIVD 3.40 — Sacred TinyLlama Factorial (AUTHORIZED EXECUTION)

**Recorded:** 2026-09-21 16:09:54 IST  
**Env hash:** `18c11b475cfe78516d44219053862af94b46c81cc9329a2bd448e46737ddb9d8`  
**n_runs:** 56  

| Field | Content |
|-------|---------|
| **OBJECTIVE** | Execute preregistered B32/BH48 × R0/R1 × 7-seed Sacred factorial on TinyLlama with AIVD340 plants. |
| **RESULT** | B32-*: firewall 0/14, verified 0/14 (leftover wall). BH-R0: firewall 14/14, verified 0/14. BH-R1: firewall 14/14; S 0/7; **U 7/7 VERIFIED** with independent_rediscovery. |
| **n_firewall_crossings** | 28 |
| **n_independent_gens (conservative)** | 7 |
| **n_verified_gens** | 7 |
| **n_leakage_failures** | 0 |
| **ARTIFACTS** | `reports/aivd_3_40_sacred_results.md`, `reports/aivd_3_40_llama/`, independence/budget/representation/reproducibility reports |
| **DECISION** | Data surprise: joint BH×R1 sufficient for U; S unresolved. Next: replicate U; design-only R1b for odd CAT-self growth — no floor retune. |
