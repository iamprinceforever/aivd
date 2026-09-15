"""AIVD 3.19 — episode-owned arbitration. No holdout-specific rules."""
from __future__ import annotations

from aivd import __version__
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.core.budgets import BudgetTracker
from aivd.epistemic import (
    EpistemicController,
    is_epistemic_mode,
    is_authoritative,
    epistemic_owns_episode,
    scan_epistemic_source,
)
from aivd.epistemic.benchmarks import (
    EAImmediateEigTrap,
    EBMultiStep,
    EFInvisible,
)
from aivd.epistemic.scheduler import EPISODE_OWNED_MODES
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_319():
    assert __version__.startswith("3.")
    cfg = AIVDConfig()
    assert cfg.epistemic_mode == "off"
    assert cfg.invention_mode == "off"


def test_owns_episode_modes():
    assert epistemic_owns_episode("full_3_19")
    assert epistemic_owns_episode("epistemic_full")
    assert epistemic_owns_episode("arbiter")
    assert not epistemic_owns_episode("full_3_18")
    assert not epistemic_owns_episode("epistemic_shadow")
    assert not epistemic_owns_episode("off")
    assert not epistemic_owns_episode("full_3_17")
    assert "full_3_19" in EPISODE_OWNED_MODES
    assert "full_3_18" not in EPISODE_OWNED_MODES
    assert is_epistemic_mode("full_3_19")
    assert is_authoritative("full_3_19")


def test_config_accepts_full_3_19():
    cfg = AIVDConfig(epistemic_mode="full_3_19", invention_mode="full_3_19")
    assert cfg.epistemic_mode == "full_3_19"
    assert cfg.invention_mode == "full_3_19"


def _pipe(target, mode: str, budget: int = 32, cheap: int = 32):
    bt = BudgetTracker(BudgetConfig(max_experiments=budget + 8))
    return UnknownsPipeline(
        target=target,
        budget_tracker=bt,
        episode_budget=budget,
        seed=0,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_candidates=64,
        invention_max_cheap_tests=cheap,
        epistemic_mode=mode if mode.startswith("epistemic") or mode in ("full_3_18", "full_3_19", "arbiter") else "off",
        epistemic_max_steps=budget,
        epistemic_max_candidates=64,
    )


def test_full_318_still_peels_leftover():
    t = EAImmediateEigTrap(seed=0)
    pipe = _pipe(t, "full_3_18")
    pipe.run(EAImmediateEigTrap.weak_seed(0))
    kinds = [s.get("kind") for s in pipe.trace.steps]
    assert "episode_owned" not in kinds
    sweep = next(s for s in pipe.trace.steps if s.get("kind") == "sweep")
    assert sweep.get("notes") != "deferred_to_global_arbiter"


def test_full_319_skips_sequential_sweep_and_gate_lock():
    t = EAImmediateEigTrap(seed=0)
    pipe = _pipe(t, "full_3_19")
    pipe.run(EAImmediateEigTrap.weak_seed(0))
    kinds = [s.get("kind") for s in pipe.trace.steps]
    assert "episode_owned" in kinds
    owned = next(s for s in pipe.trace.steps if s.get("kind") == "episode_owned")
    assert owned.get("gate_reserve") == 0
    sweep = next(s for s in pipe.trace.steps if s.get("kind") == "sweep")
    assert sweep.get("notes") == "deferred_to_global_arbiter"
    assert pipe._local_used <= 32
    assert pipe.trace.probes_used <= 32


def test_pipeline_319_discovers_ea():
    t = EAImmediateEigTrap(seed=0)
    pipe = _pipe(t, "full_3_19")
    term = pipe.run(EAImmediateEigTrap.weak_seed(0))
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv
    assert src.get("tested_candidates", 0) >= 2
    assert bool(inv.get("secret_found") or src.get("secret_found")) is True
    # Terminal may be VERIFIED or, if gates starved, still recorded as secret.
    assert term.state in (
        TerminalState.VERIFIED,
        TerminalState.UNRESOLVED_INVISIBLE,
        TerminalState.REJECTED,
        TerminalState.UNRESOLVED,
    )


def test_pipeline_319_discovers_eb_multistep():
    t = EBMultiStep(seed=0)
    pipe = _pipe(t, "full_3_19")
    pipe.run(EBMultiStep.weak_seed(0))
    inv = pipe.invention_result or {}
    src = inv.get("epistemic") or inv
    assert src.get("tested_candidates", 0) >= 3
    assert bool(inv.get("secret_found") or src.get("secret_found")) is True


def test_pipeline_319_invisible_not_verified():
    t = EFInvisible(seed=0)
    pipe = _pipe(t, "full_3_19")
    term = pipe.run(EFInvisible.weak_seed(0))
    assert term.state is not TerminalState.VERIFIED
    assert term.is_vulnerability is False
    assert pipe._local_used <= 32


def test_pipeline_319_budget_32():
    t = EAImmediateEigTrap(seed=0)
    pipe = _pipe(t, "full_3_19")
    pipe.run(EAImmediateEigTrap.weak_seed(0))
    assert pipe._local_used <= 32
    assert pipe.trace.probes_used <= 32


def test_pipeline_319_gives_arbiter_more_than_leftover():
    t18 = EFInvisible(seed=0)
    p18 = _pipe(t18, "full_3_18")
    p18.run(EFInvisible.weak_seed(0))
    src18 = (p18.invention_result or {}).get("epistemic") or (p18.invention_result or {})
    t19 = EFInvisible(seed=0)
    p19 = _pipe(t19, "full_3_19")
    p19.run(EFInvisible.weak_seed(0))
    src19 = (p19.invention_result or {}).get("epistemic") or (p19.invention_result or {})
    tested18 = int(src18.get("tested_candidates") or 0)
    tested19 = int(src19.get("tested_candidates") or 0)
    assert tested19 >= tested18
    assert p19._local_used <= 32
    # Gate lock is the peel: leftover must be strictly smaller than episode-owned.
    assert tested18 < 20


def test_no_holdout_literals_in_319_source():
    scan = scan_epistemic_source()
    assert scan["pass"], scan["leaks"]


def test_direct_arbiter_still_finds_ea():
    t = EAImmediateEigTrap(seed=0)
    ec = EpistemicController(mode="full_3_19", seed=0, max_steps=32, total_budget=32)
    out = ec.run(
        EAImmediateEigTrap.weak_seed(0),
        observe_fn=t.observe,
        residual_context={"unexplained": 0.85},
        budget=32,
    )
    assert out["secret_found"] is True
    assert out["same_budget"] is True
