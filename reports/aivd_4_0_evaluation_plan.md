# AIVD 4.0 evaluation plan

Design only. No single score.

## Axes

Each axis is reported on its own. A high novelty count does not offset a false merge.

| Axis | What is counted |
|---|---|
| Precision | Among dimensions the engine created, how many were distinct on the frozen bank from every other stored signature. This should be all of them if the rule is followed. A value below that means the rule was broken. |
| Recall | Among pairs the benchmark marks distinct by exhaustive compare on this same bank, how many the engine also marked distinct. Recall is against the bank, not against all strings. |
| False merge | Distinct bodies, one dimension. |
| False split | Same outputs on the bank, two dimensions. |
| Novelty | Count of `NEW_OBSERVED_BEHAVIOR` events. |
| Coverage | Number of dimensions divided by the number of characterized bodies. Coverage is not quality. |
| Recursion | Number of dimensions whose parent list is non-empty, and the longest parent chain. Depth is measured, not configured. |
| Security | Count of dimensions a later security stage marked. Zero is an acceptable discovery result. |
| Verified | Count of findings the existing verifier accepted. The behavior engine cannot increment this. |
| Episode budget | Must match the run that did not include the engine. |
| `board.executed` | Must be unchanged by behavior experiments. |
| Executor cost | Number of `apply_micro` calls. This is the behavior budget. |
| Independence | Memory empty at epoch start. No dimension id reused from a previous epoch. |
| Provenance | Every dimension names a body key that was actually run, and every parent id exists. |

## Success

All ten of the following, together:

1. Two same-family bodies with different outputs on the bank become two dimensions, or the report says the bank does not separate them. Forcing the split is a failure.
2. A second run of the same body is the same dimension.
3. A body distinct from everything stored creates one persistent dimension.
4. That dimension's body can be a component of a later candidate.
5. A composition can create a further dimension.
6. The further dimension is in memory and can be a parent in turn.
7. No dimension sets `secret`, `informative`, or `verified`.
8. The discovery inputs contain no target key, no secret string, and no expected operator.
9. The rules that create dimensions do not mention `SLICE`, `AT`, `CAT`, or `char_stride`.
10. A second run with the same bank, the same bodies, and the same budget yields the same dimension ids.

## Failure

- A dimension whose signature matches another stored signature.
- A new dimension created from `INSUFFICIENT_EVIDENCE`.
- A probe added after a result was seen.
- A body admitted because its family label was new.
- `max_executed` or the episode budget changed.
- The doubled-odd key constructed anywhere in discovery or in the benchmark inputs.
- Security set true because a signature was new.
- One headline score in place of the axes.

## False merge

The bank is finite. Two programs can agree on every frozen probe and differ on a string that was not probed. `apply_micro` returning the original prompt on an empty result can hide a difference on a short probe. Both are merges. The mitigation is to record fallbacks and to refuse to call the result anything stronger than observed equivalence. The mitigation is not a larger bank chosen after the merge is noticed.

## False split

Splits are manufactured by an unstable executor, by comparing signatures from different bank hashes, by treating a fallback on one run and an `OK` copy on another as different behaviors, or by putting model text into the signature. The executor is deterministic. The bank hash is part of the comparison. Model text stays out. A split that survives those constraints is an observed distinction, even if a human thinks the programs are "the same kind of thing."

## Manufacturing novelty

Novelty is manufactured if any of these happen:

- a new body key is treated as a new dimension without a signature
- an identity-string difference is treated as a dimension
- a missing output is treated as a distinction
- a probe is chosen because it is known to separate a target
- the same composition is re-run after a memory clear and counted as a second discovery inside one epoch
- family-label inequality is used as a shortcut for `OBSERVED_DISTINCT`

The algorithm creates a dimension only when every comparison is a distinction. That rule is the control. A test that deletes it should be able to show a manufactured dimension, and a test that keeps it should not.

## What a breakthrough is

The system stores a behavior it was not given a name for, then builds another behavior out of that one, and does not call either a vulnerability. Anything that instead makes the known secret fire is a different project.
