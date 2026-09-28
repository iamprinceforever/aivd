"""Investigation constants. No hidden target and no model client."""

EXPERIMENT = "INVESTIGATION-DESIGN"
EXECUTION_AUTHORIZED = False

DIMENSIONS = (
    "S1_CONFIDENTIALITY",
    "S2_AUTHORIZATION",
    "S3_POLICY_INTEGRITY",
    "S4_CONTEXT_ISOLATION",
    "S5_STATE_PERSISTENCE",
    "S6_PRIVILEGE_TRANSITION",
    "S7_INSTRUCTION_INTEGRITY",
    "S8_INFORMATION_FLOW",
)

HYPOTHESES = (
    "H1_CONFIDENTIALITY",
    "H2_AUTHORIZATION",
    "H3_POLICY_INTEGRITY",
    "H4_CONTEXT_ISOLATION",
    "H5_STATE_PERSISTENCE",
    "H6_PRIVILEGE_TRANSITION",
    "H7_INSTRUCTION_INTEGRITY",
    "H8_INFORMATION_FLOW",
)

DIMENSION_FOR = dict(zip(HYPOTHESES, DIMENSIONS))

CATEGORIES = (
    "SUPPORTED_BY_OBSERVATION",
    "PLAUSIBLE_BUT_UNTESTED",
    "CONTRADICTED_BY_OBSERVATION",
    "INSUFFICIENT_EVIDENCE",
)

PROBE_ORDER = ("CF-A", "CF-B", "CF-C", "CF-D", "CF-E", "CF-F")

FORBIDDEN_KEYS = frozenset(
    {
        "target",
        "secret",
        "protected_value",
        "relation",
        "verifier_state",
        "security_score",
        "similarity",
        "target_label",
    }
)

# Public candidate ids from the frozen END-GOAL-2 ledger. They are not reclassified.
FROZEN_FALSE_POSITIVE_IDS = frozenset(
    {
        "1b2aa4792d9621851eca1ba674b03fb2584fa90d79f98874f94fa1237a27091c",
        "b11ace46eec5cc5cb38eb4777a883b2f9dbcf57c13fa3a738abbe2f4f037224b",
        "3d3f44e58a6c0e265d24f4c199d33e738f0b9e8393684432343b5a8b0155a693",
    }
)
