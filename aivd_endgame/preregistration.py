"""Hash the end-goal protocol. The realized seal is not part of this hash."""

import hashlib
import json
from pathlib import Path

from aivd_endgame.spec import (
    EXPERIMENT,
    MAX_MODEL_CALLS,
    MODEL,
    MODEL_DIGEST,
    MODEL_SEED,
    NUM_CTX,
    NUM_PREDICT,
    PUBLIC_TASK,
    RELATION_FAMILY_SIZE,
    REPEAT_PENALTY,
    RUNTIME_COMMIT,
    RUNTIME_DIGEST,
    RUNTIME_VERSION,
    SCENARIOS,
    TARGET_COUNT,
    TEMPERATURE,
    THINK,
    TOP_K,
    TOP_P,
    MIN_P,
)

ROOT = Path(__file__).resolve().parent
HASHED = (
    "discovery.py",
    "interface.py",
    "harness.py",
    "provider.py",
    "verifier.py",
    "authorize.py",
    "execute.py",
)


def preregistration_hash() -> str:
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in HASHED}
    body = {
        "experiment": EXPERIMENT,
        "question": "Can the blind discovery procedure independently surface and reproduce the one sealed security behavior?",
        "scenarios": SCENARIOS,
        "target_count": TARGET_COUNT,
        "relation_family_size": RELATION_FAMILY_SIZE,
        "max_model_calls": MAX_MODEL_CALLS,
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "runtime_version": RUNTIME_VERSION,
        "runtime_commit": RUNTIME_COMMIT,
        "runtime_digest": RUNTIME_DIGEST,
        "seed": MODEL_SEED,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "temperature": TEMPERATURE,
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
        "repeat_penalty": REPEAT_PENALTY,
        "think": THINK,
        "public_task": PUBLIC_TASK,
        "early_stop": False,
        "files": files,
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
