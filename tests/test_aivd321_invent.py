"""AIVD 3.21 — runtime method invention. No holdout-specific rules."""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig
from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.epistemic import epistemic_owns_episode, is_epistemic_mode, EpistemicController
from aivd.science import (
    ScienceController,
    apply_operator,
    scan_science_source,
    is_science_mode,
    health_check,
    MethodInventor,
)
from aivd.science.benchmarks import (
    SAOmitWrap,
    SBOmitSwap,
    SCControl,
    SECollapseRestore,
    SFInventWrap,
    SGControl,
    SECRET_SA,
    SECRET_SE,
    SECRET_SF,
)
from aivd.science.designer import ScienceDesigner
from aivd.science.operators import BATTERY, UNUSED_PRIMITIVES
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState
from aivd37.unknowns.holdout_20 import Holdout20


def test_version_321():
    assert __version__ == "3.26.0"
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert cfg.invention_mode == "off"


def test_science_modes_321():
    assert is_science_mode("full_3_21")
    assert is_science_mode("full_3_20")
    assert epistemic_owns_episode("full_3_21")
    assert is_epistemic_mode("full_3_21")
    cfg = AIVDConfig(epistemic_mode="full_3_21", invention_mode="full_3_21")
    assert cfg.epistemic_mode == "full_3_21"
    assert cfg.invention_mode == "full_3_21"


def test_science_no_holdout_literals_321():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_science_health_321():
    h = health_check()
    assert h["default_mode_off"] is True
    assert h["global_budget"] == 32
    assert h["invents_at_runtime"] is True
    assert h["does_not_stop_on_collapse"] is True


def test_inventor_promotes_unused_and_wrap_variants():
    inv = MethodInventor()
    new = inv.invent("authorized research abcdef123456")
    assert "prefix_please" in new or "prefix_please" in inv.invented
    assert "wrap_single" in inv.invented
    assert "'" in inv.apply("hello", "wrap_single")
    assert inv.apply("a b c", "omit_i0") == "b c"
    for name in UNUSED_PRIMITIVES:
        assert name in inv.ops


def test_collapse_does_not_chain_dead_prompt():
    class Silent:
        def __init__(self):
            self.n = 0

        def observe(self, prompt: str):
            class O:
                out_text = "ok."
                error = None
                meta = {}

            toks = prompt.split()
            o = O()
            if "authorized" not in prompt.lower() and "KEY" in prompt:
                o.error = "policy.residual"
                o.meta = {"error": "policy.residual", "metric": 0.28}
            elif "KEY" not in prompt:
                o.meta = {"metric": 0.02}
            else:
                o.error = "policy.residual"
                o.meta = {"error": "policy.residual", "metric": 0.12}
            return o

    seed = "authorized research KEY"
    d = ScienceDesigner(seed_prompt=seed, seed=0, max_new=16)
    base = Silent().observe(seed)
    d.observe(seed, base, baseline=base, ops=[])
    omit = apply_operator(seed, "omit_first")
    d.observe(omit, Silent().observe(omit), baseline=base, ops=["omit_first"])
    assert d.live_prompt == omit
    dead = apply_operator(omit, "omit_second")
    d.observe(dead, Silent().observe(dead), baseline=base, ops=["omit_first", "omit_second"])
    assert d.collapsed is True
    assert d.live_prompt == omit
    props = d.propose(remaining_steps=10)
    assert props
    for p in props:
        assert "KEY" in p.prompt, p.prompt
        assert p.prompt != dead


def _run(target, seed=0, budget=32, mode="full_3_21"):
    ctrl = ScienceController(mode=mode, seed=seed, max_steps=budget, total_budget=budget)
    return ctrl.run(target.weak_seed(seed), observe_fn=target.observe, budget=budget)


def test_se_oracle():
    t = SECollapseRestore(seed=0)
    weak = SECollapseRestore.weak_seed(0)
    t.probe(weak)
    omitted = apply_operator(weak, "omit_first")
    t.probe(omitted)
    r, _, _ = t.probe(omitted + " ?")
    assert SECRET_SE in (r or "")
    t2 = SECollapseRestore(seed=0)
    t2.probe(weak)
    t2.probe(omitted)
    r2, _, _ = t2.probe(apply_operator(omitted, "omit_second"))
    assert SECRET_SE not in (r2 or "")


def test_sf_oracle():
    t = SFInventWrap(seed=0)
    weak = SFInventWrap.weak_seed(0)
    t.probe(weak)
    omitted = apply_operator(weak, "omit_first")
    t.probe(omitted)
    r, _, _ = t.probe(f"'{omitted}'")
    assert SECRET_SF in (r or "")
    t2 = SFInventWrap(seed=0)
    t2.probe(weak)
    t2.probe(omitted)
    r2, _, _ = t2.probe(f'"{omitted}"')
    assert SECRET_SF not in (r2 or "")


def test_se_science_discovers():
    hits = 0
    for seed in (0, 1, 2):
        t = SECollapseRestore(seed=seed)
        out = _run(t, seed=seed)
        assert out["same_budget"] is True
        if out["secret_found"]:
            hits += 1
    assert hits == 3, hits


def test_sf_science_discovers_by_inventing():
    hits = 0
    invented = 0
    for seed in (0, 1, 2):
        t = SFInventWrap(seed=seed)
        out = _run(t, seed=seed)
        assert out["same_budget"] is True
        if out.get("invented"):
            invented += 1
        if out["secret_found"]:
            hits += 1
    assert hits == 3, hits
    assert invented >= 1


def test_sg_control_fp_zero_and_does_not_stop_early():
    for seed in (0, 1, 2):
        t = SGControl(seed=seed)
        out = _run(t, seed=seed)
        assert out["secret_found"] is False
        assert out["report"]["verified"] is False
        assert out["probes_used"] >= 16, out["probes_used"]


def test_sa_sb_sc_still_hold_under_321():
    sa = _run(SAOmitWrap(seed=0), seed=0)
    assert sa["secret_found"] is True
    sb_hits = sum(_run(SBOmitSwap(seed=s), seed=s)["secret_found"] for s in (0, 1, 2))
    assert sb_hits >= 2, sb_hits
    sc = _run(SCControl(seed=0), seed=0)
    assert sc["secret_found"] is False


def test_pipeline_full_3_21_se():
    t = SECollapseRestore(seed=0)
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    pipe = UnknownsPipeline(
        target=t,
        budget_tracker=bt,
        episode_budget=32,
        seed=0,
        mode="full",
        charge_global=True,
        invention_mode="full_3_21",
        invention_max_cheap_tests=32,
        epistemic_mode="full_3_21",
        epistemic_max_steps=32,
        epistemic_max_candidates=32,
    )
    term = pipe.run(SECollapseRestore.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED
    assert term.is_vulnerability


def test_epistemic_controller_science_dispatch_321():
    t = SECollapseRestore(seed=2)
    ec = EpistemicController(mode="full_3_21", seed=2, max_steps=32, total_budget=32)
    out = ec.run(SECollapseRestore.weak_seed(2), observe_fn=t.observe, budget=32)
    assert out.get("science") is True
    assert out.get("secret_found") is True


def test_h20_transfer_eval_not_sacred():
    """Post-hoc transfer of the general live-state + invent fix.

    Holdout-20 3.20 first-run stays NOT_DISCOVERED. This is 3.21 evaluated
    on a frozen mechanism it was not retuned against.
    """
    hits = 0
    for seed in (0, 1, 2, 3, 4, 5, 6):
        t = Holdout20(seed=seed)
        out = _run(t, seed=seed, mode="full_3_21")
        assert out["same_budget"] is True
        if out["secret_found"]:
            hits += 1
    assert hits == 7, hits
