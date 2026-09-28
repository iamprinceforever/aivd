"""RC3 DEVELOPMENT ONLY corpus (20 security + 20 benign). Not scientific evidence; never final.

Fixed public seed, so it can never be sealed as a final corpus. Distinct from the RC1/RC2 corpora
(different provider schemas, seed and scenario ids). Covers every RC3 generic schema, including the
generate-then-repeat shapes (gen_key / gen_credential / gen_id) whose benign variants make the model
INVENT and REPEAT a key, credential or id, i.e. the RC2 false-positive pattern.

COVERAGE maps each required RC3 development case type to the (family, kind) rows that exercise it.
"""

from aivd_rc3.provider import draw

DEV_SEED = b"AIVD-RC3 DEVELOPMENT ONLY corpus seed v1"
DEV_TIMESTAMP = "2026-09-28T00:00:00Z"

COVERAGE = {
    "genuine_protected_value_disclosure": [("security", k) for k in ("public_summary", "gen_key", "used_quota")],
    "invented_value_repetition": [("benign", "used_quota"), ("benign", "gen_key")],
    "public_value_repetition": [("benign", "id_upper"), ("benign", "audit_export")],
    "transformed_public_identifier": [("benign", "id_upper"), ("benign", "id_mixed"), ("benign", "id_punct")],
    "protected_value_transformation": [("security", "id_upper"), ("security", "id_mixed"), ("security", "id_punct")],
    "state_persistence_without_disclosure": [("benign", "reset_survival"), ("benign", "gen_id")],
    "context_isolation_without_disclosure": [("benign", "tenant_switch")],
    "authorization_mismatch_without_violation": [("benign", "role_gate"), ("benign", "revocation"), ("benign", "gen_credential")],
    "genuine_authorization_violation": [("security", "role_gate"), ("security", "revocation"), ("security", "gen_credential")],
    "information_flow_violation": [("security", "audit_export"), ("security", "id_mixed")],
    "benign_repeated_invented_token": [("benign", "used_quota")],
    "benign_generated_key": [("benign", "gen_key")],
    "benign_generated_credential": [("benign", "gen_credential")],
    "benign_generated_id": [("benign", "gen_id")],
    "branch_persistence": [("security", "discarded_draft"), ("benign", "discarded_draft")],
    "reset_behavior": [("security", "reset_survival"), ("benign", "reset_survival")],
    "protected_source_provenance": [("security", k) for k in ("public_summary", "gen_key", "tenant_switch")],
    "public_source_provenance": [("benign", "id_upper"), ("benign", "id_punct")],
    "unknown_source_candidate": [("benign", "gen_key"), ("benign", "gen_id"), ("benign", "used_quota")],
    "exact_protected_value_reproduction": [("security", k) for k in ("public_summary", "used_quota", "gen_key")],
}


def dev_seal() -> dict:
    seal = draw(DEV_SEED, security_count=20, benign_count=20, development=True)
    seal["timestamp"] = DEV_TIMESTAMP
    return seal
