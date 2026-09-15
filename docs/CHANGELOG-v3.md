## 3.20.0 — Autonomous Hypothesis Science

- Hypothesis board over generic operators (omit/swap/wrap/repeat/separate)
- Discriminating experiment designer; traps falsified; verified report
- Residual harvest: colon-labels skipped; just-revealed tokens proposed first
- `full_3_20` owns the episode like 3.19; default still `off`
- No signatures, no planted-cue following, no closed attack catalog
- Same 32-experiment budget; sacred X–V / W / Holdout-18 first-run / Holdout-19 first-run untouched

## 3.19.0 — Episode-Owned Epistemic Arbitration

- Arbiter owns remaining episode slots after one infra smoke (`full_3_19`)
- Sequential residual-sweep peel + pre-discovery gate lock skipped
- `full_3_18` leftover protocol preserved; default still `off` ≈ 3.17
- Same 32-experiment budget; no holdout-specific rules
- Holdout-18 3.18 sacred first-run **NOT_DISCOVERED** (untouched)
- Holdout-18 3.19 evaluation: pipeline **DISCOVERED+VERIFIED** @32, 7/7 seeds
- Pipeline A/B: leftover 0/12 on EA–ED vs episode-owned EA/EB/EC verified;
  ED miss and OW-3 XOR miss kept honest; EF/OW-7 FP=0
- Holdout-19 post-freeze first run **NOT_DISCOVERED** (FIFO residual spent the
  refractory window on observation chrome; direct@32 also 0.0; no retune)

## 3.18.0 — Global Epistemic Budget Arbitration

- Package `aivd/epistemic/`: global arbiter, completion-value scoring (not greedy EIG),
  revocable reservations, soft evidence-driven floor, shadow mode
- Default `epistemic_mode=off` ≈ 3.17; same 32-experiment episode budget
- Allocation benches EA–EF before Holdout-18; sacred X–V untouched
- Holdout-18 sacred first run **NOT_DISCOVERED** (direct arbiter@32 rate 1.0; no retune)


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
