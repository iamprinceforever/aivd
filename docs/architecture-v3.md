# AIVD Architecture v3 (as implemented)

```
Controller (config-gated options)
   ├── Explorer: baselines (random|corpus|novelty|evolutionary|rl|rl_v2|hybrid)
   │              + ppo (state-conditioned ActorCritic)
   ├── TargetAdapter allowlist (mock, profiles A–F, optional live APIs)
   ├── Encoder: HashBehaviorEncoder (default) | torch | LearnedBehaviorEncoder
   ├── BehaviorMap → BehavioralState (z, region, novelty, density, traj, unexplored)
   ├── BehavioralWorldModel? (ensemble dynamics + variance uncertainty)
   ├── SecurityEvaluator → Verifier (independent instance) → Impact
   ├── CounterfactualEvaluator? → ResearchCritic? → lifecycle mapping
   ├── RewardCalculator → compute_reward (+ optional WM IG, hacking flag)
   └── Memory SQLite + Audit JSONL
```

## New packages / modules

| Path | Role |
|------|------|
| `aivd/behavior/state.py` | Typed `BehavioralState` |
| `aivd/behavior/learned_encoder.py` | Trainable MLP encoder |
| `aivd/behavior/encoder_train.py` | Multi-loss training (λ weights) |
| `aivd/behavior/world_model.py` | Ensemble next-z predictor |
| `aivd/rl/` | PPO: policy, buffer, loop |
| `aivd/explorers/ppo_explorer.py` | PPO explorer + `BaselineRLExplorer` alias |
| `aivd/reward/calculator.py` | Component logging + hacking flag |
| `aivd/evaluation/counterfactual.py` | Counterfactual evidence score |
| `aivd/evaluation/critic.py` | Research critic (can disagree) |
| `aivd/evaluation/lifecycle.py` | Richer finding lifecycle |
| `aivd/targets/profiles.py` | Target A–F profiles |
| `aivd/benchmarks/suite.py` | Hidden suite runner |
| `aivd/viz/pca_viz.py` | PCA for viz only |
| `configs/*.yaml` | PPO / ablations / default_v3 |
| `scripts/canonical_experiment_v3.py` | Canonical offline experiment |

## Config flags (defaults preserve v2 behavior)

- `embedding_backend: hashing|torch|learned` (default hashing)
- `world_model: false`
- `use_counterfactual: false`
- `use_critic: false`

## CLI

`aivd baseline|compare|dashboard|scan|train|benchmark|evaluate|verify|visualize|report`

## Honesty

Untrained `LearnedBehaviorEncoder` is a random-init projector until `train` / `train_step`. PPO and world model are small CPU prototypes. Mock science ≠ production discovery.
