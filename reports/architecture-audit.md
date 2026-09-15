# AIVD Architecture Audit (v3.0.0 → 3.1.0)

**Date:** 2026-09-13  
**Repo:** `/workspace/aivd`  
**Method:** Full tree + source review. No secrets read. Labels are honest.

This audit maps what **already exists** in v3 and what remaining gaps 3.1 fills.
Prior docs skimmed: `docs/audit-current-system.md`, `docs/architecture-v3.md`,
`reports/llama_planted_vuln/*`, `reports/llama_opensource/*`.

---

## 1. Component map (labels)

Labels: **learned** | **heuristic** | **rule** | **untrained** | **mock-only** | **real-model** | **incomplete**

### Adapters (`aivd/targets`)

| Component | Label | Notes |
|-----------|-------|-------|
| `protocol.py` | rule | Interface |
| `registry.py` | rule | Allowlist gate |
| `mock.py` MockTarget + profiles A–F | mock-only | Hidden GT for offline metrics |
| `openai_compat.py` | real-model | Ollama / OpenAI-compat; allowlisted URLs incl. `:11434`, `:18080` |
| `local_model.py` | real-model | Path or local server |
| `local_stub.py` | mock-only | Tests |
| `anthropic.py` / `gemini.py` | real-model | Need keys; allowlisted |
| Planted proxy `scripts/planted_llama_proxy.py` | mock-only + real-model | Planted triggers in proxy; else forwards to Ollama. **≠ stock Llama weights** |

### Ollama

| Piece | Label |
|-------|-------|
| OpenAI-compat via `http://127.0.0.1:11434/v1` | real-model |
| Open-source scan script | real-model (heuristic analyzer) |
| Planted proxy upstream | real-model on miss; planted on hit |

### Explorers (baselines — preserve)

| Name | Label |
|------|-------|
| random | heuristic |
| corpus | rule (regression) |
| novelty | heuristic archive search |
| evolutionary | heuristic population |
| rl | learned (online REINFORCE bandit) |
| rl_v2 | learned (MLP + REINFORCE + EMA) |
| hybrid | heuristic + learned (uses rl updater) |
| ppo | learned (small ActorCritic; CPU prototype) |

### Reward

| Piece | Label |
|-------|-------|
| `formula.compute_reward` | heuristic multi-term |
| `RewardCalculator` | heuristic + optional WM IG / hacking flag |
| Information gain default | heuristic (`novelty * max(sec, 0.05)`) |
| WM IG | incomplete / prototype when `world_model=true` |

### Encoders

| Piece | Label | Training status |
|-------|-------|-----------------|
| `BehaviorEncoder` / Hash | rule (hashing) | N/A |
| `TorchBehaviorEncoder` | **untrained** by default | `contrastive_step` exists; Controller does **not** call it in normal scan. Treat as **untrained random projector** unless `aivd train` / explicit steps ran. |
| `LearnedBehaviorEncoder` | **untrained** until `trained_steps>0` | Multi-loss trainer in `encoder_train.py`; CLI `train` exists. Default embedding_backend=`hashing`. |

### Behavior map / state / world model

| Piece | Label |
|-------|-------|
| `BehavioralState` | rule (typed dataclass) — **exists v3** |
| `BehaviorMap` | heuristic (KMeans, NN novelty, density, unexplored hints) |
| `BehavioralWorldModel` | incomplete / prototype (ensemble; config-gated) |
| Uncertainty | heuristic (cluster entropy) unless WM on |

### Evaluators / verification / lifecycle

| Piece | Label |
|-------|-------|
| `SecurityEvaluator` | heuristic (SECRET/DISALLOWED/override keywords) |
| `RealModelSecurityAnalyzer` (3.1) | heuristic semantic + claim/effect taxonomy |
| `Verifier` | heuristic (independent instance, same family) |
| `CounterfactualEvaluator` | heuristic / incomplete |
| `ResearchCritic` | heuristic |
| `lifecycle.assign_lifecycle` | rule (v3 statuses) |
| Lifecycle FSM OBSERVATION→…→VERIFIED (3.1) | rule — extended enforcement |

### Metrics

| Piece | Pre-3.1 | 3.1 |
|-------|---------|-----|
| DiscoveryEfficiency | unique confirmed GT / n | kept |
| CorpusEscapeRate | escape confirmed GT / confirmed GT | **documented + helpers** |
| confirmation_events vs unique_vulns | **conflated** | **separated** |
| trigger_diversity / families | missing | **added** |
| novel/overall coverage, NDE | partial | **added** |
| anomalies/candidates/reproduced/verified counts | partial via status_counts | **explicit** |

### Planted infra

| Piece | Label |
|-------|-------|
| PV-DELIM + PV-RARE-CANARY | mock-only planted (proxy) |
| Difficulty tiers (3.1) | mock-only planted + offline GT |
| Explorers importing GT | **forbidden** (preserved) |

### CLI / tests / config

| Piece | Label |
|-------|-------|
| CLI baseline/compare/dashboard/scan/train/benchmark/… | real |
| configs default_v3, ppo, ablations | real |
| `configs/research_eval.yaml` (3.1) | multi-seed/budget |
| pytest suite | real; mock-first |

---

## 2. Strengths

- Working offline mock loop; all 8 explorers comparable under one Controller.
- Honest language already in README/planted/opensource reports.
- Planted proxy correctly separates proxy backdoors from stock Llama.
- Ollama adapters allowlisted; offline/mock path intact.
- v3 BehavioralState / LearnedEncoder / WM / PPO / critic / counterfactual present — extend, don’t rewrite.

## 3. Weaknesses / debt (pre-3.1)

1. Metrics conflated confirmation **events** with unique vulnerabilities.
2. Keyword-only security evaluator on real models → textual claims look like vulns (TinyLlama `policies_disabled` anomaly).
3. Lifecycle rich statuses exist but linear OBSERVATION→…→VERIFIED not enforced as FSM.
4. Planted suite only 2 vulns; no difficulty tiers.
5. Torch/Learned encoders easy to oversell as “learned” while untrained.
6. Multi-seed / budget-sweep planted curves not demonstrated at matrix scale.
7. Open-source README lacked anomalies/candidates/verified/unique columns.

## 4. Migration plan (remaining gaps → 3.1)

| Gap | Action |
|-----|--------|
| A Metrics | `aivd/metrics/` helpers + tests; extend `compute_metrics` |
| B RealModel analyzer | New module; config flag `use_real_model_analyzer` |
| C Lifecycle FSM | Extend `lifecycle.py`; map classic statuses |
| D Planted tiers | Expand proxy + offline GT; analysis script |
| E TinyLlama regression | Test + `reports/tinyllama_anomaly_regression.md` |
| F Multi-seed / budget | Scripts + reports under `planted_multiseed/` / `planted_budget_sweep/` |
| G Reporting | Upgrade READMEs + `research-results.md`; version 3.1.0 |
| H Tests | Unit tests; keep `pytest -q` green |
| I Config | `configs/research_eval.yaml` |

**Do not:** delete explorers, fake scores, claim stock Llama backdoors, tune rare canary to force success.

## 5. TorchBehaviorEncoder — honest status

- API: `encode`, `contrastive_step`.
- Default Controller path: **hashing** backend.
- When `embedding_backend=torch` without training: **untrained random projector**.
- `LearnedBehaviorEncoder.is_trained` tracks steps; untrained until `train` / `train_step`.
- Calling either “learned” without `trained_steps>0` (or documented contrastive updates) is **incorrect**.
