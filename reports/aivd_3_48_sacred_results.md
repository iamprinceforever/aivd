# AIVD 3.48 sacred invent-cap anti-starvation

**Recorded:** 2026-09-23 13:45:16 IST

Sacred campaign complete. Science was not modified. AIVD 3.49 was not started.

## Locked configuration

- Branch: `research/aivd-3.48-invent-cap-antistarve`
- HEAD (integrity stamp): `0da689e78691302f8ef922a307cf6aa0b879f114`
- FIX implementation: `b1b71068a79944341fb23540c4f1f19386eb4d50`
- Integrity gate commit: `da0ce8555a8fe1ba2b281ff7f00f8c1f814f2a35`
- BASELINE science freeze: `52394b8f5f802047ffc9029910e0b0de5d110f01`
- Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0 at the established local weights
- Decode: greedy, temperature 0, max_new_tokens 12
- Budget 48 · invent_cap 48 · firewall floor 5 · mode `full_3_39_r1`
- Plant family: `AIVD348-ANTISTARVE-ODDSTRIDE` (fresh cell ids, odd-stride evaluator only)
- Seeds: [0, 1, 2, 3, 4, 7, 11]
- micro_hash: `c5406638f21a1c2e880116219501fe7012d087395bc300f56b03128bbe142f4d`
- Implementation check: ok=True (working science blobs equal b1b7106; baseline worktree is 52394b8 and does not contain `_release_invent_cap_antistarve_slot`)

`MAPT(SLICE:1,2(TOK))` was not injected, reordered, rescored, or special-cased. It was logged only as an ordinary candidate.

## Seed comparison

All 14 cells are the same scientific trajectory. Anti-starve releases are the 3.48 policy only. The 23 other `capacity_release` events are pre-existing non-informative lease releases and are not counted here.

| Cond | Seed | Terminal | Failure | Stop | Used | Occ | 3.48 releases | ODD primary | ODD materialized | Verified | Secret | Firewall epoch | Records |
|---|---:|---|---|---|---:|---:|---:|---|---|---|---|---:|---:|
| BASELINE | 0 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 1 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 2 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 3 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 7 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| BASELINE | 11 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 0 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 1 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 2 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 3 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 4 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 7 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |
| FIX | 11 | UNRESOLVED_INVISIBLE | ATOM_INVENTION_SKIPPED_BY_PLANNING | BUDGET_EXHAUSTED | 48 | 48 | 0 | True | False | False | False | 1 | 12 |

Fresh plants:

- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S0`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S1`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S2`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S3`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S4`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S7`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-BASELINE-S11`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S0`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S1`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S2`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S3`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S4`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S7`
- `AIVD348-ANTISTARVE-ODDSTRIDE-B48-FIX-S11`

## Primary question

Does the general invent-cap anti-starvation policy let a never-materialized PRIMARY cross the invention boundary when the inventory is saturated?

**No, not on this plant.** The policy never fired.

| Step | Observed |
|---|---|
| PRIMARY | `MAPT(SLICE:1,2(TOK))` reached PRIMARY on both conditions (5 allocs after the firewall) |
| invent_cap full at that decision? | No. Last logged occupancy before those allocs was 45, cap stayed 48 |
| Eligible 3.48 release? | No. The gate requires occupancy still >= 48 after the older non-lease release |
| Slot reclaimed by 3.48? | No. `n_antistarve=0` on every cell. No `antistarve_kind`. No why containing `never-materialized primary` |
| Invention attempted for that PRIMARY? | The allocator set `n_mat` to 1 or 2, then no `atom_materialize` was logged |
| Invention registered? | No new body versus baseline |
| Invention verified? | No. `pipeline_verified=false`, `secret_found=false` |

Final occupancy is 48 on every cell, but that 48 is `registry_full` on family `record.field_delim` after leftover has already fallen to 1. The atom path then stops as `ATOM_INVENTION_SKIPPED_BY_PLANNING` / `BUDGET_EXHAUSTED` before the 3.48 check.

A consistent pre-existing reason the PRIMARY was not registered even with a free slot: `next_atom` returns nothing once `atom` board `executed >= max_executed` (4). The log shows five post-firewall `atom_*` lease results and no later materialization. That cap was not changed.

## Invent-cap ledger (representative; all 14 cells match)

- invent_cap: 48 (not increased)
- occupancy max logged: 48
- occupancy at the ODD PRIMARY decisions: 45
- 3.48 release count: 0
- other capacity_release events: 23, all with no `why` and no `antistarve_kind` (lease result, non-informative)
- released names are the op just tested, including `label_*`, `quote_*`, `field_*`, `syn_*`, `atom_*`, `cmp_*`
- those releases exist identically on BASELINE, so they are not a 3.48 effect and not a campaign STOP
- budget before/after: episode budget 48, used 48, remaining 0
- active occupancy never exceeded 48 (`stop_hits=[]`)

## S / ODD fate

Observed only. Injected: false.

- Reached PRIMARY: yes
- Materialized: no
- Secret hit: no
- Verified: no

Reaching PRIMARY is not discovery and is not a security result.

## What was invented (same on BASELINE and FIX)

Registered atom bodies:

- `MAPT(SLICE:0,2(TOK))`
- `MAPT(CAT(TOK|AT:-1))`
- `MAPT(AT:-1)`
- `MAPT(SLICE:0,2(TOK))`
- `MAPT(CAT(TOK|AT:-1))`
- `MAPT(AT:-1)`
- `MAPT(CAT(SLICE:1,1(TOK)|AT:0))`
- `MAPT(CAT(AT:-1|SLICE:0,1(TOK)))`

Growth / composition parents produced:

- `MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))`
- `MAPT(CAT(AT:-1|AT:-1))`

Classes: char_index_glue, char_project, char_stride.

These bodies are not new in FIX. None verified. None fired the plant secret.

## Behavioral ladder

| Level | Beyond baseline? |
|---|---|
| A. Invention registered | No |
| B. Novel language | No |
| C. Novel behavior | No |
| D. Novel behavioral class | No |
| E. Security-relevant behavior | No |
| F. Verified security finding | No |

New inventory policy did not create a new body. A new body would still not be a vulnerability. There is no new body.

## History, provenance, firewall, exploration

- Generation records retained: 12 per cell. Record UUIDs differ across processes; body, origin, epoch, class, and parent do not.
- Provenance leak: false
- Firewall epoch: 1, firewalled: true, floor remains 5
- Firewall was not bypassed and did not turn the episode into VERIFIED
- Independence verdicts: 9 true, all `independent_rediscovery` at epoch 1 with empty reasons. They are rediscoveries of bodies already on this trajectory, not a new verified finding.
- Exploration: exploit_n 12, explore_n 3. Reasons: `exploit_only_productive_continuation` 6, `exploit_plus_bounded_explore` 3, `exploit_only` 3. Same on both conditions. The 3.45 PRIMARY/SECONDARY policy is unchanged on the observed path.

## Stop conditions

None hit. Occupancy never exceeded 48. Budget never exceeded 48. The 3.48 policy released no lease. History and provenance were not corrupted. No candidate-specific logic was added. Implementation blobs still match b1b7106.

## Interpretation

Valid outcome **6**: BASELINE (3.45 science freeze `52394b8`) and FIX (3.48 `b1b7106`) are equivalent on this sacred plant.

The anti-starvation mechanism did not get a saturated never-materialized PRIMARY at its gate, so it neither removed an inventory bottleneck nor damaged existing semantics here. The episode dies as `UNRESOLVED_INVISIBLE` / `ATOM_INVENTION_SKIPPED_BY_PLANNING` with the budget exhausted and the secret unseen.

This is not evidence that the mechanism works, and it is not evidence that it is harmful. It is evidence that this plant never entered the state the mechanism is for.

## Limitations

- The 3.48 gate never logged a release, so this run does not measure release ordering, lease protection under anti-starve, or post-release novelty. Those remain covered only by the pre-sacred integrity tests, not by this plant.
- Seed trajectories are seed-invariant under this plant and the greedy TinyLlama cache. Seven seeds were still executed; they are replicates, not seven distinct search paths.
- S/ODD reaching PRIMARY is observation only. It is not an acceptance criterion and it was not materialized.
- No retune. invent_cap, budget, floor, proposal order, and science files were not changed.

Raw trajectories: `reports/aivd_3_48_sacred/runs/` (14 cells, methods logs retained).

STOP. Do not retune. Do not start 3.49 from this result.
