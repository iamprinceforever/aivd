# AIVD 3.35 LLAMA LAST / ENDS — SACRED FIRST RUN

**S pipeline: DISCOVERED+VERIFIED 7/7 (last-char-only atom `atom_mapt_at_-1` fire @29 / used 32). S direct: DISCOVERED+VERIFIED 7/7. U pipeline and direct: NOT_DISCOVERED (first+last leftover-skip after 4th atom). No retune. INVENT_CAP = 48.**

Implementation freeze: `97b856bc55a14256b2f5e2c18b6218ffe877c11b`
Pin: `affb4cc4cb824672c385fd5195fcb5fd6593f831`
Evaluator hashes: S=`b54e1598…aa3d3434` U=`9689b1fe…b0dc1c7e`
Micro-language hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`

## What 3.35 added

3.34 invents an atom before the budget is exhausted, then can still
miss pipeline verification: leftover=2 at the gates pays falsify +
reproduce and starves the invariant. On TinyLlama 3.34, last-char
prefix fired at probe 30 and the pipeline never reached VERIFIED.

3.35 keeps 3.34 escalation as the frozen planner (`dynamic=False`,
floor=3 on 3.34 mode). It adds:

- an evidence ledger (one experiment is one experiment; discovery
  cannot substitute for reproduction)
- class-aware atom ranking (untried semantic class outranks a class
  that already failed; frozen proposal order is the tie-break)
- a capped dynamic floor (expected extra atom tries +2, not
  "reserve 5 for invention")
- compact leftover=2 invariant reuse of an already-paid independent
  negative. leftover=3 still pays a new invariant probe.

Did **not** raise `INVENT_CAP`. Did **not** raise the experiment budget.
Did **not** retune 3.34 leftover<3 invent skip. Did **not** add join-all /
cyclic-shift / append-reversed constructors. Did **not** replay 3.29
frontier A/B/C or 3.33/3.34 S/U. Did **not** convert a secret firing
into VERIFIED.

## Architecture

```
scientific question
        │
        ▼
3.29 families → 3.30 IR → 3.31 prim → 3.32 ext → 3.33 atom
        │
        ▼
3.34 EscalationPlanner (dynamic floor when 3.35)
        │
        ▼
rank remaining atoms by expected verified value
        │
        ▼
invent + execute
        │
        ▼
falsify + independent reproduce
        │
        ▼
invariant: new probe if leftover≥3, else reuse already-paid negative
        │
        ▼
VERIFIED  or  DISCOVERED without verification
```

## Plants (fresh, not 3.33 / 3.34)

S: last character of each identity token (`This` → `s`). Fifth
micro-candidate in frozen proposal order; third under class ranking
after glue and stride reject. 3.34 S was last-char prefix
(`This` → `sThis`). 3.33 S was last-char suffix (`This` → `Thiss`).

U: first+last characters of each token (`This` → `Ts`). Seventh
micro-candidate, same `char_index_glue` class as suffix/prefix.
Ranking does not promote it after a glue reject. Mild residuals.
Target does **not** set `ontology_gap`.

Existing-space oracle (3.29 compiler + 2-op battery): cannot fire either.
Private `evaluator_verify`: PASS. Control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | S secret | S verified | U secret | U verified |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0/7 | 0/7 |
| `full_3_34` pipeline | 0/7 | 0/7 | 0/7 | 0/7 |
| **`full_3_35` pipeline** | **7/7** | **7/7** | **0/7** | **0/7** |
| Direct 3.35 | 7/7 | 7/7 | 0/7 | 0/7 |
| Control | 0/7 | 0/7 | 0/7 | 0/7 |

S pipeline 3.34: `ATOM_INVENTION_SKIPPED_BY_PLANNING`. Last-char-only
is the 5th proposal. One reserved chain of 3 cannot buy five atom
tries. Secret 0/7, used 32/32.

S pipeline 3.35: planner path 1 IR (dynamic floor 5, escalate at
remaining 8) → 1 prim → 1 ext → 3 atoms. Class ranking after glue
reject then stride reject promotes `atom_mapt_at_-1` (`char_project`,
`INVENTED_ATOM`) to the 3rd executed atom. Fire @29, secret 7/7,
used 32/32, leftover=3 at the gates so falsify + reproduce +
invariant all run. **VERIFIED 7/7.** Ledger `reused=0` (no leftover=2
shortcut needed on this plant). Capacity releases 11.

S direct 3.35: same last-only atom fire @29, used 31/32, **verified 7/7**.

U pipeline 3.35: same ranking through last-only (3rd) and prefix
(4th), leftover 2 → `ATOM_INVENTION_SKIPPED_BY_PLANNING` before
first+last (7th, glue class). Secret 0/7. Direct same skip. Honest
expensive-path miss. Do not retune.

Control 0/7. Cap still 48.

## Mock (not sacred)

CX1 last-char-only: 3.35 VERIFIED 7/7; 3.34 0/7 (5th leftover-skip).
CX6 after cap, CX10 transfer: 7/7.
leftover=2 gates (synthetic late fire): 3.35 VERIFIED via smoke
reuse; 3.34 REJECTED (`invariant_failed`); `nocompress` REJECTED.
SX1 / NP1 / AX1 / BX1 still 7/7 on 3.35 (not always-escalate).
greedy ablation: CX1 fails (original proposal order, 5th skip).
alwaysearly ablation: SX1 fails (false escalation).
CX8 first+last / CX9 two-atom compose: not verified under 32; documented.
leftover<3 still skips new atom invention (3.33/3.34 immutable).

## Which efficiency fit the lifecycle in 32

On this sacred S plant, two complementary cuts:

1. **Class ranking** (necessary). Without it, last-only stays 5th and
   leftover-skips, as 3.34 0/7 shows.
2. **Dynamic floor** (enough leftover at the gates). Skipping the 2nd
   IR fires the 3rd atom at 29 instead of 30. leftover=3 pays a real
   invariant probe. leftover=2 reuse is the safety net, exercised on
   mock, unused here (`reused=0`).

Neither cut raised the budget or the cap. Independent falsify and
reproduction still ran.

## Q1–Q7

**Q1. Genuine computational novelty?**
Yes at the language layer. `MAPT(AT:-1)` is not a 3.32 program and
not the 3.33 suffix atom or the 3.34 prefix atom. Direct and pipeline
S promote it as `INVENTED_ATOM`. Adversarial tests still reject a
renamed duplicate of the same body.

**Q2. Question-directed, not catalog farming?**
Yes. Invention is gated on unresolved questions after 3.32 operators
fail. Ranking uses in-episode rejected semantic classes, not evaluator
GT. Frozen proposal order is unchanged; ranking only reorders remaining
candidates after a class reject.

**Q3. Independent reproduction and verification?**
Yes. Pipeline S is VERIFIED, not merely DISCOVERED. Falsify, reproduce,
and a paid invariant probe all ran (leftover=3). Discovery cannot
substitute for reproduction (ledger `cannot_substitute_for`). leftover=2
reuse, when used, reuses an already-paid *negative*, never the secret.

**Q4. False escalation contained?**
Yes. SX1 / NP1 / AX1 / BX1 still 7/7 on 3.35. `alwaysearly` still
false-escalates SX1. 3.34 mode planner remains `dynamic=False`, floor=3.

**Q5. Unknown-unknown / expensive path honest?**
U first+last is glue-class, 7th proposal. Ranking does not promote it
after suffix reject. leftover-skip 0/7 pipeline and direct. Documented.
Do not retune.

**Q6. Leakage / holdout-specific rules?**
Science leakage scan pass. No 3.35 llama tokens in `aivd/science`.
No join-all / cyclic-shift / append-reversed constructors. Plants are
evaluator-only under `aivd37/unknowns`.

**Q7. Did we manufacture success by weakening verification?**
No. DISCOVERED ≠ VERIFIED is preserved. 3.34 leftover=2 gates still
REJECTED. 3.35 leftover=2 reuses a control, not a secret. Invent
threshold leftover<3 is unchanged. Budget 32. Cap 48. 3.25–3.34
sacred first-runs untouched. 3.29 frontier A/B/C not re-scored.

## Accounting (S pipeline 3.35 seed 0)

| Stage | Experiment | Leftover after |
|---|---|---|
| Escalate IR → prim | remaining 8 | 8 |
| Escalate prim → ext | remaining 7 | 7 |
| Escalate ext → atom | remaining 6 | 6 |
| Atom 1 suffix (glue) | ~26 | 5 |
| Atom 2 even (stride) | ~27 | 4 |
| Atom 3 last-only fire | 29 | 3 |
| Falsify + reproduce + invariant | 30–32 | 0 |
| Unused reservation released | 11 capacity releases | — |

Invention experiments: 3 atoms materialized, 1 fired.
Discovery: 1 (fire @29).
Reproduction: 1 independent re-probe.
Verification: 1 paid invariant (not reused).
Failed candidates: suffix, even (revoked leases).
Successful candidate: `atom_mapt_at_-1`.

## Freeze

Implementation frozen at `97b856b` before this holdout. First-run
immutable. Do not retune U. Compact micro-language, not unbounded
invention.
