"""POST-RC3-LOCAL-V1 offline tests. No network, no Ollama request, no model call, no seal read."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from aivd_rc3.provider import commit, public_commitment_view, public_manifest
from aivd_rc3.verifier import judge
from aivd_rc3.wire import Wire

from aivd_post_rc3_local import (
    EXPERIMENT_ID, FORBIDDEN_COMMITMENTS, REPORT_DIR, V1_ABORTED_COMMITMENT, V2_LOST_COMMITMENT)
from aivd_post_rc3_local import config as C
from aivd_post_rc3_local.corpus import BENIGN_COVERAGE, KINDS, dimensions, draw
from aivd_post_rc3_local.isolation import forbidden_for
from aivd_post_rc3_local.models import MANIFEST_DIGESTS, MODELS, THINKING_MODELS
from aivd_post_rc3_local.ollama_backend import LocalModelRefused, build_request, make_inner
from aivd_post_rc3_local.seeds import discovery_seed_for
from tests.post_rc3.conftest import FakeGroqModel
from tests.post_rc3_local.conftest import fake_ollama_opener

REQUIRED_DIMS = {
    "D_CONFIDENTIALITY", "D_INFORMATION_FLOW", "D_AUTHORIZATION", "D_POLICY_INTEGRITY",
    "D_CONTEXT_ISOLATION", "D_STATE_PERSISTENCE", "D_PRIVILEGE_TRANSITION",
    "D_INSTRUCTION_INTEGRITY", "D_BRANCH_ISOLATION", "D_STATE_TRANSITION",
}
REQUIRED_BENIGN = {
    "public_identifier_formatting", "upper_lowercase_transforms", "punctuation_changes",
    "harmless_state_persistence", "harmless_invented_values", "branch_differences",
    "reset_differences", "ordinary_formatting_variation",
}


def test_identity_constants():
    assert EXPERIMENT_ID == "POST-RC3-LOCAL-V1"
    assert MODELS == ("qwen3:1.7b", "llama3.2:3b", "qwen3:8b")
    assert MANIFEST_DIGESTS == {
        "qwen3:1.7b": "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7",
        "llama3.2:3b": "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72",
        "qwen3:8b": "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41",
    }
    assert V2_LOST_COMMITMENT in FORBIDDEN_COMMITMENTS and V1_ABORTED_COMMITMENT in FORBIDDEN_COMMITMENTS
    assert (C.DISCOVERY_LIMIT, C.INVESTIGATION_LIMIT, C.VERIFICATION_LIMIT) == (48, 32, 16)
    assert C.MODEL_ALLOCATION == 96 and C.TOTAL_ALLOCATION == 288
    assert C.REPRO_COUNTS_INSIDE_96 is False and C.REPRO_CALLS_PER_MODEL == 6
    assert len({discovery_seed_for(m) for m in MODELS}) == 3


def test_corpus_shape_coverage_and_no_public_secrets():
    seal = draw(b"\x21" * 32)
    assert seal["security_count"] == seal["benign_count"] == 12 and len(seal["targets"]) == 24
    assert set(dimensions(seal)) == REQUIRED_DIMS
    assert set(BENIGN_COVERAGE) == REQUIRED_BENIGN
    assert all(set(v) <= set(KINDS) for v in BENIGN_COVERAGE.values())
    benign = [r for r in seal["targets"] if r["family"] == "benign"]
    assert {r["kind"] for r in benign} == set(KINDS) and all(r["token"] == "" for r in benign)
    assert len({r["scenario_id"] for r in seal["targets"]}) == 24
    pub = json.dumps(public_manifest(seal)) + json.dumps(public_commitment_view(seal))
    for row in seal["targets"]:
        if row["token"]:
            assert row["token"] not in pub
        assert row["note"] not in pub
        assert "family" not in json.dumps(row["public"])
    assert commit(seal) not in FORBIDDEN_COMMITMENTS
    assert commit(draw(b"\x21" * 32)) == commit(seal)  # deterministic given the seed (timestamp aside)


def test_fresh_os_random_draws_differ_and_avoid_prior_ids():
    a, b = draw(), draw()
    assert a["seed_sha256"] != b["seed_sha256"]
    prior = set()
    for m in Path("reports").glob("aivd_*/**/public_manifest.json"):
        if REPORT_DIR not in str(m):
            prior |= {r["scenario_id"] for r in json.loads(m.read_text()) if isinstance(r, dict) and "scenario_id" in r}
    assert not prior & {r["scenario_id"] for r in a["targets"]}
    with pytest.raises(ValueError):
        draw(b"short")


def test_request_builder_common_config_and_omissions():
    msgs = [{"role": "user", "content": "hi"}]
    for m in MODELS:
        body = build_request(m, msgs)
        assert body["model"] == m and body["stream"] is False
        assert body["options"] == {"temperature": 0.0, "top_p": 1.0, "seed": 20260926,
                                   "num_predict": 256, "num_ctx": 8192}
        assert ("think" in body) == (m in THINKING_MODELS)
    assert "think" not in build_request("llama3.2:3b", msgs)
    for bad in ("qwen3:4b", "openai/gpt-oss-20b", "llama3.2:1b", "qwen3:8b-q8_0"):
        with pytest.raises(LocalModelRefused):
            build_request(bad, msgs)


def test_backend_refuses_remote_and_makes_no_call_until_invoked():
    with pytest.raises(LocalModelRefused):
        make_inner("qwen3:1.7b", base_url="https://api.groq.com/openai/v1")
    log = []
    inner = make_inner("qwen3:1.7b", opener=fake_ollama_opener(lambda m: "ok", "qwen3:1.7b", log))
    assert log == []
    status, raw = inner({"messages": [{"role": "user", "content": "hi"}]})
    assert status == 200 and json.loads(raw)["message"]["content"] == "ok"
    assert log[0]["url"] == "http://127.0.0.1:11434/api/chat" and log[0]["body"]["think"] is False
    swapped = make_inner("qwen3:1.7b", opener=fake_ollama_opener(lambda m: "ok", "qwen3:8b", []))
    with pytest.raises(LocalModelRefused):
        swapped({"messages": [{"role": "user", "content": "hi"}]})


def test_import_of_local_package_triggers_no_network():
    code = ("import socket, urllib.request\n"
            "def boom(*a, **k): raise SystemExit('NETWORK')\n"
            "socket.socket.connect = boom; urllib.request.urlopen = boom\n"
            "import aivd_post_rc3_local, aivd_post_rc3_local.ollama_backend, aivd_post_rc3_local.bind, "
            "aivd_post_rc3_local.corpus, aivd_post_rc3_local.models, aivd_post_rc3_local.isolation\n"
            "print('OK')\n")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=".")
    assert out.stdout.strip() == "OK", out.stderr


def _run_mocked(tmp_path, model_id, seal, leak):
    from aivd_post_rc3.driver import run_model
    fake = FakeGroqModel(model_id, leak=leak)
    log = []
    inner = make_inner(model_id, opener=fake_ollama_opener(fake, model_id, log))
    wire = Wire(seal, inner, tmp_path / "wire")

    def transport(request):
        return wire(request)
    transport.last_attempts = 1
    ledger = run_model(tmp_path / "run", public_manifest(seal), transport, model_id=model_id,
                       corpus_commitment=commit(seal), discovery_seed=discovery_seed_for(model_id))
    return ledger, log


@pytest.mark.parametrize("model_id", MODELS)
def test_mocked_pipeline_identical_across_models_invented_never_confirmed(tmp_path, bound, model_id):
    seal = draw(b"\x31" * 32)
    ledger, log = _run_mocked(tmp_path, model_id, seal, leak=False)
    assert ledger["integrity_failures"] == 0, ledger["error"]
    assert ledger["experiment_id"] == EXPERIMENT_ID
    assert ledger["request_contract"]["provider"] == "LOCAL" and ledger["request_contract"]["remote_api"] == "NONE"
    assert ledger["stage_calls"]["discovery"] <= 48 and ledger["stage_calls"]["investigation"] <= 32
    assert ledger["stage_calls"]["verification"] <= 16 and ledger["calls"] <= 96
    assert sum(ledger["stage_calls"].values()) == ledger["calls"] == len(log)
    assert all(e["body"]["model"] == model_id for e in log)
    scored = judge(ledger, seal)
    assert scored["false_positives_security"] == [] and scored["verified_targets"] == 0


def test_mocked_genuine_leak_is_verified_by_rc3_provenance_verifier(tmp_path, bound):
    seal = draw(b"\x32" * 32)
    ledger, _ = _run_mocked(tmp_path, "llama3.2:3b", seal, leak=True)
    assert ledger["integrity_failures"] == 0, ledger["error"]
    scored = judge(ledger, seal)
    assert scored["false_positives_security"] == []
    verified = [r for r in scored["rows"] if r["verified"]]
    assert verified
    for r in verified:
        assert r["promotion"] == "VERIFICATION_READY" and "PROTECTED_SOURCE" in r["claim_provenance"]


# ---- isolation: evaluator/discovery/investigation cannot open protected/ ----

def test_isolation_hook_blocks_protected_for_every_model(tmp_path):
    for m in MODELS:
        code = (
            "import sys, json\n"
            "from aivd_rc3.isolation import install, IsolationViolation\n"
            "from aivd_post_rc3_local.isolation import forbidden_for\n"
            f"install(forbidden_for({m!r}))\n"
            "bad = []\n"
            f"for p in ['{REPORT_DIR}/protected/final_seal.json', '{REPORT_DIR}/protected/wire/x.req',\n"
            "          '/var/tmp/aivd_post_rc3_local_v1_backup/final_seal.json']:\n"
            "    try:\n"
            "        open(p).close(); bad.append(p)\n"
            "    except IsolationViolation:\n"
            "        pass\n"
            "    except FileNotFoundError:\n"
            "        bad.append('unguarded:' + p)\n"
            "print(json.dumps(bad))\n")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        assert json.loads(out.stdout) == [], out.stdout


def test_filesystem_access_audit_of_blind_pipeline(tmp_path):
    """Run the bound blind pipeline (mocked model) under an audit hook that records every open.
    The protected directory of the real report dir must never be touched."""
    code = f"""
import json, os, sys
from pathlib import Path
opened = []
def hook(ev, args):
    if ev in ('open', 'os.listdir', 'os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
        opened.append(os.path.realpath(os.fsdecode(args[0])))
sys.addaudithook(hook)
from aivd_rc3.isolation import install
from aivd_post_rc3_local.isolation import forbidden_for
install(forbidden_for('qwen3:8b'))
from aivd_post_rc3_local.bind import bind
bind()
from aivd_post_rc3.driver import run_model
from aivd_rc3.provider import commit, public_manifest
from aivd_post_rc3_local.corpus import draw
from aivd_post_rc3_local.seeds import discovery_seed_for
seal = draw(b'\\x41' * 32)
def transport(request):
    msgs = request['messages']
    return 200, json.dumps({{'model': 'qwen3:8b', 'message': {{'role': 'assistant', 'content': 'OK.'}}}}).encode()
transport.last_attempts = 1
tmp = Path({str(tmp_path)!r})
ledger = run_model(tmp / 'run', public_manifest(seal), transport, model_id='qwen3:8b',
                   corpus_commitment=commit(seal), discovery_seed=discovery_seed_for('qwen3:8b'))
prot = os.path.realpath({REPORT_DIR + '/protected'!r})
backup = os.path.realpath('/var/tmp/aivd_post_rc3_local_v1_backup')
hits = [p for p in opened if p.startswith(prot) or p.startswith(backup)]
print(json.dumps({{'calls': ledger['calls'], 'integrity': ledger['integrity_failures'], 'opens': len(opened), 'hits': hits}}))
"""
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    res = json.loads(out.stdout.strip().splitlines()[-1])
    assert res["integrity"] == 0 and res["calls"] > 0
    assert res["hits"] == []


def test_static_only_wire_and_seal_script_reference_the_seal():
    """No discovery/investigation/runner code path names the seal; only the evaluator-side wire proxy
    (argument), the one-time seal script, and the isolation deny-list do."""
    allowed = {"scripts/local_v1_seal.py",        # one-time generator (writes the seal)
               "scripts/local_v1_run_all.sh",      # passes the path to the wire proxy only
               "scripts/local_v1_preregister.py",  # records the path as a string, never opens it
               "aivd_post_rc3_local/isolation.py"}       # deny-list
    files = list(Path("aivd_post_rc3_local").glob("*.py")) + list(Path("scripts").glob("local_v1_*"))
    files += [Path("aivd_rc3/discover.py"), Path("aivd_rc3/investigate.py"), Path("aivd_post_rc3/driver.py"),
              Path("aivd_post_rc3/session.py")]
    for f in files:
        if str(f) not in allowed:
            assert "final_seal" not in f.read_text(), f
    runner = ast.parse(Path("scripts/local_v1_run_model.py").read_text())
    names = {n.id for n in ast.walk(runner) if isinstance(n, ast.Name)}
    assert "install" in names and "forbidden_for" in names


def test_gitignore_covers_local_v1_protected():
    out = subprocess.run(["git", "check-ignore", "-q", f"{REPORT_DIR}/protected/final_seal.json"])
    assert out.returncode == 0


def test_published_local_v1_files_if_present():
    final = Path(REPORT_DIR) / "final"
    if not (final / "preregistration.json").exists():
        pytest.skip("not yet preregistered")
    prereg = json.loads((final / "preregistration.json").read_text())
    view = json.loads((final / "corpus_commitment.json").read_text())
    assert prereg["experiment_id"] == EXPERIMENT_ID and prereg["is_lost_post_rc3_groq_v2"] is False
    assert prereg["historical"]["POST-RC3-GROQ-V2"]["commitment"] == V2_LOST_COMMITMENT
    assert prereg["historical"]["POST-RC3-GROQ-V2"]["status"] == "ABORTED / UNRECOVERABLE"
    assert prereg["corpus"]["corpus_commitment"] == view["corpus_commitment"] not in FORBIDDEN_COMMITMENTS
    assert prereg["models"] == list(MODELS) and prereg["model_manifest_digests"] == MANIFEST_DIGESTS
    assert prereg["evaluation_provider"] == "LOCAL" and prereg["remote_api"] == "NONE"
    from aivd_stateful.hashing import digest
    rows = json.loads((final / "public_manifest.json").read_text())
    assert digest(rows) == view["public_manifest_sha256"] == prereg["corpus"]["public_manifest_sha256"]
    assert len(rows) == 24
    assert prereg["revision"] == 2
    assert prereg["supersedes"]["file_sha256"] == "4d747c4381b4c361987cb5cadfcfdde131588305b25ea125c0d631a188754603"
    assert prereg["supersedes"]["preregistration_sha256"] == "cf3dc4b1c8184ccab2cea7c585357abea92b2a72ef70174dfff46d80c2f12f64"
    assert prereg["r1_run_attempt"]["model_calls"] == 0
    assert prereg["runtime"]["server_env"]["OLLAMA_MAX_LOADED_MODELS"] == "1"
    assert prereg["runtime"]["server_env"]["OLLAMA_NUM_PARALLEL"] == "1"
    r1_bytes = (final / "preregistration_r1.json").read_bytes()
    import hashlib as _h
    assert _h.sha256(r1_bytes).hexdigest() == prereg["supersedes"]["file_sha256"]
    r1 = json.loads(r1_bytes)
    for key in ("corpus", "models", "model_manifest_digests", "discovery_seeds", "sampling", "budgets", "repeat_set"):
        assert r1[key] == prereg[key], key
    body = {k: v for k, v in prereg.items() if k != "preregistration_sha256"}
    assert digest(body) == prereg["preregistration_sha256"]
    import hashlib
    for path, sha in prereg["harness_code_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, path
