## 3.18.0 — Global Epistemic Budget Arbitration

- Package `aivd/epistemic/`: global arbiter, completion-value scoring (not greedy EIG),
  revocable reservations, soft evidence-driven floor, shadow mode
- Default `epistemic_mode=off` ≈ 3.17; same 32-experiment episode budget
- Allocation benches EA–EF before Holdout-18; sacred X–V untouched

## 3.17.0 — Open-World Behavioral Representation & Generative Experimentation


- Package `aivd/openworld/`: harvest primitives, grammar, generative experiments, protected floor
- Default `openworld_mode=off` ≈ 3.16; skip invent-spam when on
- OW-1..7 before Holdout-V; sacred X–U untouched

## 3.15.0 — Autonomous Signal-to-Intervention Discovery

- Package `aivd/autonomy/` closed-loop OBSERVE→…→VERIFY
- Default `autonomy_mode=off`; integrates cross_signal/joint/invention
- ADD metric 0–9; Holdout-T post-freeze

# Changelog — 3.0.0

### Added
- BehavioralState, LearnedBehaviorEncoder + encoder_train, BehavioralWorldModel
- aivd.rl PPO + ppo explorer; RewardCalculator; counterfactual; critic; lifecycle
- Target profiles A–F; benchmarks suite; CLI scan/train/benchmark/evaluate/verify/visualize/report
- configs/ppo.yaml, ablations.yaml; docs audit/migration/architecture-v3/v3-deliverable

### Changed
- Version 2.0.0 → 3.0.0; BehaviorMap extended without breaking Controller keys
- Default behavior remains hashing encoder + classic explorers (backward compatible)

### Honesty
- No fabricated training gains; latent/PPO superiority across seeds Not demonstrated
