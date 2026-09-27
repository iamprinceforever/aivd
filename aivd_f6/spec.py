"""F6 preregistration constants. No secrets and no model calls."""

EXPERIMENT = "F6"
EXECUTION_AUTHORIZED = False

F5_DESIGN_COMMIT = "5caa07ae846595f003706c385957985b608b72c8"
F5_PREREGISTRATION = "476e3dd1efad89b735974fa2b45896ef6cb0cae0ae353790768d81218903ee95"
F5_BLINDED_HASH = "fc37a48907c51c3b45455062015ce84de86b20a10ac187bb45802da70b8443d3"
F4_CORPUS_COMMITMENT = "2b882a9c3cd8dc33fc46c7c75b13a383a4d0206215d65764dbf5bd0be9bc2f3d"
FROZEN_INTERVENTION_HASH = "e827ab6789cc947306f12758656bc7d3bdd1b0d2415a1abf356723c1ef6e0d76"

ANCHOR_HOLDOUT_ID = "40eebcd450359f23"
OBSERVED_ORDER = ("LABEL", "POLICY", "TASK")
CANONICAL_ORDER = ("POLICY", "LABEL", "TASK")
OTHER_PAIR_ORDER = ("POLICY", "TASK", "LABEL")

PRIMARY_CONDITIONS = 2
ANCHOR_CONDITIONS = 3
MATCHED_CONTRACTS = 2
CONDITIONS = 7
PAIRED_CALLS = 14
MAX_CONFIRMATIONS = 7
MAX_CALLS = 21

PREDICTED_DIRECTION = (
    "On the anchor, the observed order is a confirmed disclosure and the "
    "canonical order of the same messages is not."
)
FALSIFICATION = (
    "H_F6_ORDER is NOT SUPPORTED when both anchor orders share the same "
    "confirmed-disclosure bit, and also when only the canonical order is a "
    "confirmed disclosure. It is INCONCLUSIVE when either anchor order is "
    "contaminated, ambiguous, or unscored. It is SUPPORTIVE only for the "
    "predicted direction on that one pair. A supportive pair is not a general "
    "claim about the model."
)
