"""AIVD 3.41 — behavior-preserving planner audit ledger (T01–T16)."""
from __future__ import annotations

import hashlib
import inspect
import os
import random
import subprocess
from pathlib import Path

import pytest

from aivd.science.atom_synth import AtomSynthesizer, propose_atoms
from aivd.science.grow import REDISCOVERY_FLOOR
from aivd.science.lifecycle import expected_verified_value, rank_atoms
from aivd.science.methods import INVENT_CAP
from aivd.science.planner_audit_ledger import (
    MODE_ENV,
    NEVER_PROPOSED,
    NOT_REACHED_BEFORE_BUDGET_EXHAUSTION,
    NOT_RECORDED,
    PROPOSED,
    REQUIRED_FIELDS,
    SELECTED,
    SKIPPED,
    audit_enabled,
    clear_ledger,
    disable_audit,
    enable_audit,
    get_ledger,
    observe_invent,
    observe_not_recorded,
    observe_propose,
    observe_rank,
    observe_score,
    observe_skip,
    reset_ledger,
    snapshots_equal,
    twin_outcome_snapshot,
)

REPO = Path(__file__).resolve().parents[1]
BASELINE = "a380e3c"
PROMPT = "ab cd ef gh ij kl"
ODD_STRIDE_KEY = "MAPT(SLICE:1,2(TOK))"


def _git_blob(rev: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{rev}:{path}"], cwd=REPO, text=True
    ).strip()


def _work_blob(path: str) -> str:
    return subprocess.check_output(
        ["git", "hash-object", path], cwd=REPO, text=True
    ).strip()


@pytest.fixture(autouse=True)
def _audit_isolation():
    disable_audit()
    clear_ledger()
    os.environ.pop(MODE_ENV, None)
    yield
    disable_audit()
    clear_ledger()
    os.environ.pop(MODE_ENV, None)


def _plan_once(*, seed: int = 0, representation: str = "R0") -> dict:
    random.seed(seed)
    syn = AtomSynthesizer(representation=representation)
    kept = syn.plan(prompt=PROMPT, question=True, known_ops=set())
    selected: list[str] = []
    while True:
        a = syn.next_atom()
        if a is None:
            break
        selected.append(a.key())
    return {
        "kept_keys": [a.key() for a in kept],
        "selected_keys": selected,
        "proposal_raw": [a.key() for a in propose_atoms(prompt=PROMPT, question=True)],
        "board_dup": syn.board.duplicates,
        "board_val_fail": syn.board.validation_fail,
        "board_val_ok": syn.board.validation_ok,
    }


def test_T01_deterministic_replay_off():
    assert _plan_once(seed=7) == _plan_once(seed=7)


def test_T02_deterministic_replay_on():
    enable_audit()
    reset_ledger(seed=7, plant_id="t02")
    a = _plan_once(seed=7)
    dig_a = get_ledger().digest()
    clear_ledger()
    reset_ledger(seed=7, plant_id="t02")
    b = _plan_once(seed=7)
    dig_b = get_ledger().digest()
    assert a == b
    assert dig_a == dig_b


def test_T03_on_vs_off_semantic_equality():
    off = _plan_once(seed=11)
    snap_off = twin_outcome_snapshot(
        proposal_keys=off["proposal_raw"],
        selections=off["selected_keys"],
        inventions=off["kept_keys"],
        budget_series=[off["board_dup"], off["board_val_fail"], off["board_val_ok"]],
        final_state="ok",
    )
    enable_audit()
    reset_ledger(seed=11, plant_id="t03")
    on = _plan_once(seed=11)
    snap_on = twin_outcome_snapshot(
        proposal_keys=on["proposal_raw"],
        selections=on["selected_keys"],
        inventions=on["kept_keys"],
        budget_series=[on["board_dup"], on["board_val_fail"], on["board_val_ok"]],
        final_state="ok",
    )
    assert off == on
    assert snapshots_equal(snap_off, snap_on)


def test_T04_zero_budget_consumption():
    off = _plan_once(seed=3)
    enable_audit()
    reset_ledger(seed=3, plant_id="t04")
    on = _plan_once(seed=3)
    assert off == on


def test_T05_zero_rng_consumption():
    def stream(audit: bool):
        random.seed(42)
        if audit:
            enable_audit()
            reset_ledger(seed=42, plant_id="t05")
        else:
            disable_audit()
            clear_ledger()
        observe_propose(propose_atoms(prompt=PROMPT, question=True))
        return [random.random() for _ in range(16)]

    assert stream(False) == stream(True)


def test_T06_proposal_ledger_emission():
    enable_audit()
    reset_ledger(seed=0, plant_id="t06")
    syn = AtomSynthesizer(representation="R0")
    syn.plan(prompt=PROMPT, question=True, known_ops=set())
    props = [r for r in get_ledger().rows if r.event == "propose"]
    assert len(props) >= 8
    for r in props:
        assert r.proposal_state == PROPOSED
        assert r.candidate_key != NOT_RECORDED
        assert r.proposal_index != NOT_RECORDED
    odd = [r for r in props if r.proposal_index == 3]
    assert len(odd) == 1
    assert odd[0].candidate_key == ODD_STRIDE_KEY


def test_T07_reject_ledger_emission():
    enable_audit()
    reset_ledger(seed=0, plant_id="t07")
    syn = AtomSynthesizer(representation="R0")
    raw = propose_atoms(prompt=PROMPT, question=True)
    for a in raw:
        syn.board.seen.add(a.key())
    syn.plan(prompt=PROMPT, question=True, known_ops=set())
    rejects = [r for r in get_ledger().rows if r.event == "reject"]
    assert rejects
    assert any(r.rejection_reason == "duplicate_key" for r in rejects)


def test_T08_score_ledger_emission():
    enable_audit()
    reset_ledger(seed=0, plant_id="t08")
    atoms = propose_atoms(prompt=PROMPT, question=True)
    ranked = rank_atoms(
        list(atoms),
        rejected_classes=set(),
        leftover=5,
        invariant_ready=True,
        greedy=False,
    )
    for a in ranked:
        sc = expected_verified_value(
            p_discovery=0.35,
            p_verification=0.85,
            causal_value=1.0,
            reuse_value=1.1,
            cost=1.0,
        )
        observe_score(a, score=sc, score_components={"semantic_class": a.semantic_class})
    observe_rank(ranked, rejected_classes=set(), leftover=5)
    scores = [r for r in get_ledger().rows if r.event == "score"]
    assert len(scores) == len(ranked)
    assert all(r.score != NOT_RECORDED for r in scores)


def test_T09_rank_ledger_emission():
    enable_audit()
    reset_ledger(seed=0, plant_id="t09")
    atoms = propose_atoms(prompt=PROMPT, question=True)
    ranked = rank_atoms(
        list(atoms),
        rejected_classes={"char_stride"},
        leftover=5,
        invariant_ready=True,
    )
    observe_rank(ranked, rejected_classes={"char_stride"}, leftover=5)
    rows = [r for r in get_ledger().rows if r.event == "rank"]
    assert [r.rank for r in rows] == list(range(len(ranked)))
    assert [r.candidate_key for r in rows] == [a.key() for a in ranked]


def test_T10_select_skip_ledger_emission():
    enable_audit()
    reset_ledger(seed=0, plant_id="t10")
    syn = AtomSynthesizer(representation="R0")
    syn.plan(prompt=PROMPT, question=True, known_ops=set())
    a = syn.next_atom()
    assert a is not None
    selects = [r for r in get_ledger().rows if r.event == "select"]
    assert selects and selects[0].selection_state == SELECTED
    observe_skip(
        selection_reason="ATOM_INVENTION_SKIPPED_BY_PLANNING",
        budget_before=2,
        budget_after=2,
    )
    skips = [r for r in get_ledger().rows if r.event == "skip"]
    assert skips and skips[0].selection_state == SKIPPED


def test_T11_invent_not_invent_ledger():
    enable_audit()
    reset_ledger(seed=0, plant_id="t11")
    atoms = propose_atoms(prompt=PROMPT, question=True)
    observe_propose(atoms)
    observe_invent(atoms[0], body_key=atoms[0].key(), budget_before=5, budget_after=4)
    invents = [r for r in get_ledger().rows if r.event == "invent"]
    assert invents and invents[0].body_key == atoms[0].key()
    observe_skip(
        selection_reason="INVENTORY_CAPACITY_FAILURE",
        budget_before=4,
        budget_after=4,
    )
    assert any(r.selection_reason == "INVENTORY_CAPACITY_FAILURE" for r in get_ledger().rows)


def test_T12_never_proposed_vs_budget_not_reached():
    enable_audit()
    reset_ledger(seed=0, plant_id="t12")
    atoms = propose_atoms(prompt=PROMPT, question=True)
    observe_propose(atoms)
    led = get_ledger()
    assert led.classify_budget_reach("NO_SUCH_CANDIDATE") == NEVER_PROPOSED
    observe_skip(
        selection_reason="ATOM_INVENTION_SKIPPED_BY_PLANNING",
        budget_before=2,
        budget_after=2,
        candidate_key=atoms[3].key(),
    )
    assert led.classify_budget_reach(atoms[3].key()) == NOT_REACHED_BEFORE_BUDGET_EXHAUSTION
    clear_ledger()
    reset_ledger(seed=0, plant_id="t12b")
    assert get_ledger().classify_budget_reach("x") == NOT_RECORDED


def test_T13_s_observational_non_seeding():
    src = inspect.getsource(propose_atoms)
    for tok in ("ODDSTRIDE", "odd_double", "S-ATOM", "S_ATOM", "S-CAT", "S_CAT", "S-DIAG", "seed_s"):
        assert tok not in src
    base = [a.key() for a in propose_atoms(prompt=PROMPT, question=True)]
    enable_audit()
    reset_ledger(seed=0, plant_id="t13")
    on = [a.key() for a in propose_atoms(prompt=PROMPT, question=True)]
    assert base == on
    assert ODD_STRIDE_KEY in base


def test_T14_natural_success_controls():
    enable_audit()
    reset_ledger(seed=0, plant_id="t14")
    syn = AtomSynthesizer(representation="R0")
    kept = syn.plan(prompt=PROMPT, question=True, known_ops=set())
    assert kept
    props = [r.candidate_key for r in get_ledger().rows if r.event == "propose"]
    for a in kept:
        assert a.key() in props


def test_T15_forbidden_surface_freeze():
    for path in (
        "aivd/science/grow.py",
        "aivd/science/lifecycle.py",
        "aivd/science/methods.py",
        "aivd/science/language.py",
    ):
        assert _work_blob(path) == _git_blob(BASELINE, path), path
    for mod_path, fn in (
        ("aivd/science/atom_synth.py", propose_atoms),
        ("aivd/science/lifecycle.py", rank_atoms),
        ("aivd/science/lifecycle.py", expected_verified_value),
    ):
        baseline_src = subprocess.check_output(
            ["git", "show", f"{BASELINE}:{mod_path}"], cwd=REPO, text=True
        )
        cur = inspect.getsource(fn)
        assert cur in baseline_src, f"{fn.__name__} drifted from {BASELINE}"
    assert INVENT_CAP == 48
    assert REDISCOVERY_FLOOR == 5


def test_T16_instrumentation_off_regression():
    assert audit_enabled() is False
    assert get_ledger() is None
    out = _plan_once(seed=99)
    assert get_ledger() is None
    os.environ[MODE_ENV] = "0"
    assert audit_enabled() is False
    observe_propose(propose_atoms(prompt=PROMPT, question=True))
    assert get_ledger() is None
    os.environ[MODE_ENV] = "1"
    assert audit_enabled() is True
    reset_ledger(seed=1, plant_id="t16")
    observe_propose(propose_atoms(prompt=PROMPT, question=True))
    assert get_ledger() is not None and len(get_ledger().rows) >= 8
    row = get_ledger().rows[0].as_dict()
    for f in REQUIRED_FIELDS:
        assert f in row
    observe_not_recorded("grow._keep", reason="grow.py frozen; FILTER path not hooked")
    assert any(r.event == "not_recorded" for r in get_ledger().rows)
    os.environ.pop(MODE_ENV, None)
    disable_audit()
    clear_ledger()
    assert _plan_once(seed=99) == out


def test_odd_stride_observed_never_special_cased():
    enable_audit()
    reset_ledger(seed=0, plant_id="odd")
    syn = AtomSynthesizer(representation="R0")
    syn.plan(prompt=PROMPT, question=True, known_ops=set())
    props = [r for r in get_ledger().rows if r.event == "propose"]
    assert props[3].proposal_index == 3
    assert props[3].candidate_key == ODD_STRIDE_KEY
    ledger_src = (REPO / "aivd/science/planner_audit_ledger.py").read_text()
    assert "SLICE:1,2" not in ledger_src
    assert "ODDSTRIDE" not in ledger_src
