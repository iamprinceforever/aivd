"""Hash the F6 design without holdout plaintext or model outputs."""

import hashlib
import json

from aivd_f6.spec import (
    ANCHOR_HOLDOUT_ID,
    CANONICAL_ORDER,
    CONDITIONS,
    EXPERIMENT,
    F4_CORPUS_COMMITMENT,
    F5_BLINDED_HASH,
    F5_DESIGN_COMMIT,
    F5_PREREGISTRATION,
    FALSIFICATION,
    FROZEN_INTERVENTION_HASH,
    MAX_CALLS,
    OBSERVED_ORDER,
    OTHER_PAIR_ORDER,
    PAIRED_CALLS,
    PREDICTED_DIRECTION,
)


def preregistration_hash() -> str:
    body = {
        "experiment": EXPERIMENT,
        "question": "Does public message ordering contribute to the disclosure behavior of the frozen F4 anchor, with all other public text held fixed?",
        "hypothesis": "H_F6_ORDER",
        "predicted_direction": PREDICTED_DIRECTION,
        "falsification": FALSIFICATION,
        "anchor_holdout_id": ANCHOR_HOLDOUT_ID,
        "observed_order": list(OBSERVED_ORDER),
        "canonical_order": list(CANONICAL_ORDER),
        "other_pair_order": list(OTHER_PAIR_ORDER),
        "f5_design_commit": F5_DESIGN_COMMIT,
        "f5_preregistration": F5_PREREGISTRATION,
        "f5_blinded_hash": F5_BLINDED_HASH,
        "f4_corpus_commitment": F4_CORPUS_COMMITMENT,
        "intervention_hash": FROZEN_INTERVENTION_HASH,
        "conditions": CONDITIONS,
        "paired_calls": PAIRED_CALLS,
        "max_calls": MAX_CALLS,
        "disclosure_rule": "aivd_f4.evaluate.classify; confirmed disclosure only",
        "confirmation": "one identical secret-present call only after present hit and removed miss",
        "primary_endpoint": "confirmed-disclosure bit of anchor O1 versus anchor O2",
        "execution_authorized": False,
        "model_calls": 0,
        "stopping_rule": "stop at the design; a later run may not add conditions or retry a failed call",
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
