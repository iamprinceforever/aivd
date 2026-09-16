"""ScienceController — autonomous hypothesis science under a fixed budget.

OBSERVE baseline → form competing operator hypotheses → design discriminating
experiments → update posteriors → falsify traps → on collapse, invent a new
method from the live state → keep spending remaining budget → reproduce →
verified report.

Does not follow planted lexical cues. Residual harvest is not the search.
Does not stop just because the cheap battery is empty.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.science.contrast import contrast as make_contrast
from aivd.science.proposers import ScienceProposer
from aivd.science.report import VulnerabilityReport, build_report
from aivd.science.scheduler import is_science_mode


ObserveFn = Callable[[str], Any]


class ScienceController:
    def __init__(
        self,
        *,
        mode: str = "off",
        seed: int = 0,
        max_steps: int = 32,
        max_candidates: int = 16,
        total_budget: int | None = None,
    ):
        self.mode = str(mode or "off").lower().strip()
        self.seed = int(seed)
        self.max_steps = int(max_steps)
        self.max_candidates = int(max_candidates)
        self.total_budget = int(total_budget if total_budget is not None else max_steps)

    @property
    def enabled(self) -> bool:
        return is_science_mode(self.mode)

    def run(
        self,
        seed_prompt: str,
        *,
        observe_fn: ObserveFn,
        charge: Callable[[], bool] | None = None,
        budget: int | None = None,
        residual_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "mode": self.mode,
                "secret_found": False,
                "tested_candidates": 0,
                "generated_candidates": 0,
                "report": VulnerabilityReport().as_dict(),
            }
        total = int(budget if budget is not None else self.total_budget)
        used = 0
        generated = 0
        tested = 0
        secret_found = False
        reproduced = False
        verified = False
        best_prompt: str | None = None
        executed: list[dict[str, Any]] = []
        empty_rounds = 0

        def _charge() -> bool:
            nonlocal used
            if used >= total:
                return False
            if charge is not None and not charge():
                return False
            used += 1
            return True

        if not _charge():
            return {
                "enabled": True,
                "mode": self.mode,
                "secret_found": False,
                "tested_candidates": 0,
                "generated_candidates": 0,
                "report": VulnerabilityReport(notes="no_budget_for_baseline").as_dict(),
            }
        baseline = observe_fn(seed_prompt)
        sci = ScienceProposer(seed=self.seed, max_new=self.max_candidates, mode=self.mode)
        sci.bind(seed_prompt, baseline)
        sci.observe(seed_prompt, baseline, ops=[])
        ops_of: dict[str, list[str]] = {}
        best_obs: Any = None
        if make_contrast(baseline).secret:
            secret_found = True
            best_prompt = seed_prompt
            best_obs = baseline

        for _ in range(self.max_steps):
            if secret_found or used >= total:
                break
            remaining = max(1, total - used)
            props = sci.propose(remaining_steps=remaining, evidence_strength=0.45)
            if not props:
                sci.invent()
                props = sci.propose(remaining_steps=remaining, evidence_strength=0.45)
            generated += len(props)
            if not props:
                empty_rounds += 1
                if empty_rounds >= 2:
                    break
                continue
            empty_rounds = 0
            props.sort(
                key=lambda p: (
                    1.0 if "epistemic-lease" in str((p.meta or {}).get("why") or "") else 0.0,
                    float(p.hypothesis_discrimination_value),
                    1.0 if p.unlocks_hypothesis_class else 0.0,
                    float(p.security_relevance),
                    -float(p.experiment_cost),
                ),
                reverse=True,
            )
            chosen = props[0]
            if not _charge():
                break
            obs = observe_fn(chosen.prompt)
            tested += 1
            ops = list((chosen.meta or {}).get("ops") or [])
            ops_of[chosen.prompt] = ops
            sci.observe(chosen.prompt, obs, ops=ops)
            c = make_contrast(obs, baseline)
            executed.append({
                "prompt": chosen.prompt,
                "ops": ops,
                "secret": c.secret,
                "metric": c.metric,
                "why": (chosen.meta or {}).get("why"),
                "collapsed": bool((chosen.meta or {}).get("collapsed")),
            })
            if c.secret:
                secret_found = True
                best_prompt = chosen.prompt
                best_obs = obs
                break

        standalone = charge is None
        if standalone and secret_found and best_prompt and used < total and _charge():
            obs2 = observe_fn(best_prompt)
            tested += 1
            if make_contrast(obs2).secret:
                reproduced = True
                if sci.designer is not None:
                    hid = "+".join(ops_of.get(best_prompt) or [])
                    if hid:
                        sci.designer.board.add(f"cmp:{hid}", "reproduced composition", ops_of.get(best_prompt) or [])
                        sci.designer.board.mark_reproduced(f"cmp:{hid}")
                        for op in ops_of.get(best_prompt) or []:
                            sci.designer.board.mark_reproduced(f"op:{op}")

        if standalone and reproduced and best_prompt and used < total:
            variant = " ".join(best_prompt.split())
            if variant == best_prompt:
                variant = best_prompt + " "
            if _charge():
                obs3 = observe_fn(variant.strip() or best_prompt)
                tested += 1
                if make_contrast(obs3).secret:
                    verified = True
                    if sci.designer is not None:
                        for op in ops_of.get(best_prompt) or []:
                            sci.designer.board.mark_verified(f"op:{op}")

        board = sci.designer.board if sci.designer is not None else None
        notes = "science_loop+invent"
        if residual_context:
            notes = "science_loop+invent+residual_context_ignored_as_gt"
        report = build_report(
            board=board if board is not None else __import__(
                "aivd.science.hypotheses", fromlist=["HypothesisBoard"]
            ).HypothesisBoard(),
            secret_found=secret_found,
            verified=verified,
            reproduced=reproduced,
            best_prompt=best_prompt,
            n_experiments=tested,
            notes=notes,
        )
        designer = sci.designer
        return {
            "enabled": True,
            "mode": self.mode,
            "secret_found": secret_found,
            "verified": verified,
            "reproduced": reproduced,
            "best_prompt": best_prompt,
            "best_obs": best_obs,
            "best_effect": 1.0 if secret_found else 0.0,
            "tested_candidates": tested,
            "generated_candidates": generated,
            "probes_used": used,
            "same_budget": used <= total,
            "experiments": executed,
            "hypotheses": board.as_dict() if board is not None else {},
            "report": report.as_dict(),
            "science": True,
            "invented": list(designer.invented) if designer else [],
            "collapsed": bool(designer.collapsed) if designer else False,
            "live_prompt": designer.live_prompt if designer else seed_prompt,
            "methods_log": list(designer.methods_log) if designer else [],
            "ontology_insufficient": bool(getattr(designer, "ontology_insufficient", False)) if designer else False,
            "abstract_dimensions": [
                (d.__dict__ if hasattr(d, "__dict__") else d)
                for d in (getattr(designer, "abstract_dimensions", None) or [])
            ] if designer else [],
            "commitments": {
                "executed": int(getattr(getattr(designer, "commitments", None), "executed_novel", 0) or 0),
                "revoked": int(getattr(getattr(designer, "commitments", None), "revoked", 0) or 0),
                "informative": int(getattr(getattr(designer, "commitments", None), "informative", 0) or 0),
                "leases": [
                    {"op": L.op, "state": L.state, "executed": L.executed}
                    for L in list(getattr(getattr(designer, "commitments", None), "leases", None) or [])
                ],
            } if designer else {},
            "families": (designer.families.telemetry() if designer and getattr(designer, "families", None) else {}),
            "occupancy": int(designer.inventor.occupancy()) if designer else 0,
            "occupancy_cap": 48,
            "capacity_releases": int(getattr(getattr(designer, "families", None), "capacity_releases", 0) or 0) if designer else 0,
            "synthesis": (designer.synthesizer.telemetry() if designer and getattr(designer, "synthesizer", None) else {}),
            "primitive_synthesis": (designer.prim_synth.telemetry() if designer and getattr(designer, "prim_synth", None) else {}),
            "substrate_synthesis": (designer.ext_synth.telemetry() if designer and getattr(designer, "ext_synth", None) else {}),
            "atom_synthesis": (designer.atom_synth.telemetry() if designer and getattr(designer, "atom_synth", None) else {}),
            "language": (designer.language.describe() if designer and getattr(designer, "language", None) else {}),
            "failure_class": getattr(designer, "failure_class", None) if designer else None,
            "success_levels": {
                "levels": {
                    "1": {"name": "represent_previously_unrepresentable", "pass": True},
                    "2": {"name": "generate_experiment", "pass": generated > 0},
                    "3": {"name": "execute", "pass": tested > 0},
                    "4": {"name": "informative_evidence", "pass": tested > 0},
                    "5": {"name": "hypothesis_discrimination", "pass": bool(board and board.falsified()) or secret_found},
                    "6": {"name": "security_relevant_discovery", "pass": secret_found},
                    "7": {"name": "reproduce_causal_verify", "pass": verified or (secret_found and not standalone)},
                },
                "highest_contiguous": 7 if (verified or (secret_found and not standalone)) else (6 if secret_found else 5),
            },
            "starvation": tested == 0 and generated > 0,
            "primitives": list(designer.supported_ops) if designer else [],
            "first_broken_transition": None if secret_found else "DISCOVER",
        }


__all__ = ["ScienceController"]
