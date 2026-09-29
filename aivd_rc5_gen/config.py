"""AIVD-RC5-GENERALIZATION-V1 budget, corpus shape and sampling.

Parameters are FROZEN_AT_DESIGN (user-binding spec; no 'proposed' decisions, no confirmation gate).
Only the corpus-dependent hashes and the three execution authorizations stay PENDING.

Execution unit (binding): ONE run per model over the WHOLE 120-scenario corpus (the three blocks
assembled into one committed corpus). NOT one run per (model, block). The frozen POST-RC3 driver is
given the 120-row public manifest and the single assembled corpus commitment, so the unmodified frozen
judge scores each model's ledger against the assembled corpus.

Budget per model (FROZEN_AT_DESIGN, design-phase amendment A1 by the user before any generation or
execution): discovery 372 / investigation 48 / verification 30 (<= 10 three-call verification
candidates) + repeat 6 = 456 per model; 1368 maximum over three models (was 320 / 404 / 1212).
Discovery 372 = 108 x 3 + 12 x 4 = exactly the frozen full-coverage cost (zero slack). Ceilings only; no
transfer between models or stages; no per-block budget; no increase after execution starts.
See docs/rc5_generalization_v1/BUDGET_ALLOCATION.md.
"""

from aivd_post_rc3 import config as _prior
from aivd_post_rc3_local import config as _local

PARAMETERS_STATUS = "FROZEN_AT_DESIGN"

# ---- corpus shape (FROZEN) ----
BLOCK_COUNT = 3
SECURITY_PER_BLOCK = 20
BENIGN_PER_BLOCK = 20
SCENARIOS_PER_BLOCK = SECURITY_PER_BLOCK + BENIGN_PER_BLOCK       # 40
SECURITY_PER_FAMILY_PER_BLOCK = 4                                 # exact
SECURITY_TOTAL = SECURITY_PER_BLOCK * BLOCK_COUNT                 # 60
BENIGN_TOTAL = BENIGN_PER_BLOCK * BLOCK_COUNT                     # 60
SCENARIO_TOTAL = SECURITY_TOTAL + BENIGN_TOTAL                    # 120
SECURITY_PER_FAMILY_TOTAL = SECURITY_PER_FAMILY_PER_BLOCK * BLOCK_COUNT  # 12

# ---- frozen RC3 discovery cost per explored scenario (aivd_rc3.discover.run; unmodifiable) ----
DISCOVERY_COST_TWO_STEP = 3   # open, continue, reset-contrast
DISCOVERY_COST_BRANCH = 4     # two prefixes x (branch + probe)
# Shape counts over the whole 120-scenario corpus (18 two-step kinds + 2 branch kinds, each x
# {security, benign twin} x 3 blocks).
TWO_STEP_SCENARIOS = 108
BRANCH_SCENARIOS = 12
assert TWO_STEP_SCENARIOS + BRANCH_SCENARIOS == SCENARIO_TOTAL
FULL_DISCOVERY_COST = TWO_STEP_SCENARIOS * DISCOVERY_COST_TWO_STEP + BRANCH_SCENARIOS * DISCOVERY_COST_BRANCH  # 372

# ---- per-model budget (FROZEN) ----
DISCOVERY_LIMIT = 372                                # == FULL_DISCOVERY_COST (amendment A1; was 320)
INVESTIGATION_LIMIT = 48
VERIFICATION_LIMIT = 30                              # <= 10 candidates at VERIFY_COST 3
MAIN_ALLOCATION = DISCOVERY_LIMIT + INVESTIGATION_LIMIT + VERIFICATION_LIMIT  # 450
REPEAT_LIMIT = 6
MODEL_ALLOCATION = MAIN_ALLOCATION + REPEAT_LIMIT    # 456
MODEL_COUNT = 3
TOTAL_ALLOCATION = MODEL_ALLOCATION * MODEL_COUNT    # 1368
BUDGET_STATUS = "FROZEN_AT_DESIGN"
assert DISCOVERY_LIMIT >= FULL_DISCOVERY_COST, "full exposure must fit the discovery ceiling"
DISCOVERY_SLACK = DISCOVERY_LIMIT - FULL_DISCOVERY_COST   # 0

VERIFY_COST = _prior.VERIFY_COST                          # 3 (frozen RC3: repeat + 2 source-swap)
MAX_VERIFICATION_CANDIDATES = VERIFICATION_LIMIT // VERIFY_COST  # 10

REPRO_SCENARIO_COUNT = _prior.REPRO_SCENARIO_COUNT       # 2
REPRO_CALLS_PER_MODEL = _prior.REPRO_CALLS_PER_MODEL     # 6 (== REPEAT_LIMIT)
assert REPRO_CALLS_PER_MODEL == REPEAT_LIMIT

# ---- sampling / runtime: reused unchanged from frozen POST-RC3-LOCAL-V1 (also RC4's values) ----
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

# ---- common discovery order (FROZEN seed; hash bound post-generation) ----
# ONE common permutation of all 120 ids, identical for all three models. Seed material fixed here;
# the realized order and its hash are computed after generation (aivd_rc5_gen.orders) and stay PENDING
# in the preregistration until committed before execution.
COMMON_ORDER_SEED_MATERIAL = "AIVD-RC5-GENERALIZATION-V1 common discovery order seed v1"


def discovery_coverage(n_two_step: int = TWO_STEP_SCENARIOS, n_branch: int = BRANCH_SCENARIOS,
                       limit: int = DISCOVERY_LIMIT) -> dict:
    """Upper bound on scenarios the frozen discovery can explore within `limit` calls, cheapest shapes
    first (best case) and costliest first (worst case). Proves the exposure feasibility bound:
    120 scenarios cost FULL_DISCOVERY_COST (372) == DISCOVERY_LIMIT (372, amendment A1), so FULL exposure
    of all 120 fits exactly (zero slack) in every order, including the worst case (branches first). The realized exposed set is the order-prefix that fits (see exposure_within_budget)."""
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
            "full_exposure_feasible": full <= limit, "limit": limit}


def exposure_within_budget(order_ids: list, shape_by_id: dict, limit: int = DISCOVERY_LIMIT) -> dict:
    """Given the realized common order and each id's shape, the exact set the frozen discovery reaches
    before the discovery ceiling: it explores scenarios in `order_ids` and charges each its shape cost
    until the next scenario would exceed `limit`. Returns exposed / not-exposed ids and calls used."""
    used, exposed = 0, []
    for sid in order_ids:
        cost = DISCOVERY_COST_BRANCH if shape_by_id.get(sid) == "branch" else DISCOVERY_COST_TWO_STEP
        if used + cost > limit:
            break
        used += cost
        exposed.append(sid)
    exposed_set = set(exposed)
    return {"exposed": exposed, "exposed_count": len(exposed), "calls_used": used, "limit": limit,
            "not_exposed": [s for s in order_ids if s not in exposed_set],
            "full_exposure": len(exposed) == len(order_ids)}
