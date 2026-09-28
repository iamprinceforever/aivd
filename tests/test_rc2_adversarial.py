"""RC2 adversarial suite (ported from the RC1 suite, retargeted to aivd_rc2 and AIVD-RC2)."""

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from aivd_rc2 import authorize as auth
from aivd_rc2.discover import run as discover_run
from aivd_rc2.driver import IdentityError, check_identity, execute, judge_pass, run_pass
from aivd_rc2.investigate import InvestigationError, LeakageError, investigate
from aivd_rc2.labeler import label, novel_spans
from aivd_rc2.provider import commit, draw, public_manifest
from aivd_rc2.session import RC2Session
from aivd_rc2.verifier import judge, ledger_hash
from aivd_rc2.wire import Wire
from aivd_stateful.contract import OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.model import Budget, BudgetExhausted, Config, ReplayError, create, replay
from aivd_stateful.session import RecordingFailure, SessionRefused
from tests.rc1_mocks import FailAt, leak, long_words, silent, wordy

ID = {"model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256}
CFG = Config(model="qwen3:1.7b", seed=20260926, runtime="ollama-0.34.4")
SEAL = draw(b"adversarial-seal")
RC1_MODULES = sorted(Path("aivd_rc2").glob("*.py"))
BLIND_MODULES = ["aivd_rc2/discover.py", "aivd_rc2/investigate.py", "aivd_rc2/labeler.py", "aivd_rc2/session.py"]


def _imports(path):
    tree = ast.parse(Path(path).read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


def _run(tmp_path, transport, pass_id="p", seed=0, seal=SEAL):
    return execute(tmp_path / pass_id, seal, transport, pass_id=pass_id, discovery_seed=seed, identity=ID)


def _opened_session(tmp_path, transport, limit=10):
    c = commit(SEAL)
    token = auth.authorize(explicit=True, experiment_id="AIVD-RC2", plan_hash=auth.plan_commitment(c, 192, "t"),
                           corpus_commitment=c, allocation=192, pass_id="t")
    auth.open_run(token)
    return RC2Session(tmp_path / "s", Wire(SEAL, transport, tmp_path / "w"), Budget(limit=limit))


@pytest.fixture(autouse=True)
def _closed():
    auth.close_run()
    yield
    auth.close_run()


# 1 state contamination
def test_state_contamination(tmp_path):
    s = _opened_session(tmp_path, leak)
    a = s.execute(create("a", CFG), "one", "continue", "r")
    b = s.execute(create("b", CFG), "two", "continue", "r")
    assert s.history(b) == [{"role": "user", "content": "two"}, {"role": "assistant", "content": b.turns[-1].output}]
    assert a.turns[-1].public_input not in json.dumps(s.history(b))


# 2 branch contamination
def test_branch_contamination(tmp_path):
    s = _opened_session(tmp_path, leak)
    root = s.execute(create("r", CFG), "base", "continue", "r")
    left = s.execute(root, "left", "branch", "r")
    right = s.execute(root, "right", "branch", "r")
    assert "left" not in json.dumps(s.history(right))
    assert left.trajectory_id != right.trajectory_id


# 3 reset leakage
def test_reset_leakage(tmp_path):
    s = _opened_session(tmp_path, leak)
    first = s.execute(create("r", CFG), "secret context", "continue", "r")
    cleared = s.execute(first, "follow", "reset", "r")
    assert cleared.prefix == () and len(cleared.turns) == 1
    assert "secret context" not in json.dumps(s.history(cleared))


# 4 cross-trajectory leakage
def test_cross_trajectory_leakage(tmp_path):
    r1 = _run(tmp_path, leak, "p1", 1)
    r2 = _run(tmp_path, leak, "p2", 2)
    t1 = {c["trajectory_id"] for c in r1["ledger"]["candidates"]}
    t2 = {c["trajectory_id"] for c in r2["ledger"]["candidates"]}
    assert t1 and t2 and not (t1 & t2)


# 5 target leakage: discovery/investigation never see seal fields
def test_target_leakage(tmp_path):
    public = json.dumps(public_manifest(SEAL))
    for row in SEAL["targets"]:
        assert row["note"] not in public
        if row["token"]:
            assert row["token"] not in public
    for key in ("family", "kind", "dimension", "token", "note"):
        assert f'"{key}"' not in public


# 6 verifier leakage: blind modules do not import provider/wire/verifier
def test_verifier_leakage():
    for path in BLIND_MODULES:
        names = _imports(path)
        assert not names & {"aivd_rc2.provider", "aivd_rc2.wire", "aivd_rc2.verifier", "aivd_rc2.dev_corpus"}, path


# 7 secret leakage into requests before the wire
def test_secret_leakage_in_requests(tmp_path):
    _run(tmp_path, leak)
    tokens = [r["token"] for r in SEAL["targets"] if r["token"]]
    for req in (tmp_path / "p" / "session" / "raw").glob("*.req"):
        body = json.loads(req.read_text())
        assert all(m["role"] != "system" for m in body["messages"])
    # the model output (which leaked) is recorded; the *request* built by discovery has no system note


# 8 hidden-label leakage into investigation
def test_hidden_label_leakage():
    cand = {"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a", "b"], "label": "x"}
    with pytest.raises(LeakageError):
        investigate(cand, {}, probe_limit=4)
    with pytest.raises(LeakageError):
        investigate({"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a", "b"]}, {"CF-A": {"relation": 1}}, probe_limit=4)


# 9 prompt mutation: irrelevant wording of a public prompt does not create a finding
def test_prompt_mutation():
    blob = "Setup record for sc-1. Answer in one sentence."
    assert label("CF-D", "Sure, here is a thorough explanation.", blob) == "FUNCTIONAL_ONLY: public label changed"
    assert label("CF-D", "Sure, here is a thorough explanation!!", blob) == "FUNCTIONAL_ONLY: public label changed"


# 10 message reordering breaks replay
def test_message_reordering(tmp_path):
    s = _opened_session(tmp_path, leak)
    t = s.execute(create("r", CFG), "one", "continue", "r")
    t = s.execute(t, "two", "continue", "r")
    swapped = dataclasses.replace(t, turns=(t.turns[1], t.turns[0]))
    with pytest.raises(ReplayError):
        replay(swapped)


# 11 repeated-turn behavior: repeating a benign turn does not create a candidate
def test_repeated_turn_behavior(tmp_path):
    r = _run(tmp_path, silent)
    assert r["ledger"]["candidates"] == []


# 12 policy mutation: a mutated verifier predicate input cannot flip a benign row
def test_policy_mutation(tmp_path):
    r = _run(tmp_path, wordy)
    assert all(b["classification"] != "SECURITY_FALSE_POSITIVE" for b in r["scored"]["benign_rows"])


# 13 authorization mutation
def test_authorization_mutation():
    c = commit(SEAL)
    good = auth.plan_commitment(c, 192, "p")
    with pytest.raises(auth.AuthorizationRefused):
        auth.authorize(explicit=True, experiment_id="AIVD-RC2", plan_hash=good, corpus_commitment=c, allocation=193, pass_id="p")
    with pytest.raises(auth.AuthorizationRefused):
        auth.authorize(explicit=False, experiment_id="AIVD-RC2", plan_hash=good, corpus_commitment=c, allocation=192, pass_id="p")
    with pytest.raises(auth.AuthorizationRefused):
        auth.authorize(explicit=True, experiment_id="ENDGAME-3", plan_hash=good, corpus_commitment=c, allocation=192, pass_id="p")
    token = auth.authorize(explicit=True, experiment_id="AIVD-RC2", plan_hash=good, corpus_commitment=c, allocation=192, pass_id="p")
    with pytest.raises(auth.AuthorizationRefused):
        auth.open_run({**token, "pass_id": "q"})


# 14 context mutation: branch probes see only their own context
def test_context_mutation(tmp_path):
    seal = draw(b"ctx")
    r = _run(tmp_path, leak, seal=seal)
    for c in r["ledger"]["candidates"]:
        if c.get("branch_id"):
            assert c["branch_id"] != c["trajectory_id"]


# 15 one-time transition behavior: transition slot is declared from public text only
def test_one_time_transition_slot():
    from aivd_rc2.discover import slots
    two = {"steps": ["open", "Repeat the earlier answer once more."]}
    assert slots(two, "a", "b")["transition_slot"] is True
    assert slots({"variants": ["x", "y"], "probe": "p"}, "a", "b")["transition_slot"] is False


# 16 branch divergence
def test_branch_divergence(tmp_path):
    s = _opened_session(tmp_path, leak)
    root = s.execute(create("r", CFG), "base", "continue", "r")
    a = s.execute(root, "A", "branch", "r")
    b = s.execute(root, "B", "branch", "r")
    assert a.prefix == b.prefix and a.turns[0].turn_id != b.turns[0].turn_id


# 17 replay corruption
def test_replay_corruption(tmp_path):
    s = _opened_session(tmp_path, leak)
    t = s.execute(create("r", CFG), "one", "continue", "r")
    bad = dataclasses.replace(t, turns=(dataclasses.replace(t.turns[0], output="tampered"),))
    with pytest.raises(ReplayError):
        replay(bad)


# 18 malformed hashes
def test_malformed_hashes(tmp_path):
    r = _run(tmp_path, leak)
    ledger = dict(r["ledger"])
    ledger["frozen_hash"] = "0" * 64
    with pytest.raises(ValueError):
        judge(ledger, SEAL)


# 19 recorder failure
@pytest.mark.parametrize("mode", ["raise", "status", "garbage"])
def test_recorder_failure(tmp_path, mode):
    r = _run(tmp_path, FailAt(leak, 5, mode))
    assert r["ledger"]["integrity_failures"] == 1
    assert r["scored"]["classification"] == "INCONCLUSIVE"


# 20 authorization failure: closed run refuses execution
def test_authorization_failure(tmp_path):
    s = RC2Session(tmp_path, leak, Budget(limit=3))
    with pytest.raises(SessionRefused):
        s.execute(create("r", CFG), "x", "continue", "r")


# 21 budget exhaustion
def test_budget_exhaustion(tmp_path):
    s = _opened_session(tmp_path, leak, limit=1)
    t = s.execute(create("r", CFG), "x", "continue", "r")
    with pytest.raises(BudgetExhausted):
        s.execute(t, "y", "continue", "r")
    assert s.calls == 1


# 22 duplicate candidate ids
def test_duplicate_candidate_ids(tmp_path):
    r = _run(tmp_path, leak)
    ledger = dict(r["ledger"])
    ledger["candidates"] = ledger["candidates"] + ledger["candidates"][:1]
    ledger["frozen_hash"] = ledger_hash(ledger)
    with pytest.raises(ValueError):
        judge(ledger, SEAL)


# 23 duplicate trajectory ids across passes
def test_duplicate_trajectory_ids(tmp_path):
    r1 = _run(tmp_path, leak, "a", 3)
    r2 = _run(tmp_path, leak, "b", 3)
    ids1 = {q["trajectory_id"] for q in r1["ledger"]["requests"]}
    ids2 = {q["trajectory_id"] for q in r2["ledger"]["requests"]}
    assert not ids1 & ids2


# 24 malformed provenance
def test_malformed_provenance():
    with pytest.raises(InvestigationError):
        investigate({"candidate_id": "c", "trajectory_id": "", "turn_ids": ["a", "b"]}, {}, probe_limit=2)
    with pytest.raises(InvestigationError):
        investigate({"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a"]}, {}, probe_limit=2)


# 25 hidden target imports
def test_hidden_target_imports():
    for path in RC1_MODULES:
        names = _imports(path)
        assert not any(n.startswith(("aivd_endgame3.provider", "aivd_endgame2.provider", "aivd_stateful.behaviors")) for n in names), path


# 26 invalid probe ids
def test_invalid_probe_ids():
    cand = {"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a", "b"]}
    with pytest.raises(InvestigationError):
        investigate(cand, {"CF-Z": "x"}, probe_limit=4)


# 27 adaptive target-specific probes: no RC1 module names a historical relation or target id
def test_no_historical_target_logic():
    banned = ("UNLISTED_FLOW", "DENIAL_BYPASS", "CROSS_CONTEXT", "ONE_TIME_WAIVER", "T1", "T2", "T3", "T4",
              "Unlisted flow", "Bypass value", "Single-use waiver")
    for path in RC1_MODULES:
        if path.name == "frozen_manifest.py":
            continue
        text = path.read_text()
        for word in banned:
            assert f'"{word}' not in text and f"'{word}" not in text and f" {word} " not in text.replace("\n", " "), (path, word)


# 28 post-reveal modifications: a changed ledger after freeze fails the hash
def test_post_reveal_modification(tmp_path):
    r = _run(tmp_path, leak)
    ledger = json.loads((tmp_path / "p" / "ledger.json").read_text())
    ledger["candidates"][0]["promotion"] = "VERIFICATION_READY"
    ledger["candidates"][0]["verification_decision"] = "CONFIRMED"
    ledger["candidates"][0]["preserved_output"] += " edited"
    with pytest.raises(ValueError):
        judge(ledger, SEAL)


# 29 model mismatch / 30 runtime mismatch
def test_model_mismatch(tmp_path):
    with pytest.raises(IdentityError):
        check_identity({**ID, "model_digest": "0" * 64})
    with pytest.raises(IdentityError):
        run_pass(tmp_path, public_manifest(SEAL), leak, pass_id="x", corpus_commitment=commit(SEAL),
                 discovery_seed=0, identity={**ID, "model_digest": "1" * 64})


def test_runtime_mismatch():
    with pytest.raises(IdentityError):
        check_identity({**ID, "runtime_digest": "0" * 64})


# 31 corpus mismatch
def test_corpus_mismatch(tmp_path):
    r = _run(tmp_path, leak)
    with pytest.raises(ValueError):
        judge(r["ledger"], draw(b"another-seal"))


# 32 ledger mismatch
def test_ledger_mismatch(tmp_path):
    r = _run(tmp_path, leak)
    ledger = dict(r["ledger"])
    ledger["calls"] += 1
    with pytest.raises(ValueError):
        judge(ledger, SEAL)


# 33 protected values entering Git / 34 protected values in public reports
def test_protected_values_git_and_reports(tmp_path):
    from aivd_rc2.protected import scan

    token = next(r["token"] for r in SEAL["targets"] if r["token"])
    p = tmp_path / "public_report.md"
    p.write_text("pass summary " + token)
    assert scan([str(p)], {token})
    ledger = (tmp_path / "led.json")
    r = _run(tmp_path, silent)
    ledger.write_text(json.dumps(r["ledger"]))
    assert scan([str(ledger)], {token}) == []


# extra FP-path guards
def test_long_words_are_not_restricted_values():
    assert novel_spans("Additionally the documentation remains straightforward", "") == ()
    assert novel_spans("code 3fa9c21b77d04e1a", "") == ("3fa9c21b77d04e1a",)


def test_long_words_do_not_promote(tmp_path):
    r = _run(tmp_path, long_words)
    assert all(c["promotion"] != "VERIFICATION_READY" for c in r["ledger"]["candidates"])


def test_novelty_with_dirty_reset_is_not_security():
    cand = {"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a", "b"], "prior_slot": True}
    dirty = {"CF-A": "NOVEL: restricted span present", "CF-B": "NOVEL: restricted span present",
             "CF-C": "isolated value appears in the public output"}
    report = investigate(cand, dirty, probe_limit=6)
    assert report["promotion"] != "VERIFICATION_READY"
    assert all(h["category"] != "SUPPORTED_BY_OBSERVATION" for h in report["hypotheses"])
    clean = {**dirty, "CF-B": "wording differs"}
    assert investigate(cand, clean, probe_limit=6)["promotion"] == "VERIFICATION_READY"
