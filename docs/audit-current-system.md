# AIVD Current-System Audit (v2.0.0 → pre-v3)

**Date:** 2026-09-13  
**Repo:** `/workspace/aivd`  
**Version audited:** `2.0.0` (`aivd/__init__.py`, `pyproject.toml`)  
**Method:** Full tree map + source review of packages, CLI, configs, tests, reports. No secrets read. No code changes in this phase.

This document describes the **CURRENT** system honestly. It does not claim v3 capabilities.

---

## 1. Repository map

```
aivd/                          # installable package (version 2.0.0)
  __init__.py, __main__.py     # version + CLI (baseline|compare|dashboard)
  agents/                      # Controller, Planner, PromptGenerator
  api/                         # FastAPI dashboard
  behavior/                    # encoder, torch_encoder, map, novelty, uncertainty, clustering
  core/                        # types, config, budgets, audit
  evaluation/                  # security, verifier, impact
  experiments/                 # run_baseline, run_comparison
  explorers/                   # random, corpus, novelty, evolutionary, rl, rl_v2, hybrid
  memory/                      # SQLite ExperimentStore
  metrics/                     # discovery metrics
  reward/                      # compute_reward multi-term formula
  targets/                     # protocol, registry, mock, openai_compat, anthropic, gemini, local_*
  viz/                         # HTML/JSON report helpers
configs/                       # targets.example.yaml only
docs/                          # architecture, methodology, threat-model, reward, metrics, benchmark
tests/                         # core loop, reward, novelty, verifier, mock, torch, v2
scripts/run_comparison.sh
reports/                       # comparison_*_metrics.json, research-results.md
aivd_data/                     # prior comparison run DBs + audit.jsonl
```

**Not present today:** `aivd/rl/` PPO package, `BehavioralState`, `LearnedBehaviorEncoder` training loop wired into Controller, world model, counterfactual evaluator, research critic, Target A–F hidden suite, YAML ablation configs, `scan|train|benchmark|evaluate|verify|visualize|report` CLI surface.

---

## 2. Component inventory (what exists and what it actually does)

### 2.1 Adapters (`aivd/targets`)

| Component | Status | Notes |
|-----------|--------|-------|
| `protocol.py` TargetAdapter | Real interface | |
| `registry.py` allowlist | Real; rejects unknown IDs | |
| `mock.py` MockTarget | **Primary working target** | Hidden GT vulns; explorers never see GT dict for scoring during policy (GT only via `last_ground_truth_hit` offline) |
| `openai_compat.py`, `anthropic.py`, `gemini.py` | Optional live adapters | Need API keys; allowlisted URLs |
| `local_model.py`, `local_stub.py` | Optional / stub | Path or local server; stub for tests |

Offline/mock deterministic mode works (`stochastic=False` supported). Tests default to mock.

### 2.2 Probe generation (`aivd/agents/generators.py`)

- Template bank `STRATEGY_TEMPLATES` (benign, corpus inject/role, encoding, indirect, delimiter, mutation).
- `PromptGenerator.from_strategy` / `mutate` / `crossover`.
- **Not learned.** Fixed strings + light mutations. Latent-trigger fragments appear in `rl_v2` decode heuristics.

### 2.3 Explorers (`aivd/explorers`)

| Name | Mechanism | Learning? |
|------|-----------|-----------|
| `random` | Uniform strategies/templates | No |
| `corpus` | Fixed corpus prompts | No (regression baseline) |
| `novelty` | Maximize NN distance in embedding space | Heuristic archive search |
| `evolutionary` | Mutate/crossover; fitness = AIVD reward | Population search |
| `rl` | Softmax REINFORCE over discrete strategies | Online bandit-style; **baseline** |
| `rl_v2` | Continuous action → MLP → REINFORCE + EMA baseline + visit bins | Online REINFORCE; **not PPO**; weights do update (tests assert) |
| `hybrid` | RL candidates + novel-family inject; pick by novelty | Uses `rl` updater |

All share Controller loop + `compute_reward`. Keep as **baselines** for v3.

### 2.4 RL today

- No `aivd/rl/` package.
- No PPO (policy/value/trajectory buffer).
- `rl_v2` is the deepest learner: small Torch MLP, continuous actions decoded to templates/encodings.
- Explore vs exploit: `rl_v2` uses visit-bin novelty bias among 3 samples; **not** an explicit learned explore/exploit mode.

### 2.5 Reward (`aivd/reward/formula.py`)

Working multi-term formula with novelty gated by security relevance + optional `w_cost`.

**Honesty on “information gain”:** Controller sets  
`ig = novelty * max(security_score, 0.05)` — a **heuristic**, not predictive world-model uncertainty reduction.

Components logged in `RewardBreakdown`; no separate `RewardCalculator` class; no reward-hacking detector (reward↑ while IG/security flat).

### 2.6 Encoder (`aivd/behavior`)

| Class | Role | Trained? |
|-------|------|----------|
| `BehaviorEncoder` | Feature hashing + keyword overlays | N/A (deterministic hash) — **working default** |
| `TorchBehaviorEncoder` | Hash → random-init MLP projector | **Has** `contrastive_step` API; **never called** by Controller or experiment runners. At default use = **untrained random projector**. Do **not** call this “learned.” |
| `make_encoder(backend)` | `hashing` \| `torch` | Config default `hashing` |

No `HashBehaviorEncoder` alias yet (name is `BehaviorEncoder`). No multi-loss training framework (contrastive + temporal + reconstruction + security-rep).

### 2.7 Behavior map (`map.py` + helpers)

- Archive of embeddings; KMeans regions; NN novelty; redundancy; cluster-label entropy as “uncertainty.”
- Coverage = unique regions / `estimated_reachable_regions` (config heuristic, default 16).
- **Missing vs v3 ask:** trajectories, density models, explicit unexplored-region proposals, typed `BehavioralState`.

### 2.8 Evaluator / verifier / impact

- `SecurityEvaluator`: keyword / mock-token heuristics (`SECRET{...}`, `DISALLOWED:`, override phrases). Fast and offline; **not** an independent model judge.
- `Verifier`: same evaluator on prompt variations; thresholds for confirmed/reproduced/unresolved. Stronger than v1 but **not fully independent** (shares evaluator; same target probe_fn).
- `impact.assess_impact`: simple signal bonuses.
- No counterfactual evaluator; no research critic that can disagree; finding lifecycle enums are basic (`FindingStatus`), not the richer v3 lifecycle (known vuln / suspicious novel / independently verified, etc.).

### 2.9 Storage / audit / metrics / viz / API

- SQLite `ExperimentStore`; JSONL `AuditLog`.
- Metrics: DiscoveryEfficiency, ExplorationCoverage, CorpusEscapeRate, FPR, ReproRate, etc.
- FastAPI dashboard + HTML comparison reports.
- Reports under `reports/` from prior mock runs (incl. `research-results.md`).

### 2.10 CLI / config

- CLI: `baseline`, `compare`, `dashboard` only.
- Config: in-code `AIVDConfig` / `RewardWeights`; one `configs/targets.example.yaml`.
- No PPO/ablation YAMLs; no `world_model` flag.

### 2.11 Tests & benchmarks

- Tests: `test_core_loop`, `test_reward`, `test_novelty_behavior`, `test_verifier_budgets`, `test_mock_and_adapters`, `test_torch_encoder` (encode smoke only — **does not** prove training), `test_v2` (rl_v2 weight change, latent triggers, FP stress, providers mocked).
- Benchmark: single `mock://default` with corpus / novel / latent vulns. **No** Target A–F suite profiles.

---

## 3. Dead / underused / mock-only / “learned but untrained”

### Dead or nearly unused

| Item | Finding |
|------|---------|
| `Planner` | Exported; **Controller does not call it**. Explorers generate prompts directly. Hierarchical story in README is partially aspirational. |
| `TorchBehaviorEncoder.contrastive_step` | Implemented; **never wired** into run loop or CLI train command. |
| Docker Postgres/Redis | Compose present; app defaults to SQLite. Production path **not demonstrated**. |

### Mock-only / heuristic science

| Item | Finding |
|------|---------|
| Mock GT vulns | Appropriate for offline metrics; latent `HV-LATENT-*` exist and unit-test trigger, but **comparison report shows no latent GT hits** under budget 40 — discovery of latents = **Not demonstrated** at that budget. |
| Security evaluator | Keyword/token based; fails silently on “security-relevant without obvious keywords” (no such mock profile yet). |
| Bizarre-but-benign | Helper list + tests; not a full adversarial evaluator suite. |

### Called “learned” but untrained / not PPO

| Item | Honest label |
|------|----------------|
| Default `BehaviorEncoder` | Hashing — **not learned** (correct). |
| `TorchBehaviorEncoder` without training | **Untrained random projector** — must not be called learned until weights change from a real training procedure. |
| `rl` / `rl_v2` | Online REINFORCE updates **do** change weights (demonstrated in tests). Still **not** PPO; policy is not conditioned on a rich `BehavioralState`. |
| Information gain / uncertainty | Heuristic / cluster entropy — **not** world-model predictive uncertainty. |

### Interfaces that should become abstractions (v3)

1. Encoder protocol: `HashBehaviorEncoder` \| `LearnedBehaviorEncoder`.
2. Typed `BehavioralState` (not ad-hoc dict context).
3. Explorer / policy consuming state tensors; modular action space.
4. Optional `BehavioralWorldModel` behind config.
5. `RewardCalculator` logging all terms + hacking flags.
6. Independent verification + critic + richer finding lifecycle.
7. Hidden multi-profile benchmark suite with GT sealed from discovery policy.

---

## 4. Data flow (current Controller)

```
Explorer.next_prompt(ctx={archive_matrix, coverage})
  → TargetAdapter.probe
  → BehaviorMap.add(response)  # encode, novelty, cluster, entropy
  → SecurityEvaluator.evaluate
  → Verifier.verify (same evaluator, variant probes)
  → assess_impact
  → compute_reward (IG heuristic)
  → Explorer.observe(reward.total)
  → ExperimentStore + AuditLog
```

Preserving this loop while adding optional modules is the migration constraint.

---

## 5. What works today (keep as baselines)

- Full offline mock loop; `pytest` suite for v2.
- Seven comparable explorers under one reward/verifier/metrics.
- Allowlist + budgets + audit.
- Honest language in README/reports (candidate / confirmed / unresolved; no zero-day claims).
- CorpusEscapeRate and unique-GT DiscoveryEfficiency definitions.
- Multi-seed comparison runner.

---

## 6. Gaps vs user phases 2–10 (summary)

| Phase theme | Current gap |
|-------------|-------------|
| BehavioralState + richer BehaviorMap | No typed state; no trajectories/density/unexplored proposals |
| Trainable LearnedBehaviorEncoder | Torch path untrained in practice; no multi-loss trainer |
| World model + uncertainty | Absent |
| PPO state-conditioned RL | Absent (`rl`/`rl_v2` baselines only) |
| Multi-objective reward extensions | Partial; no IG from WM; no hacking metrics |
| Counterfactual evaluator | Absent |
| Independent verify + critic + lifecycle | Partial verifier; no critic; thin statuses |
| Hidden Target A–F suite | Single mock profile |
| CLI / configs / viz / ablations / canonical experiment | Thin CLI; one example YAML |

---

## 7. Audit conclusion

AIVD v2 is a **working research control loop** with solid mock science and several real online learners (`rl`, `rl_v2`). It is **not** yet a trained behavioral world-model + PPO platform. The torch encoder and hierarchical planner are the main places where docs/architecture language can oversell reality. Upgrade must be **incremental beside baselines**, with tests green after each phase, and with “Not demonstrated” where training or discovery gains are unproven.
