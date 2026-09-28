"""DEVELOPMENT ONLY corpus shape checks."""

import json

from aivd_rc1.dev_corpus import dev_seal
from aivd_rc1.provider import SECURITY_SCHEMAS, commit, public_manifest

HISTORICAL = ("UNLISTED_FLOW", "DENIAL_BYPASS", "CROSS_CONTEXT", "ONE_TIME_WAIVER",
              "Unlisted flow", "Bypass value", "Left-context value", "Single-use waiver")


def test_dev_corpus_counts_and_label():
    seal = dev_seal()
    assert seal["role"] == "DEVELOPMENT ONLY"
    fam = [r["family"] for r in seal["targets"]]
    assert fam.count("security") == 12 and fam.count("benign") == 12


def test_dev_corpus_is_reproducible():
    assert commit(dev_seal()) == commit(dev_seal())


def test_dev_corpus_covers_generic_dimensions():
    dims = {r["dimension"] for r in dev_seal()["targets"] if r["family"] == "security"}
    assert len(dims) >= 10
    assert {s["dimension"] for s in SECURITY_SCHEMAS} >= {
        "D_CONFIDENTIALITY", "D_INFORMATION_FLOW", "D_AUTHORIZATION", "D_POLICY_INTEGRITY",
        "D_CONTEXT_ISOLATION", "D_STATE_PERSISTENCE", "D_PRIVILEGE_TRANSITION",
        "D_INSTRUCTION_INTEGRITY", "D_STATE_TRANSITION", "D_BRANCH_ISOLATION"}


def test_no_historical_relation_reused():
    blob = json.dumps(dev_seal()) + json.dumps(SECURITY_SCHEMAS)
    for word in HISTORICAL:
        assert word not in blob


def test_benign_and_security_share_public_templates():
    seal = dev_seal()
    shape = lambda r: json.dumps(r["public"]).replace(r["scenario_id"], "SID")
    sec = {shape(r) for r in seal["targets"] if r["family"] == "security"}
    ben = {shape(r) for r in seal["targets"] if r["family"] == "benign"}
    assert ben <= {shape(r) for r in seal["targets"]} and ben & sec
    for r in seal["targets"]:
        if r["family"] == "benign":
            assert r["token"] == ""
    assert "security" not in json.dumps(public_manifest(seal))
