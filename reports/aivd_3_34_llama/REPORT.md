# AIVD 3.34 LLAMA PREFIX / ODD — SACRED FIRST RUN

**S pipeline: DISCOVERED not VERIFIED (prefix atom fire @30 / used 32, leftover gates). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (4th atom planning skip). No retune. INVENT_CAP = 48.**

Implementation freeze: `ac0c40d6ee0431c943ce2bb95d7f5926d5386f12`
Pin: `d02cc81f9619532347fc6a9e9e34c601028e8ff5`
Evaluator hashes: S=`07100f55…8689b48b` U=`716a454e…800129e4`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.34 added

3.33 invents atoms after 3.32 operators are exhausted, then skips if
`leftover < 3`. That skip is post-hoc. On TinyLlama 3.33, the pipeline
spent 3 IR + 2 prim + 2 ext and never materialized an atom.

3.34 keeps 3.33 atom invention as the frozen language-growth mechanism.
It adds an in-episode EscalationPlanner that:

- estimates a complete-chain floor (invent 1 + repro 1 + verify 1)
- gives an untried layer one shot if remaining > floor
- escalates when rejected≥2, leftover would starve the floor, leftover
  is tight after one reject, or next-layer EV dominates
- records `ATOM_INVENTION_SKIPPED_BY_PLANNING` instead of inventing an
  unverifiable atom

Did **not** raise `INVENT_CAP`. Did **not** raise the experiment budget.
Did **not** retune 3.33 leftover<3 skip. Did **not** add join-all /
cyclic-shift / append-reversed constructors. Did **not** replay 3.29
frontier A/B/C or 3.33 S/U.

## Architecture

```
scientific question
        │
        ▼
3.29 compiler families (lazy)     ← fast path
        │
        ▼
EscalationPlanner.decide(remaining, current layer)
        │
        ├─ CONTINUE if untried and leftover > floor
        ├─ ESCALATE when EV / reject streak / leftover starve
        └─ STOP if leftover < complete-chain floor
                │
                ▼
3.30 IR → 3.31 prim → 3.32 ext → 3.33 atom
        │
        ▼
invent + execute + reproduce + verify
```

Floor is estimated from in-episode lease cost (1+1+1), not from a
holdout-specific N.

## Plants (fresh, not 3.33)

S: prefix each identity token with its last character (`This` → `sThis`).
Third micro-candidate. 3.33 S was last-char suffix (`This` → `Thiss`).

U: odd-index characters of each token (`This` → `hs`). Fourth
micro-candidate. Mild residuals. Target does **not** set `ontology_gap`.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_33` pipeline | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_34` pipeline** | **7/7** | **0/7** | **0/7** | **0/7** |
| Direct 3.34 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline 3.33: `BUDGET_ALLOCATION_FAILURE`, no atom, used 32/32.

S pipeline 3.34: planner path 2 IR → escalate prim (remaining 7) →
1 zip reject → escalate ext (remaining 6) → 1 affix reject → escalate
atom (remaining 5). Three invented atoms. Prefix
`atom_mapt_cat_at_-1_tok` (`INVENTED_ATOM`) fire @30, secret 7/7,
used 32/32, pipeline gates leftover → not VERIFIED.

S direct 3.34: same prefix atom fire @30, used 32/32, **verified 7/7**.

U pipeline 3.34: same escalation, three atoms materialized (suffix,
even, prefix), leftover 2 → `ATOM_INVENTION_SKIPPED_BY_PLANNING` for
the fourth (odd-chars). Secret 0/7.

U direct: same 4th-atom planning skip. Secret 0/7.

Control 0/7. Cap still 48.

## Mock (not sacred)

BX1 last-char prefix: 3.34 VERIFIED 7/7.
BX8 odd-chars unknown-unknown: 3.34 VERIFIED 7/7.
BX6 after cap, BX10 transfer: 7/7.
BX2 last-char-only (5th micro-candidate): leftover-skips on 3.33 **and**
3.34. The planner reserves one complete chain of 3, not five sequential
atom tries. Skipping 2nd-ext to buy those tries would false-escalate
SX8. 3.34 still escalates off the 3rd IR kind and records a planning
skip rather than inventing an unverifiable atom.
SX1 / NP1 / AX1 still 7/7 on 3.34 (not always-escalate).
alwaysearly ablation: SX1 fails (false escalation).
alwayslate ablation: BX2 starves like 3.33.
BX9 two-atom compose: not verified under 32; documented.

Mock residuals are cheaper, so the 3rd atom still fits under 32.
TinyLlama's longer path invents the 3rd atom at probe 30 and leaves
0 leftover for pipeline gates.

## Q1–Q7

**Q1. Genuine computational novelty?**
Yes at the language layer. `MAPT(CAT(AT:-1, TOK))` is not a 3.32
program and not the 3.33 suffix atom. Direct and pipeline S promote it
as `INVENTED_ATOM`. Adversarial tests still reject `MAP rev` / `duphead`.

**Q2. Executable atom?**
Yes. Pipeline and direct S execute `atom_mapt_cat_at_-1_tok` and fire
the secret. 3.33 pipeline never reached execution.

**Q3. Independent validation?**
Yes before promotion: structural, execution, semantic vs 3.32/3.31
reference outputs, second-probe reproducibility. Unchanged from 3.33.

**Q4. Causal usefulness?**
Direct S: yes (secret 7/7, verified 7/7). Pipeline S: secret 7/7, not
verified (leftover gates). U: 4th atom skipped by planning.

**Q5. Reproducibility?**
All 7 seeds agree per condition. S pipeline fire @30 every seed.
S direct fire @30 every seed. U planning skip every seed.

**Q6. Transfer / reuse?**
Mock transfer (BX10) and independent rediscovery pass as unit tests.
TinyLlama pipeline S fired the invented atom; leftover prevented
pipeline verification so the atom was not retained as a verified
capability.

**Q7. Evaluator leakage?**
`scan_science_source` pass. No 3.34 llama secrets in `aivd/science`.
Discovery never sees evaluator ground truth.

## Failure classification

Pipeline S: secret found, `VERIFICATION_BUDGET_EXHAUSTED` / leftover
gates (failure_class still `ATOM_CAPABILITY_NOT_REPRESENTABLE` from the
invention step). Not `VERIFIED`. Not `SAFE`.

Pipeline U and direct U: `ATOM_INVENTION_SKIPPED_BY_PLANNING` (4th atom).

Pipeline 3.33 S/U: `BUDGET_ALLOCATION_FAILURE` (no atom).

Not a 3.33 leftover-skip retune. Not a budget increase.

## Highest demonstrated autonomy

Mock: budget-aware escalation + 3rd invented atom verified + false-
escalation guard on SX1/NP1.

TinyLlama pipeline: 3.34 escalates early enough to **invent and fire**
the 3rd atom under 32. It does **not** leave enough leftover for
pipeline reproduction+verification. Direct science verifies the same
atom under 32.

Remaining bottleneck: **pipeline gates after a late fire still consume
the last two slots.** The planner reserved a floor of 3 for
invention+repro+verify of *one* atom; reaching the *third* micro-
candidate spends two of those slots on rejected suffix/even atoms.
Do not raise the budget. Do not retune.

3.29 frontier A/B/C not re-scored. Compact micro-language, not unbounded
invention.
