# AIVD 4.0 behavioral model

Design only. The words below are the contract for a later implementation. They are not code.

## Signature

A signature is the ordered list of outputs of one program on one frozen bank.

For probe `p` and body `b`:

- Run `apply_micro(p, b)` once.
- If the executor returns `p` because the program produced no tokens, status is `EXECUTOR_FALLBACK` and the stored output is `p`. The fallback is visible. It is not treated as a successful transform that happened to copy the input, unless the program really did copy the input and the executor did not take the empty branch. The engine cannot see that difference from the return value alone. Both cases are recorded as the output string `p` with status `EXECUTOR_FALLBACK` only when the empty branch was taken. A true identity transform that returns tokens equal to the input is status `OK`. The implementation must distinguish those two by observing the empty branch, not by guessing from the string.
- Any other return is status `OK`.

The signature does not contain `semantic_class_of`, `informative`, `secret`, or `representation_gap`.

The same body on the same bank is the same signature. Replay is a byte compare of that list.

## Distance

Compare two signatures on the same bank hash. If the hashes differ, the result is `INSUFFICIENT_EVIDENCE`. Do not align probes after the fact.

On a shared bank, probe by probe:

- Both statuses comparable and outputs equal: agreement.
- Both comparable and outputs unequal: a distinction.
- Either side missing: that probe is not evidence.

Then:

- At least one distinction: `OBSERVED_DISTINCT`.
- No distinction, and every probe comparable: `OBSERVED_EQUIVALENT`.
- No distinction, but some probe not comparable: `INSUFFICIENT_EVIDENCE`.

`OBSERVED_EQUIVALENT` means "same outputs on this bank." It does not mean the programs are the same function. `OBSERVED_DISTINCT` means "they differed on at least one frozen probe." It does not mean they differ on every string.

There is no operator-specific rule. `SLICE`, `AT`, and `CAT` are not consulted. Body keys are not consulted. A family label is not a distance.

## Dimension

A dimension is one stored signature plus the bodies that matched it.

The first body whose comparison against every stored dimension is `OBSERVED_DISTINCT`, with no `INSUFFICIENT_EVIDENCE` against any of them, creates a dimension. Its id is a hash of the bank hash and the signature, not a hash of the body key and not a name like `char_stride`.

A later body that is `OBSERVED_EQUIVALENT` to that signature is a new observation of the same dimension. The body key is stored. The dimension id does not change.

`INSUFFICIENT_EVIDENCE` creates nothing. Missing outputs are not novelty.

A new dimension is `NEW_OBSERVED_BEHAVIOR`. That phrase is the whole claim. It is not security-relevant, not verified, and not a family.

## Memory

Memory answers four questions.

- Seen before: an `OBSERVED_EQUIVALENT` hit.
- Distinguishable: `OBSERVED_DISTINCT` from every stored signature.
- New dimension: distinguishable, and no insufficient comparison.
- What composed into it: the parent body keys and their dimension ids, recorded at creation. They are not inferred later.

Memory is empty at the start of a fresh plant and empty after a firewall epoch boundary. A dimension learned before the firewall is not "already seen" after it. Carrying it across would make an independent rediscovery look like a known behavior.

Two bodies with the same key are one observation. Two bodies with different keys and equivalent signatures are one dimension. The family label may be the same or different. The label is stored as a side note and is never the lookup key.

## Novelty

```
signature = experiment(body, frozen_bank)
if signature cannot be completed:
    return INSUFFICIENT_EVIDENCE
for dimension in memory:
    relation = compare(signature, dimension.signature)
    if relation is OBSERVED_EQUIVALENT:
        return KNOWN(dimension)
    if relation is INSUFFICIENT_EVIDENCE:
        return INSUFFICIENT_EVIDENCE
return NEW_OBSERVED_BEHAVIOR
```

The loop does not stop at the first distinction. A new dimension requires a distinction from every stored one. The first equivalent hit is enough to call it known.

No score is added to `informative`. No secret bit is set.

## Frontier

The frontier is the set of unevaluated compositions of bodies that already have dimensions, plus the bodies that have been characterized and the pairs that have been tried.

A pair is unexplored until its composition has a signature. After the signature, the pair is either a new dimension, a known dimension, or insufficient. It is not left in a fourth state that means "probably new."

Selection spends a declared behavior budget of executor calls. It does not spend `board.executed` and it does not spend the episode budget. A fixed fraction of that behavior budget, chosen before the run, goes to unevaluated pairs. The rest may re-evaluate bodies already in memory when a later security stage asks for them. The fraction is not tuned because a particular body has not yet appeared.

There is no maximum depth. Growth stops when the behavior budget is spent or the frontier has no unevaluated pair whose components are already in memory. The depth of the resulting chain is an outcome.

## Growth

Given dimensions `B1` from body `A` and `B2` from body `C`, a candidate is the sequential program `C` after `A`, which is the shape `language.compose` already uses: `fb(fa(p))`. The candidate is not admitted because the family labels differ, and it is not rejected because one identity string matched. It is executed on the same frozen bank.

- Distinct from `B1`, from `B2`, and from every other stored dimension: new dimension `B3`, with parents `B1` and `B2`.
- Equivalent to any stored dimension, including a parent: known. Record the composition as another body of that dimension.
- Insufficient: do not store a dimension. The pair stays unexplored or is marked insufficient. It is not novelty.

`B3` is then an ordinary dimension. Later pairs may use any body that maps to it. That is the recursion. Nobody writes "level 3" into the engine.

A composition that stays inside `char_stride` and is `OBSERVED_DISTINCT` from its component is a new dimension in the same family. The even-stride double is the historical example of that shape. The engine is not allowed to special-case it. If the frozen bank separates it, the general rule will. If the bank does not, the engine must not add a probe to make it so.

## What this refuses to mean

A new body is not a new dimension. A new family label is not a new dimension. A difference on the identity string alone is not a new dimension. A model completion is not part of the signature. `informative=false` does not merge two signatures. `representation_gap` does not split them.
