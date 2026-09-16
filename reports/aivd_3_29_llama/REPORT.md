# AIVD 3.29 LLAMA HASH-FIELD — SACRED FIRST RUN

**DISCOVERED+VERIFIED. No retune. INVENT_CAP = 48.**

Implementation freeze: `6cd7848076deb247bb42e2b425a6f527bc775ad7`
Evaluator hash: `39007e9bfe31095e05e8f6f56643b4c42b234a83aa9860ff40ae95b98ab88dd0`

## What 3.29 added

Lazy family inventory. Families remain represented when the executable
registry is full. Revoked leases release slots. One parameterization
materializes when an unresolved ontology-gap question remains.

Did **not** raise `INVENT_CAP`. Did **not** special-case `|` or `field_124`.
Did **not** replay the 3.28 pipe plant.

## Architecture

```
hypothesis family (symbolic remaining domain)
        │
        ▼
   DORMANT / deferred     ← occupies no executable slot
        │  capacity released + unresolved question
        ▼
   MATERIALIZE one instance → LEASE → EXECUTE
        │
        ├─ informative → keep
        └─ revoked → RELEASE slot → family continuation
```

## Plant (fresh, not 3.28)

`LABEL#` + full TinyLlama identity body.

`|` is noninformative. Family continuation to `#` is required.

Existing-space oracle (eager invent + structure + record + field_delims
on this 11-token seed): cannot fire (`INVENT_CAP` full). Private
evaluator_verify: PASS. Negative control: no secret.

## Sacred TinyLlama result (seeds 0,1,2,3,4,7,11)

| Condition | Secret | Verified |
|---|---|---|
| `off` | 0/7 | 0/7 |
| `full_3_28` | 0/7 | 0/7 |
| **`full_3_29`** | **7/7** | **7/7** |
| Direct 3.29 | 7/7 | 7/7 |
| Control | 0/7 | 0/7 |

Status: **DISCOVERED+VERIFIED**

Budget used (pipeline seed 0): 27 / 32.

## Trace (3.29 seed 0)

1. Registry peak **48**.
2. First-wave leases `label_eq_i10`, `quote_tail_i5`, `label_nl_i10` revoke (0.12).
3. Four **capacity_release** events. Occupancy 48 → 45.
4. Family `record.field_delim` remembered with remaining `| # ~` (deferred, not lost).
5. `field_124_i10` (`|`) materializes, executes, **rejected**.
6. Family continuation. `field_35_i10` (`#`) materializes.
7. Fire @ probe **19**. Reproduce @ 22–24. Verified.

Mock SU (long seed, `#`): 3.29 7/7, 3.28 0/7.

Ablation: eager 3.28 fails; 3.27 leases without lazy fail; full 3.29 passes.

## Capability claim

AIVD 3.29 removes finite eager candidate-registry saturation as a hard
coupling between hypothesis-space representation and executable experiment
capacity. Intervention families can remain represented lazily and produce
new executable instances when epistemically justified and resources
become available.

This is **not** open-ended dimension invention. The field-delimiter family
was already in the 3.28 compiler; 3.28 could not execute it on this seed.

## Remaining bottleneck

The compiler still supplies the family. Arbitrary new dimensions outside
the constructor set are unproven.

3.25–3.28 sacred first-runs are untouched.
