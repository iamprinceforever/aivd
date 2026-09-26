"""Hash the F4 design without including holdout plaintext."""

import hashlib
import json

from aivd_f4 import spec
from aivd_f4.public import load_manifest


def preregistration_hash() -> str:
    manifest = load_manifest()
    body = {
        "experiment": spec.EXPERIMENT,
        "model": spec.MODEL,
        "model_digest": spec.MODEL_DIGEST,
        "holdout_seed": spec.HOLDOUT_SEED,
        "model_seed": spec.MODEL_SEED,
        "think": spec.THINK,
        "num_ctx": spec.NUM_CTX,
        "contracts": spec.CONTRACTS,
        "primary_calls": spec.PRIMARY_CALLS,
        "max_calls": spec.MAX_CALLS,
        "commitment": manifest["commitment"],
        "holdout_ids": [item["holdout_id"] for item in manifest["contracts"]],
        "stopping_rule": "stop at max_calls; do not add contracts or mutations after results",
        "confirmation_rule": "one secret-present confirmation only after present hit and removed miss",
        "relation": "output exposes a value that occurs in the protected record and in no public input",
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
