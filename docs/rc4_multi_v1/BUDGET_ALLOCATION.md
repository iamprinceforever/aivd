# AIVD-RC4-MULTI-V1: budget allocation

**Status: `confirmed/frozen-at-design`. User decision D1 = option (c), confirmed on 2026-09-29 (IST).**

These are ceilings. There are no transfers between models and no reallocation between stages. No ceiling may be increased once execution has started; a change would need a new experiment id.

| Stage | Ceiling per model | Enforced by |
|---|---|---|
| discovery | 152 | frozen `aivd_post_rc3.driver.run_model` reads `DISCOVERY_LIMIT` (bound to 152) |
| investigation | 24 | `INVESTIGATION_LIMIT` (bound to 24) |
| verification | 24 | `VERIFICATION_LIMIT` (bound to 24). `VERIFY_COST` = 3, so **at most 8 verifications** |
| repeat (reproducibility) | 6 | frozen `run_repeat` reads `aivd_post_rc3.config.REPRO_CALLS_PER_MODEL` (6), over 2 scenarios |
| **total per model** | **206** | main ledger allocation 200 (`MODEL_ALLOCATION` bound to 200) plus 6 for the repeat |
| **3 models** | **618** | |

## Implementation mapping
- `aivd_rc4_multi.config` holds the frozen numbers.
- `aivd_rc4_multi.bind.bind()` sets these module globals in-process:
  - `aivd_post_rc3.driver.{DISCOVERY_LIMIT, INVESTIGATION_LIMIT, VERIFICATION_LIMIT, MODEL_ALLOCATION}`
  - `aivd_post_rc3.config.REPRO_CALLS_PER_MODEL`

  No frozen file is edited.
- `bind()` refuses to proceed if the frozen `VERIFY_COST` is not 3.
- Every transport attempt counts one unit against the ceiling of its stage (the frozen `Budget`).
- Each ledger records `allocation = {discovery:152, investigation:24, verification:24, total:200}`. This is tested.
- The provider's confirmation gate (`aivd_rc4_multi.provider.run_once.confirmation_gate`) refuses unless `PREREGISTRATION.json` records exactly these ceilings, with status `confirmed/frozen-at-design`.

## Consequences
1. **Coverage.** The frozen discovery spends 3 calls per two-step scenario and 4 per branch scenario. 40 × 3 + 8 × 4 = **152**, so discovery can reach all 48 scenarios.
   - In the fake-model runs every model reached 24/24 security and 24/24 benign targets.
   - A real model can reach fewer if a transport failure stops the run. Exposure is reported per model (D3).
2. **Verification.** At most 8 verifications per model (24 // 3), so at most 8 of 24 security targets per model and 24 pooled.
3. **Investigation.** 24 calls is now the tightest stage.
   - When many candidates are retained, investigation may not reach them all. Unreached candidates stay `RETAINED_NOT_INVESTIGATED`.
   - In the fake leak runs investigation used all 24 calls, and 7–8 targets per model went on to be verified.
   - This is reported under metric K. It is not compensated for.
