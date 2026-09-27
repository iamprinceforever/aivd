"""F5 preregistration constants. No holdout secrets and no model calls."""

EXPERIMENT = "F5"
EXECUTION_AUTHORIZED = False

F4_IMPLEMENTATION = "412a1bcb545fad2f238cc6977f4ea6dacabbcb89"
F4_PREREGISTRATION = "48d9cc748a551ea8a710f90a473ff8a7c7cbe969277a3ae9af7c7134a5e6223b"
F4_CORPUS_COMMITMENT = "2b882a9c3cd8dc33fc46c7c75b13a383a4d0206215d65764dbf5bd0be9bc2f3d"
F4_RESULTS_COMMIT = "3bbfbf93c88019accadb96edb200b76479e2f3e6"
F4_RESULTS_SHA256 = "5082b74dcff0a4ad93a55986f83002abea68a94eef74b159259769da61210bc2"
SUCCESS_HOLDOUT_ID = "40eebcd450359f23"

FROZEN_BLINDED_HASH = "fc37a48907c51c3b45455062015ce84de86b20a10ac187bb45802da70b8443d3"
FROZEN_METADATA_HASH = "d96fb7fc1400012338b8ac8006d28cdedd55a11fa8205c27b2832d89ac18e589"

FUTURE_COUNTERFACTUALS = 6
FUTURE_PRIMARY_CALLS = 12
FUTURE_MAX_CALLS = 18

COUNTERFACTUALS = (
    {
        "id": "CF1",
        "hypothesis": "H1",
        "baseline_holdout_id": "40eebcd450359f23",
        "factor": "operator",
        "change": {"operator": "NONE"},
        "held_fixed": ["task_id", "policy_id", "record_format", "category", "sealed_value"],
        "authorized": False,
    },
    {
        "id": "CF2",
        "hypothesis": "H1",
        "baseline_holdout_id": "4b02919c24fc3260",
        "factor": "operator",
        "change": {"operator": "ROLE_PERMUTE"},
        "held_fixed": ["task_id", "policy_id", "record_format", "category", "sealed_value"],
        "authorized": False,
    },
    {
        "id": "CF3",
        "hypothesis": "H9",
        "baseline_holdout_id": "40eebcd450359f23",
        "factor": "record_format",
        "change": {"record_format": "sentence"},
        "held_fixed": ["task_id", "policy_id", "operator", "category", "sealed_value"],
        "authorized": False,
    },
    {
        "id": "CF4",
        "hypothesis": "H9",
        "baseline_holdout_id": "40eebcd450359f23",
        "factor": "task_id",
        "change": {"task_id": "T_C1"},
        "held_fixed": ["policy_id", "record_format", "operator", "category", "sealed_value"],
        "authorized": False,
    },
    {
        "id": "CF5",
        "hypothesis": "H1",
        "baseline_holdout_id": "43c676073509e6b3",
        "factor": "operator",
        "change": {"operator": "ROLE_PERMUTE"},
        "held_fixed": ["task_id", "policy_id", "record_format", "category", "sealed_value"],
        "authorized": False,
    },
    {
        "id": "CF6",
        "hypothesis": "H9",
        "baseline_holdout_id": "40eebcd450359f23",
        "factor": "policy_id",
        "change": {"policy_id": "P_A"},
        "held_fixed": ["task_id", "record_format", "operator", "category", "sealed_value"],
        "authorized": False,
    },
)
