"""Machinery tests. The fixtures are not a Source-D corpus and they are not F3 evidence."""

import json

import pytest

from aivd.experiments.aivd40.source_d.claim import evaluate
from aivd.experiments.aivd40.source_d.corpus import (
    CapabilityError,
    CorpusInvalid,
    compare_provider_result,
    decrypt,
    lock_discovery,
    observe,
    open_artifact,
    recompute,
    recompute_independently,
    seal_corpus,
    submit_replacement,
    verifier_result,
    verify_order,
    verify_specification,
)
from aivd.experiments.aivd40.source_d.crypto import InsufficientSeal, SealBroken, seal, seal_hash_only
from aivd.experiments.aivd40.source_d.isolate import ENVIRONMENT_CHECKS, HISTORY_FIELDS, qualify
from aivd.experiments.aivd40.source_d.scan import scan
from aivd.experiments.aivd40.source_d.schema import SchemaError, validate_artifact
from aivd.experiments.aivd40.source_d.spec import REQUEST, specification_hash

KEY = b"k" * 32
PRIVATE = b"\x11private-bytes-marker"
PROGRAM = "program-text-marker"
POLICY_MARK = "policy-body-marker"


def _snapshot(**overrides):
    body = {name: True for name in ENVIRONMENT_CHECKS}
    body.update({name: "NOT_RECORDED" for name in HISTORY_FIELDS})
    body.update(overrides)
    return body


def _artifact(**overrides):
    body = {
        "policy": None,
        "private_channel": (PRIVATE, PRIVATE, PRIVATE, PRIVATE),
        "program": PROGRAM,
        "projections": ("same", "same", "same", "same"),
        "public_input": "public",
        "sealed_provider_result": {"relation_a": "HOLDS", "relation_b": "NOT_APPLICABLE"},
    }
    body.update(overrides)
    return body


def _seal(artifacts=None, snapshot=None):
    return seal_corpus(
        artifacts or [_artifact()],
        key=KEY,
        timestamp="2026-01-01T00:00:00Z",
        snapshot=snapshot or _snapshot(),
    )


def test_valid_schema_and_missing_channel_is_not_a_verdict():
    parsed = validate_artifact(_artifact(private_channel=None, projections=None))
    assert parsed["private_channel"] is None
    assert recompute(parsed)["relation_a"] == "NOT_APPLICABLE"


def test_malformed_policy_and_channel_and_forbidden_field():
    with pytest.raises(SchemaError):
        validate_artifact(_artifact(policy={"alike": ["a"]}))
    with pytest.raises(SchemaError):
        validate_artifact(_artifact(private_channel=(PRIVATE,)))
    with pytest.raises(SchemaError):
        validate_artifact({**_artifact(), "vulnerable": True})
    with pytest.raises(SchemaError):
        validate_artifact(_artifact(program=""))


def test_one_invalid_artifact_rejects_the_whole_corpus():
    with pytest.raises(CorpusInvalid, match="corpus rejected"):
        _seal([_artifact(), {"public_input": "x"}])


def test_authorized_decrypt_and_discovery_cannot_decrypt_or_read_verifier():
    sealed = _seal()
    handle = sealed["ledger"]["artifacts"][0]["handle"]
    plain = decrypt(sealed["sealer_token"], handle)
    assert plain["program"] == PROGRAM
    with pytest.raises(CapabilityError):
        decrypt(sealed["discovery_token"], handle)
    with pytest.raises(CapabilityError):
        verifier_result(sealed["discovery_token"])
    with pytest.raises(CapabilityError):
        decrypt(sealed["verifier_token"], handle)
    lock_discovery(sealed["discovery_token"])
    recomputed = recompute_independently(sealed["verifier_token"])
    assert recomputed[handle]["relation_a"] == "HOLDS"
    assert compare_provider_result(sealed["verifier_token"])["status"] == "MATCH"


def test_verifier_disagreement_is_corpus_integrity_not_a_discovery_input():
    sealed = _seal(
        [
            _artifact(
                projections=("a", "b", "c", "d"),
                sealed_provider_result={"relation_a": "HOLDS", "relation_b": "NOT_APPLICABLE"},
            )
        ]
    )
    lock_discovery(sealed["discovery_token"])
    found = recompute_independently(sealed["verifier_token"])
    handle = next(iter(found))
    assert found[handle]["relation_a"] == "VIOLATION"
    assert compare_provider_result(sealed["verifier_token"])["status"] == "CORPUS_INTEGRITY_FAILURE"
    with pytest.raises(CapabilityError):
        verifier_result(sealed["discovery_token"])


def test_public_ledger_has_no_plaintext_private_bytes_or_label():
    sealed = _seal(
        [
            _artifact(
                policy={"alike": ["p", "q"], "observations": {"p": POLICY_MARK, "q": POLICY_MARK}},
                sealed_provider_result={"relation_a": "VIOLATION", "relation_b": "HOLDS"},
            )
        ]
    )
    public = json.dumps(sealed["ledger"])
    assert PROGRAM not in public
    assert PRIVATE.hex() not in public
    assert POLICY_MARK not in public
    assert "VIOLATION" not in public
    assert "HOLDS" not in public
    assert sealed["sealer_token"] not in public
    opened = open_artifact(sealed["discovery_token"], sealed["ledger"]["artifacts"][0]["handle"])
    assert "program" not in opened
    assert opened["private_channel_present"] is True
    assert "private_channel" not in opened


def test_hash_only_seal_is_rejected_and_tamper_is_detected():
    with pytest.raises(InsufficientSeal):
        seal_hash_only(b"abc")
    sealed = _seal()
    handle = sealed["ledger"]["artifacts"][0]["handle"]
    from aivd.experiments.aivd40.source_d import corpus as corpus_mod

    packed = corpus_mod._VAULT[sealed["sealer_token"]]["records"][0]["packed"]
    packed["payload"] = ("0" if packed["payload"][0] != "0" else "1") + packed["payload"][1:]
    with pytest.raises(SealBroken):
        decrypt(sealed["sealer_token"], handle)


def test_replacement_order_and_specification_mutations_are_rejected():
    sealed = _seal([_artifact(program="aaaa"), _artifact(program="bbbb")])
    with pytest.raises(CorpusInvalid):
        submit_replacement(sealed["sealer_token"])
    verify_order(sealed["ledger"])
    broken = json.loads(json.dumps(sealed["ledger"]))
    broken["artifacts"] = list(reversed(broken["artifacts"]))
    with pytest.raises(CorpusInvalid):
        verify_order(broken)
    broken = json.loads(json.dumps(sealed["ledger"]))
    broken["specification_hash"] = "0" * 64
    with pytest.raises(CorpusInvalid):
        verify_specification(broken)
    assert sealed["ledger"]["specification_hash"] == specification_hash()


def test_commitments_repeat_under_a_fixed_key_and_order_is_not_insertion():
    first = _seal([_artifact(program="one"), _artifact(program="two")])
    second = _seal([_artifact(program="one"), _artifact(program="two")])
    assert first["ledger"]["sealer_commitment"] == second["ledger"]["sealer_commitment"]
    assert first["ledger"]["order_commitment"] == second["ledger"]["order_commitment"]
    handles = [row["handle"] for row in first["ledger"]["artifacts"]]
    assert handles == sorted(handles)


def test_manifest_missing_evidence_is_not_verified_and_claim_downgrades():
    manifest = qualify({})
    assert manifest["provider_history_isolation"] == "NOT_VERIFIED"
    assert all(value == "NOT_RECORDED" for value in manifest["environment"].values())
    assert manifest["history"]["fresh_context_verified"] == "NOT_RECORDED"
    mounted = qualify(_snapshot(filesystem_aivd_mount=False, aivd_env=False))
    assert mounted["environment"]["filesystem_aivd_mount"] == "NOT_VERIFIED"
    claim = evaluate(qualify(_snapshot()), leakage_clean=True, corpus_valid=True, sealed=True)
    assert claim["status"] == "ENGINE_ISOLATED_ONLY"
    ready = evaluate(
        qualify(_snapshot(**{name: "TRUE" for name in HISTORY_FIELDS})),
        leakage_clean=True,
        corpus_valid=True,
        sealed=True,
        physical_separation=True,
    )
    assert ready["status"] == "SOURCE_D_READY"
    logical = evaluate(
        qualify(_snapshot(**{name: "TRUE" for name in HISTORY_FIELDS})),
        leakage_clean=True,
        corpus_valid=True,
        sealed=True,
    )
    assert logical["status"] == "PROVIDER_ISOLATED"
    assert "physical_separation" in logical["missing"]
    assert evaluate(mounted, leakage_clean=True, corpus_valid=True, sealed=True)["status"] == "SOURCE_D_INVALID"


def test_scanner_detects_tokens_but_a_clean_scan_is_not_isolation():
    assert scan("schema source public channel")["clean"] is True
    assert scan("schema source public channel")["history_isolation"] == "NOT_VERIFIED"
    assert scan("contains ODD and secret{ and disallowed: and vulnerability C")["clean"] is False
    assert scan("doubled-even reverse-each S U")["clean"] is False
    with pytest.raises(CorpusInvalid):
        _seal([_artifact(program="ODD")])


def test_request_has_no_target_example_and_observation_hides_private_bytes():
    lowered = REQUEST.lower()
    assert "vulnerable" not in lowered
    assert "insecure" not in lowered
    assert "information leak" not in lowered
    sealed = _seal()
    handle = sealed["ledger"]["artifacts"][0]["handle"]
    seen = observe(sealed["discovery_token"], handle, 0)
    assert seen == {"status": "PUBLIC_OBSERVATION", "value": "same"}
    assert PRIVATE.hex() not in json.dumps(seen)
    assert "verifier_handoff" not in json.dumps(sealed["ledger"]["audit_log"])
    lock_discovery(sealed["discovery_token"])
    assert sealed["ledger"]["audit_log"][-1] == {"event": "verifier_handoff"}
    assert KEY.hex() not in json.dumps(sealed["ledger"])
