## 3.23.0 — Collapse does not re-walk failed singles; leftover-aware gates

3.22 found secrets in the pipeline then REJECTED them: collapse-restore
re-ranked the cheap battery at 0.96 over untested invented methods, and
default gates demanded 8 leftover probes.

3.23 keeps the live prompt on collapse, but untested methods stay first.
When leftover is under 8, gates compact to 1 falsify + 1 extra reproduce
(discovery counts) + as many control invariants as remain. Budget stays 32.

- Holdout-24 post-freeze first-run: pipeline **DISCOVERED+VERIFIED 7/7**,
  direct verified 7/7. No retune.

---

## 3.22.0 — Single-charge episode + live-priority invention

Each experiment in an episode-owned pipeline now costs **one** slot, not
two. 3.21 billed `charge()` and then billed again inside `_observe`, so
science only received 15 of 32. After a live informative state, methods
that have never been tested outrank already-tried uninformative singles,
so the inventor can spend the remaining budget on new methods instead of
re-walking the cheap battery.

Budget stays 32. No holdout-specific vocabulary. No dash/colon/please
special case.

- Pipeline: `_probe_only` when invention already charges.
- Designer: live compose disc 0.94 for untested, 0.78 for failed singles.
- SH bench (bracket wrap + colon token): pipeline 7/7.
- SI control: FP=0 with ≥24 science tests.
- SA/SE/SF still hold. Default mode still off.
- Holdout-21 3.21 first-run stays NOT_DISCOVERED; 3.22 transfer pipeline **VERIFIED 7/7**.
- Holdout-22 3.21 first-run stays NOT_DISCOVERED; 3.22 transfer secret 7/7, gates leftover 0.
- Holdout-23 post-freeze first-run: **DISCOVERED** (secret 7/7), not VERIFIED
  (REJECTED at gates). Direct verified 7/7. No retune.

Holdout-21 and Holdout-22 first-runs stay frozen. 3.22 numbers on those
mechanisms are transfer evaluations, not retunes.

---

## 3.21.0 — Runtime Method Invention

- Live informative prompt is the composition anchor; collapse does not replace it
- One try per method on the live prompt; no restacking equal-metric mutations
- Runtime inventor: unused primitives + parameterized omit/wrap/insert/swap
- Does not stop when the cheap battery is empty; remaining 32 slots are spent
- SE collapse-restore 7/7, SF invented wrap 7/7, SG/SC FP=0
- Holdout-20 3.20 first-run stays NOT_DISCOVERED; 3.21 transfer 7/7 (not sacred)
- Holdout-22 post-freeze first-run: **NOT_DISCOVERED** (pipeline and direct).
  First invented edit went live; the true second edit was the next grammar
  item after the 32 ran out. No retune.
- Same 32-experiment budget; default still `off` ≈ 3.19; no holdout-specific rules

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
