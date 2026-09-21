"""Phase-1 replay: CF labeling, U gate, no discovery imports, no Stage-2 mutation."""
from __future__ import annotations

import hashlib
import importlib
import inspect
from pathlib import Path

import pytest

from aivd.experiments.aivd340 import phase1_replay as replay_mod
from aivd.experiments.aivd340.phase1_normalize import normalize_all, sha256_file
from aivd.experiments.aivd340.phase1_replay import (
    FORBIDDEN_DISCOVERY_MODULES,
    ODD_CAT_SELF,
    ODD_STRIDE_ATOM,
    is_odd_stride_atom,
    replay_all,
    run_u_positive_control_gate,
    what_if_grow,
    what_if_select,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def batch():
    return normalize_all(repo_root=ROOT)


@pytest.fixture(scope="module")
def replay_batch(batch):
    return replay_all(batch)


def test_no_forbidden_discovery_imports():
    import ast

    src_path = Path(inspect.getfile(replay_mod))
    tree = ast.parse(src_path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    for mod in FORBIDDEN_DISCOVERY_MODULES:
        assert mod not in imports
        assert not any(i.startswith(mod + ".") for i in imports)
    # AST: no Call to propose_atoms / invent discovery entrypoints
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                call_names.add(f.id)
            elif isinstance(f, ast.Attribute):
                call_names.add(f.attr)
    assert "propose_atoms" not in call_names
    assert "invent_atoms" not in call_names


def test_u_positive_control_gate_pass(batch, replay_batch):
    gate = replay_batch["u_positive_control_gate"]
    assert gate["status"] == "PASS"
    assert gate["n_pass"] == 7
    assert gate["n_seeds_expected"] == 7
    assert replay_batch["tooling_valid"] is True
    for row in gate["per_seed"]:
        assert row["pass"] is True
        assert row["checks"]["terminal_state_VERIFIED"] is True
        assert row["checks"]["strict_independence"] is True
        assert row["checks"]["firewall_epoch_ge_1"] is True
        assert row["checks"]["rotate_left_body_in_produced_census"] is True


def test_observed_vs_counterfactual_separation(replay_batch):
    for rep in replay_batch["replays"]:
        for row in rep["counterfactual_events"]:
            assert row["record_label"] == "counterfactual"
            assert row.get("discovery_feedback", False) is False
            assert row.get("sacred_credit", False) is False


def test_what_if_grow_cf_not_sacred(batch):
    ep = next(
        e
        for e in batch["episodes"]
        if e["condition_id"] == "BH-R1b" and e["target_role"] == "S" and e["seed"] == 0
    )
    assert any(is_odd_stride_atom(b) for b in ep["produced_bodies"])
    cf = what_if_grow(ep, parent_atom_body_key=ODD_STRIDE_ATOM)
    assert cf["record_label"] == "counterfactual"
    assert cf["sacred_credit"] is False
    assert cf["discovery_feedback"] is False
    assert cf["hypothesis_input"]["body_key"] == ODD_CAT_SELF
    assert cf["evaluator_result"]["would_accept"] is True
    assert "COUNTERFACTUAL" in cf["counterfactual_statement"]
    assert "not historical discovery" in cf["counterfactual_statement"]
    assert "live invent" in cf["not_simulated"]


def test_what_if_select_unknown_selection_noted(batch):
    ep = next(
        e
        for e in batch["episodes"]
        if e["condition_id"] == "BH-R1" and e["target_role"] == "U" and e["seed"] == 0
    )
    body = next(b for b in ep["produced_bodies"] if "SLICE:1,1" in b)
    cf = what_if_select(ep, body_key=body)
    assert cf["record_label"] == "counterfactual"
    assert cf["sacred_credit"] is False
    assert "UNKNOWN" in cf["evaluator_result"]["reason"] or "selection" in cf[
        "evaluator_result"
    ]["reason"].lower()


def test_stage2_files_unmutated_after_replay(batch, replay_batch):
    # Capture hashes before/after conceptually: compare to normalize-time sha
    for ep in batch["episodes"]:
        path = ROOT / ep["source_artifact_path"]
        assert path.is_file()
        now = sha256_file(path)
        assert now == ep["source_artifact_sha256"]
    # ensure no write under stage2 from our modules (hash stable)
    stage2 = ROOT / "reports/aivd_3_40_stage2/runs"
    assert len(list(stage2.glob("*.json"))) == 28


def test_no_evaluator_to_discovery_feedback_flag(replay_batch):
    for rep in replay_batch["replays"]:
        for row in rep["counterfactual_events"]:
            assert row.get("discovery_feedback") is False
