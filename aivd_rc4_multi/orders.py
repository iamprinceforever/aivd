"""D3 = A: each model gets its own independently randomized discovery order (frozen before execution).

The per-model seed (aivd_rc4_multi.seeds) is fixed now. The exact order is a pure function of the public
manifest and that seed via the frozen aivd_rc3.discover.order, so it is recorded (ids + sha256 per model)
once the corpus exists, BEFORE any model call, and the runner refuses if the recorded order differs.
"""

from aivd_stateful.hashing import digest

from aivd_rc3.discover import order

from aivd_rc4_multi.seeds import discovery_seed_for
from aivd_post_rc3_local.models import MODELS


def order_record(public: list, model_id: str) -> dict:
    seed = discovery_seed_for(model_id)
    ids = [s["scenario_id"] for s in order(public, seed)]
    return {"model_id": model_id, "discovery_seed": seed, "order": ids, "order_sha256": digest({"order": ids})}


def all_orders(public: list, public_manifest_sha256: str) -> dict:
    return {"decision": "D3=A", "public_manifest_sha256": public_manifest_sha256,
            "models": {m: order_record(public, m) for m in MODELS}}
