"""AIVD 3.9 Open Intervention Invention — unit, leakage, anti-mem, controls."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.invention import (
    InventionController,
    generate_candidates,
    rank_candidates,
    scan_invention_source,
)
from aivd.invention.intervention_space import (
    morph_forms,
    compound_forms,
    extract_residual_tokens,
    ACTION_STEMS,
)
from aivd.invention.scoring import score_intervention
from aivd.invention.intervention_space import Intervention, InterventionOp
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout import HoldoutX, SECRET_HOLDOUT_X, HOLDOUT_GT_ID
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
)
from aivd37.unknowns.leakage import scan_paths_for_tokens, FORBIDDEN_EXACT

ROOT = Path(__file__).resolve().parents[1]


def _pipe(target, *, seed=0, budget=32, mode="full", invention_mode="off"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
        invention_mode=invention_mode,
        invention_max_candidates=32,
        invention_max_cheap_tests=12,
    )


def test_config_invention_mode_default_off():
    cfg = AIVDConfig()
    assert cfg.invention_mode == "off"


def test_morph_forms_derive_ance_suffix():
    forms = morph_forms("clear")
    assert "clear" + "ance" in forms


def test_compound_forms_hyphen():
    forms = compound_forms("ack", "bound")
    assert "ack" + "-" + "bound" in forms


def test_extract_residual_tokens_from_error():
    toks = extract_residual_tokens({"error": "bound.trip", "security_shaped_residuals": ["error"]})
    assert "bound" in toks
    assert "trip" in toks


def test_generate_candidates_off_empty():
    assert generate_candidates(mode="off", seed=0, budget=16) == []


def test_generate_candidates_random_no_residual_compounds_required():
    cands = generate_candidates(mode="random", seed=0, budget=8)
    assert len(cands) >= 4
    assert all(c.strategy == "random" for c in cands)


def test_novelty_alone_not_scored_without_ig():
    inv = Intervention(
        ops=[InterventionOp(kind="insert", token="zzzunique")],
        sequence=["zzzunique"],
        novelty=1.0,
        strategy="novelty",
    )
    s = score_intervention(inv, residual_context={})  # no residual / eig
    # novelty gated off → score should not be high from novelty alone
    assert inv.novelty >= 0.0
    assert s < 0.5


def test_rank_prefers_residual_compounds_under_error():
    ctx = {
        "error": "bound.trip",
        "error_text": "bound.trip",
        "security_shaped_residuals": ["error"],
        "unexplained": 1.0,
    }
    cands = generate_candidates(mode="full", seed=0, residual_context=ctx, budget=32)
    ranked = rank_candidates(cands, residual_context=ctx, top_k=12)
    seqs = [" ".join(c.sequence) for c in ranked]
    assert any(s == "ack-bound" or s.replace("_", "-") == "ack-bound" or s == "ackbound" for s in seqs), seqs


def test_invention_controller_off_skips():
    ic = InventionController(mode="off", seed=0)
    r = ic.run("authorized research", observe_fn=lambda p: type("O", (), {"out_text": "ok", "error": None})())
    assert r["enabled"] is False


def test_leakage_scan_invention_source_clean():
    leaks = scan_invention_source(ROOT)
    assert leaks == [], leaks


def test_holdout_x_names_not_importable_as_solutions_from_invention():
    """X/Y names must not be importable as solution helpers from invention package."""
    import aivd.invention as inv
    assert not hasattr(inv, "HoldoutX")
    assert not hasattr(inv, "HoldoutY")
    assert not hasattr(inv, "holdout_x_bound_key")
    assert not hasattr(inv, "SECRET_HOLDOUT_X")
    blob = "\n".join(
        f.read_text(errors="ignore")
        for f in (ROOT / "aivd" / "invention").rglob("*.py")
        if f.name != "audit.py"
    )
    assert "HoldoutX" not in blob
    assert "HoldoutY" not in blob
    assert SECRET_HOLDOUT_X not in blob
    assert HOLDOUT_GT_ID not in blob


def test_anti_mem_explorers_still_clean():
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks
    assert SECRET_HOLDOUT_X in FORBIDDEN_EXACT


def test_invention_off_holdout_x_not_discovered():
    """Control: invention OFF preserves 3.8 NOT_DISCOVERED behavior."""
    r = _pipe(HoldoutX(seed=0), invention_mode="off").run(HoldoutX.weak_seed(0))
    assert r.is_vulnerability is False
    assert r.state is not TerminalState.VERIFIED


def test_invention_full_can_recover_holdout_x_under_stated_conditions():
    """Replay with invention ON — recovered under residual+morph/compound, NOT open-world claim."""
    r = _pipe(HoldoutX(seed=0), invention_mode="full").run(HoldoutX.weak_seed(0))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True


def test_ao_still_invisible_with_invention_full():
    r = _pipe(AOInvisibleTarget(seed=0), invention_mode="full").run(AOInvisibleTarget.weak_seed(0))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    assert r.is_vulnerability is False


def test_regression_a_b_c_h7_with_invention_off():
    assert _pipe(ObservableUnknownA(0)).run(ObservableUnknownA.weak_seed(0)).is_vulnerability
    assert _pipe(ObservableUnknownB(0)).run(ObservableUnknownB.weak_seed(0)).is_vulnerability
    assert _pipe(ObservableUnknownC(0)).run(ObservableUnknownC.weak_seed(0)).is_vulnerability
    assert _pipe(SparseUnknownH7(0)).run(SparseUnknownH7.weak_seed(0)).is_vulnerability


def test_action_stems_do_not_contain_holdout_triggers():
    joined = " ".join(ACTION_STEMS)
    assert "ack-bound" not in joined
    assert "clearance" not in joined


def test_version_3_9_0():
    import aivd
    assert aivd.__version__ == "3.9.0"
