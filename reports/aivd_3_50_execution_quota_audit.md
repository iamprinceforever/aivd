# AIVD 3.50 atom-execution quota audit

Offline only. Production code was not modified. Sacred was not rerun. No repair is authorized.

## Precise statement

The design intent of the constant `4` remains **NOT_RECORDED**. No comment, test, or commit states why `max_executed` is 4.

Operationally, `board.executed` counts completed `atom_*` lease results since the last firewall reset. The fourth such result makes `executed >= max_executed`. `next_atom` then returns `None`. On this trace a fifth `atom_*` lease also lands before the next call, because that atom was already dispensed in the same batch. The waiting PRIMARY is therefore refused at reconstructed `executed = 5`, while occupancy is 45, invent_cap is 48, and leftover is 8.

The waiting key on this trace is `MAPT(SLICE:1,2(TOK))`. The gate does not read that key.

## Lineage

| Item | Value |
|---|---|
| Parent audit | `research/aivd-3.49-primary-materialization-audit` @ `98fa0d4` |
| This branch | `research/aivd-3.50-atom-execution-quota-audit` |
| Implementation (unchanged) | `b1b7106` |
| Science freeze | `52394b8` |
| Evidence | 14 sacred cells in `reports/aivd_3_48_sacred/runs/` |
| Cells identical on this trace | yes |

## What the implementation does

`AtomInventory` (`aivd/science/atom.py`) is created with `executed = 0`, `max_executed = 4`, `max_generated = 8`, `max_depth = 4`. Introduced in `468994e` (AIVD 3.33). That commit names invent_cap and the leftover `< 3` skip. It does not mention `max_executed`.

`max_depth` is never read. `max_generated` limits how many bodies `plan()` keeps. Neither is the gate that returned `None`.

The only atom-path read of `max_executed` is `AtomSynthesizer.next_atom`:

- if `executed >= max_executed`, return `None`
- else if `remaining` is empty, return `None`
- else pop `remaining[0]`

Writes:

- `_maybe_firewall` sets `atom_synth.board.executed = 0` immediately before `provenance_firewall`
- a completed lease whose op starts with `atom_` does `executed += 1`, for both informative and non-informative results, with no test of origin, class, rank, or rediscovery

Not increments: `atom_materialize`, `language_grow`, `language_compose`, `cmp_*` leases, `capacity_release`, non-atom leases.

Sibling layers use the same comparison twice: `next_program` / `next_primitive` / `next_extension` return `None`, and `_ir_kinds_exhausted` / `_prim_kinds_exhausted` / `_ext_kinds_exhausted` treat the cap as “this layer is done, escalate.” IR uses 6. Primitive and extension use 4. The atom layer copies only the `next_atom` stop. It has no exhaustion helper that reads `atom_synth.board.executed`. Structural resemblance is not an atom-path purpose.

## Resource separation

| Resource | Where it lives | At the blocked call | Coupled to `next_atom`? |
|---|---|---|---|
| 1. Experiment budget | `remaining_steps` / episode used | leftover 8, used not yet 48 | No. The `leftover < 3` return is earlier and did not fire. |
| 2. invent_cap | `inventor.occupancy` vs 48 | occupancy 45 | No. `atom_capacity_wait` absent. |
| 3. Firewall floor | `REDISCOVERY_FLOOR = 5` | firewall already ran at leftover 16 | No. Firewall resets `executed` to 0. It does not fill it. |
| 4. `board.max_executed` | atom board, default 4 | reconstructed executed 5 | Yes. This is the predicate `next_atom` checks. |
| 5. Materialization width | `ExplorationAllocator.n_mat` | `n_mat` is 2, then 1 | The allocator does not read `executed`. It can grant a slot that `next_atom` then voids. |

Confirmed from the trace and the code: resource 4 is exhausted while 1, 2, and the chain floor are not.

```text
firewall reset executed=0
        │
        ▼
atom_* lease_result  ──►  executed += 1     (any atom_ op, informative or not)
        │
        ▼
executed >= 4
        │
        ▼
next_atom() = None          allocator n_mat is ignored
        │
        ▼
no atom_materialize
```

Episode budget, invent_cap, and the firewall floor are other counters. They are not consulted inside `next_atom`.

## Counter consumption

Initial `executed` is 0. Two epochs. All 14 cells match.

### Epoch before the firewall (does not block the later PRIMARY)

Three `atom_*` leases, then reset. The cap of 4 is not reached. None verified. All `informative=false`, `secret=false`.

| # | Body | Origin | Materialized before the lease | Role |
|---:|---|---|---|---|
| 1 | `MAPT(SLICE:0,2(TOK))` | invented | yes | first even-stride |
| 2 | `MAPT(CAT(TOK\|AT:-1))` | invented | yes | first index-glue |
| 3 | `MAPT(AT:-1)` | invented | yes | first project |

`provenance_firewall` then sets `executed = 0`.

### Epoch after the firewall (this is the blocking window)

Five `atom_*` leases before the first blocked `next_atom`. All `origin=independent_rediscovery`, `informative=false`, `secret=false`, not verified. Each was materialized earlier in the epoch, then promoted (`computational_usefulness`) and leased.

| # | After this lease | Body | Class | Notes |
|---:|---:|---|---|---|
| 1 | 1 | `MAPT(SLICE:0,2(TOK))` | char_stride | rediscovery of even-stride |
| 2 | 2 | `MAPT(CAT(TOK\|AT:-1))` | char_index_glue | rediscovery of index-glue |
| 3 | 3 | `MAPT(AT:-1)` | char_project | rediscovery of project |
| 4 | **4** | `MAPT(CAT(SLICE:1,1(TOK)\|AT:0))` | char_stride | first lease that makes `executed >= 4` |
| 5 | **5** | `MAPT(CAT(AT:-1\|SLICE:0,1(TOK)))` | char_stride | already dispensed while executed was still 3, so its lease lands before the next `next_atom` |

`cmp_*` growth and compose leases in this window do not increment the atom counter.

The next `atom_explore_alloc` names `MAPT(SLICE:1,2(TOK))` with `n_mat > 0`. `next_atom` sees `5 >= 4` and returns `None`. That repeats for five allocations. No `atom_materialize` follows any of them.

## Successful versus blocked

Score and numeric rank are NOT_RECORDED. Do not use them.

| Candidate | `next_atom` calls that could return a body | Post-firewall `executed` before that call | Materialized |
|---|---|---:|---|
| even-stride | yes, pre-firewall and again after reset | 0 on the rediscovery | yes |
| index-glue | yes | 1 | yes |
| project | yes | 2 | yes |
| `MAPT(CAT(SLICE:1,1(TOK)\|AT:0))` | yes | 3 | yes |
| `MAPT(CAT(AT:-1\|SLICE:0,1(TOK)))` | yes, same batch, still at 3 | 3 | yes |
| later PRIMARY `MAPT(SLICE:1,2(TOK))` | allocator asked; `next_atom` returned `None` | 5 | no |

What differed: not a recorded score. The blocked candidate was the first PRIMARY offered to `next_atom` after the post-firewall atom-lease count had already passed 4. Earlier bodies were offered while the count was 0, 1, 2, or 3. The quota does not look at whether the candidate is unexplored.

## Generality

The increment tests only `op.startswith("atom_")`. It does not test the body, the class, rank, rediscovery, or whether a never-materialized PRIMARY is still on the board.

So already-executed atom work fills a finite window, and a later valid PRIMARY can be waiting with `n_mat > 0` and still receive no body. That is what this trace shows. It is not a property of one key.

| Generic role | What this quota does with it |
|---|---|
| Already materialized productive atom | Its later lease consumes one count. |
| Rediscovery of that atom | Same. Origin is not consulted. |
| Redundant / non-informative lease | Same. `informative=false` still increments. |
| Active lease | The count moves when the lease result is logged, not while it is merely open. |
| Rejected candidate | Not a separate counter. A non-informative atom lease both rejects and increments. |
| Unexplored PRIMARY still waiting | Not reserved. `next_atom` refuses every further candidate once the count is ≥ 4. |
| Multiple unexplored classes | Not consulted. `max_executed` is not per class. |

## Hypotheses

| Id | Verdict |
|---|---|
| H17a | **Partly supported as an effect, not as a name.** The cap did leave a later PRIMARY unmaterialized while invent_cap and leftover still allowed work. The code does not treat the count as exploration versus exploitation. Every `atom_*` lease consumes it. |
| H17b | **Not established.** Nothing in the implementation says the constant is safety-critical or that it must not change. This audit does not raise it. |
| H17c | **Coupling observed.** A materialization grant (`n_mat > 0`) is voided by a lease counter the allocator does not read. Calling that coupling “incorrect” would be a repair judgment. Not made. |
| H17d | **Consumption observed.** The four leases that cross the cap, and the fifth that lands before the refusal, are rediscoveries of bodies already materialized in this episode. No count is reserved for a never-materialized PRIMARY. The word “should” is not a change request. |
| H17e | **Not supported.** The increment has no branch for productive versus rediscovery versus redundant. Separate success/rejection fields exist. They do not gate `next_atom`. |
| H17f | **Not a conclusion.** Necessity of the quota, and any new allocation policy, are not established here. |
| H17g | **Supported.** Budget, invent_cap, firewall floor, `max_executed`, and `n_mat` are separate. On this trace only `max_executed` is the one that is already spent. |
| H17-REJECT | Not needed for the operational effect. Required for the design intent of the literal 4, which stays NOT_RECORDED. |

## Offline counterfactuals

These are arithmetic on the observed event list. They are not a planner replay. No materialization is claimed.

| Id | Change | At the observed refusal (`executed = 5`) | Claim |
|---|---|---|---|
| CF1 | `max_executed = 5` | `5 >= 5` is still true | Gate stays closed. The fifth lease already happened before that call. |
| CF2 | `max_executed = 6` | `5 >= 6` is false | The executed gate would be open. Other predicates were never reached. Materialization is not claimed. |
| CF3 | reserve one dispense for a never-materialized PRIMARY | not in the code | Not simulated. No reservation exists today. Materialization is not claimed. |
| CF4 | do not count `independent_rediscovery` leases | all five post-firewall consumers are that origin, so the reconstructed count at the refusal would be 0 | The executed gate would be open. Materialization is not claimed. |

OBSERVED: five post-firewall `atom_*` leases, then five PRIMARY allocations with no `atom_materialize`. COUNTERFACTUAL: only the gate’s open/closed bit under a different constant or a different increment rule. Nothing was re-executed.

## NOT_RECORDED

- why the constant is 4
- `board.executed` as a logged field (reconstructed from the two writes)
- numeric score and numeric rank
- whether a dispensed body would have passed `name in inventor.ops` or `_register` had `next_atom` returned it
- any per-class or per-candidate execution budget

## First blocking predicate

Unchanged from 3.49, now with the consumer named:

`next_atom` returns `None` because `board.executed >= board.max_executed` after atom-lease events 1–5 of the post-firewall epoch. The crossing event is lease 4. The refusal is observed after lease 5. invent_cap and the chain floor are not that predicate.

## Protections not touched

Experiment budget, invent_cap, firewall, novelty, equivalence, provenance, independence, verification, and recursive growth were not modified. No global resource was increased.

STOP. No production intervention authorized.
