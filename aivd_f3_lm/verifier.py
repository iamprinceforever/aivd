"""Independent reproduction runner. Synthetic fixtures only."""

from aivd_f3_lm.relations import classify_leakage, violates_non_interference, violates_policy, POLICY_TEXT

FORBIDDEN_FIELDS = frozenset(
    {
        "aivd_confidence",
        "aivd_label",
        "aivd_rank",
        "aivd_hypothesis_ranking",
        "aivd_finding_label",
    }
)


class VerifierContamination(Exception):
    pass


def independent_reproduce(package: dict) -> dict:
    leaked = FORBIDDEN_FIELDS.intersection(package.keys())
    if leaked:
        raise VerifierContamination("verifier received AIVD conclusion fields: " + ",".join(sorted(leaked)))
    required = ("output", "private_value", "status", "policy_text")
    missing = [key for key in required if key not in package]
    if missing:
        raise ValueError("fixture missing " + ",".join(missing))
    output = package["output"]
    private_value = package["private_value"]
    status = package["status"]
    policy_text = package["policy_text"]
    leakage = classify_leakage(output, private_value, status)
    return {
        "leakage_class": leakage,
        "non_interference_violated": violates_non_interference(output, private_value, status),
        "policy_violated": violates_policy(output, private_value, policy_text, status),
        "policy_sha_checked": policy_text == POLICY_TEXT,
        "used_aivd_label": False,
    }
