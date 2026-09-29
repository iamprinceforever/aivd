"""AIVD-RC5-GENERALIZATION-V1 budget, block shape and sampling (DESIGN; budget = proposed decision D1).

Execution unit: one (model, block) run of the frozen POST-RC3 driver against ONE block seal, so the
unmodified frozen judge scores each block ledger against its own block commitment.

Per (model, block) ceilings (D1, proposed): discovery 126 / investigation 32 / verification 18.
Per model: 3 blocks x 176 + 6 repeat (block 1 only) = 534. Three models: 1602. Ceilings only; no
transfers between models, blocks or stages, no increase after execution starts.
See docs/rc5_generalization_v1/BUDGET_ALLOCATION.md.
"""

from aivd_post_rc3 import config as _prior
from aivd_post_rc3_local import config as _local

BLOCK_COUNT = 3
SECURITY_PER_BLOCK = 20
BENIGN_PER_BLOCK = 20
SECURITY_PER_FAMILY_PER_BLOCK = 4
SECURITY_TOTAL = SECURITY_PER_BLOCK * BLOCK_COUNT  # 60
BENIGN_TOTAL = BENIGN_PER_BLOCK * BLOCK_COUNT      # 60
SECURITY_PER_FAMILY_TOTAL = SECURITY_PER_FAMILY_PER_BLOCK * BLOCK_COUNT  # 12

# Frozen RC3 discovery cost per explored scenario (aivd_rc3.discover.run).
DISCOVERY_COST_TWO_STEP = 3   # open, continue, reset-contrast
DISCOVERY_COST_BRANCH = 4     # two prefixes x (branch + probe)
# Per block: 17 two-step kinds + 3 branch kinds, each as security + benign twin.
TWO_STEP_ROWS_PER_BLOCK = 34
BRANCH_ROWS_PER_BLOCK = 6

# Per (model, block) ceilings.
DISCOVERY_LIMIT = TWO_STEP_ROWS_PER_BLOCK * DISCOVERY_COST_TWO_STEP + BRANCH_ROWS_PER_BLOCK * DISCOVERY_COST_BRANCH  # 126
INVESTIGATION_LIMIT = 32
VERIFICATION_LIMIT = 18
BLOCK_ALLOCATION = DISCOVERY_LIMIT + INVESTIGATION_LIMIT + VERIFICATION_LIMIT  # 176
REPEAT_LIMIT = 6        # once per model, on block 1 only
REPEAT_BLOCK = 1
MODEL_ALLOCATION = BLOCK_ALLOCATION * BLOCK_COUNT + REPEAT_LIMIT  # 534
MODEL_COUNT = 3
TOTAL_ALLOCATION = MODEL_ALLOCATION * MODEL_COUNT                 # 1602
BUDGET_STATUS = "proposed/pending-user-confirmation"
BUDGET_DECISION = "D1"

VERIFY_COST = _prior.VERIFY_COST                          # 3, frozen RC3 (independent repeat + 2 source-swap calls)
MAX_VERIFICATIONS_PER_BLOCK = VERIFICATION_LIMIT // VERIFY_COST  # 6

REPRO_SCENARIO_COUNT = _prior.REPRO_SCENARIO_COUNT        # 2
REPRO_CALLS_PER_MODEL = _prior.REPRO_CALLS_PER_MODEL      # 6 (== REPEAT_LIMIT)
assert REPRO_CALLS_PER_MODEL == REPEAT_LIMIT

# Sampling / runtime: reused unchanged from the frozen POST-RC3-LOCAL-V1 config (also RC4's values).
TEMPERATURE = _local.TEMPERATURE       # 0.0
TOP_P = _local.TOP_P                   # 1.0
SEED = _local.SEED                     # 20260926
NUM_CTX = _local.NUM_CTX               # 8192
NUM_PREDICT = _local.NUM_PREDICT       # 256
STREAM = _local.STREAM                 # False
THINK = _local.THINK                   # False (Qwen3 only; field omitted for llama3.2)
COMMON_OPTIONS = dict(_local.COMMON_OPTIONS)
TRANSPORT_TIMEOUT_SECONDS = _local.TRANSPORT_TIMEOUT_SECONDS  # 900
MAX_TRANSPORT_ATTEMPTS = _local.MAX_TRANSPORT_ATTEMPTS        # 1
WARMUP_CALLS = 0
FROZEN_SAMPLING = {"temperature": 0.0, "top_p": 1.0, "seed": 20260926, "num_predict": 256, "num_ctx": 8192}
assert COMMON_OPTIONS == FROZEN_SAMPLING and STREAM is False and THINK is False

# Common discovery order (D2, proposed): one seed shared by all three models; fixed now, at design.
COMMON_ORDER_SEED_MATERIAL = "AIVD-RC5-GENERALIZATION-V1 common discovery order seed v1"


def discovery_coverage(n_two_step: int = TWO_STEP_ROWS_PER_BLOCK, n_branch: int = BRANCH_ROWS_PER_BLOCK,
                       limit: int = DISCOVERY_LIMIT) -> dict:
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
    return {"scenarios": len(costs), "calls_to_cover_all": sum(costs),
            "best_case_explored": fit(sorted(costs)), "worst_case_explored": fit(sorted(costs, reverse=True)),
            "limit": limit}
