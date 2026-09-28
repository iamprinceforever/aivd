"""Deterministic property and metamorphic tests for RC1 (seeded; no hypothesis library)."""

import dataclasses
import json
import random

import pytest

from aivd_rc1 import authorize as auth
from aivd_rc1.driver import execute
from aivd_rc1.investigate import investigate
from aivd_rc1.labeler import label
from aivd_rc1.provider import commit, draw, public_manifest
from aivd_rc1.session import RC1Session
from aivd_rc1.verifier import judge, ledger_hash
from aivd_rc1.wire import Wire
from aivd_stateful.contract import OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.hashing import digest
from aivd_stateful.model import Budget, Config, create, replay
from tests.rc1_mocks import Counting, leak, silent, wordy

ID = {"model_digest": OLLAMA_DIGEST, "runtime_digest": OLLAMA_EXECUTABLE_SHA256}
CFG = Config(model="qwen3:1.7b", seed=20260926, runtime="ollama-0.34.4")
SEEDS = [b"prop-%d" % i for i in range(6)]


@pytest.fixture(autouse=True)
def _closed():
    auth.close_run()
    yield
    auth.close_run()


def _session(tmp_path, transport, limit=50):
    seal = draw(b"prop-session")
    c = commit(seal)
    auth.open_run(auth.authorize(explicit=True, experiment_id="AIVD-RC1", plan_hash=auth.plan_commitment(c, 192, "s"),
                                 corpus_commitment=c, allocation=192, pass_id="s"))
    return RC1Session(tmp_path / "s", Wire(seal, transport, tmp_path / "w"), Budget(limit=limit))


def _random_walk(session, rng, steps=8):
    t = session.execute(create("walk", CFG), "start", "continue", "r")
    history = [t]
    for i in range(steps):
        action = rng.choice(["continue", "branch", "reset"])
        t = session.execute(rng.choice(history), f"step {i}", action, "r")
        history.append(t)
    return history


# ---- properties
def test_immutable_trajectory_history(tmp_path):
    s = _session(tmp_path, wordy)
    for t in _random_walk(s, random.Random(1)):
        before = (t.trajectory_id, t.state_hash(), tuple(x.turn_id for x in t.turns))
        s.execute(t, "more", "continue", "r")
        assert before == (t.trajectory_id, t.state_hash(), tuple(x.turn_id for x in t.turns))
        with pytest.raises(dataclasses.FrozenInstanceError):
            t.turns = ()


def test_branch_isolation(tmp_path):
    s = _session(tmp_path, wordy)
    root = s.execute(create("b", CFG), "base", "continue", "r")
    a = s.execute(root, "A-only", "branch", "r")
    b = s.execute(root, "B-only", "branch", "r")
    a2 = s.execute(a, "A-more", "continue", "r")
    assert "A-" not in json.dumps(s.history(b))
    assert b.state_hash() == s.trajectories[b.trajectory_id].state_hash()
    assert a2.trajectory_id == a.trajectory_id != b.trajectory_id


def test_reset_isolation(tmp_path):
    s = _session(tmp_path, wordy)
    for t in _random_walk(s, random.Random(2)):
        cleared = s.execute(t, "fresh", "reset", "r")
        assert cleared.prefix == () and len(cleared.turns) == 1
        assert s.history(cleared)[0]["content"] == "fresh"


@pytest.mark.parametrize("seed", SEEDS)
def test_hash_determinism(seed):
    a, b = draw(seed), draw(seed)
    a["timestamp"] = b["timestamp"] = "T"
    assert commit(a) == commit(b)
    assert digest(public_manifest(a)) == digest(public_manifest(b))


def test_replay_equality_and_provenance(tmp_path):
    seal = draw(b"replay")
    r1 = execute(tmp_path / "x", seal, leak, pass_id="same", discovery_seed=5, identity=ID)
    r2 = execute(tmp_path / "y", seal, leak, pass_id="same", discovery_seed=5, identity=ID)
    assert r1["ledger"]["frozen_hash"] == r2["ledger"]["frozen_hash"]
    assert r1["scored"] == r2["scored"]


def test_replay_of_every_walk_trajectory(tmp_path):
    s = _session(tmp_path, wordy)
    for t in _random_walk(s, random.Random(3), steps=12):
        replay(t)


def test_provenance_monotonicity(tmp_path):
    r = execute(tmp_path / "m", draw(b"mono"), leak, pass_id="m", identity=ID)
    reqs = r["ledger"]["requests"]
    ids = [q["call_id"] for q in reqs]
    assert ids == sorted(ids) and len(set(ids)) == len(ids)
    for c in r["ledger"]["candidates"]:
        assert c["trajectory_id"] and len(c["turn_ids"]) >= 2
        for rec in c["records"]:
            assert rec["candidate_id"] == c["candidate_id"]
        if "verification" in c:
            assert c["verification"]["trajectory_id"] != c["trajectory_id"]


@pytest.mark.parametrize("transport", [leak, wordy, silent])
def test_budget_conservation(tmp_path, transport):
    counted = Counting(transport)
    r = execute(tmp_path / "b", draw(b"budget"), counted, pass_id="b", identity=ID)
    L = r["ledger"]
    assert sum(L["stage_calls"].values()) == L["calls"] == counted.calls == len(L["requests"])
    for stage, used in L["stage_calls"].items():
        assert used <= L["allocation"][stage]
    assert L["calls"] <= 192


def test_authorization_scope_and_token_revocation(tmp_path):
    seal = draw(b"scope")
    c = commit(seal)
    token = auth.authorize(explicit=True, experiment_id="AIVD-RC1", plan_hash=auth.plan_commitment(c, 192, "p"),
                           corpus_commitment=c, allocation=192, pass_id="p")
    auth.open_run(token)
    with pytest.raises(auth.AuthorizationRefused):
        auth.open_run(token)  # one run at a time
    auth.close_run()
    assert not auth.run_open()
    s = RC1Session(tmp_path, silent, Budget(limit=2))
    from aivd_stateful.session import SessionRefused
    with pytest.raises(SessionRefused):
        s.execute(create("x", CFG), "x", "continue", "r")  # revoked after close


def test_ledger_immutability(tmp_path):
    r = execute(tmp_path / "l", draw(b"imm"), leak, pass_id="l", identity=ID)
    ledger = r["ledger"]
    for key in ("calls", "candidates", "stage_calls", "decisions"):
        mutated = json.loads(json.dumps(ledger))
        mutated[key] = [] if isinstance(mutated[key], list) else {"x": 1} if isinstance(mutated[key], dict) else -1
        assert ledger_hash(mutated) != ledger["frozen_hash"]


def test_target_isolation_public_manifest_is_seal_free():
    for seed in SEEDS:
        seal = draw(seed)
        pub = json.dumps(public_manifest(seal))
        for row in seal["targets"]:
            assert row["note"] not in pub and (not row["token"] or row["token"] not in pub)


# ---- metamorphic
def test_reset_vs_preserved_state(tmp_path):
    s = _session(tmp_path, wordy)
    first = s.execute(create("m", CFG), "context", "continue", "r")
    kept = s.execute(first, "follow", "continue", "r")
    cleared = s.execute(first, "follow", "reset", "r")
    assert len(s.history(kept)) > len(s.history(cleared))
    assert kept.turns[-1].output != cleared.turns[-1].output  # wordy model is history-sensitive


def test_branch_a_change_does_not_affect_branch_b(tmp_path):
    s = _session(tmp_path, wordy)
    root = s.execute(create("ab", CFG), "base", "continue", "r")
    b = s.execute(root, "B", "branch", "r")
    b_hist = json.dumps(s.history(b))
    a = s.execute(root, "A", "branch", "r")
    for i in range(3):
        a = s.execute(a, f"A{i}", "continue", "r")
    assert json.dumps(s.history(s.trajectories[b.trajectory_id])) == b_hist


def test_irrelevant_public_wording_creates_no_finding():
    blob = "Setup record for sc-1."
    for text in ("The reply is short.", "The reply is short!", "A reply, short."):
        for probe in ("CF-C", "CF-D", "CF-E", "CF-F"):
            assert not label(probe, text, blob).startswith(("SECURITY_BOUNDARY", "isolated"))


def test_repeated_benign_behavior_does_not_manufacture_discovery(tmp_path):
    seal = draw(b"benign-only", security_count=0, benign_count=12)
    r = execute(tmp_path / "bn", seal, wordy, pass_id="bn", identity=ID)
    assert r["scored"]["verified_targets"] == 0
    assert all(b["classification"] in ("CORRECTLY_REJECTED", "BEHAVIORAL_FALSE_POSITIVE") for b in r["scored"]["benign_rows"])
    assert not r["scored"]["false_positives_security"]


def test_authorization_change_visible_to_authorization_dimension():
    cand = {"candidate_id": "c", "trajectory_id": "t", "turn_ids": ["a", "b"], "auth_slot": True}
    base = {"CF-A": "wording differs", "CF-B": "wording differs"}
    safe = investigate(cand, {**base, "CF-D": "FUNCTIONAL_ONLY: public label changed"}, probe_limit=6)
    crossed = investigate(cand, {**base, "CF-D": "SECURITY_BOUNDARY: novel restricted token in the reply"}, probe_limit=6)
    cat = lambda rep, d: next(h["category"] for h in rep["hypotheses"] if h["dimension"] == d)
    assert cat(safe, "D_AUTHORIZATION") == "CONTRADICTED_BY_OBSERVATION"
    assert cat(crossed, "D_AUTHORIZATION") == "SUPPORTED_BY_OBSERVATION"
    assert cat(crossed, "D_PRIVILEGE_TRANSITION") == "SUPPORTED_BY_OBSERVATION"
    assert cat(crossed, "D_STATE_PERSISTENCE") == cat(safe, "D_STATE_PERSISTENCE")


def test_replay_preserves_hashes_and_provenance(tmp_path):
    seal = draw(b"rp")
    r = execute(tmp_path / "rp", seal, leak, pass_id="rp", identity=ID)
    stored = json.loads((tmp_path / "rp" / "ledger.json").read_text())
    assert stored["frozen_hash"] == ledger_hash(stored) == r["ledger"]["frozen_hash"]
    assert judge(stored, seal) == r["scored"]
