"""AIVD-RC4-MULTI-V1 budget and sampling (DESIGN; budget is an OPEN DESIGN DECISION).

The requested budget is recorded exactly. It is NOT confirmed: see docs/rc4_multi_v1/BUDGET_ALLOCATION.md.
"""

from aivd_post_rc3 import config as _prior

# Requested allocation (per model). Status: pending_user_confirmation.
DISCOVERY_LIMIT = 48
INVESTIGATION_LIMIT = 24
VERIFICATION_LIMIT = 12
REPEAT_LIMIT = 6
MAIN_ALLOCATION = DISCOVERY_LIMIT + INVESTIGATION_LIMIT + VERIFICATION_LIMIT  # 84
MODEL_ALLOCATION = MAIN_ALLOCATION + REPEAT_LIMIT                              # 90
MODEL_COUNT = 3
TOTAL_ALLOCATION = MODEL_ALLOCATION * MODEL_COUNT                              # 270
BUDGET_STATUS = "pending_user_confirmation"

VERIFY_COST = _prior.VERIFY_COST            # 3, frozen RC3 (independent repeat + 2 source-swap calls)
MAX_VERIFICATIONS = VERIFICATION_LIMIT // VERIFY_COST  # 4 per model

REPRO_SCENARIO_COUNT = _prior.REPRO_SCENARIO_COUNT  # 2
REPRO_CALLS_PER_MODEL = _prior.REPRO_CALLS_PER_MODEL  # 6 (== REPEAT_LIMIT)
assert REPRO_CALLS_PER_MODEL == REPEAT_LIMIT

# Frozen RC3 discovery cost per explored scenario (aivd_rc3.discover.run).
DISCOVERY_COST_TWO_STEP = 3   # open, continue, reset-contrast
DISCOVERY_COST_BRANCH = 4     # two prefixes x (branch + probe)

SHARED_DISCOVERY_SEED_MATERIAL = "AIVD-RC4-MULTI-V1 shared discovery seed v1"
TRANSPORT_TIMEOUT_SECONDS = 900
WARMUP_CALLS = 0
MAX_TRANSPORT_ATTEMPTS = 1


def discovery_coverage(n_two_step: int, n_branch: int, limit: int = DISCOVERY_LIMIT) -> dict:
    """Upper bound on scenarios the frozen discovery can explore within `limit` calls,
    cheapest shapes first (best case) and costliest first (worst case)."""
    def fit(costs):
        used = n = 0
        for c in costs:
            if used + c > limit:
                break
            used += c
            n += 1
        return n
    costs = [DISCOVERY_COST_TWO_STEP] * n_two_step + [DISCOVERY_COST_BRANCH] * n_branch
    full = sum(costs)
    return {"scenarios": len(costs), "calls_to_cover_all": full,
            "best_case_explored": fit(sorted(costs)), "worst_case_explored": fit(sorted(costs, reverse=True)),
            "limit": limit}
