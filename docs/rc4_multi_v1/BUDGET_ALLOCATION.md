# AIVD-RC4-MULTI-V1: budget allocation

**Status: `pending_user_confirmation` (OPEN DESIGN DECISION D1). The budget was recorded exactly as requested and has not been changed.**

| Stage | Calls per model | Ceiling enforced by |
|---|---|---|
| discovery | 48 | frozen `aivd_post_rc3.driver.run_model` reading `DISCOVERY_LIMIT` (bound to 48) |
| investigation | 24 | `INVESTIGATION_LIMIT` (bound to 24) |
| verification | 12 | `VERIFICATION_LIMIT` (bound to 12); each verification needs `VERIFY_COST` = 3 |
| repeat (reproducibility) | 6 | frozen `run_repeat` reading `aivd_post_rc3.config.REPRO_CALLS_PER_MODEL` (6) on 2 scenarios |
| **total** | **90** | main ledger allocation 84 (`MODEL_ALLOCATION` bound to 84) + repeat 6 |
| **3 models** | **270** | no transfers between models, no reallocation between stages |

## Implementation mapping
- `aivd_rc4_multi.bind.bind()` sets these module globals in-process:
  - `aivd_post_rc3.driver.{DISCOVERY_LIMIT, INVESTIGATION_LIMIT, VERIFICATION_LIMIT, MODEL_ALLOCATION}`
  - `aivd_post_rc3.config.REPRO_CALLS_PER_MODEL`
- The frozen driver reads those globals, so no frozen file is edited.
- `bind()` refuses if the frozen `VERIFY_COST` is not 3.
- Every transport attempt counts one unit against its stage ceiling (frozen `Budget`).
- The ledger records `allocation = {discovery:48, investigation:24, verification:12, total:84}`, which is tested.

## Consequences (prominent)
1. **At most 4 verifications per model** (12 // 3), so at most 4 of 24 security targets can be verified per model. The pooled maximum is 12 of 24.
   - E1 (≥ 2 distinct) is reachable by a single model.
   - E3 per-model ratios are capped at 4/24.
2. **Discovery covers about one third of the corpus.**
   - The frozen discovery costs 3 calls per two-step scenario and 4 per branch scenario.
   - Covering all 48 scenarios (40 two-step, 8 branch) takes **152** calls.
   - At 48 calls a model explores at most **16 of 48** scenarios in the best case and about 13 in the worst case. Mocked runs explored 14–15.
   - LOCAL-V1 explored 15–16 of 24 with the same 48.
   - Each model therefore never sees about 2/3 of the security targets. A NOT_DEMONSTRATED result cannot distinguish "the model failed" from "the model never reached the target".
3. **Investigation.** At 24 calls, investigation may not reach every retained candidate. Candidates it does not reach stay `RETAINED_NOT_INVESTIGATED`, and any that promote but are not verified are reported as `BUDGET_GAP`.

## Options (user chooses; none selected here)
| Option | Discovery / Inv / Ver / Rep | Per model | Total | Coverage | Max verifications per model |
|---|---|---|---|---|---|
| (a) as requested | 48 / 24 / 12 / 6 | 90 | 270 | ≤ 16/48 | 4 |
| (b) full discovery coverage | 152 / 24 / 12 / 6 | 194 | 582 | 48/48 | 4 |
| (c) full coverage + more verification | 152 / 24 / 24 / 6 | 206 | 618 | 48/48 | 8 |
| (d) smaller corpus | n/a | n/a | n/a | n/a | not allowed (requires ≥ 24 + 24) |

Whatever is chosen is written into `PREREGISTRATION.json` (`budget.status` = `confirmed_by_user`) and committed **before** the provider runs. Changing it after the provider runs requires a new experiment id.
