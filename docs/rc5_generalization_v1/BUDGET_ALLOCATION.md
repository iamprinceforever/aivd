# Budget allocation (FROZEN_AT_DESIGN; binding user spec)

| stage | calls per model |
|---|---|
| discovery | 320 |
| investigation | 48 |
| verification | 30 (≤ 10 candidates × VERIFY_COST 3) |
| repeat | 6 |
| **total** | **404** |

- The maximum total over 3 models is **1212**.
- No per-block budgets and no transfers between stages or models. Ceilings are enforced by the frozen
  driver after `aivd_rc5_gen.bind` installs the allocation.
- **Exposure ledger.** `aivd_rc5_gen.scoring.score.exposure` records, per model, **security exposed/60**
  and **benign exposed/60** (a scenario counts as exposed when the frozen discovery explored it). The
  preflight also pre-computes exposure from the committed order and public shapes.

## Spec contradiction: full exposure within 320 is impossible
- The binding spec asks the scheduler to expose all 120 scenarios at least once within 320 discovery
  calls.
- The frozen `aivd_rc3.discover.run` spends **3 calls per two-step scenario** (open, continue,
  reset-contrast) and **4 per branch scenario** (two prefixes × branch + probe), with no retries.
- The corpus has 108 two-step and 12 branch scenarios, so **full coverage costs 108 × 3 + 12 × 4 = 372
  calls > 320**.
- The most scenarios coverable within 320 is **106** (best case: branches last) and **102** (worst case).
  `config.discovery_coverage()` computes this; the audit and tests check it.
- This design does **not** modify the frozen discovery and does **not** change the binding budget.
  Instead:
  - exposure is recorded exactly;
  - per the spec, E-ROBUST-UNSEEN is marked **NOT_DEMONSTRATED** for any model whose security exposure
    is not 60/60;
  - so E-ROBUST-UNSEEN condition (4) is **structurally expected to be NOT_DEMONSTRATED for every model**.
- E-CROSS-FAMILY is not affected.
- **User decision required.** Options that would make full exposure feasible (none is adopted here):
  - (a) discovery ≥ 372 per model (e.g. 372/48/30/6 = 456 per model, 1368 total);
  - (b) a corpus with fewer or cheaper scenarios;
  - (c) accept the structural NOT_DEMONSTRATED.
