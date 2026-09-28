"""RC2 DEVELOPMENT ONLY corpus shape checks."""

import json

from aivd_rc1.dev_corpus import dev_seal as rc1_dev_seal
from aivd_rc2.dev_corpus import dev_seal
from aivd_rc2.provider import SECURITY_SCHEMAS, commit, public_manifest

HISTORICAL = ("UNLISTED_FLOW", "DENIAL_BYPASS", "CROSS_CONTEXT", "ONE_TIME_WAIVER",
              "Unlisted flow", "Bypass value", "Left-context value", "Single-use waiver")


def test_counts_and_label():
    seal = dev_seal()
    assert seal["role"] == "DEVELOPMENT ONLY"
    fam = [r["family"] for r in seal["targets"]]
    assert fam.count("security") == 16 and fam.count("benign") == 16


def test_covers_all_schemas_including_public_id_transforms():
    seal = dev_seal()
    kinds_sec = {r["kind"] for r in seal["targets"] if r["family"] == "security"}
    kinds_ben = {r["kind"] for r in seal["targets"] if r["family"] == "benign"}
    every = {s["kind"] for s in SECURITY_SCHEMAS}
    assert kinds_sec == every and kinds_ben == every
    assert {"id_upper", "id_mixed", "id_punct", "reset_survival", "discarded_draft", "used_quota"} <= kinds_ben
    assert len({r["dimension"] for r in seal["targets"] if r["family"] == "security"}) == 10


def test_not_rc1_corpus_and_no_historical_relation():
    assert commit(dev_seal()) != commit(rc1_dev_seal())
    assert not {r["scenario_id"] for r in dev_seal()["targets"]} & {r["scenario_id"] for r in rc1_dev_seal()["targets"]}
    blob = json.dumps(dev_seal())
    for word in HISTORICAL:
        assert word not in blob


def test_public_view_hides_family():
    pub = json.dumps(public_manifest(dev_seal()))
    for word in ("security", "benign", "token", "note", "dimension"):
        assert word not in pub
