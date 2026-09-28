"""Design constants. No sealed target and no model client."""

EXPERIMENT = "STATEFUL-DISCOVERY"
EXECUTION_AUTHORIZED = False
MODEL_CALLS = 0

FORBIDDEN_STATE_KEYS = frozenset(
    {
        "relation",
        "secret",
        "protected_value",
        "security_label",
        "verifier_state",
        "target",
        "target_token",
    }
)
