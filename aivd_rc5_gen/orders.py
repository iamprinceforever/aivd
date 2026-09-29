"""D2 (proposed): one COMMON discovery order, identical for all three models, per block.

The order of block k is a pure function of that block's PUBLIC manifest and the common seed
(aivd_rc5_gen.seeds) via the frozen aivd_rc3.discover.order, i.e. exactly what the frozen driver
executes when given discovery_seed = common seed. It is recorded (ids + sha256 per block, plus one
common_order_sha256 over the three blocks) once all three blocks exist, BEFORE any model call; the
runner refuses if the recorded order differs. Public inputs only: no seal is read.
"""

from aivd_stateful.hashing import digest

from aivd_rc3.discover import order

from aivd_rc5_gen import BLOCKS
from aivd_rc5_gen.models import MODELS
from aivd_rc5_gen.seeds import common_order_seed


def block_order(public: list) -> dict:
    seed = common_order_seed()
    ids = [s["scenario_id"] for s in order(public, seed)]
    return {"discovery_seed": seed, "order": ids, "order_sha256": digest({"order": ids})}


def common_order(manifests: dict) -> dict:
    """manifests: block -> public manifest (list). Returns the full order record."""
    if sorted(manifests) != list(BLOCKS):
        raise ValueError("all three blocks are required")
    blocks = {str(b): block_order(manifests[b]) for b in BLOCKS}
    return {"decision": "D2=A (common order, all models)", "models": list(MODELS),
            "discovery_seed": common_order_seed(),
            "public_manifest_sha256": {str(b): digest(manifests[b]) for b in BLOCKS},
            "blocks": blocks,
            "common_order_sha256": digest({"orders": [blocks[str(b)]["order"] for b in BLOCKS]})}
