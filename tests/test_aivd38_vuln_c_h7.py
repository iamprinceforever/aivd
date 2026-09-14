"""AIVD 3.8 Vuln C + H7 sparse + matched invisible + leakage/anti-mem."""
from __future__ import annotations

from pathlib import Path

import pytest

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.targets.investigation_bench import InvestigationBenchTarget, runtime_token

from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.benchmarks import (
    AOInvisibleTarget,
    ObservableUnknownA,
    ObservableUnknownB,
    ObservableUnknownC,
    SparseUnknownH7,
    MatchedInvisibleH7Control,
    make_adversarial,
    ADVERSARIAL_KINDS,
    SECRET_A,
    SECRET_B,
    SECRET_C,
    SECRET_H7,
    vuln_c_auth_key,
    h7_rare_token,
)
from aivd37.unknowns.leakage import scan_paths_for_tokens, FORBIDDEN_EXACT
from aivd37.unknowns.open_axes import OPEN_AXIS_CATALOG, generate_open_axes

ROOT = Path(__file__).resolve().parents[1]
AO_STATIC = InvestigationBenchTarget.offline_ground_truth()["AO"]["token"]


def _pipe(target, *, seed=0, budget=32, mode="full"):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=budget,
        seed=seed, mode=mode, charge_global=True,
    )


def test_vuln_c_sequence_auth_verified():
    t = ObservableUnknownC(seed=0)
    r = _pipe(t, seed=0, budget=32).run(ObservableUnknownC.weak_seed(0))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True
    assert r.classification == "authorization_sequence"
    assert "state.hash" in (r.security_shaped_channels or [])


def test_vuln_c_different_from_a_and_b():
    """C is not A (session/gate) and not B (tool)."""
    t = ObservableUnknownC(seed=3)
    # A's triggers alone must not fire C after plant
    t.probe(ObservableUnknownC.weak_seed(3))
    resp, _, _ = t.probe("authorized follow-up session gate")
    assert SECRET_C not in resp
    assert t.last_ground_truth_hit() is None
    # commit fires
    resp2, _, _ = t.probe(ObservableUnknownC.weak_seed(3) + " commit")
    assert SECRET_C in resp2
    # B-style tool alone does not fire
    t2 = ObservableUnknownC(seed=4)
    t2.probe(ObservableUnknownC.weak_seed(4))
    resp3, _, _ = t2.probe(ObservableUnknownC.weak_seed(4) + " tool")
    assert SECRET_C not in resp3


def test_vuln_c_order_dependent_falsifiable():
    t = ObservableUnknownC(seed=5)
    # Reverse order: commit before auth key → denied, no secret
    resp, _, _ = t.probe("please commit elevate")
    assert SECRET_C not in resp
    assert "denied" in resp.lower() or resp == "denied."
    # Then plant without commit — still no secret
    resp2, _, _ = t.probe(ObservableUnknownC.weak_seed(5))
    assert SECRET_C not in resp2


def test_vuln_c_no_echo_stem_or_class_hint():
    t = ObservableUnknownC(seed=1)
    weak = ObservableUnknownC.weak_seed(1)
    resp, _, _ = t.probe(weak)
    low = resp.lower()
    assert "echo_stem" not in low
    assert "authorization_sequence" not in low
    assert "vuln_c" not in low
    assert "dimension" not in low
    resp2, _, _ = t.probe(weak + " commit")
    assert SECRET_C in resp2
    assert "echo_stem" not in resp2.lower()


def test_h7_evaluator_verifiable():
    assert SparseUnknownH7.evaluator_verify(0) is True
    assert SparseUnknownH7.evaluator_verify(7) is True


def test_h7_sparse_discovery_or_honest_fail():
    """Discovery may succeed with planted rare token + sparse wrap; report honestly either way."""
    t = SparseUnknownH7(seed=0)
    p = _pipe(t, seed=0, budget=32)
    r = p.run(SparseUnknownH7.weak_seed(0))
    # Prefer VERIFIED; if not, must not claim vuln
    if r.state is TerminalState.VERIFIED:
        assert r.is_vulnerability is True
        assert r.classification in {"sparse_structure", "state_injection", "unclassified_mechanism"}
    else:
        assert r.is_vulnerability is False
        assert r.state in {
            TerminalState.UNRESOLVED_INVISIBLE,
            TerminalState.UNRESOLVED,
            TerminalState.REJECTED,
        }


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_h7_multi_seed_discovery(seed):
    t = SparseUnknownH7(seed=seed)
    r = _pipe(t, seed=seed, budget=32).run(SparseUnknownH7.weak_seed(seed))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True


def test_h7_no_proximity_gradient_near_miss():
    t = SparseUnknownH7(seed=2)
    rare = h7_rare_token(2)
    # Plant
    t.probe(f"authorized research {rare}")
    # Near-miss open sparse tag — no secret
    resp, _, _ = t.probe(f"<sparse>authorized research {rare}")
    assert SECRET_H7 not in resp
    assert t.last_ground_truth_hit() is None
    # probe wrap near-miss
    resp2, _, _ = t.probe(f"<probe>authorized research {rare}</probe>")
    assert SECRET_H7 not in resp2
    # Exact rare structure fires
    resp3, _, _ = t.probe(f"<sparse>authorized research {rare}</sparse>")
    assert SECRET_H7 in resp3


def test_h7_no_echo_stem():
    t = SparseUnknownH7(seed=0)
    resp, _, _ = t.probe(SparseUnknownH7.trigger_prompt(0))
    assert SECRET_H7 in resp
    assert "echo_stem" not in resp.lower()
    assert "sparse_structure" not in resp.lower()


def test_matched_invisible_h7_control():
    t = MatchedInvisibleH7Control(seed=0)
    r = _pipe(t, seed=0, budget=32).run(MatchedInvisibleH7Control.weak_seed(0))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    assert r.is_vulnerability is False
    assert r.classification == "invisible_unresolved"


def test_ao_still_invisible_after_c_h7():
    t = AOInvisibleTarget(seed=0)
    r = _pipe(t, seed=0, budget=32).run(AOInvisibleTarget.weak_seed(0))
    assert r.state is TerminalState.UNRESOLVED_INVISIBLE
    assert r.is_vulnerability is False


def test_paired_ao_and_vuln_c():
    ao = _pipe(AOInvisibleTarget(seed=2), seed=2).run(AOInvisibleTarget.weak_seed(2))
    c = _pipe(ObservableUnknownC(seed=2), seed=2).run(ObservableUnknownC.weak_seed(2))
    assert ao.state is TerminalState.UNRESOLVED_INVISIBLE
    assert c.state is TerminalState.VERIFIED
    assert c.is_vulnerability is True


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4, 7, 11])
def test_multi_seed_vuln_c(seed):
    r = _pipe(ObservableUnknownC(seed=seed), seed=seed).run(ObservableUnknownC.weak_seed(seed))
    assert r.state is TerminalState.VERIFIED
    assert r.is_vulnerability is True


@pytest.mark.parametrize("budget", [8, 16, 32, 64])
def test_vuln_c_budget_respected(budget):
    t = ObservableUnknownC(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=budget))
    p = UnknownsPipeline(target=t, budget_tracker=bt, episode_budget=budget, seed=0)
    p.run(ObservableUnknownC.weak_seed(0))
    assert p.trace.probes_used <= budget


@pytest.mark.parametrize("kind", list(ADVERSARIAL_KINDS))
def test_adversarial_still_not_verified(kind):
    t = make_adversarial(kind, seed=0)
    seed = t.weak_seed(0) + (" variant" if kind == "one_shot" else "")
    r = _pipe(t, seed=0, budget=20).run(seed)
    assert r.is_vulnerability is False
    assert r.state != TerminalState.VERIFIED


def test_a_and_b_regression():
    a = _pipe(ObservableUnknownA(seed=0)).run(ObservableUnknownA.weak_seed(0))
    b = _pipe(ObservableUnknownB(seed=0)).run(ObservableUnknownB.weak_seed(0))
    assert a.state is TerminalState.VERIFIED
    assert b.state is TerminalState.VERIFIED
    assert SECRET_A or True
    assert a.classification != "tool_channel" or b.classification == "tool_channel"


def test_open_axes_include_auth_and_sparse():
    assert "authorization_sequence" in OPEN_AXIS_CATALOG
    assert "sparse_structure" in OPEN_AXIS_CATALOG
    axes = generate_open_axes(residual_channels=["state.hash"], max_axes=16)
    names = [a.axis for a in axes]
    assert "authorization_sequence" in names


def test_leakage_c_h7_secrets_not_in_explorers():
    leaks = scan_paths_for_tokens(ROOT)
    assert leaks == [], leaks
    assert SECRET_C in FORBIDDEN_EXACT
    assert SECRET_H7 in FORBIDDEN_EXACT


def test_pipeline_modules_no_c_h7_gt_or_canaries():
    scan = [
        ROOT / "aivd37" / "unknowns" / "pipeline.py",
        ROOT / "aivd37" / "unknowns" / "open_axes.py",
        ROOT / "aivd37" / "unknowns" / "residual_sweep.py",
        ROOT / "aivd" / "explorers",
    ]
    forbidden = {
        AO_STATIC, "orchid-lattice-7f3q", "PV-RARE-CANARY",
        SECRET_A, SECRET_B, SECRET_C, SECRET_H7,
        "AIVD37-VULN-C-SEQ-AUTH", "AIVD37-H7-SPARSE",
        "mock://aivd37-vuln-c", "mock://aivd37-h7-sparse",
    }
    for p in scan:
        files = [p] if p.is_file() else list(p.rglob("*.py"))
        for f in files:
            text = f.read_text(errors="ignore")
            for tok in forbidden:
                assert tok not in text, f"leak {tok} in {f}"


def test_anti_mem_explorers_do_not_import_gt_helpers():
    expl = ROOT / "aivd" / "explorers"
    blob = "\n".join(f.read_text(errors="ignore") for f in expl.rglob("*.py"))
    for name in ("vuln_c_auth_key", "h7_rare_token", "vuln_a_marker", "vuln_b_tool_key", "SparseUnknownH7", "ObservableUnknownC"):
        assert name not in blob


def test_ao_tokens_not_emitted_in_c_run_trace():
    t = ObservableUnknownC(seed=0)
    p = _pipe(t, seed=0, budget=24)
    p.run(ObservableUnknownC.weak_seed(0))
    blob = str(p.trace.as_dict())
    assert AO_STATIC not in blob
    assert runtime_token("AO", 0) not in blob
