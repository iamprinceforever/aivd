"""Hash the F5 design without holdout plaintext."""

import hashlib
import json

from aivd_f5.analyze import CLASSES
from aivd_f5.features import SCHEMA
from aivd_f5.spec import (
    COUNTERFACTUALS,
    EXPERIMENT,
    F4_CORPUS_COMMITMENT,
    F4_PREREGISTRATION,
    F4_RESULTS_COMMIT,
    F4_RESULTS_SHA256,
    FROZEN_BLINDED_HASH,
    FROZEN_METADATA_HASH,
    FUTURE_MAX_CALLS,
    SUCCESS_HOLDOUT_ID,
)


def preregistration_hash() -> str:
    body = {
        "experiment": EXPERIMENT,
        "objective": "identify candidate structural properties of the one reproduced F4 holdout; do not establish a mechanism",
        "f4_preregistration": F4_PREREGISTRATION,
        "f4_corpus_commitment": F4_CORPUS_COMMITMENT,
        "f4_results_commit": F4_RESULTS_COMMIT,
        "f4_results_sha256": F4_RESULTS_SHA256,
        "success_holdout_id": SUCCESS_HOLDOUT_ID,
        "blinded_feature_hash": FROZEN_BLINDED_HASH,
        "sealed_metadata_hash": FROZEN_METADATA_HASH,
        "schema_before_outcome": list(SCHEMA),
        "hypothesis_classes": list(CLASSES),
        "counterfactuals": list(COUNTERFACTUALS),
        "future_max_calls": FUTURE_MAX_CALLS,
        "execution_authorized": False,
        "stopping_rule": "stop at the design; do not add model calls; a later intervention may not grow the six counterfactuals after results",
        "causal_rule": "a mechanism is not established until a preregistered one-factor intervention changes the disclosure result",
        "leakage_rule": "planner and blinded table do not receive protected plaintext, distinctive values, or secret-present disclosure text",
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
