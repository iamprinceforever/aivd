"""RC3 DEVELOPMENT ONLY corpus shape and coverage checks."""

import json

from aivd_rc2.dev_corpus import dev_seal as rc2_dev_seal
from aivd_rc3.dev_corpus import COVERAGE, dev_seal
from aivd_rc3.provider import RELATION_BY_KIND, SECURITY_SCHEMAS, public_manifest

REQUIRED = {
    "genuine_protected_value_disclosure", "invented_value_repetition", "public_value_repetition",
    "transformed_public_identifier", "protected_value_transformation", "state_persistence_without_disclosure",
    "context_isolation_without_disclosure", "authorization_mismatch_without_violation",
    "genuine_authorization_violation", "information_flow_violation", "benign_repeated_invented_token",
    "benign_generated_key", "benign_generated_credential", "benign_generated_id", "branch_persistence",
    "reset_behavior", "protected_source_provenance", "public_source_provenance", "unknown_source_candidate",
    "exact_protected_value_reproduction",
}


def test_counts_and_label():
    seal = dev_seal()
    assert seal["role"] == "DEVELOPMENT ONLY"
    fam = [r["family"] for r in seal["targets"]]
    assert fam.count("security") >= 20 and fam.count("benign") >= 20


def test_every_required_case_type_is_mapped_and_present():
    assert set(COVERAGE) == REQUIRED
    present = {(r["family"], r["kind"]) for r in dev_seal()["targets"]}
    for case, rows in COVERAGE.items():
        assert rows and all(row in present for row in rows), case


def test_all_schemas_and_relation_types_present():
    seal = dev_seal()
    every = {s["kind"] for s in SECURITY_SCHEMAS}
    assert {r["kind"] for r in seal["targets"] if r["family"] == "security"} == every
    assert {r["kind"] for r in seal["targets"] if r["family"] == "benign"} == every
    rels = {r["relation"] for r in seal["targets"] if r["family"] == "security"}
    assert {"A_EXACT_PROTECTED_VALUE_DISCLOSURE", "B_PROTECTED_INFORMATION_FLOW", "C_AUTHORIZATION_BOUNDARY",
            "D_POLICY_BOUNDARY", "E_STATE_CONTEXT_ISOLATION"} <= rels
    assert set(RELATION_BY_KIND) == every


def test_not_rc2_corpus():
    a = {r["scenario_id"] for r in dev_seal()["targets"]}
    b = {r["scenario_id"] for r in rc2_dev_seal()["targets"]}
    assert not a & b


def test_public_view_hides_family_relation_and_values():
    pub = json.dumps(public_manifest(dev_seal()))
    for word in ("security", "benign", "token", "note", "dimension", "relation", "EXACT_PROTECTED"):
        assert word not in pub
    for r in dev_seal()["targets"]:
        if r["token"]:
            assert r["token"] not in pub
