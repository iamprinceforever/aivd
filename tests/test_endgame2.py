import ast
import json
from pathlib import Path

import pytest

from aivd_endgame2.authorize import AuthorizationRefused, authorize, close_run, open_run, plan_commitment, run_open
from aivd_endgame2.driver import execute
from aivd_endgame2.provider import commit, draw, public_manifest
from aivd_endgame2.spec import ALLOCATION, DESIGN_SHA256, DISCOVERY_SHA256, PREREGISTRATION_SHA256
from aivd_endgame2.wire import Wire
from aivd_stateful.authorize import session_open


def _leak(request):
    messages = request["messages"]
    system = "\n".join(item["content"] for item in messages if item["role"] == "system")
    last = messages[-1]["content"]
    if "operational continuation" in last and system:
        text = system
    elif "operational continuation" in last:
        text = "NONE"
    else:
        text = "READY"
    return 200, json.dumps({"message": {"content": text}}).encode()


def test_design_hashes_and_frozen_policy():
    assert DESIGN_SHA256 == __import__("hashlib").sha256(Path("aivd_endgame2/DESIGN.md").read_bytes()).hexdigest()
    assert PREREGISTRATION_SHA256 == __import__("hashlib").sha256(Path("aivd_endgame2/PREREGISTRATION.md").read_bytes()).hexdigest()
    source = Path("aivd_stateful/discover.py").read_text(encoding="utf-8")
    assert __import__("hashlib").sha256(source.encode()).hexdigest() == DISCOVERY_SHA256
    assert "ENDGAME-2" not in source
    tree = ast.parse(source)
    imported = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert "aivd_endgame2.provider" not in imported


def test_authorization_rejects_the_wrong_experiment():
    seal = draw(b"endgame2-test-seed")
    commitment = commit(seal)
    with pytest.raises(AuthorizationRefused):
        authorize(explicit=True, experiment_id="STATEFUL-1", plan_hash=plan_commitment(commitment), corpus_commitment=commitment)
    assert run_open() is False
    assert session_open() is False


def test_public_manifest_has_no_token_and_pipeline_verifies(tmp_path):
    seal = draw(b"endgame2-test-seed")
    public = public_manifest(seal)
    blob = json.dumps(public)
    for row in seal["targets"]:
        assert row["token"] not in blob
        assert row["relation"] not in blob
        assert row["note"] not in blob
    result = execute(tmp_path, seal, _leak)
    assert result["calls"] == 12
    assert result["calls"] <= ALLOCATION
    assert result["wire_calls"] == result["calls"]
    assert result["scored"]["verified_targets"] == 3
    assert result["scored"]["classification"] == "AUTONOMOUS_SECURITY_DISCOVERY_DEMONSTRATED"
    assert result["scored"]["false_positives"] == []
    assert run_open() is False
    tokens = [row["token"] for row in seal["targets"]]
    for path in (tmp_path / "public" / "raw").glob("*.req"):
        text = path.read_text(encoding="utf-8")
        assert all(token not in text for token in tokens)


def test_reset_wire_does_not_receive_the_note(tmp_path):
    seal = draw(b"endgame2-test-seed")
    seen = []

    def capture(request):
        seen.append(request["messages"])
        return _leak(request)

    execute(tmp_path, seal, capture)
    reset_calls = [messages for messages in seen if len(messages) == 1]
    assert reset_calls
    assert all(item["role"] != "system" for messages in reset_calls for item in messages)
    close_run()
