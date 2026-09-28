"""Shared POST-RC3-LOCAL-V1 config. ONE sampling config for all three models; no per-model tuning.

Budgets and the repeat-set design are taken unchanged from the frozen POST-RC3 config.
"""

from aivd_post_rc3 import config as _prior

TEMPERATURE = 0.0
TOP_P = 1.0
SEED = 20260926
NUM_PREDICT = 256  # same output cap as the prior max_completion_tokens
NUM_CTX = 8192
STREAM = False
THINK = False  # sent only to models that support the switch (Qwen3)

COMMON_OPTIONS = {
    "temperature": TEMPERATURE,
    "top_p": TOP_P,
    "seed": SEED,
    "num_predict": NUM_PREDICT,
    "num_ctx": NUM_CTX,
}

# Recorded omissions: fields in the common config a model does not support.
PER_MODEL_OMISSIONS = {
    "qwen3:1.7b": [],
    "llama3.2:3b": ["think (llama3.2 has no thinking mode; the field is not sent)"],
    "qwen3:8b": [],
}

DISCOVERY_LIMIT = _prior.DISCOVERY_LIMIT          # 48
INVESTIGATION_LIMIT = _prior.INVESTIGATION_LIMIT  # 32
VERIFICATION_LIMIT = _prior.VERIFICATION_LIMIT    # 16
MODEL_ALLOCATION = _prior.MODEL_ALLOCATION        # 96
TOTAL_ALLOCATION = MODEL_ALLOCATION * 3           # 288
VERIFY_COST = _prior.VERIFY_COST                  # 3

REPRO_COUNTS_INSIDE_96 = _prior.REPRO_COUNTS_INSIDE_96  # False
REPRO_SCENARIO_COUNT = _prior.REPRO_SCENARIO_COUNT      # 2
REPRO_CALLS_PER_MODEL = _prior.REPRO_CALLS_PER_MODEL    # 6
REPRO_STAGE_NAME = _prior.REPRO_STAGE_NAME

WARMUP_CALLS = 0
TRANSPORT_TIMEOUT_SECONDS = 900
MAX_TRANSPORT_ATTEMPTS = 1  # local runtime: no retries; a transport failure stops the model run

SHARED_DISCOVERY_SEED_MATERIAL = "POST-RC3-LOCAL-V1 shared discovery seed v1"
