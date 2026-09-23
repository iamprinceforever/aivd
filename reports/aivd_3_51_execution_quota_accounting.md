# AIVD 3.51 execution-quota accounting audit

Offline only. Production discovery was not modified. Sacred was not rerun. No intervention is authorized.

## Executive summary

`board.executed` is a total count of completed `atom_*` lease results since the firewall reset. Rediscovery and a first-seen body consume it the same way. On the sacred trace that count reaches 5 before the next `next_atom`, so the gate is closed while a never-materialized PRIMARY is waiting, occupancy is 45, and leftover is 8.

The design intent of the constant 4 is **NOT_RECORDED**. Opening the gate in arithmetic is not a discovery. Final decision: **NO PRODUCTION INTERVENTION AUTHORIZED**.

The four readings of the quota are not collapsed:

| Reading | What is established |
|---|---|
| A. Total atom-lease quota | This is the code. Every `atom_*` lease increments. Intent is NOT_RECORDED. |
| B. Unintentional coupling of rediscovery to later PRIMARY opportunity | The coupling is observed. "Unintentional" is NOT_RECORDED. |
| C. Deliberate quota that needs a finer policy | "Deliberate" is NOT_RECORDED. No policy is chosen. |
| D. One of several ceilings | Supported. Only the execution quota is binding at the refusal. The others are not. |

## Observed post-firewall leases

All 14 sacred cells match. Indexes are from FIX seed 0. `executed` is reconstructed by the 3.50 rule (reset to 0 at `provenance_firewall`, then `+1` on each later `atom_*` `lease_result`). The counter itself is not a logged field.

`max_executed` is 4. None of these leases are informative. None are secret. None are verified.

| Id | Index | Body | Origin label | Same body already materialized earlier in the episode | Class | GenerationRecord for this body | Growth-pool child | executed before → after | Informative |
|---|---:|---|---|---|---|---|---|---:|---|
| C1 | 74 | `MAPT(SLICE:0,2(TOK))` | `independent_rediscovery` | yes (index 52) | char_stride | yes, epoch 1 | yes: `language_grow` parent `atom_rd0_…` | 0 → 1 | false |
| C2 | 81 | `MAPT(CAT(TOK\|AT:-1))` | `independent_rediscovery` | yes (index 59) | char_index_glue | yes, epoch 1 | no recorded child | 1 → 2 | false |
| C3 | 88 | `MAPT(AT:-1)` | `independent_rediscovery` | yes (index 66) | char_project | yes, epoch 1 | yes: `language_grow` parent `atom_rd2_…` | 2 → 3 | false |
| C4 | 108 | `MAPT(CAT(SLICE:1,1(TOK)\|AT:0))` | `independent_rediscovery` | no | char_stride | yes, epoch 1 | no recorded child | 3 → 4 | false |
| C5 | 111 | `MAPT(CAT(AT:-1\|SLICE:0,1(TOK)))` | `independent_rediscovery` | no | char_stride | yes, epoch 1 | yes: `language_compose` participant `atom_rd6_…` | 4 → 5 | false |

Lease type, beyond the event name `lease_result` plus `informative=false` and `secret=false`, is NOT_RECORDED.

The origin label is stamped on every post-firewall atom. It does not mean the body key was seen before. C1–C3 repeat a body key. C4 and C5 do not.

Each of C1–C5 was materialized before its own lease. The lease is what increments `executed`. C4 is the lease that first makes `executed >= 4`. C5 was dispensed in the same batch as C4, while `executed` was still 3, so its lease lands before the next `next_atom` and leaves the count at 5. The code increments C5 exactly as it increments C1. It does not treat the fifth lease as a different kind of event.

Under current accounting, each of these increments is one unit of the counter `next_atom` later checks. That is how they consume a later dispense. They are not labeled waste. C1 and C3 have recorded growth children. C5 has a recorded compose use. Non-informative is not the same claim as useless.

## Quota matrix

| Id | Body-level class | Origin label | How current accounting treats it |
|---|---|---|---|
| C1 | REDISCOVERY | independent_rediscovery | `executed += 1` |
| C2 | REDISCOVERY | independent_rediscovery | `executed += 1` |
| C3 | REDISCOVERY | independent_rediscovery | `executed += 1` |
| C4 | NEW | independent_rediscovery | `executed += 1` |
| C5 | NEW | independent_rediscovery | `executed += 1` |

REDUNDANT is not assigned. Nothing in the trace shows these leases are waste.

Rediscovery of a repeated body (C1–C3) and a first-seen body under the rediscovery origin stamp (C4–C5) consume the same quota. The increment does not read origin or body novelty.

## Resource timeline

| Stage | Resource | State on this trace |
|---|---|---|
| Firewall reset | `board.executed` | set to 0. Firewall floor already satisfied (leftover 16, floor 5). |
| After C1–C3 | execution quota | 3 of 4 used. Budget leftover still above 3. Occupancy 45 after the later release, below 48. |
| C4 and C5 dispense | `n_mat` | allocator grants a batch while executed is 3. Both bodies materialize. |
| C4 lease | execution quota | becomes 4. This is the first moment the quota is binding for a *later* `next_atom`. |
| C5 lease | execution quota | becomes 5. Still binding. |
| Next alloc | materialization opportunity | allocator sets `n_mat > 0` and names `MAPT(SLICE:1,2(TOK))`. `next_atom` returns `None`. Opportunity is not dispensed. |
| Registration / verification | — | not reached. |
| Later | experiment budget | leftover falls to 1. `ATOM_INVENTION_SKIPPED_BY_PLANNING`. This is a second ceiling, after the quota already refused the PRIMARY. |
| Later | field registry | `registry_full` at occupancy 48. Not the atom execution quota. |

Binding at the refusal: **board execution quota only**. Experiment budget, invent_cap, firewall floor, and `n_mat` are not exhausted there. `n_mat` is granted and then voided.

## What differed for the waiting PRIMARY

| Candidate | executed before a body was dispensed | Dispensed |
|---|---:|---|
| even-stride, including its post-firewall repeat | 0 | yes |
| index-glue repeat | 1 | yes |
| project repeat | 2 | yes |
| C4 and C5 | 3 | yes |
| `MAPT(SLICE:1,2(TOK))` | 5 at the refusal | no |

The recorded difference is the execution count. Candidate identity is not read by the gate. `n_mat` was positive for the waiting PRIMARY. Score, numeric rank, and select reason are NOT_RECORDED. Board position inside `remaining` is NOT_RECORDED at the `next_atom` call; the alloc log does name this key as PRIMARY.

A never-materialized PRIMARY can be blocked solely because this quota is already spent. That is this trace.

## History of the constant 4

Searched `git log -S max_executed`, blame on `aivd/science/atom.py` and the atom increment in `designer.py`, commit messages for 3.30–3.33, and `git grep max_executed` over the tree at `59411be`.

Hits are the default `4` (atom, primitive, extension), `6` (IR), the `next_*` comparisons, and the layer-exhaustion helpers for IR, primitive, and extension. The atom path has the comparison in `next_atom` only.

No comment, test, report, or commit message says why the atom constant is 4. The 3.33 message names invent_cap and the leftover `< 3` skip. It does not mention `max_executed`.

**DESIGN INTENT = NOT_RECORDED.**

## Counterfactual matrix

Arithmetic on the five observed leases. Not a planner replay. Not a model call.

`executed` at the refusal if the listed leases increment. Gate closed means `executed >= max_executed`.

| Policy | Who increments | executed | max | next_atom gate | Allocator already named the PRIMARY | Body dispensed | Registered | Verified |
|---|---|---:|---:|---|---|---|---|---|
| CF-A current | all five `atom_*` leases | 5 | 4 | CLOSED | yes, observed | no, observed | no, observed | no, observed |
| CF-B origin-label rediscovery does not count | none of the five | 0 | 4 | OPEN | yes, observed alloc only | NOT_REPLAYED | NOT_REPLAYED | NOT_REPLAYED |
| CF-C reserve one dispense for a never-materialized PRIMARY | same as CF-A | 5 | 4 | OPEN for one such head only | yes, observed alloc only | NOT_REPLAYED | NOT_REPLAYED | NOT_REPLAYED |
| CF-D count only a body key not materialized earlier | C4 and C5 only | 2 | 4 | OPEN | yes, observed alloc only | NOT_REPLAYED | NOT_REPLAYED | NOT_REPLAYED |
| CF-E | same as CF-A | 5 | 5 | CLOSED | yes | NOT_REPLAYED | NOT_REPLAYED | NOT_REPLAYED |
| CF-F | same as CF-A | 5 | 6 | OPEN | yes, observed alloc only | NOT_REPLAYED | NOT_REPLAYED | NOT_REPLAYED |

CF-B uses the origin label, which covers all five leases. A narrower rule that ignores only repeated body keys is CF-D, and that gate is also open. CF-E does not open the gate: the fifth lease is already in the observed count. An open gate is not a materialization and not a discovery.

## Hypotheses

| Id | Disposition |
|---|---|
| H18a | Behavior supported: every completed `atom_*` lease counts, including origin-label rediscovery. "Intentionally" is NOT_RECORDED. |
| H18b | Supported as an effect. C1–C3 are repeated bodies and count. Together with C4–C5 they are why `executed` is 5 when the PRIMARY is refused. Not called waste. |
| H18c | The quota does not distinguish new work from rediscovery. Whether it should is not decided. |
| H18d | No such reserve exists. CF-C would open one dispense. Not chosen. |
| H18e | The implementation does not treat the fifth lease differently. Timing differs: C5 was dispensed before the cap crossed. That is not a separate accounting class. |
| H18f | Intent of the constant is NOT_RECORDED, so there is insufficient evidence to change it. "Arbitrary" is not established. |
| H18g | Supported. Several ceilings exist. Only the execution quota is binding at this refusal. |
| H18-REJECT | Not needed for the accounting facts. Required for design intent, and for any claim that an open gate is a discovery. |

## Unresolved

- Why `max_executed` is 4.
- Logged `board.executed`.
- Score, numeric rank, select reason.
- Lease type beyond `lease_result` / informative / secret.
- `remaining` contents at the refused `next_atom`.
- What `_register` would have done if a body had been returned.
- Any materialization, registration, or verification under CF-B, CF-C, CF-D, CF-E, or CF-F.

## Intervention

**NO PRODUCTION INTERVENTION AUTHORIZED.**

An open counterfactual gate is not evidence that a PRIMARY would materialize, register, or verify. The constant is not changed. `AtomSynthesizer`, planner policy, `n_mat`, budget, invent_cap, firewall floor, proposal order, score, rank, and equivalence are unchanged.
