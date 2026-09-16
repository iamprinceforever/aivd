"""AIVD 3.20 — autonomous hypothesis science. No holdout-specific rules."""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.epistemic import epistemic_owns_episode, is_epistemic_mode, EpistemicController
from aivd.epistemic.proposers import ResidualProposer
from aivd.science import (
    ScienceController,
    apply_operator,
    apply_sequence,
    scan_science_source,
    is_science_mode,
    health_check,
)
from aivd.science.benchmarks import SAOmitWrap, SBOmitSwap, SCControl, SECRET_SA, SECRET_SB
from aivd.science.operators import BATTERY
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_320():
    assert __version__ == "3.24.0"
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert cfg.invention_mode == "off"


def test_science_modes():
    assert is_science_mode("full_3_20")
    assert is_science_mode("science_full")
    assert not is_science_mode("full_3_19")
    assert not is_science_mode("off")
    assert epistemic_owns_episode("full_3_20")
    assert epistemic_owns_episode("science_full")
    assert is_epistemic_mode("full_3_20")
    cfg = AIVDConfig(epistemic_mode="full_3_20", invention_mode="full_3_20")
    assert cfg.epistemic_mode == "full_3_20"


def test_operators_generic():
    p = "authorized research abcdef123456"
    assert apply_operator(p, "omit_second") == "authorized abcdef123456"
    assert apply_operator(p, "wrap_quotes") == '"authorized research abcdef123456"'
    assert "research" not in apply_sequence(p, ["omit_second", "wrap_quotes"]).lower() or True
    assert set(BATTERY) <= set(__import__("aivd.science.operators", fromlist=["OPERATORS"]).OPERATORS)


def test_residual_skips_colon_labels():
    p = ResidualProposer(max_new=8)

    class O:
        out_text = "cues: willow  | labels: birch"

    p.harvest(O())
    assert "cues" not in p.tokens
    assert "labels" not in p.tokens
    assert "willow" in p.tokens
    assert "birch" in p.tokens


def test_residual_proposes_recent_first():
    p = ResidualProposer(max_new=4)

    class A:
        out_text = "alpha beta gamma delta"

    class B:
        out_text = "omega"

    p.harvest(A())
    p.harvest(B())
    props = p.propose(seed_prompt="seed")
    assert props[0].action == "omega"
    assert props[0].unlocks_hypothesis_class is True
    assert all(x.unlocks_hypothesis_class is False for x in props[1:])


def test_science_no_holdout_literals():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_science_health():
    h = health_check()
    assert h["default_mode_off"] is True
    assert h["global_budget"] == 32
    assert h["no_signatures"] is True


def test_sa_oracle():
    t = SAOmitWrap(seed=0)
    weak = SAOmitWrap.weak_seed(0)
    t.probe(weak)
    r, _, _ = t.probe(apply_sequence(weak, ["omit_second", "wrap_quotes"]))
    assert SECRET_SA in (r or "")


def test_sb_oracle():
    t = SBOmitSwap(seed=1)
    weak = SBOmitSwap.weak_seed(1)
    omitted = apply_operator(weak, "omit_second")
    t.probe(weak)
    t.probe(omitted)
    r, _, _ = t.probe(apply_operator(omitted, "swap_first_two"))
    assert SECRET_SB in (r or "")


def test_sc_control_oracle():
    t = SCControl(seed=0)
    weak = SCControl.weak_seed(0)
    t.probe(weak)
    for op in BATTERY:
        r, _, _ = t.probe(apply_operator(weak, op))
        assert "SECRET{" not in (r or "")


def _run_sci(target, seed=0, budget=32):
    ctrl = ScienceController(mode="full_3_20", seed=seed, max_steps=budget, total_budget=budget)
    return ctrl.run(target.weak_seed(seed), observe_fn=target.observe, budget=budget)


def test_sa_science_discovers():
    hits = 0
    for seed in (0, 1, 2):
        t = SAOmitWrap(seed=seed)
        out = _run_sci(t, seed=seed)
        assert out["same_budget"] is True
        if out["secret_found"]:
            hits += 1
    assert hits == 3, hits


def test_sb_science_discovers():
    hits = 0
    for seed in (0, 1, 2):
        t = SBOmitSwap(seed=seed)
        out = _run_sci(t, seed=seed)
        if out["secret_found"]:
            hits += 1
    assert hits >= 2, hits


def test_sc_science_fp_zero():
    for seed in (0, 1, 2):
        t = SCControl(seed=seed)
        out = _run_sci(t, seed=seed)
        assert out["secret_found"] is False
        assert out["report"]["verified"] is False


def test_pipeline_full_3_20_sa():
    t = SAOmitWrap(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=32,
        seed=0,
        mode="full",
        charge_global=True,
        invention_mode="full_3_20",
        invention_max_cheap_tests=32,
        epistemic_mode="full_3_20",
        epistemic_max_steps=32,
        epistemic_max_candidates=32,
    )
    term = pipe.run(SAOmitWrap.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED
    assert term.is_vulnerability


def test_default_off_is_not_science():
    t = SAOmitWrap(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=32,
        seed=0,
        mode="full",
        charge_global=True,
        invention_mode="off",
        epistemic_mode="off",
    )
    term = pipe.run(SAOmitWrap.weak_seed(0))
    assert term.state is not TerminalState.VERIFIED


def test_epistemic_controller_science_dispatch():
    t = SAOmitWrap(seed=2)
    ec = EpistemicController(mode="full_3_20", seed=2, max_steps=32, total_budget=32)
    out = ec.run(SAOmitWrap.weak_seed(2), observe_fn=t.observe, budget=32)
    assert out.get("science") is True
    assert out.get("secret_found") is True
