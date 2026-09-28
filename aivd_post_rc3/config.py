"""Shared POST-RC3 Groq evaluation config. ONE config for all three models.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
No per-model tuning. Provider-mandated parameter differences are documented
neutrally in PROVIDER_MANDATED and applied only where the provider requires them.
"""

from aivd_post_rc3.models import GPT_OSS_MODELS, MODELS

PROVIDER = "Groq"
BASE_URL = "https://api.groq.com/openai/v1"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MODELS_PATH = "/models"
HTTP_LIBRARY = "urllib.request (stdlib)"
API_SURFACE = "OpenAI-compatible Chat Completions"

# Shared sampling (identical for all three models).
TEMPERATURE = 0.0
MAX_COMPLETION_TOKENS = 256
TOP_P = 1.0
SEED = 20260926  # sent whenever the API accepts it
STREAM = False

# Message structure: system (evaluator-injected note, when applicable) + user turns.
# Discovery/investigation never author system messages; only the evaluator wire does.
MESSAGE_ROLES = ("system", "user", "assistant")

# Provider-mandated extras that apply ONLY to GPT-OSS (not llama-3.3-70b-versatile).
# Documented neutrally; not a tuning choice. reasoning_effort=low keeps token use bounded
# under the shared max_completion_tokens; include_reasoning=false keeps the visible
# completion text comparable to non-reasoning models.
PROVIDER_MANDATED = {
    "openai/gpt-oss-20b": {"reasoning_effort": "low", "include_reasoning": False},
    "openai/gpt-oss-120b": {"reasoning_effort": "low", "include_reasoning": False},
}

# ---- Budget (preregistered; no reallocation after observing results) ----
DISCOVERY_LIMIT = 48
INVESTIGATION_LIMIT = 32
VERIFICATION_LIMIT = 16
MODEL_ALLOCATION = DISCOVERY_LIMIT + INVESTIGATION_LIMIT + VERIFICATION_LIMIT  # 96
TOTAL_ALLOCATION = MODEL_ALLOCATION * len(MODELS)  # 288
VERIFY_COST = 3  # identical to frozen RC3: independent repeat + two source-swap calls

# Retry policy (transport errors only). EVERY attempt, including retries, counts as one
# budget unit against the current stage ceiling.
MAX_TRANSPORT_ATTEMPTS = 3  # 1 initial + 2 retries
RETRYABLE_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
RETRY_BACKOFF_SECONDS = (1.0, 2.0)  # after attempt 1 and 2 respectively
TRANSPORT_TIMEOUT_SECONDS = 120

# Reproducibility repeat set: SEPARATE from the 96. After the main ledger is frozen,
# re-run discovery for the first REPRO_SCENARIO_COUNT scenarios under a fresh namespace
# (same public prompts). Enables within-model L2/L3/L4 comparison on those scenarios.
# Does NOT count against the 96. Fixed now; not reallocatable.
REPRO_COUNTS_INSIDE_96 = False
REPRO_SCENARIO_COUNT = 2
REPRO_CALLS_PER_MODEL = 6  # 2 scenarios * ~3 discovery calls (two-step shape)
REPRO_STAGE_NAME = "repro_repeat"

# Shared discovery seed material (per-model seed is derived; see seeds.py).
SHARED_DISCOVERY_SEED_MATERIAL = "POST-RC3-GROQ shared discovery seed v1"

WARMUP_CALLS = 0  # no warm-up on the hosted API (preregistered)
