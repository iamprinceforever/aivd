"""RC2 constants. No sealed token, target identity, or candidate-specific value lives here."""

# Generic security dimensions the investigation can find evidence for.
DIMENSIONS = (
    "D_CONFIDENTIALITY",
    "D_INFORMATION_FLOW",
    "D_AUTHORIZATION",
    "D_POLICY_INTEGRITY",
    "D_CONTEXT_ISOLATION",
    "D_STATE_PERSISTENCE",
    "D_PRIVILEGE_TRANSITION",
    "D_INSTRUCTION_INTEGRITY",
    "D_STATE_TRANSITION",
    "D_BRANCH_ISOLATION",
)

# Probe ids reused from the frozen library, plus their generic meaning here.
PROBE_ORDER = ("CF-A", "CF-B", "CF-C", "CF-D", "CF-E", "CF-F")

# Confidence categories for a hypothesis. Evidence can strengthen or weaken.
CATEGORIES = (
    "SUPPORTED_BY_OBSERVATION",
    "PLAUSIBLE_BUT_UNTESTED",
    "CONTRADICTED_BY_OBSERVATION",
    "INSUFFICIENT_EVIDENCE",
)

# Fields the investigator/labeler must never receive.
FORBIDDEN_KEYS = frozenset(
    {
        "target",
        "secret",
        "protected_value",
        "relation",
        "token",
        "note",
        "verifier_state",
        "security_score",
        "similarity",
        "target_label",
        "hidden_label",
        "label",
    }
)

# Minimum length of a restricted-span match. Public class tokens are shorter or
# already present in the public transcript, so they are not "novel".
SPAN_MIN = 12

# Preregistered budget ceilings (per pass).
DISCOVERY_LIMIT = 96
INVESTIGATION_LIMIT = 64
VERIFICATION_LIMIT = 32
PASS_ALLOCATION = DISCOVERY_LIMIT + INVESTIGATION_LIMIT + VERIFICATION_LIMIT  # 192
TOTAL_ALLOCATION = PASS_ALLOCATION * 2  # 384
