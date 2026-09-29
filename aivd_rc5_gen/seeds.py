"""RC5 uses NO per-model discovery seed. The common order (aivd_rc5_gen.orders) is realized in the
ordered manifest itself and the frozen driver is called with discovery_seed=None, so the frozen
aivd_rc3.discover.run performs no further shuffle and every model explores the identical order."""

from aivd_rc5_gen.models import MODELS

DISCOVERY_SEED = None


def discovery_seed_for(model_id: str):
    if model_id not in MODELS:
        raise ValueError(f"unknown model: {model_id}")
    return DISCOVERY_SEED
