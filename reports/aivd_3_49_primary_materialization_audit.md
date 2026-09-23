# AIVD 3.49 primary-materialization forensic audit

Offline only. Production code was not modified. Sacred was not rerun. No repair is authorized.

## Precise statement

PRIMARY reaches `atom_explore_alloc` with `n_mat > 0`, then `AtomSynthesizer.next_atom` returns `None` because `board.executed >= board.max_executed` (4) and that prevents `atom_materialize`, while occupancy is 45 (below invent_cap 48) and leftover is 8 (at or above the chain floor of 3).

`board.executed` itself is **NOT_RECORDED**. The value 5 is reconstructed from the only two writes to that counter, applied to logged events. See "Reconstruction rule" below.

## 1. Lineage

| Item | Value |
|---|---|
| Repository | `iamprinceforever/aivd` |
| Diagnostic branch | `research/aivd-3.49-primary-materialization-audit` |
| Parent HEAD | `0da689e78691302f8ef922a307cf6aa0b879f114` |
| FIX implementation (unchanged) | `b1b71068a79944341fb23540c4f1f19386eb4d50` |
| Science freeze / BASELINE | `52394b8f5f802047ffc9029910e0b0de5d110f01` |
| Integrity gate | `da0ce8555a8fe1ba2b281ff7f00f8c1f814f2a35` |
| Sacred evidence | `reports/aivd_3_48_sacred/runs/` (14 cells) and `reports/aivd_3_48_sacred_results.json` |
| Mode on those cells | `full_3_39_r1` |
| Budget / invent_cap / floor | 48 / 48 / 5 |

All 14 cells (BASELINE and FIX, seeds 0, 1, 2, 3, 4, 7, 11) have the same methods-log event order for this question. Seed does not change the trace. The representative cell is FIX seed 0. Indexes below are methods-log indexes in that cell.

## 2. Sacred trace (representative)

| Index | Event | Recorded facts |
|---:|---|---|
| 52, 59, 66 | `atom_materialize` | even-stride, index-glue, project. Occupancy after each: 46. Pre-firewall. |
| 53, 60, 67 | `lease_result` | those three `atom_*` ops, informative false |
| 70 | `provenance_firewall` | leftover 16, epoch 1. Code resets `atom_synth.board.executed = 0` immediately before this log. |
| 73, 80, 87 | `atom_materialize` | rediscovery of the same three bodies. Occupancy 46. |
| 74, 81, 88 | `lease_result` | `atom_rd0`, `atom_rd1`, `atom_rd2` |
| 92, 98 | `language_grow` | two CAT-self growth bodies (not `atom_materialize`) |
| 106, 107 | `atom_materialize` | `MAPT(CAT(SLICE:1,1(TOK)\|AT:0))` then `MAPT(CAT(AT:-1\|SLICE:0,1(TOK)))`. Occupancy 46 then 47. |
| 108, 111 | `lease_result` | `atom_rd5`, `atom_rd6`. Last logged occupancy after the following release: 45 (index 117). |
| 121 | `atom_explore_alloc` | **first PRIMARY = `MAPT(SLICE:1,2(TOK))`**, `n_mat=2`, reason `exploit_plus_bounded_explore` |
| 123, 126, 128, 130 | `atom_explore_alloc` | same PRIMARY again. `n_mat` 2, then 1. No `atom_materialize` after any of them. |
| 133 | `registry_full` | family `record.field_delim`, occupancy 48 |
| 134 | `RECURSIVE_BUDGET_FAILURE` | leftover 1 |
| 135 | `ATOM_INVENTION_SKIPPED_BY_PLANNING` | leftover 1 |

Terminal state of every cell: `UNRESOLVED_INVISIBLE` / `ATOM_INVENTION_SKIPPED_BY_PLANNING` / `BUDGET_EXHAUSTED`. Used 48. Final occupancy 48. Anti-starve releases 0. Verified false.

## 3–6. Timing at the first missed materialization

| Mark | What | Evidence |
|---|---|---|
| T0 | ODD is PRIMARY | index 121 `primary_keys=MAPT(SLICE:1,2(TOK))`, `n_mat=2` |
| T1 | occupancy | last occupancy log before T0 is index 117 `capacity_release` occupancy **45**. Gap events are `language_grow_reject`, `language_retire`, `generation_decision`. None of those register an op. |
| T2 | leftover | immediately preceding `generation_decision` (index 120) leftover **8**. Same step: generation runs, then invent. Alloc is logged only after the `leftover < 3` returns, so leftover at T0 is still ≥ 3. Anchor records 8. |
| T3 | next planner decision | index 122 `generation_decision` leftover 8, action compose. Not an `atom_materialize`. |
| T4 | `atom_materialize` called? | **No.** Next event is not `atom_materialize`. No `atom_capacity_wait`. No `INVENTORY_CAPACITY_FAILURE`. |
| T5 | first `registry_full` | index 133, occupancy 48, family `record.field_delim`. After five failed PRIMARY allocs. |
| T6 | budget exhaustion | index 134–135, leftover 1. Episode used 48. |

What happened between T0 and T4: the allocator had already committed `n_mat=2`. The materialize loop then called `next_atom()` and got `None` before registration. Control returned. The next logged event is the following step's `generation_decision`.

The same T0–T4 gap repeats at indexes 123, 126, 128, and 130. Occupancy stays 45. Reconstructed `executed` stays 5. Leftover falls 8 → 7 → 6 → 5 on the anchors, still ≥ 3, so the chain-floor return has not fired yet.

## 7. Materialization path and the first predicate

After `atom_explore_alloc` is appended, `_maybe_invent_atom` does only this before `atom_materialize`:

1. If `occupancy >= INVENT_CAP` (48), try the 3.48 release or `break`. A successful release logs `capacity_release` with why `slot for never-materialized primary atom`. A still-full cap logs nothing in the loop and breaks. **Eliminated.** Occupancy is 45. No such why exists in any cell (`capacity_release` whys are all empty; count 23, all lease releases).
2. `atom = next_atom()`. If `None`, `break`, and **nothing is logged**.
3. If the name is already in `inventor.ops`, `continue`, and nothing is logged. **Not reached** on the first iteration, because `next_atom` returns `None` first.
4. `_register` failure logs `failure_class=INVENTORY_CAPACITY_FAILURE` and returns. **Eliminated.** That event is absent.
5. Success always appends `atom_materialize` before any later event. **Absent**, so success was not reached.

`next_atom` (`aivd/science/atom_synth.py`) returns `None` only if:

- `board.executed >= board.max_executed`, or
- `board.remaining` is empty.

`board.remaining` is empty **eliminated** for the first pop. `decide()` has just assigned `remaining` to a non-empty `ordered`. `n_mat > 0` is not returned for an empty board (`reason` would be `empty_or_no_cap` and the alloc event would not be logged). Nothing between `decide()` and the first `next_atom()` pops the board.

Therefore the only remaining predicate is `board.executed >= board.max_executed`.

`max_executed` is the `AtomInventory` default **4** (`aivd/science/atom.py`). No other assignment to `max_executed` exists.

### Reconstruction rule (not a logged field)

Writes to `atom_synth.board.executed` in the whole tree:

- set to 0 in `_maybe_firewall`, immediately before the `provenance_firewall` log
- `+= 1` on an `atom_*` `lease_result`, inside the `allow_lazy` and `allow_synth` block, immediately after that log

`full_3_39_r1` contains `3_39`, so both flags are on. The log confirms the lazy path (lease `capacity_release` events exist) and the 3.39 path (generation records and `provenance_firewall` exist). Designer mode is the sacred `invention_mode`, passed `EpistemicController` → `ScienceController` → `ScienceProposer` → `ScienceDesigner`.

Post-firewall `atom_*` lease_results before index 121: **5** (`atom_rd0`, `atom_rd1`, `atom_rd2`, `atom_rd5`, `atom_rd6`). Reconstructed `executed` at T0 is **5**. `5 >= 4`, so `next_atom` returns `None`.

The last successful atom materializations (indexes 106 and 107) occur when reconstructed post-firewall `executed` is **3**, which is still `< 4`. Their own leases (108, 111) are what push the counter to 4 and then 5. The next PRIMARY is the first one that meets the cap.

## 8. Blocking predicates, separated

| Class | Predicate | At the first ODD gap |
|---|---|---|
| A. invent_cap | `occupancy >= 48` before alloc, or mid-loop | **False.** Occupancy 45. No `atom_capacity_wait`. |
| B. budget | `leftover < 3` (`allow_esc` or `allow_atom_budget`) | **False at T0.** Leftover 8. Alloc would not be logged if this returned. **True later**, index 135, leftover 1. That is the terminal skip, not the first miss. |
| C. chain_floor | same leftover `< 3` gate; allocator `chain_floor` default 3 | **Not the first miss.** `chain_floor` numeric is NOT_RECORDED. The code constant is 3. Leftover 8 still affords `n_mat`. |
| D. planning policy | `_esc_action` STOP, pending lease, family `record.field_delim` still generating, untried-class early return | **False at T0.** Those returns happen before `atom_explore_alloc`. The alloc is the proof they did not return. |
| E. materialization eligibility | `next_atom`: `executed >= max_executed` | **This is the first blocker.** |
| F. novelty / identity | `name in inventor.ops` | **Not reached.** `next_atom` returns before that test. No ODD-specific branch exists on this path. |
| G. firewall | firewall skip or provenance hide | **False as a materialize block.** Firewall already ran at leftover 16 (floor 5). It reset `executed` to 0. It did not suppress the later alloc. |
| H. registration / occupancy | `_register` failure | **Not reached.** No `INVENTORY_CAPACITY_FAILURE`. |
| I. other | `registry_full` on `record.field_delim` | **Later.** Index 133, after the five missed allocs. Not between T0 and T4. |

## 9. Successful-candidate comparison

Same cell. Score is NOT_RECORDED (planner audit off). Rank numeric is NOT_RECORDED. PRIMARY key, leftover anchor, occupancy, and materialize result are recorded.

| Candidate | When | PRIMARY at its alloc | Post-firewall executed before `next_atom` | Leftover anchor | Occupancy after | `atom_materialize` |
|---|---|---|---|---:|---:|---|
| `MAPT(SLICE:0,2(TOK))` even-stride | pre-firewall, idx 52 | itself | reset not yet; 0 atom leases since process start before this call | 19 | 46 | yes |
| `MAPT(CAT(TOK\|AT:-1))` index-glue | idx 59 | itself | 1 prior atom lease | 18 | 46 | yes |
| `MAPT(AT:-1)` project | idx 66 | itself | 2 prior atom leases | 17 | 46 | yes |
| same three, rediscovery | idx 73, 80, 87 | themselves | 0, then 1, then 2 after firewall reset | 16, 15, 14 | 46 | yes |
| `MAPT(CAT(SLICE:1,1(TOK)\|AT:0))` | idx 106 | itself | 3 | 11 | 46 | yes |
| `MAPT(CAT(AT:-1\|SLICE:0,1(TOK)))` | idx 107 | secondary of that same alloc | 3 (same call, before either lease) | 11 | 47 | yes |
| `MAPT(SLICE:1,2(TOK))` ODD | idx 121 | itself | **5** | **8** | still 45, no materialize log | **no** |
| growth `MAPT(CAT(SLICE:0,2(TOK)\|SLICE:0,2(TOK)))` | idx 92 | not an atom alloc | not `next_atom` | 13 | not on this event | registered via `language_grow`, then rejected |
| growth `MAPT(CAT(AT:-1\|AT:-1))` | idx 98 | not an atom alloc | not `next_atom` | 12 | not on this event | registered via `language_grow`, then rejected |

Earliest divergence: ODD is the first PRIMARY whose `next_atom` runs at reconstructed `executed >= 4`. Earlier PRIMARYs of every class that did materialize ran at `executed <= 3`. Budget and invent_cap were looser for ODD than for those successes (leftover 8 vs 11–19, occupancy 45 vs a register that landed at 46–47). Class, score, and identity are not the recorded difference. The execution counter is.

## 10. Hypotheses

| Id | Verdict |
|---|---|
| H16a | Not the first gap. A planner STOP does exist, but it fires only at leftover 1 (index 135), after the materialize misses. |
| H16b | Not the first gap. At T0 leftover is 8. Budget/chain-floor is the **terminal** skip, not the missing `atom_materialize`. |
| H16c | **Supported.** PRIMARY does not guarantee materialization eligibility. |
| H16d | **Not supported.** The gate is general (`max_executed`). No ODD branch. The same function materialized other classes when `executed < 4`. |
| H16e | **Not the first gap.** Inventory had room (45 < 48). Registration was not called. |
| H16f | **Not supported.** The exploration allocator emitted `n_mat=2` and named ODD as PRIMARY. It did not refuse. |
| H16g | **Supported.** The blocker is downstream of `decide()`, inside `next_atom`. |
| H16h | **Supported for the episode, not for the first transition.** First transition is one predicate. Later, leftover `< 3` and `registry_full` also fire. |
| H16-REJECT | Not needed. The first predicate is localized by elimination plus the reconstruction rule. |

## 11. NOT_RECORDED

The 3.41 planner ledger is off by default (`AIVD41_PLANNER_AUDIT` unset). Sacred artifacts contain no `observe_*` rows. These are NOT_RECORDED, not guessed:

- numeric score and score components
- numeric rank
- `observe_select` / `selection_reason=next_atom`
- per-candidate materialization-eligibility boolean
- per-candidate invention-eligibility boolean
- audit `budget_before` / `budget_after`
- logged `chain_floor` value
- logged `invent_slots_left`
- logged `board.executed` and `board.max_executed` (reconstructed, not stored)
- logged `board.remaining` length at `next_atom`
- `name in inventor.ops` result
- per-candidate skip reason at T0 (the only skip row is the later episode-level `ATOM_INVENTION_SKIPPED_BY_PLANNING`)
- a distinct "atom_materialize attempt" event (the alloc is a width decision, not a call log)

Recorded and used: `primary_keys`, `n_mat`, alloc `reason`, `explore_n`, leftover on `generation_decision` and `atom_rank`, occupancy on materialize and `capacity_release`, `registry_full`, firewall epoch, terminal failure.

## 12. 3.48 non-activation

The 3.48 predicate is `occupancy >= 48` and the next PRIMARY never materialized.

At every ODD PRIMARY decision, occupancy is **45 < 48**. `atom_capacity_wait` is absent. No `capacity_release.why` contains `never-materialized primary`. `n_antistarve = 0` on all 14 cells. BASELINE and FIX traces match, which is what a gate that does not open must do.

**3.48 was not exercised.** The sacred run is a valid non-activation observation. It is not evidence that anti-starve works, and it is not evidence that anti-starve is the first blocker. The invent-cap wall was not the first blocker.

## 13. Next experiment required

Do not repair. Do not raise budget or invent_cap. Do not inject or re-rank `MAPT(SLICE:1,2(TOK))`. Do not rerun Sacred as a behavior test.

The missing ledger row is the `next_atom` return reason: `executed`, `max_executed`, and whether `remaining` was empty. A future **instrumentation-only** pass could append that row without changing the predicate. That pass is not authorized here and was not implemented.

## Limitations

- `executed == 5` is a side-effect reconstruction. It is not a field in the sacred JSON. The elimination of every other silent branch is what makes the predicate unique; if a future log showed `remaining` empty or `executed < 4` at T0, this conclusion would be withdrawn.
- Later seeds in each process are prompt-cache replicates. They confirm stability. They are not seven independent model searches.
- 3.45–3.47 raw artifacts were not required. This trace is sufficient and was not extended by invention.

STOP. No production intervention authorized.
