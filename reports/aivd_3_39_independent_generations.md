# AIVD 3.39.0 Independent Generations — Implementation Report

**Status:** Phase 5A–5O implemented on `research/aivd-3.39-independent-generations`  
**Package version:** `3.39.0`  
**Date (Asia/Kolkata):** 2026-09-20 ~19:45 IST  
**Audit pin:** `f0fed2b` (`reports/aivd_3_39_independent_generations_AUDIT.md`)

---

## Absolute constraints — confirmed

| Constraint | Status |
|------------|--------|
| Frozen 3.38 sacred results untouched | YES — `reports/aivd_3_38_llama/first_run.json` / `REPORT.md` / freeze not rewritten |
| `propose_atoms` 8-set frozen | YES — length 8; no plant bodies |
| Sacred budget 32 / invent_cap 48 | YES — unchanged |
| U leftover-skip / leftover floors | YES — leftover&lt;3 invent/grow/compose; REDISCOVERY_FLOOR=5 |
| No Level-14 / FX8 / doubled-even / reverse-each / CAT-self as discovery proposal targets | YES — canary `scan_discovery_target_leakage` clean |
| New features behind `full_3_39` / flags default OFF | YES — `allow_gen_record` only when `3_39` in mode |
| `full_3_38` identical decision path | YES — no generation_records emitted; flags unchanged |
| Sacred TinyLlama only after mock gate | Mock gate PASSED; Sacred **NOT RUN** (env) |

---

## Schema summary (`aivd/science/generation_record.py`)

`GenerationRecord` fields (required for independence proof):

- Identity: `record_id`, `experiment_id`, `plant_id`, `generation_id`, `parent_generation_id`, `run_id`, `timestamp`
- Epoch / language: `generation_epoch` (= firewall epoch), `generation_index`, `language_id`, `parent_language_id`, `growth_count`
- Model: `seed`, `model`, `model_revision`
- Candidate: `candidate_id`, `candidate`, `candidate_origin`, `proposal_origin`, `provenance`, `eid`, `parent_eids`, `body_key`, `semantic_class`, `novelty`
- Evidence: `behavioral_signature`, `semantic_signature`, `causal_evidence`, `falsification_result`, `reproduction_result`, `verification_state`
- Budget: `budget_before`, `budget_after`, `leftover`, `leftover_after`
- Independence bits: `textual_identity_to_hidden`, `behavioral_equiv_to_hidden`, `provenance_leak`
- Terminal: `terminal_reason`, `stop_reason`, `mode`, `notes`, `kind`, `action`, `capability_delta`

### Origin enum (`CandidateOrigin`)

Discovery-path only (evaluator cannot retro-label independent):

`model_generated`, `independent_rediscovery`, `inherited`, `transformed`, `recombined`, `replayed`, `evaluator_derived`, `fixture_derived`, `human_supplied`

Compatible aliases (same system, no duplicate provenance): `invented_atom`, `language_growth`, `compose_sequential`, `hydrated_memory`, `base_operator`, `synthesized_*`.

`independence_verdict()` distinguishes **exists** vs **independently_discovered** (requires origin=`independent_rediscovery`, `generation_epoch>0`, no `provenance_leak`).

---

## Files changed

### New
- `aivd/science/generation_record.py` — schema, origins, builders, independence checks
- `aivd37/unknowns/llama_339.py` — fresh evaluator-only plants (`AIVD339-LLAMA-ODDDOUBLE`, `AIVD339-LLAMA-ROTATE`)
- `tests/test_aivd339_independent_generations.py` — mock independence + regression + leakage
- `tests/test_aivd339_llama.py` — env-dependent sacred plant tests (skip without transformers/model)
- `scripts/run_aivd_3_39_mock_independence.py` — mock experiment + controls A–F
- `scripts/run_aivd_3_39_llama.py` — sacred runner with env gate
- `reports/aivd_3_39_independent_generations.md` (this file)
- `reports/aivd_3_39_independent_generations/mock_experiment.json`
- `reports/aivd_3_39_llama/{env_gate.json,REPORT.md}` — Sacred NOT RUN

### Extended
- `aivd/science/language.py` — `firewall_epoch`, `generation_records`, `emit_generation_record`
- `aivd/science/designer.py` — `full_3_39` mode flags, `allow_gen_record`, emit at firewall/grow/compose/atom
- `aivd/science/audit.py` — 339 plant tokens + `scan_discovery_target_leakage`
- `aivd/science/benchmarks.py` — GX8/GX14 mock independence plants (`AIVD339-GX*`)
- `aivd/science/scheduler.py`, `aivd/epistemic/scheduler.py`, `aivd/core/config.py`, `aivd/invention/controller.py`, `aivd37/unknowns/pipeline.py` — `full_3_39` recognition
- `aivd/__init__.py`, `pyproject.toml` — version `3.39.0`
- `aivd/science/__init__.py` — export canary

### Untouched (sacred 3.38)
- `reports/aivd_3_38_llama/*`
- `aivd37/unknowns/llama_338.py`
- `propose_atoms` 8-set body list
- `INVENT_CAP=48`, `REDISCOVERY_FLOOR=5`, leftover&lt;3 gates

---

## Test matrix

| Suite | Result |
|-------|--------|
| `tests/test_aivd339_independent_generations.py` | **30 passed** |
| `tests/test_aivd339_llama.py` | **1 skipped** (module-level; no transformers) |
| `tests/test_aivd338_lang.py` | **25 passed** (3.38 regression lock) |
| Non-LLM core (excluding llama oracles) | **980 passed** |
| Llama/orphan/ortho/disc/field env tests | **12 failed** — environment-dependent (`transformers` missing); same class as 3.38 audit baseline |
| Sacred TinyLlama 3.39 | **NOT RUN** — `transformers` not installed; `/workspace/models/tinyllama` absent |

Honest categories: **pass** / **fail (env)** / **skip (env)** / **NOT RUN (env)**. No claimed unrun sacred results.

---

## Mock experiment + controls (5I–5J)

Source: `reports/aivd_3_39_independent_generations/mock_experiment.json`  
Mode: `full_3_39`. **No `MAX_GENERATIONS=14` / depth target.**

### Normal (FX8 mock doubled-even)

| Seed | Terminal | Firewall | Epoch | Records | Independent | Leak |
|------|----------|----------|-------|---------|-------------|------|
| 0 | VERIFIED | True | 1 | 8 | 5 | False |
| 1 | VERIFIED | True | 1 | 8 | 5 | False |
| 2 | VERIFIED | True | 1 | 8 | 5 | False |

GX8 (odd-double fresh mock): 0/3 VERIFIED under current open pick (earliest even CAT-self preferred) — honest miss; plant retained for isolation ID protocol, not claimed as rediscovery success.

### Controls A–F

| Control | Mode | Terminal | Firewall | Growth | Interpretation |
|---------|------|----------|----------|--------|----------------|
| A normal | `full_3_39` | VERIFIED | True | 1 | Baseline independence path |
| B forced replay | `full_3_39_nofirewall` | VERIFIED | **False** | 1 | Success without independent epoch (not rediscovery credit) |
| C provenance leak | `full_3_39` | VERIFIED | True | 1 | Success path `provenance_leak=False`; unit tests prove recall→leak |
| D evaluator leak | `full_3_39` | VERIFIED | True | 1 | Unit: evaluator origin never independent |
| E deterministic transform | `full_3_39_noopen` | UNRESOLVED | True | 3 | No open CAT-self pick → doubled-even miss |
| F no-growth | `full_3_39_nogrow` | UNRESOLVED | False | 0 | No growth → miss |

**Mock gate: PASS** (FX8 independence records + control matrix behave as designed).

---

## Sacred TinyLlama gate (5K–5L)

**Status: BLOCKED — NOT RUN (environment)**

- Reason: `transformers` not installed; `/workspace/models/tinyllama` absent
- Did **not** install packages to hide failures
- Plants prepared: `LlamaOddDoubleTarget` (S), `LlamaRotateTarget` (U) under `aivd37/unknowns/llama_339.py`
- Runner: `scripts/run_aivd_3_39_llama.py` writes `reports/aivd_3_39_llama/env_gate.json`
- Policy: budget 32, invent_cap 48, no retune, no Level-14 instruction, seeds `(0,1,2,3,4,7,11)`

---

## Residual risks

1. GX8 odd-double is not currently solved by open-ended pick (even CAT-self outranks) — do not claim GX8 sacred-equivalent success.
2. Sacred 3.39 TinyLlama outcomes unknown until HF env present.
3. `firewall_epoch` metadata is now incremented on all modes that call `firewall()` (including `full_3_38`); decision semantics unchanged; `generation_records` remain empty under 3.38.
4. Control E can still arm firewall via compose exhaustion without verifying FX8 — expected.

---

## Parent handoff checklist

- [x] VERSION `3.39.0`
- [x] Branch `research/aivd-3.39-independent-generations`
- [x] 5A–5G implemented; 5H tests green (non-LLM)
- [x] Mock experiment + controls recorded
- [x] Sacred BLOCKED (env) — scripts/docs prepared
- [x] 3.38 sacred artifacts untouched
- [x] Report paths: `reports/aivd_3_39_independent_generations.md`, `.../mock_experiment.json`, `reports/aivd_3_39_llama/`
