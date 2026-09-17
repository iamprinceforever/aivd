## 3.35.0 — End-to-end invention→verification efficiency

3.34 can invent an atom before the budget is exhausted, then still
fail pipeline verification because leftover=2 at the gates pays
falsify+reproduce and starves the invariant. 3.35 keeps 3.34
escalation as the frozen planner (dynamic=False, floor=3) and adds
an evidence ledger, class-aware atom ranking, a capped dynamic
floor, and compact leftover=2 invariant reuse of already-paid
negatives. Independent falsify and reproduction still run.
Discovery cannot substitute for reproduction. INVENT_CAP stays 48.
Budget 32. Do not retune 3.34 leftover<3 invent skip. No
target-specific operators. Compact micro-language, not unbounded
invention.

- EvidenceLedger: one experiment is one experiment. Search negatives
  and controls may satisfy an invariant; a secret firing may not.
- rank_atoms: untried semantic class outranks a class that already
  failed. Frozen proposal order is the tie-break. greedy ablation
  keeps original order.
- dynamic_floor: expected extra atom tries capped at +2 (floor 5
  when untried). 3.34 planner remains bit-identical (dynamic=False).
- Compact leftover=2 gates: reuse already-paid smoke/ledger negative
  as invariant. leftover=3 still pays a new invariant probe.
- CX1 last-char-only (5th proposal, 3rd under class ranking) vs
  3.34 leftover-skip of the same atom as 5th.
- CX8 first+last is still glue-class (7th); leftover-skip is an
  honest expensive-path outcome, not a retune target.
- SX1/NP1/AX1/BX1 still 7/7 on 3.35 (not always-escalate).
- leftover<3 still skips new atom invention (3.33/3.34 immutable).
- Llama last-char-only / first+last first-run is post-freeze.

---

---
## 3.34.0 — Budget-aware adaptive escalation

3.33 invents atoms after 3.32 is exhausted, then skips if leftover < 3.
That skip is post-hoc. 3.34 keeps 3.33 atom invention as the frozen
language-growth mechanism and adds backward budget planning: reserve a
complete chain (invent + reproduce + verify) before spending the next
experiment on a layer whose expected value is collapsing. INVENT_CAP
stays 48. Budget 32. Do not retune 3.33 leftover<3 skip. No target-
specific operators. Compact micro-language, not unbounded invention.

- EscalationPlanner: CONTINUE / escalate to IR, primitive, substrate,
  atom / STOP_AND_PRESERVE_VERIFICATION_BUDGET
- Untried layer gets one shot if remaining > floor (false-escalation
  guard). rejected≥2, leftover starve, or tight leftover after one
  reject escalates. Layer EV from in-episode evidence only.
- BX1 last-char prefix (3rd micro-candidate) and BX8 odd-chars mock
- BX2 last-char-only (5th atom): leftover-skips on 3.33 and 3.34;
  3.34 escalates off the 3rd IR and records a planning skip rather
  than inventing an unverifiable atom. One reserved chain is 3, not 5.
- SX1/NP1/AX1 still 7/7 on 3.34 (not always-escalate)
- alwaysearly ablation false-escalates SX1; alwayslate starves BX2
- 3.33 leftover skip remains BUDGET_ALLOCATION_FAILURE
- Llama last-char-prefix / odd-chars first-run (post-freeze `ac0c40d`):
  S pipeline **secret 7/7**, **verified 0/7** (prefix atom
  `atom_mapt_cat_at_-1_tok` fire @30 / used 32, leftover gates).
  S direct **DISCOVERED+VERIFIED 7/7** @30. 3.33 pipeline 0/7 both
  (`BUDGET_ALLOCATION_FAILURE`, no atom). U pipeline and direct 0/7
  (4th atom `ATOM_INVENTION_SKIPPED_BY_PLANNING`). Control 0/7. Cap 48.
  Planner path: 2 IR → 1 prim → 1 ext → 3 atoms. Not a 3.33 retune.
  Compact micro-language, not unbounded invention. Do not raise 32.

---

---
## 3.33.0 — Atom invention + open-ended experiment-language growth

3.32 synthesizes operators from a developer-defined atom catalog. That
catalog was the remaining language boundary. 3.33 keeps 3.32 as the
fast path and, after those operators fail, invents a genuinely new atom
from a lower-level character/index micro-language (TOK / AT / SLICE /
CAT / REV / MAPT). The atom is validated, leased, lazy, and added to
an evolving language L_t. INVENT_CAP stays 48. Budget 32. leftover<3
skips new atom invention (addresses 3.32 U without retuning it). No
join-all / cyclic-shift / append-reversed constructors. The 3.32 atom
catalog is not expanded.

- AX1 last-char suffix: 3.33 VERIFIED 7/7; 3.32 0/7
- AX8 even-chars (unknown-unknown), AX6 after cap: 7/7
- NP1 zip and SX1 affix still 7/7 on 3.33 (3.32 fast path)
- SU still verified. 3.25–3.32 sacred first-runs untouched
- Compact micro-language, not unbounded invention. 3.29 frontier A/B/C not re-scored.
- leftover<3 → BUDGET_ALLOCATION_FAILURE for new atoms only. Do not retune 3.32 U.
- Llama last-char-suffix + even-chars first-run (post-freeze `468994e`):
  S pipeline **NOT_DISCOVERED** 0/7 (`BUDGET_ALLOCATION_FAILURE`, leftover<3
  skip, no atom). S direct **DISCOVERED+VERIFIED** 7/7 via
  `atom_mapt_cat_tok_at_-1` @30 used 32. U pipeline and direct 0/7
  (second atom skipped). 3.32 0/7 both. Control 0/7. Cap still 48.
  Compact micro-language, not unbounded invention. Do not retune.
  3.29 frontier A/B/C not re-scored.

---
## 3.32.0 — Runtime substrate-operator synthesis

3.31 synthesized primitives from a developer-provided combinator set.
That combinator set was the remaining language boundary. 3.32 keeps
3.31 as the fast path and, after those primitives fail, synthesizes an
executable operator from a lower-level meta-language (GET / RANGE /
STRIDE / CAT / GLUE / FOLD / MAP). The operator is validated, leased,
lazy, and reusable. INVENT_CAP stays 48. Budget 32. No join-all /
cyclic-shift / append-reversed constructors.

- SX1 cross-token affix: 3.32 VERIFIED 7/7; 3.31 0/7
- SX8 strided gather (unknown-unknown), SX9 fold-of-stride, SX10 n-ary fold, SX6 after cap: 7/7
- NP1 zip and OW1 swap-ends still 7/7 on 3.32
- SU still verified. 3.25–3.31 sacred first-runs untouched
- Compact meta-language, not unbounded invention. 3.29 frontier A/B/C not re-scored.
- Llama cross-token affix + even-odd gather first-run (post-freeze `8607b48`):
  S **DISCOVERED+VERIFIED** 7/7. U secret 7/7, pipeline verified 0/7 (gates
  REJECTED at fire @30 / used 32). Direct U 7/7. 3.31 0/7 both. Control 0/7.
  Cap still 48.
  S: `ext_map_glue_get_0_cur` (NEW_SUBSTRATE_CAPABILITY) fire @29, used 32/32.
  U: affix rejected, then `ext_cat_stride_0_2_stride_1_2` fire @30, secret
  found, leftover gates REJECTED. No target `ontology_gap` flag on U.
  Compact meta-language, not unbounded invention. Do not retune U. 3.29
  frontier A/B/C not re-scored.

---
## 3.31.0 — Self-extending experiment language (primitive synthesis)

3.30 removed the compiler-family boundary; the compact IR then became
the experiment-language boundary. 3.31 keeps 3.30 as the fast path and
adds a question-directed primitive synthesizer over a bounded token-
sequence substrate (MAP / ZIP / PAIR_JOIN / WIN_SWAP / SLICE). New
primitives are executable, leased, lazy, and reusable. INVENT_CAP stays
48. Budget 32. No join-all / cyclic-shift / append-reversed constructors.

- NP1 zip-stutter: 3.31 VERIFIED 7/7; 3.30 0/7
- NP4 zip-then-pair composition, NP5 continuation, NP6 after cap, NP7 unknown-unknown: 7/7
- OW1/OW2 (3.30 programs/families) still 7/7 on 3.31
- SU still verified. 3.25–3.30 sacred first-runs untouched
- Llama zip-stutter + pair-join first-run (post-freeze `3ad5d9d`):
  **DISCOVERED+VERIFIED**. Pipeline 7/7 and 7/7. 3.30 0/7 both. 3.29 0/7.
  Direct 7/7. Control 0/7. Cap still 48.
  S: `p_zip` (NEW_PRIMITIVE / ZIP) fire @27, used 32/32.
  U: `p_zip` rejected, then `p_pairjoin` (NEW_PRIMITIVE / PAIR_JOIN)
  fire @28, used 32/32. No target `ontology_gap` flag on U.
  Compact substrate, not unbounded invention. 3.29 frontier A/B/C not re-scored.

---
## 3.30.0 — Open-world intervention IR synthesis

The 3.29 compiler was the experiment language. 3.30 keeps that compiler
as the fast path and adds a question-directed IR synthesizer (SWAP any
indices, MOVE, WRAP_EACH) only after known leases fail to distinguish.
INVENT_CAP stays 48. Budget 32. No JOIN_ALL / CYCLIC_SHIFT / APPEND_REVERSED
constructors.

- OW1 swap-ends, OW2 wrap-each, OW3 move-last, OW5 continuation, OW6 after cap: 7/7
- 3.29 cannot find OW1
- SU/ST/SO still verified on 3.30
- 3.25–3.29 sacred first-runs untouched
- Llama swap-ends + wrap-each first-run (post-freeze `56ca5fe`):
  **DISCOVERED+VERIFIED**. Pipeline 7/7 and 7/7. 3.29 0/7 both.
  Direct 7/7. Control 0/7. Cap still 48.
  S: `syn_swap_0_10` (NOVEL_PROGRAM) fire @21, used 29/32.
  U: SWAP and MOVE rejected, then `syn_wrap_each_[_]_4` (NOVEL_FAMILY)
  fire @23, used 31/32. No target `ontology_gap` flag on U.
  Compact IR, not unbounded invention. 3.29 frontier A/B/C not re-scored.

---
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
