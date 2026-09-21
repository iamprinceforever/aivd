# AIVD 3.40 Phase-2 Results — H2/H3 Mechanism Localization

**Recorded:** 2026-09-21 17:50:42 IST
**Design tip (frozen):** `7be4124`
**Execution HEAD:** `66b5a979542e0e5255ad4cae22f7d588f5bd658c`
**Status:** `PHASE-2 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED`

## Manifest

| Field | Value |
|-------|-------|
| Seeds | `[0, 1, 2, 3, 4, 7, 11]` |
| Budget | BH48 (48) |
| invent_cap | 48 (unchanged) |
| REDISCOVERY_FLOOR | 5 (unchanged) |
| Plants | S=`AIVD340-P2-S` U=`AIVD340-P2-U` (fresh Phase-2) |
| Odd-stride body (historical) | `MAPT(SLICE:1,2(TOK))` |
| Odd CAT-self body | `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` |
| micro_hash | `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d` |
| version | `3.39.0` |

## Integrity

- Env gate: **PASS** failures=[]
- U positive control (Mode A × U): **PASS** V7/F7/I7 (expect F7/I7/V7) — label `OBSERVED`
- Frozen historical artifacts (Stage-2/Phase-1/Stage-3/3.38/3.39) were not mutated by this runner.
- Instrumentation is observational; Mode B injection uses CONTROLLED_INPUT provenance only.

## Mode A (AUTONOMOUS namespace) — P2-R1-INSTR

### Mode A × U (positive control)

- n=7 verified=7 fw=7 strict_ind=7

### Mode A × S

- n=7 verified=0
- Mechanism aggregate: `{"1": 7, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}` → **H2 SUPPORTED**
- Claim namespace: `AUTONOMOUS` (autonomous invent credit allowed for invent path)
- Odd-stride in produced generation_records: absent in 7/7 (H1 continuity expectation under R1) — label OBSERVED

## Mode B (CONTROLLED_INPUT namespace) — P2-R1-MODEB-ODD

**NOT autonomous discovery.** `autonomous_discovery_credit=false`.

### Mode B × S (primary H2/H3 path)

- n=7 verified=0 (verify reported for engineering continuity only; no invent credit)
- Outcome counts 1–6: `{"1": 7, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}`
- Cell conclusion: **H2 SUPPORTED**
  - seed 0: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 1: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 2: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 3: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 4: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 7: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))
  - seed 11: outcome=1 reading=H2/earlier growth present=False ranks=[] selected=False — relevant candidate absent from growth pools (looking for MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK))))

### Mode B × U (null-injection control)

- n=7 verified=7
- Odd-stride injection: **null** (must not privilege S). Instrumentation path active.

## Autonomous vs Controlled separation

| Namespace | Conditions | Discovery credit |
|-----------|------------|------------------|
| AUTONOMOUS | P2-R1-INSTR | Yes (invent/grow under R1+instr) |
| CONTROLLED_INPUT | P2-R1-MODEB-ODD | **No** — availability is evaluator-controlled |

Do **not** merge Mode A and Mode B discovery counts.

## H1–H6 (Phase-2 update)

| H | Status | Evidence class |
|---|--------|----------------|
| H1 | Continuity check under Mode A R1×S (odd-stride invent absence) | OBSERVED |
| H2 vs H3 | **H2 SUPPORTED** from Mode B×S outcomes 1–6 | CONTROLLED (availability) + OBSERVED (pool/rank/select) |
| H4 | Only if outcome 4 dominates | OBSERVED |
| H5 | Not reopened (budget frozen BH48) | — |
| H6 | Not primary | — |

## Comparison note (not identical conditions)

Compare Stage-2 BH-R1 S, BH-R1b S, Phase-2 Mode-A S/U, Mode-B S **without** treating as identical conditions (different plants; Mode B controlled availability; instrumentation additive).

## Uncertainty / R1b caveat

- Optional `P2-R1b-SACRED-AS-EXECUTED` **not executed**.
- Sacred R1b remains observational under caveat `7a3457e` (invent-basis trim after smoke).
- If Mode A/B cannot distinguish and R1b continuity were needed: STOP and report necessity — do not auto-launch.

## Data quality

- Episodes written under `reports/aivd_3_40_phase2/runs/`.
- Labels used: OBSERVED | CONTROLLED | COUNTERFACTUAL | UNKNOWN as applicable.
- No COUNTERFACTUAL claims in primary conclusion.


## Mode B pool/score/rank/select evidence (detail)

Label: **CONTROLLED** (availability) + **OBSERVED** (pool/rank/select).

- Injection: `MAPT(SLICE:1,2(TOK))` with `origin=controlled_availability_mode_b`, language PROMOTED, **invent_cap untouched**.
- Growth pre_selection pools (Mode B×S, all seeds): even CAT-self / `MAPT(CAT(AT:-1|AT:-1))` / compose pairs appear; **`MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` absent from all pools**.
- Selection: selector chose among non-odd growth/compose candidates; odd CAT-self never selected because never pooled.
- Verify: N/A for odd CAT-self (never selected).
- Outcome classification: **1 absent from pool → H2** on 7/7 Mode B×S seeds.
- Final conclusion: **H2 SUPPORTED** (Mode B primary). Not H3 (would require present+low-rank).

## R1b optional continuity

`P2-R1b-SACRED-AS-EXECUTED` **not executed**. Mode A vs Mode B already distinguish invent-absence (H1 continuity) from growth-pool-absence given availability (H2). No auto-launch.

## Conclusion

**Final (Mode B primary): `H2 SUPPORTED`**

```
PHASE-2 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED
```

