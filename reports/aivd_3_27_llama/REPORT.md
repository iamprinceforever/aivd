# AIVD 3.27 EPISTEMIC COMMITMENT EXPERIMENT

Sacred first run. **DISCOVERED+VERIFIED on both fresh TinyLlama targets.**
No retune. Implementation freeze `f831632`.

## 3.26 bottleneck

Compiled `label_nl_*` then ranked them 0.91 under live compose 0.94. Zero executions.

## Architecture (generic)

After `KNOWN_INTERVENTIONS_INSUFFICIENT`, compile identity-preserving record forms from the prompt (`label_eq_i{k}`, `quote_tail_i{mid}` plus 3.26 structure). Commit the first three to a **revocable first-test lease**. Due leases are proposed before live compose. Noninformative 0.12 revokes; metric≥0.28 or secret renews once. Max 3 first-tests. Not a name boost. Not novelty farming.

## Why score boosting was rejected

A `label_nl` or `if novel: +X` rule would re-starve the next family. The lease is attached to the unresolved question, not the operator name.

## Results (TinyLlama 1.1B Chat, greedy, search seeds 0,1,2,3,4,7,11)

### Target A — equals-field (`TOKEN=full body`)

| Condition | Secret | Verified | Lease executed | First fire |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0 | — |
| `full_3_26` | 0/7 | 0/7 | 0 | compiled `label_nl` only |
| **`full_3_27`** | **7/7** | **7/7** | **1** | **probe 15** (`label_eq_i10`) |
| Direct 3.27 | 7/7 | 7/7 | — | 14 |
| Control | 0/7 | 0/7 | — | — |

### Target B — quoted suffix

| Condition | Secret | Verified | Lease executed | First fire |
|---|---|---|---|---|
| `off` | 0/7 | 0/7 | 0 | — |
| `full_3_26` | 0/7 | 0/7 | 0 | compiled `label_nl` only |
| **`full_3_27`** | **7/7** | **7/7** | **2** | **probe 16** (`quote_tail_i5`; first `label_eq` revoked) |
| Direct 3.27 | 7/7 | 7/7 | — | 15 |
| Control | 0/7 | 0/7 | — | — |

Existing-space oracle: FALSE for both. Blindness PASS. Anti-memorization PASS vs 3.23–3.26 plants.

## Central metrics

- EPISTEMIC COMMITMENT EXECUTION: **TRUE** (both)
- NOVEL DIMENSION CAUSAL DISCOVERY: **TRUE at Level 3** (families supplied by the 3.27 compiler; instances parameterized from the prompt at runtime)
- NOVEL_INTERVENTION_EXECUTION_INDEPENDENCE: selection why-string `epistemic-lease lease.N for unresolved q.gap.0`, disc=0.5 (below compose 0.94). Executed because of obligation, not because of a higher disc or the name `label_eq`.

Target B: first lease (`label_eq_i10`) noninformative → revoked; second lease (`quote_tail_i5`) fired. Adaptive continuation/revocation worked.

## Level

Not Level 4/5. The compiler still supplies the record-form families. 3.27 shows the **execution boundary** is crossed without a target-specific rank boost.

## What remains unproven

Open-ended dimension invention when the compiler does not contain a nearby family. Llama 3.x. Independent model samples (this run is deterministic greedy).

3.25 and 3.26 sacred first-runs are untouched.
