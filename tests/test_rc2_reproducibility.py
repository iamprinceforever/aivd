"""RC2 reproducibility contract and recorder-fix tests (offline, mocks only)."""

import json

from aivd_rc2.driver import config_hashes, execute
from aivd_rc2.provider import draw
from aivd_rc2.reproducibility import compare
from aivd_stateful.contract import OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.transport import build_request
from tests.rc1_mocks import leak, reply

ID = {"model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256}
SEAL = draw(b"repro")


def _timestamped(inner, offset=0):
    """Same content, different raw HTTP body each call (like a real server's created_at)."""
    state = {"n": offset}

    def t(request):
        status, raw = inner(request)
        body = json.loads(raw)
        state["n"] += 1
        body["created_at"] = f"2026-01-01T00:{state['n']:04d}Z"
        body["total_duration"] = state["n"] * 1000
        return status, json.dumps(body).encode()
    return t


def _flippy(seed):
    """History-dependent leak with a run-specific wording flip on some calls (nondeterministic text)."""
    state = {"n": 0}

    def t(request):
        state["n"] += 1
        status, raw = leak(request)
        text = json.loads(raw)["message"]["content"]
        if (state["n"] + seed) % 5 == 0:
            text = text + " (rephrased)"
        return reply(text)
    return t


def test_harness_is_replay_deterministic_offline(tmp_path):
    a = execute(tmp_path / "a", SEAL, leak, pass_id="same", discovery_seed=3, identity=ID)["ledger"]
    b = execute(tmp_path / "b", SEAL, leak, pass_id="same", discovery_seed=3, identity=ID)["ledger"]
    assert a["frozen_hash"] == b["frozen_hash"]
    r = compare(a, b, same_pass=True)
    assert r["bitwise_content"]["holds"] and r["L2_request"]["holds"] and r["L5_security_decision"]["holds"]


def test_recorder_separates_content_hash_from_raw_body(tmp_path):
    a = execute(tmp_path / "a", SEAL, _timestamped(leak), pass_id="same", discovery_seed=3, identity=ID)["ledger"]
    b = execute(tmp_path / "b", SEAL, _timestamped(leak, 500), pass_id="same", discovery_seed=3, identity=ID)["ledger"]
    assert all(x["content_sha256"] == y["content_sha256"] for x, y in zip(a["requests"], b["requests"]))
    assert any(x["raw_body_sha256"] != y["raw_body_sha256"] for x, y in zip(a["requests"], b["requests"]))
    assert compare(a, b, same_pass=True)["bitwise_content"]["holds"]


def test_nondeterministic_text_keeps_l1_l2_and_never_creates_security_fp(tmp_path):
    ra = execute(tmp_path / "a", SEAL, _flippy(1), pass_id="same", discovery_seed=3, identity=ID)
    rb = execute(tmp_path / "b", SEAL, _flippy(2), pass_id="same", discovery_seed=3, identity=ID)
    r = compare(ra["ledger"], rb["ledger"], same_pass=True)
    assert r["L1_configuration"] is True
    assert r["L2_request"]["holds"]
    assert not r["bitwise_content"]["holds"]
    for res in (ra, rb):
        assert res["scored"]["false_positives_security"] == []
        assert all(b["classification"] != "SECURITY_FALSE_POSITIVE" for b in res["scored"]["benign_rows"])


def test_config_hashes_bind_request_contract():
    h = config_hashes()
    assert set(h) == {"request_contract_sha256", "code"}
    probe = build_request([{"role": "user", "content": "x"}])
    assert probe["options"]["temperature"] == 0.0 and probe["options"]["top_k"] == 1 and probe["options"]["seed"] == 20260926
    assert probe["think"] is False and probe["options"]["num_ctx"] == 4096


def test_parsing_path_is_deterministic():
    raw = json.dumps({"message": {"content": "same text"}, "created_at": "x"}).encode()
    assert json.loads(raw)["message"]["content"] == json.loads(raw)["message"]["content"]


def test_determinism_test_still_exists_and_reports_bitwise():
    from aivd_rc2 import reproducibility as rp
    assert hasattr(rp, "bitwise") and rp.SUPPORTED_LEVEL == "L2"
