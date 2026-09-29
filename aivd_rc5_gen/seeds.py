"""Common discovery-order seed for AIVD-RC5-GENERALIZATION-V1 (D2, proposed): ONE seed shared by all
three models, fixed at design from public material (independent of LOCAL-V1 / RC4 seed material)."""

import hashlib

from aivd_rc5_gen.config import COMMON_ORDER_SEED_MATERIAL


def common_order_seed() -> int:
    d = hashlib.sha256(COMMON_ORDER_SEED_MATERIAL.encode()).hexdigest()
    return int(d[:8], 16) & 0x7FFFFFFF


def discovery_seed_for(model_id: str) -> int:
    """Every model uses the same common seed (no per-model order)."""
    from aivd_rc5_gen.models import MODELS
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    return common_order_seed()
