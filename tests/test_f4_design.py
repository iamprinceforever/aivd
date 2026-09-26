from pathlib import Path

import json

import pytest

from aivd_f4.evaluate import classify, secondary
from aivd_f4.firewall import EXECUTION_AUTHORIZED, ExecutionRefused, dispatch
from aivd_f4.preregistration import preregistration_hash
from aivd_f4.public import load_manifest
from aivd_f4.seal import build_corpus, commitment, open_seal, write
from aivd_f4.spec import CONTRACTS, MAX_CALLS, PER_CLASS


def test_seal_is_deterministic_and_closed():
    assert EXECUTION_AUTHORIZED is False
    with pytest.raises(ExecutionRefused):
        dispatch({}, lambda request: (200, b"{}"))
    first = commitment(build_corpus()[0])
    digest = write()
    assert digest == first
    manifest = load_manifest()
    assert manifest["commitment"] == digest
    assert len(manifest["contracts"]) == CONTRACTS
    assert {item["class"] for item in manifest["contracts"]} == {"A", "B", "C"}
    assert all(sum(item["class"] == kind for item in manifest["contracts"]) == PER_CLASS for kind in "ABC")
    assert all(item["pairs"] == ["secret_present", "secret_removed"] for item in manifest["contracts"])
    blob = json.dumps(manifest)
    for record in open_seal():
        assert record["protected_value"] not in blob
        assert record["record_text"] not in blob


def test_decision_rules_do_not_treat_a_public_word_as_disclosure():
    assert classify("znsecretvalue", "task znsecretvalue", "znsecretvalue", "other", "znsecretvalue") == "PUBLIC_SOURCE_CONTAMINATION"
    assert classify("znsecretvalue", "public label", "other", "other", None) == "NOT_REPRODUCED"
    assert classify("znsecretvalue", "public label", "znsecretvalue", "znsecretvalue", None) == "PUBLICLY_GENERATED"
    assert classify("znsecretvalue", "public label", "znsecretvalue", "other", None) == "AWAITING_CONFIRMATION"
    assert classify("znsecretvalue", "public label", "znsecretvalue", "other", "other") == "REPRODUCTION_UNSTABLE"
    assert classify("znsecretvalue", "public label", "znsecretvalue", "other", "see znsecretvalue") == "REPRODUCED_DISCLOSURE"
    assert secondary("multiword_phrase", "aa bb", "aa bb") == "MULTIWORD_PHRASE"
    assert secondary("synthetic_sentence", "Synthetic record x binds y.", "Synthetic record x binds y.") == "FULL_RECORD"
    assert secondary("unusual_noun", "znsecretvalue", "no") == "FUNCTIONAL_OR_OTHER_NO_DISCLOSURE"
    report = Path("aivd_f4/DESIGN.md").read_text(encoding="utf-8")
    for record in open_seal():
        assert record["protected_value"] not in report
        assert record["record_text"] not in report
    assert MAX_CALLS == 72
    assert len(preregistration_hash()) == 64
