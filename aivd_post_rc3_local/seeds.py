"""Per-model discovery seeds for POST-RC3-LOCAL-V1. Independent of V1/V2 seed material."""

import hashlib

from aivd_post_rc3_local.config import SHARED_DISCOVERY_SEED_MATERIAL
from aivd_post_rc3_local.models import MODELS


def discovery_seed_for(model_id: str) -> int:
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    digest = hashlib.sha256(f"{SHARED_DISCOVERY_SEED_MATERIAL}|{model_id}".encode()).hexdigest()
    return int(digest[:8], 16) & 0x7FFFFFFF
