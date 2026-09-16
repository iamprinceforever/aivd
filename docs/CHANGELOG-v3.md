## 3.29.0 — Lazy family inventory; INVENT_CAP unchanged

3.28 could not register a second-wave family on an 11-token seed because
the eager inventor was full (INVENT_CAP=48). 3.29 does **not** raise the
cap. It separates hypothesis-family representation from the executable
registry: revoked leases release slots; a deferred family materializes
one parameterization at a time.

- INVENT_CAP remains 48
- SU hash-field (TOKEN#body, long seed): 3.29 VERIFIED 7/7; 3.28 0/7
- ST/SO/SP/SM/SK still verified
- 3.25–3.28 sacred first-runs untouched
- No `|` / field_124 / cap bump
- Llama hash-field first-run (post-freeze): **DISCOVERED+VERIFIED**.
  3.29 pipeline 7/7 (`field_35_i10` @19, 4 capacity releases).
  3.28 0/7. Direct 7/7. Control 0/7. Cap still 48.

---
## 3.28.0 — Second-wave field delimiters after first-wave revocation

3.27 executed the first leased family. If that family was the wrong
record form, leases exhausted and the search returned to compose.
3.28 compiles unused field delimiters (`field_{ord}_i{k}`) only after
first-wave leases revoke. Not a pipe constructor named for the plant.
Budget 32.

- ST pipe-field: 3.28 VERIFIED 7/7; 3.27 does not find it
- SO/SP/SM/SK still verified. 3.27 first-runs untouched.
- Llama pipe-field first-run (post-freeze): **NOT_DISCOVERED**.
  First-wave leases revoked; INVENT_CAP=48 blocked `field_*` on the
  11-token TinyLlama seed. Do not raise the cap. No retune.

---

## 3.27.0 — Epistemic commitment / first-test lease

3.26 compiled gap-addressing interventions then starved them under familiar
compose (0.94 vs 0.91). 3.27 gives a temporary, revocable lease to the
first few experiments compiled for an unresolved ontology-gap question.
Not a label_nl boost. Not novelty farming (max 3 first-tests; revoke on
noninformative 0.12). Budget 32.

- SO long-seed starvation: 3.27 VERIFIED 7/7
- SP quoted-suffix: 3.27 VERIFIED
- SQ control FP=0
- SM/SK still verified. 3.26 first-runs untouched.
- Llama equals-field + quoted-suffix first-runs (post-freeze):
  3.27 pipeline **VERIFIED 7/7 and 7/7**. 3.26 0/7 both. Control 0/7.
  Lease executed the gap-op (disc 0.5) instead of compose (0.94).
  No label_nl boost. No retune.

---

## 3.26.0 — Empty-harvest structure compiler

3.25 declared an ontology gap then halted because observation harvest was
empty. 3.26 still compiles from the identity prompt: token-as-field-label
(`label_nl_i{k}`) and unused whitespace joiners. Not a newline constructor
for the 3.25 plant. Budget 32.

- SM field-label bench: 3.26 VERIFIED 7/7; 3.25 does not find it
- SN control FP=0
- SK/SH still verified
- 3.25 Llama discourse-split first-run untouched
- Llama field-label first-run (post-freeze): **NOT_DISCOVERED**.
  Compiled `label_nl_i*` after empty harvest; executed 0 (lengthen compose
  ate the budget). Do not raise `label_nl` rank. No retune.

---

## 3.25.0 — Ontology-gap detection; observation-driven rejoin compiler

3.24 could compile a new *instance* of an intra-token family that the
architecture supplied. 3.25 records `KNOWN_INTERVENTIONS_INSUFFICIENT`
and compiles rejoin operators only from characters that appeared in
observations. No dimension library. No newline constructor.

Sacred Llama discourse-split first-run: **NOT_DISCOVERED**. Gap declared;
harvest empty; 0 rejoin ops; never a newline probe. 3.24 also 0/7.
Do not retune. Do not add a newline constructor because of this failure.

---

## 3.24.0 — Intra-token invention after unexplained slot residual

3.23 could discover an unknown *condition* with a known *intervention* (omit).
3.24 compiles identity-preserving intra-token mutations (revchar / caseflip /
duphead) from a hot token index when a token-slot residual is unexplained.
Those ops are not in the cheap battery. Budget stays 32.

- SK bench (caseflip of one long token): pipeline VERIFIED 7/7
- SL control: FP=0
- SH still verified. 3.23 first-runs untouched.
- Llama unknown-dimension first-run (post-freeze): intra-token reversal.
  3.23 pipeline 0/7. 3.24 pipeline **VERIFIED 7/7** via runtime `revchar_i10`.
  Control 0/7. No retune.

---

## 3.23.0 — Collapse does not re-walk failed singles; leftover-aware gates

3.22 found secrets in the pipeline then REJECTED them: collapse-restore
re-ranked the cheap battery at 0.96 over untested invented methods, and
default gates demanded 8 leftover probes.

3.23 keeps the live prompt on collapse, but untested methods stay first.
When leftover is under 8, gates compact to 1 falsify + 1 extra reproduce
(discovery counts) + as many control invariants as remain. Budget stays 32.

- Holdout-24 post-freeze first-run: pipeline **DISCOVERED+VERIFIED 7/7**,
  direct verified 7/7. No retune.
- Holdout-25 post-freeze first-run: pipeline **DISCOVERED+VERIFIED 7/7**,
  direct verified 7/7. Swap-last-two + bracket wrap. No retune.

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
