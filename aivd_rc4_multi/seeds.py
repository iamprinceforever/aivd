"""Per-model discovery seeds for AIVD-RC4-MULTI-V1 (independent of LOCAL-V1 / V1 / V2 material)."""

import hashlib

from aivd_post_rc3_local.models import MODELS
from aivd_rc4_multi.config import SHARED_DISCOVERY_SEED_MATERIAL


def discovery_seed_for(model_id: str) -> int:
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    d = hashlib.sha256(f"{SHARED_DISCOVERY_SEED_MATERIAL}|{model_id}".encode()).hexdigest()
    return int(d[:8], 16) & 0x7FFFFFFF
