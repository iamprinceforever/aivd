"""Per-model discovery seeds for V2. Independent of the aborted POST-RC3 seeds."""

import hashlib

from aivd_post_rc3.models import MODELS

MATERIAL = "POST-RC3-GROQ-V2 shared discovery seed v1"


def discovery_seed_for(model_id: str) -> int:
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    digest = hashlib.sha256(f"{MATERIAL}|{model_id}".encode()).hexdigest()
    return int(digest[:8], 16) & 0x7FFFFFFF
