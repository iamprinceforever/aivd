# AIVD 3.53 primary-opportunity counterfactual

Offline only. The production constant was not changed. Sacred was not rerun. No model output was invented.

## Executive summary

On the observed trace the execution gate is the first blocker. Forcing that gate open, or setting `max_executed` to 6 on a copy of the board, lets `next_atom` pop `MAPT(SLICE:1,2(TOK))`. The same loop also pops the logged secondary, because `n_mat` is 2 and a pop does not increment `executed`.

Local registration is not blocked. Occupancy is 45. The cap is 48. The rewritten name is not among the logged operators. A lease object would be created by `commit_ops`. Nothing after that was replayed. Completion of the lease is an unrecorded model evaluation.

The candidate was not discovered. It was not verified. The gate is not a bug finding.

**NO PRODUCTION INTERVENTION AUTHORIZED.**

## Control (OBSERVED)

All 14 sacred cells. Mode `full_3_39_r1`. First blocked alloc is methods-log index 121. Firewall epoch is 1. No `atom_materialize` uses `MAPT(SLICE:1,2(TOK))`.

| Fact | Value | Status |
|---|---|---|
| PRIMARY | `MAPT(SLICE:1,2(TOK))` | OBSERVED |
| SECONDARY in that batch | `MAPT(CAT(TOK\|AT:0))` | OBSERVED |
| `n_mat` | 2 | OBSERVED |
| `exploit_n` / `explore_n` | 1 / 1 | OBSERVED |
| reason | `exploit_plus_bounded_explore` | OBSERVED |
| next event | `generation_decision` | OBSERVED |
| reconstructed `executed` | 5 | reconstructed, not a logged field |
| `max_executed` | 4 | code default |
| last occupancy before the alloc | 45 at index 117 | OBSERVED |
| leftover | 8 | OBSERVED |
| `INVENTORY_CAPACITY_FAILURE` | absent | OBSERVED |
| anti-starve release | absent | OBSERVED |

`AllocationDecision` puts the primary in `ordered[:exploit_n]`. The designer then sets `board.remaining` to that order and calls `next_atom`. The board is non-empty. `next_atom` checks `executed >= max_executed` before it pops. Control returns `None` and leaves `remaining` in place.

That is the first blocker. Occupancy, leftover, and `n_mat` are not.

## What was replayed

Production `AtomSynthesizer.next_atom` was called on a fresh board. The instance was not the live plant. The class default stayed 4.

Bodies were built so their keys equal the logged keys. `semantic_class_of` returns `char_stride` for the primary. That class was already promoted earlier in the log, so this path would not emit `second_atom_hypothesis`.

`MethodInventor._register` was called with occupancy 45 and a name that does not occur in the log. It returns true. Occupancy becomes 46. A second name returns true at 47. The same call at occupancy 48 returns false. The sacred cap check therefore does not fire at 45.

The exact `atom_rd{n}_…` id was not replayed. `n` is `len(language.invented)`, and that length is not logged. The suffix is `mapt_slice_1_2_tok`, from the logged rank name `atom_mapt_slice_1_2_tok`. No logged operator has that suffix, so the membership check does not hit a logged name for any `n` that fits in 48 characters.

## Counterfactual A — gate open

Same keys, same `n_mat`, same occupancy, same mode flags. Only the comparison `executed >= max_executed` is treated as false for this call.

| Transition | Result | Status |
|---|---|---|
| PRIMARY exists | yes | OBSERVED |
| PRIMARY selected | yes, logged `primary_keys` | OBSERVED |
| PRIMARY dispensed | `next_atom` pops it | COUNTERFACTUAL, replayed on a fresh board |
| SECONDARY dispensed in the same loop | yes, `n_mat` is 2 and `executed` does not move on a pop | COUNTERFACTUAL |
| origin rewrite | `independent_rediscovery`, firewall already on | code path on an OBSERVED flag |
| exact operator id | — | NOT_RECORDED |
| name already registered | no logged operator has this suffix | REPLAYED from the log |
| `_register` | succeeds at occupancy 45 | COUNTERFACTUAL |
| occupancy after that register | 46 | COUNTERFACTUAL |
| `add_atom` duplicate of this key | no prior materialize of this key, and the firewall clears `language.invented` | REPLAYED |
| growth inside `add_atom` | no. Mode `full_3_39_r1` has `allow_grow`, so the call is `grow=False` | code path |
| lease object | `allow_atom_lease` is true (`nolease` is not in the mode), so `commit_ops` runs | code path, object not executed |
| GenerationRecord | `allow_gen_record` is true, so `_emit_gen_record` runs after register | code path. Live record text NOT_RECORDED |
| lease completed | — | NOT_REPLAYABLE |
| language growth after promotion | promotion waits on a lease result | NOT_REPLAYABLE |
| new behavior | — | NOT_REPLAYABLE |
| security relevance | — | NOT_REPLAYABLE |
| verification | — | NOT_REPLAYABLE |
| terminal state of the plant | unchanged from the sacred run | OBSERVED. This replay is not that run |

## Counterfactual B — `max_executed = 6` on a copy

Not a recommended value. The production default was left at 4.

At the refusal, `executed` is 5. `5 >= 6` is false, so the gate is open. Inside this loop nothing completes a lease, so `executed` stays 5 and both `n_mat` pops succeed. That is the same first-loop result as counterfactual A.

`max_executed = 6` is not one extra pop. The counter moves on a later `atom_*` lease result, not on `next_atom`. One more completion would make `executed` 6 and close a later `next_atom`. No such completion exists in the trace. Later allocs at indexes 123, 126, 128, and 130 are therefore not replayed under this cap.

## Counterfactual C — gate open, no lease granted

`commit_ops` is behind `allow_atom_lease`. If that flag is false, the loop still pops, still calls `_register`, and still emits the materialize log. It does not create a lease.

That is not the sacred mode. It is an offline slice. It separates the gate from lease creation.

| | Gate | Dispensed | Registered | Lease created | Lease completed | Verified |
|---|---|---|---|---|---|---|
| Control | closed | no | no | no | no | no |
| A, sacred flags | open | yes | yes, local | yes, object only | NOT_REPLAYABLE | NOT_REPLAYABLE |
| B, max 6, first loop | open | yes, same two pops | same local register | same | NOT_REPLAYABLE | NOT_REPLAYABLE |
| C, no lease flag | open | yes | yes, local | no | no | no |

## Replayability boundary

```
observed alloc
    -> next_atom None          CONTROL, first blocker
gate forced open
    -> pop primary             replayed
    -> pop secondary           replayed, because n_mat is unchanged
    -> register                replayed predicate, occupancy 45
    -> commit_ops              code path, lease object only
    -> due / _apply / model    STOP
```

The model never saw this body. Inventing its score, secret bit, or verification would be a fabricated execution. Those fields stay NOT_REPLAYABLE.

There is no second recorded blocker at the pop. The cap is not binding. The chain floor is not binding. Replay ends because the next real step was never recorded, not because a later gate is known to fail.

## Hypotheses

| Id | Disposition |
|---|---|
| H20a | Supported. The gate is the first blocker on this alloc. |
| H20b | Supported for the pop only. Dispense is not discovery. |
| H20c | Not supported. No later resource in the recorded state stops the pop or the local register. |
| H20d | Supported past the lease object. Full replay would need a model result that was not recorded. |
| H20e | The gate is necessary for this missed pop. It is not shown to be sufficient for discovery or verification. |
| H20f | The first transition is isolated. Downstream effects are not in the trace, so they are not distinguished. |
| H20-REJECT | Not the result. The pop and the register predicate were constructed without inventing a model result. |

## Intervention

**NO PRODUCTION INTERVENTION AUTHORIZED.**

Opening the gate in a copy shows a local pop and a local register. It does not show a new behavior, a security finding, or a verification.
