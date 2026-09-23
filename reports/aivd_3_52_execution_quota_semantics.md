# AIVD 3.52 execution-quota semantics audit

Offline only. Production discovery was not modified. Sacred was not rerun. No quota was changed.

## Executive summary

The code behavior is known. The design intent is not.

`board.max_executed` is a field on one atom board. `next_atom` returns `None` when `executed >= max_executed`. The only atom increment is one completed `atom_*` lease result, and it does not read origin, novelty, or whether the body was seen before. The only reset is the provenance-firewall board wipe. The default is 4. Nothing in the introducing commit, later commits, tests, comments, or docs says why that number exists or which resource it is supposed to bound.

Blocking a never-materialized PRIMARY is the observed consequence on the 3.48 trace. That is not, by itself, a bug.

**DESIGN INTENT = NOT_RECORDED.**

**NO PRODUCTION INTERVENTION AUTHORIZED.**

## What the quota is not shown to mean

No source selects one of these. They stay unchosen.

| Proposed meaning | Evidence |
|---|---|
| A. Total atom-lease operations | This is what the increment does. No document says that was the aim. |
| B. Atom exploration attempts | Exploration is `n_mat` / PRIMARY / SECONDARY. This counter is not that allocator. |
| C. Expensive model calls | The counted step is `inventor.apply` of an already registered function. It is not a model request. "Expensive" is not in the code. |
| D. Materialization attempts | Materialize happens in `next_atom` before the lease. The counter moves only after `lease_result`. |
| E. Firewall rediscovery work | Pre-firewall leases count too. The firewall zeroes the counter. It is not a rediscovery-only tally. |
| F. Recursion explosion | `next_atom` is not recursive. `AtomInventory.max_depth` is never read. `micro.MAX_DEPTH` is a different check. |
| G. Legacy safety bound | "Unknown original meaning" is accurate. The word "safety" is not in the record. |
| H. A combination | Not established. |

## Call graph

One `ScienceDesigner` owns one `AtomSynthesizer`. That object creates one `AtomInventory` in `AtomSynthesizer.__init__`.

```
AtomSynthesizer.__init__
    board = AtomInventory()          # executed = 0, max_executed = 4
plan / rank / allocator
    board.remaining reordered
    n_mat chosen                     # does not read executed
_maybe_invent_atom
    for _ in range(n_mat):
        next_atom()
            if executed >= max_executed: return None
            if not remaining: return None
            pop remaining[0]
        _register + commit_ops       # ExperimentLease created; executed unchanged
later propose
    due = commitments.due()
    _apply(prompt, due.op)           # inventor.apply, local function
on result, all of these true:
    allow_commit
    used op is that lease
    allow_lazy
    allow_synth
    op startswith "atom_"
        board.executed += 1          # informative/secret do not gate this
        then successes or rejections
_maybe_firewall
    board.executed = 0               # with the rest of the atom-board wipe
```

Exact predicates, current tree:

- Check: `AtomSynthesizer.next_atom` in `aivd/science/atom_synth.py`. `executed >= max_executed`, then an empty `remaining`.
- Increment: `ScienceDesigner` result path in `aivd/science/designer.py`, `op0.startswith("atom_")` then `atom_synth.board.executed += 1`. Nested under `allow_commit`, a matching lease, `allow_lazy`, and `allow_synth`.
- Reset: `_maybe_firewall`, `atom_synth.board.executed = 0`, in the same wipe as `remaining`, `materialized`, `seen`, `generated`, `successes`, `rejections`.
- Initialization: `AtomInventory` defaults in `aivd/science/atom.py`. No later assignment to `max_executed` exists.

Sibling layers are not the atom quota. IR (`max_executed = 6`), primitive (`4`), and extension (`4`) each have their own board. Their `next_*` methods use the same comparison. Their `*_kinds_exhausted` helpers also treat `executed >= max_executed` as "this layer is done." The atom path has no such helper. The IR helper's docstring says more SWAP/MOVE/WRAP_EACH instances are not a new capability. It does not mention the number 6, and it does not apply to atoms.

`CommitmentBoard.max_leases_executed` (default 3) is a third counter. It limits lease renewal in `due()`. It is not `board.executed`.

`micro.MAX_DEPTH = 4` rejects a micro expression whose `depth()` exceeds 4. `AtomInventory.max_depth = 4` is stored and never read. Same digit, different field. Not linked in any comment.

The telemetry key `atom_execution_attempts` is `self.executed`. That is a label on the dict, added with the field in 3.33. A label is not a design document.

## Lifecycle

| Event | `executed` | Scope |
|---|---|---|
| `AtomInventory()` | 0 | this board only |
| atom materialize / `_register` | unchanged | |
| completed `atom_*` lease under the flags above | +1 | this board |
| `language.generation` bump (promote, grow, compose) | unchanged | generation is a different counter |
| provenance firewall | 0 | this board, this designer |
| new `ScienceDesigner` | new board at 0 | not an experiment-wide total |

The counter is not per generation. After the firewall, generation keeps climbing while `executed` starts again at 0. It is not stored on the episode budget. It is not shared with the IR, primitive, or extension boards.

If the firewall never fires, the count is every qualifying atom lease since that designer was constructed. The firewall wipe is what makes the post-firewall count local to that epoch. The 3.38 commit that added the wipe does not say the quota is "per epoch."

## Historical origin

| Commit | What was introduced | What the message says about this bound |
|---|---|---|
| `56ca5fe` AIVD 3.30 | `SynthBoard.max_executed = 6`, `next_program` returns `None` at the cap, `syn_` lease increments `executed` | nothing |
| `3ad5d9d` AIVD 3.31 | primitive board `max_executed = 4`; `_ir_kinds_exhausted` and `_prim_kinds_exhausted` also return true at the cap | "after 3.30 IR kinds fail." The number is not named. |
| `8607b48` AIVD 3.32 | extension board `max_executed = 4` and the same two uses | nothing about the number |
| `468994e` AIVD 3.33 | `AtomInventory.max_executed = 4`, `next_atom`, `atom_` increment | invent_cap, budget, leftover `< 3`. Not `max_executed`. |
| `34bc665` AIVD 3.38 | `atom_synth.board.executed = 0` inside the firewall wipe | rediscovery floor and invent_cap. Not this counter. |

`git log -S max_executed` finds those four introduction commits and the later audit commits. No commit message, comment, changelog entry, or pre-audit report explains the atom constant 4. `docs/` has no hit. Older Llama `first_run.json` files only dump the telemetry key `atom_execution_attempts`.

**DESIGN INTENT = NOT_RECORDED.**

## Tests

| Test | What failure it actually prevents | What it says about `executed` |
|---|---|---|
| `tests/test_aivd330_synth.py::test_7_family_continuation_programs` | `next_program` returns two programs with different keys | It pops `remaining` while `executed` is still the default 0. It never sets or reads `max_executed`. |
| `tests/test_aivd341_planner_audit.py` `_plan_once`, T01, T10 | plan order is deterministic; a select audit row is emitted | The loop calls `next_atom` until `None` and never increments `executed`, so `None` means `remaining` is empty. The cap is not the invariant. |
| `tests/test_aivd338_lang.py`, `tests/test_aivd339_independent_generations.py` | firewall epoch, origin labels, rediscovery floor | They do not read `board.executed`. |
| `tests/test_aivd351_execution_quota_accounting.py` | the 3.51 accounting report does not drift | Locks observed arithmetic and "intent NOT_RECORDED." It is not a design source. |

No test fails if `max_executed` is changed, except the 3.51 audit lock that the default is still 4. No test states whether the count is a cost, a safety bound, or a candidate bound. The tests establish behavior only where they touch the queue pop. They do not establish intent.

## Lease semantics

One representative `atom_*` lease:

1. **Create.** `next_atom` pops a body. `_register` stores the function. `commit_ops` appends an `ExperimentLease` with `executed = 0` and `remaining = 1`. That lease field is not the board counter.
2. **Dispatch.** `commitments.due()` returns it.
3. **Execute.** `_apply` calls `inventor.apply`. Local function. Not a model call.
4. **Complete.** `on_result` sets the lease REVOKED or INFORMATIVE and logs `lease_result`.
5. **Count.** If the flags above hold and the op starts with `atom_`, `board.executed += 1`. Secret adds successes. Non-informative adds rejections. Neither choice skips the increment.
6. **Reuse.** A later body with the same key, or a new key under `independent_rediscovery`, hits the same `startswith("atom_")` branch.

| | First-seen body | Repeated body | Origin label `independent_rediscovery` |
|---|---|---|---|
| Increment predicate | `startswith("atom_")` | same | same |
| Documented as equivalent | no | no | no |

**OBSERVED BEHAVIOR:** they consume the counter identically.

**DESIGN INTENT** of that equality: **NOT_RECORDED.** The missing branch is not a written policy that says they should be the same.

## Resource model

These stay separate. None of them is read by `next_atom` except the atom board's own `executed`.

```
episode budget (remaining_steps / leftover)
    chain floor leftover < 3 skips new invention
    rediscovery floor leftover < 5 skips the firewall
invent_cap
    registered methods
    3.48 anti-starve, only when occupancy is already at the cap
firewall floor
    whether independent rediscovery is allowed to start
allocator n_mat
    how many bodies may be dispensed this call
    does not consult executed
board.max_executed
    how many completed atom_* leases this board may have
    before next_atom returns None
micro.MAX_DEPTH
    expression-tree depth at validation
    not this counter
CommitmentBoard.max_leases_executed
    lease renewal cap
    not this counter
```

On the observed refusal, only `board.max_executed` is binding. Occupancy is 45 of 48. Leftover is 8. `n_mat` was already granted. That separation was established in 3.49 and 3.51. It still does not name the purpose of the constant.

The role that is documented: none.

The role that is implemented: a per-board stop on further `next_atom` pops after enough `atom_*` lease completions, cleared when the firewall wipes that board.

Calling that a cost budget, a safety bound, a diversity bound, or a recursion bound is not supported.

## Successful path versus blocked path

The gate does not mention a candidate. It does not allow even-stride and forbid the waiting PRIMARY. It pops while `executed < max_executed` and returns `None` otherwise.

| Body | Reconstructed `executed` when `next_atom` could pop it | Result |
|---|---:|---|
| even-stride, first time | 0 | popped |
| its post-firewall repeat | 0 after the wipe | popped |
| index-glue repeat | 1 | popped |
| project repeat | 2 | popped |
| the two later stride bodies | 3 | popped, then their leases take the count through 4 and 5 |
| `MAPT(SLICE:1,2(TOK))` | 5 at the later `next_atom` | `None` |

Score, numeric rank, and select reason remain NOT_RECORDED. Outcome is not a policy.

## Counterfactuals

No semantic model was established, so no preferred counterfactual is constructed. 3.51 already recorded the arithmetic under unlabeled accounting rules. Those stay offline arithmetic. They are not replayed here and they are not evidence for a repair.

| Item | Status |
|---|---|
| Current gate closed at executed 5, max 4 | OBSERVED (reconstructed count, logged leases) |
| A model in which rediscovery should not count | NOT_RECORDED |
| A model in which 4 is a hard safety total that must not move | NOT_RECORDED |
| Materialization if the gate were open | NOT_REPLAYED |

## Hypotheses

| Id | Disposition |
|---|---|
| H19a | Not supported. No document calls it a total-operation safety bound. |
| H19b | Not supported. No document calls it an expensive-execution budget. The increment is not a model call. |
| H19c | Not supported. The counter does not move at materialization. |
| H19d | Not supported. Not documented as recursion or firewall protection. The firewall only zeroes it. |
| H19e | Supported. Behavior is the call graph above. Original intent is absent. |
| H19f | Not established. A bound was written. A purpose for it was not. |
| H19g | Not established for the atom counter. IR later reused its own counter for layer escalation. The atom copy never gained that second use. That is lineage, not a conflated atom meaning. |
| H19-REJECT | Not the result. The architectural mechanism is characterized. The intended resource is not. |

## Unresolved

- Why `max_executed` is 4 rather than 6, or rather than anything else.
- Why the atom copy did not also get a `*_kinds_exhausted` use.
- Whether the firewall zero was meant to refresh a quota or was only part of clearing the board.
- Logged `board.executed`.
- Score, numeric rank, select reason.
- Any discovery consequence of opening the gate.

## Intervention

**NO PRODUCTION INTERVENTION AUTHORIZED.**

Known behavior plus unknown intent does not justify a repair. The PRIMARY block is not reclassified as a bug.
