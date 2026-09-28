"""Per-model discovery seeds derived from a shared material. Deterministic isolation."""

import hashlib

from aivd_post_rc3.config import SHARED_DISCOVERY_SEED_MATERIAL
from aivd_post_rc3.models import MODELS


def discovery_seed_for(model_id: str) -> int:
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    digest = hashlib.sha256(f"{SHARED_DISCOVERY_SEED_MATERIAL}|{model_id}".encode()).hexdigest()
    # Positive 31-bit int for Random()
    return int(digest[:8], 16) & 0x7FFFFFFF
