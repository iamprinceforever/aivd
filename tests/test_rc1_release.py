"""Release-path checks: label commitments, redacted public ledger, pass isolation, wire proxy."""

import json
import subprocess
import sys
import textwrap

from aivd_rc1.driver import execute
from aivd_rc1.provider import commit, draw, label_commitment, label_reveal, public_commitment_view
from aivd_rc1.publish import public_ledger, redact_text, span_tag
from aivd_stateful.contract import OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from tests.rc1_mocks import leak

ID = {"model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256}


def test_label_reveal_matches_commitment_without_token():
    seal = draw(b"reveal")
    view = public_commitment_view(seal)
    reveal = label_reveal(seal)
    for row in reveal:
        assert "token" not in row and "note" not in row
        assert label_commitment(row) == view["label_commitments"][row["scenario_id"]]
    forged = dict(reveal[0], family="benign" if reveal[0]["family"] == "security" else "security")
    assert label_commitment(forged) != view["label_commitments"][forged["scenario_id"]]


def test_public_ledger_redacts_leaked_tokens(tmp_path):
    seal = draw(b"redact")
    ledger = execute(tmp_path / "r", seal, leak, pass_id="r", identity=ID)["ledger"]
    view = json.dumps(public_ledger(ledger))
    for row in seal["targets"]:
        if row["token"]:
            assert row["token"] not in view
    leaked = [r["token"] for r in seal["targets"] if r["token"] and any(r["token"] in c["preserved_output"] for c in ledger["candidates"])]
    assert leaked and span_tag(leaked[0]) in view
    assert redact_text("Additionally plain words") == "Additionally plain words"


def test_pass_isolation_hook_blocks_other_pass(tmp_path):
    other = tmp_path / "P1"
    other.mkdir()
    (other / "ledger.json").write_text("{}")
    code = textwrap.dedent(f"""
        from aivd_rc1.isolation import install, IsolationViolation
        install([{str(other)!r}])
        try:
            open({str(other / 'ledger.json')!r}).read()
            print("READ")
        except IsolationViolation:
            print("BLOCKED")
        try:
            import os; os.listdir({str(other)!r}); print("LISTED")
        except IsolationViolation:
            print("BLOCKED")
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=".").stdout.split()
    assert out == ["BLOCKED", "BLOCKED"]


def test_pass_runner_forbids_seal_and_other_pass():
    src = open("scripts/rc1_run_pass.py").read()
    assert "install(forbidden)" in src
    assert src.index("install(forbidden)") < src.index("from aivd_rc1.driver import")
    assert "final_seal.json" in src
    assert "aivd_rc1.provider" not in src and "aivd_rc1.wire" not in src and "aivd_rc1.verifier" not in src


def test_final_provider_reads_no_pipeline_output():
    src = open("scripts/rc1_final_provider.py").read()
    for banned in ("ledger", "candidate", "discover", "investigat", "verifier", "P1", "P2"):
        assert banned not in src.split('"""', 2)[2], banned


def test_commitment_binds_labels_and_salts():
    seal = draw(b"bind")
    c = commit(seal)
    seal["targets"][0]["label_salt"] = "00" * 16
    assert commit(seal) != c
