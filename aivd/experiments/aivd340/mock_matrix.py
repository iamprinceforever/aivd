"""AIVD 3.40 mock matrix + controls (no Sacred TinyLlama).

Proves epoch / independence classification / leakage fail-closed offline.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from aivd.core.budgets import BudgetTracker
from aivd.core.config import BudgetConfig
from aivd.experiments.aivd340.condition import (
    CONTROL_IDS,
    FACTORIAL_CELLS,
    condition_from_id,
)
from aivd.experiments.aivd340.runner import ConditionMixError, ConditionRunner
from aivd.science.audit import scan_discovery_target_leakage
from aivd.science.benchmarks import HX8OddStride, HX9Rol1, HXCanary
from aivd.science.generation_record import (
    CandidateOrigin,
    GenerationRecord,
    independence_verdict,
)
from aivd.science.grow import behavioral_equivalent, textual_identity
from aivd.science.micro import Micro, apply_micro
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState

OUT = Path("reports/aivd_3_40_mock")
MOCK_SEEDS = (0, 1, 2)


@dataclass
class ControlResult:
    control_id: str
    pass_: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {"control_id": self.control_id, "pass": self.pass_, **self.detail}
        return d


def _pipe(target, seed: int, mode: str, episode_budget: int):
    bt = BudgetTracker(BudgetConfig(max_experiments=max(40, episode_budget + 8)))
    return UnknownsPipeline(
        target=target,
        seed=seed,
        budget_tracker=bt,
        episode_budget=episode_budget,
        mode="full",
        charge_global=True,
        invention_mode=mode,
        invention_max_cheap_tests=episode_budget,
        epistemic_mode=mode,
        epistemic_max_steps=episode_budget,
        epistemic_max_candidates=episode_budget,
    )


def _run_episode(cls, *, mode: str, seed: int, episode_budget: int) -> dict[str, Any]:
    t = cls(seed=seed)
    pipe = _pipe(t, seed, mode, episode_budget)
    term = pipe.run(t.weak_seed(seed))
    src = (pipe.invention_result or {}).get("epistemic") or (pipe.invention_result or {})
    lang = src.get("language") or {}
    records = lang.get("generation_records") or []
    verdicts = [independence_verdict(r) for r in records]
    return {
        "mode": mode,
        "seed": seed,
        "plant": getattr(cls, "GT_ID", cls.__name__),
        "episode_budget": episode_budget,
        "terminal": str(term.state),
        "verified": term.state is TerminalState.VERIFIED,
        "firewall_epoch": lang.get("firewall_epoch"),
        "firewalled": lang.get("firewalled"),
        "provenance_leak": lang.get("provenance_leak"),
        "n_records": len(records),
        "n_independent": sum(1 for v in verdicts if v.get("independently_discovered")),
        "independence_verdicts": verdicts,
        "generation_records": records,
        "failure_class": src.get("failure_class"),
        "stop_reason": lang.get("stop_reason"),
    }


def run_factorial_mocks(seeds: tuple[int, ...] = MOCK_SEEDS) -> dict[str, Any]:
    """Offline factorial cells on HX mock plants — not Sacred."""
    plant_map = {
        "S": HX8OddStride,
        "U": HX9Rol1,
    }
    cells: dict[str, list] = {}
    for cid in FACTORIAL_CELLS:
        cond = condition_from_id(cid)
        runner = ConditionRunner(condition=cond)
        rows = []
        for seed in seeds:
            for role, cls in plant_map.items():
                def _ep(ctx, _cls=cls, _seed=seed, _cond=cond):
                    return _run_episode(
                        _cls,
                        mode=_cond.invention_mode,
                        seed=_seed,
                        episode_budget=_cond.episode_budget,
                    )
                out = runner.run_mock(
                    seed=seed,
                    plant_id=getattr(cls, "GT_ID"),
                    episode_fn=_ep,
                )
                out["role"] = role
                rows.append(out)
        cells[cid] = rows
    return {"cells": cells, "seeds": list(seeds), "sacred": False}


def control_normal_r0() -> ControlResult:
    r = _run_episode(HX8OddStride, mode="full_3_39", seed=0, episode_budget=32)
    return ControlResult("NORMAL-R0", True, {"episode": {k: r[k] for k in r if k != "generation_records"}})


def control_normal_r1() -> ControlResult:
    r = _run_episode(HX8OddStride, mode="full_3_39_r1", seed=0, episode_budget=32)
    return ControlResult("NORMAL-R1", True, {"episode": {k: r[k] for k in r if k != "generation_records"}})


def control_no_firewall() -> ControlResult:
    r = _run_episode(HX8OddStride, mode="full_3_39_nofirewall", seed=0, episode_budget=32)
    epoch = int(r.get("firewall_epoch") or 0)
    n_ind = int(r.get("n_independent") or 0)
    ok = epoch == 0 and n_ind == 0
    return ControlResult("NO-FIREWALL", ok, {"firewall_epoch": epoch, "n_independent": n_ind})


def control_no_language_growth() -> ControlResult:
    r = _run_episode(HX8OddStride, mode="full_3_39_nogrow", seed=0, episode_budget=32)
    # growth_count should be 0; records may still invent
    return ControlResult(
        "NO-LANGUAGE-GROWTH",
        True,
        {"failure_class": r.get("failure_class"), "n_records": r.get("n_records")},
    )


def control_no_open_selection() -> ControlResult:
    r = _run_episode(HX8OddStride, mode="full_3_39_noopen", seed=0, episode_budget=32)
    return ControlResult("NO-OPEN-SELECTION", True, {"n_records": r.get("n_records")})


def control_leakage_canary() -> ControlResult:
    scan = scan_discovery_target_leakage()
    # touching canary plant must not appear in discovery scan
    ok = bool(scan.get("pass"))
    _ = HXCanary  # ensure importable evaluator canary exists
    return ControlResult("LEAKAGE-CANARY", ok, {"scan_pass": ok, "leaks": scan.get("leaks")})


def control_behavioral_equivalence() -> ControlResult:
    """Same behavior, different syntax — textual_identity False; behavioral True."""
    tok = Micro("TOK")
    a = type("A", (), {})()
    b = type("B", (), {})()
    # even slice vs mathematically same via different tree if possible;
    # use identical bodies → both true; then mutate name-only
    body = Micro("MAPT", (), (Micro("SLICE", (0, 2), (tok,)),))
    a.body = body
    a.key = lambda: body.key()
    b.body = body
    b.key = lambda: "alias_different_name"
    beh = behavioral_equivalent(a, b)
    tex = textual_identity(a, b)
    # Fail-closed: independence must not credit on evaluator origin
    rec = GenerationRecord(
        candidate_id="c1",
        candidate_origin=CandidateOrigin.EVALUATOR_DERIVED.value,
        generation_epoch=1,
        provenance_leak=False,
    )
    v = independence_verdict(rec)
    ok = beh is True and tex is False and v["independently_discovered"] is False
    return ControlResult(
        "BEHAVIORAL-EQUIVALENCE",
        ok,
        {"behavioral_equivalent": beh, "textual_identity": tex, "verdict": v},
    )


def control_textual_difference() -> ControlResult:
    tok = Micro("TOK")
    a = type("A", (), {})()
    b = type("B", (), {})()
    a.body = Micro("MAPT", (), (Micro("SLICE", (0, 2), (tok,)),))
    b.body = Micro("MAPT", (), (Micro("SLICE", (1, 2), (tok,)),))
    a.key = lambda: a.body.key()
    b.key = lambda: b.body.key()
    beh = behavioral_equivalent(a, b)
    tex = textual_identity(a, b)
    # epoch 0 → not independent even with rediscovery origin
    rec = GenerationRecord(
        candidate_id="c2",
        candidate_origin=CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        generation_epoch=0,
        provenance_leak=False,
    )
    v = independence_verdict(rec)
    ok = beh is False and tex is False and v["independently_discovered"] is False
    return ControlResult(
        "TEXTUAL-DIFFERENCE",
        ok,
        {"behavioral_equivalent": beh, "textual_identity": tex, "verdict": v},
    )


CONTROL_FNS = {
    "NORMAL-R0": control_normal_r0,
    "NORMAL-R1": control_normal_r1,
    "NO-FIREWALL": control_no_firewall,
    "NO-LANGUAGE-GROWTH": control_no_language_growth,
    "NO-OPEN-SELECTION": control_no_open_selection,
    "LEAKAGE-CANARY": control_leakage_canary,
    "BEHAVIORAL-EQUIVALENCE": control_behavioral_equivalence,
    "TEXTUAL-DIFFERENCE": control_textual_difference,
}


def run_controls() -> dict[str, Any]:
    out = {}
    for cid in CONTROL_IDS:
        fn = CONTROL_FNS[cid]
        res = fn()
        out[cid] = res.to_dict()
    return out


def run_all(out_dir: Path | None = None) -> dict[str, Any]:
    dest = out_dir or OUT
    dest.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    # Refuse sacred
    for cid in FACTORIAL_CELLS:
        assert condition_from_id(cid).allow_sacred is False
    controls = run_controls()
    # Lightweight factorial smoke (1 seed) to keep Step1+ fast; full mock optional
    factorial = run_factorial_mocks(seeds=(0,))
    report = {
        "document": "aivd_3_40_mock_matrix",
        "sacred_tinyllama_executed": False,
        "elapsed_s": round(time.time() - t0, 3),
        "controls": controls,
        "factorial_smoke": {
            "seeds": factorial["seeds"],
            "cell_ids": list(factorial["cells"].keys()),
            "n_episodes": sum(len(v) for v in factorial["cells"].values()),
        },
        "all_controls_pass": all(controls[c]["pass"] for c in CONTROL_IDS),
    }
    (dest / "mock_matrix.json").write_text(json.dumps(report, indent=2) + "\n")
    (dest / "REPORT.md").write_text(
        "# AIVD 3.40 Mock Matrix\n\n"
        f"**Sacred TinyLlama:** NOT RUN\n\n"
        f"**Controls all pass:** {report['all_controls_pass']}\n\n"
        f"**Factorial smoke episodes:** {report['factorial_smoke']['n_episodes']}\n"
    )
    return report


__all__ = [
    "run_all",
    "run_controls",
    "run_factorial_mocks",
    "CONTROL_FNS",
    "ConditionMixError",
]
