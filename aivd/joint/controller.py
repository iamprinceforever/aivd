"""JointResidualController — Level-4 joint residual budget allocation.

Pipeline (after 3.12 interaction hypothesis):
JOINT DEPENDENCY ESTIMATION → CO-EXPLORATION → ALLOCATE ACROSS COMPONENTS →
CHARACTERIZE A → CHARACTERIZE B → CHECK INTERACTION READINESS → TEST A+B →
(caller continues: counterfactuals → causal → investigation → falsify → verify)

Config defaults OFF. No Holdout/Q/Z special-casing.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.invention.intervention_space import Intervention
from aivd.joint.audit import complexity_metrics, joint_audit_record
from aivd.joint.budget_allocator import allocate_budget
from aivd.joint.coexploration import coexplore_families, compose_ordered_prompts
from aivd.joint.dependency import hypothesize_joint_residuals, JointResidualHypothesis
from aivd.joint.readiness import pair_interaction_ready
from aivd.joint.reserve import BudgetReserve
from aivd.joint.residual_graph import ResidualGraph
from aivd.joint.scheduler import (
    JointScheduler,
    is_joint_mode,
    JOINT_MODES,
)
from aivd.joint.traces import JointTrace


ObserveFn = Callable[[str], Any]


def _secret_in_obs(obs: Any) -> bool:
    if obs is None:
        return False
    text = ""
    if hasattr(obs, "out_text"):
        text = obs.out_text or ""
    elif isinstance(obs, dict):
        text = str(obs.get("out_text") or obs.get("text") or "")
    elif isinstance(obs, tuple) and obs:
        text = str(obs[0] or "")
    else:
        text = str(obs)
    t = text.lower()
    return "secret{" in t or "disallowed:" in t


class JointResidualController:
    """Recognize joint residual dependency and allocate characterization + reserve."""

    def __init__(
        self,
        *,
        mode: str = "off",
        seed: int = 0,
        max_hypotheses: int = 6,
        max_combinations: int = 4,
        alloc_policy: str = "joint_aware",
        reserve_fraction: float = 0.25,
        ablation: str | None = None,
        total_budget: int | None = None,
    ):
        self.mode = str(mode or "off").lower().strip()
        self.seed = int(seed)
        self.max_hypotheses = int(max_hypotheses)
        self.max_combinations = int(max_combinations)
        self.alloc_policy = str(alloc_policy or "joint_aware")
        self.reserve_fraction = float(reserve_fraction)
        self.ablation = ablation
        self.total_budget = total_budget
        self.graph = ResidualGraph()
        self.reserve = BudgetReserve(0)
        self.trace = JointTrace(mode=self.mode)
        self.scheduler = JointScheduler(
            mode=self.mode if is_joint_mode(self.mode) else "joint",
            seed=self.seed,
            ablation=ablation,
            max_hypotheses=self.max_hypotheses,
            max_combinations=self.max_combinations,
            alloc_policy=self.alloc_policy,
        )

    @property
    def enabled(self) -> bool:
        return is_joint_mode(self.mode)

    def run(
        self,
        seed_prompt: str,
        *,
        individuals: list[Intervention],
        observe_fn: ObserveFn,
        residual_context: dict[str, Any] | None = None,
        charge: Callable[[], bool] | None = None,
        individual_effects: dict[str, float] | None = None,
        budget: int | None = None,
    ) -> dict[str, Any]:
        self.trace = JointTrace(mode=self.mode)
        self.graph = ResidualGraph()
        if not self.enabled:
            return {
                "enabled": False,
                "secret_found": False,
                "best_prompt": None,
                "n_hypotheses": 0,
                "n_combinations_tested": 0,
                "trace": self.trace.as_dict(),
                "allocation": {},
                "complexity": {},
            }

        inds = list(individuals or [])
        if len(inds) < 2:
            self.trace.add("skip", reason="need_two_individuals")
            return {
                "enabled": True,
                "skipped": True,
                "secret_found": False,
                "best_prompt": None,
                "n_hypotheses": 0,
                "n_combinations_tested": 0,
                "trace": self.trace.as_dict(),
                "allocation": {},
                "complexity": {},
            }

        ctx = dict(residual_context or {})
        effects = dict(individual_effects or {})
        for inv in inds:
            if inv.id not in effects:
                effects[inv.id] = float(inv.effect or inv.security or 0.0)
            fid = (inv.meta or {}).get("family_id") or "unknown"
            # Seed graph with prior individual evidence (characterization credit)
            self.graph.observe(
                fid,
                variant="|".join(inv.sequence or []) or inv.id,
                effect=effects.get(inv.id, 0.0),
            )
        self.graph.refresh_readiness()

        # JOINT DEPENDENCY ESTIMATION
        hyps = hypothesize_joint_residuals(
            inds,
            residual_context=ctx,
            max_hypotheses=self.max_hypotheses * 2,
            family_stats=self.graph.family_stats(),
        )
        if self.ablation == "no_dependency":
            hyps = []
        chosen = self.scheduler.select_hypotheses(hyps, budget=self.max_hypotheses)
        for h in chosen:
            self.graph.add_edge(
                h.family_a, h.family_b,
                linkage=h.linkage, residual=h.residual, hyp_id=h.id,
            )
        self.trace.hypotheses = [h.as_dict() for h in chosen]
        self.trace.add("hypotheses", n=len(chosen))

        # ALLOCATE
        total = int(budget if budget is not None else (self.total_budget or 8))
        if self.ablation == "no_reserve":
            rf = 0.0
        else:
            rf = self.reserve_fraction
        policy = self.alloc_policy
        if self.ablation in ("static", "equal", "greedy", "random"):
            policy = self.ablation
        allocation = allocate_budget(
            chosen,
            total_budget=total,
            policy=policy,
            reserve_fraction=rf,
            ablation=self.ablation if self.ablation in ("static", "equal", "greedy", "random") else None,
        )
        self.reserve = BudgetReserve(int(allocation.get("reserve") or 0))
        self.trace.allocations.append(allocation)
        self.trace.add(
            "allocated",
            policy=allocation.get("policy"),
            reserve=allocation.get("reserve"),
            per_family=allocation.get("per_family"),
            asymmetric=allocation.get("asymmetric"),
        )

        # Soft-reserve high-EVI hypotheses
        for h in chosen:
            if self.ablation == "no_reserve":
                break
            self.reserve.reserve(h, reason="joint_evi")
        self.trace.reservations = list(self.reserve.reservations)

        best_prompt = None
        best_obs = None
        best_effect = 0.0
        secret_found = False
        probes_used = 0
        combinations_tested = 0
        security_joints: list[dict[str, Any]] = []

        def _charge_wrap() -> bool:
            nonlocal probes_used
            if charge is not None:
                ok = charge()
                if ok:
                    probes_used += 1
                return ok
            probes_used += 1
            return True

        per_fam = dict(allocation.get("per_family") or {})

        # CO-EXPLORATION / CHARACTERIZE
        if self.ablation != "combo_only":
            for h in chosen:
                if secret_found:
                    break
                aa = int(per_fam.get(h.family_a) or 0)
                bb = int(per_fam.get(h.family_b) or 0)
                # Avoid double-counting shared families across hyps: consume alloc
                per_fam[h.family_a] = 0
                per_fam[h.family_b] = 0
                if aa <= 0 and bb <= 0:
                    continue
                cex = coexplore_families(
                    seed_prompt,
                    h,
                    individuals=inds,
                    observe_fn=observe_fn,
                    graph=self.graph,
                    alloc_a=aa,
                    alloc_b=bb,
                    charge=_charge_wrap,
                    secret_fn=_secret_in_obs,
                )
                self.trace.add(
                    "coexplore",
                    hyp=h.id,
                    readiness_a=cex.get("readiness_a"),
                    readiness_b=cex.get("readiness_b"),
                    ready=cex.get("interaction_ready"),
                    probes=cex.get("probes"),
                )
                self.trace.readiness.extend(self.graph.readiness_trace())
                if cex.get("secret_found"):
                    secret_found = True
                    best_prompt = cex.get("best_prompt")
                    best_obs = cex.get("best_obs")
                    best_effect = 1.0
                # Revise reserve based on updated readiness
                self.reserve.revise(h)

        self.graph.refresh_readiness()

        # CHECK READINESS → TEST COMBINATIONS (ordered)
        if not secret_found and self.ablation != "no_combo":
            for h in chosen:
                if secret_found:
                    break
                ready = h.interaction_ready or pair_interaction_ready(
                    h.readiness_a, h.readiness_b
                )
                # Soft path: high joint EVI + reserve available
                soft = float(h.joint_evi) >= 0.3 and self.reserve.can_test_combination()
                if not ready and not soft and self.ablation != "force_combo":
                    self.trace.add("not_ready", hyp=h.id,
                                   ra=h.readiness_a, rb=h.readiness_b)
                    continue
                orders = self.scheduler.select_combination_orders(
                    h, max_orders=self.max_combinations,
                )
                prompts = compose_ordered_prompts(
                    seed_prompt, h, orders=tuple(orders),
                )
                for item in prompts:
                    if not self.reserve.consume(h.id) and self.ablation != "force_combo":
                        # try ad-hoc if reserve empty but force
                        if not self.reserve.can_test_combination() and self.ablation != "force_combo":
                            break
                    if charge is not None and not _charge_wrap():
                        break
                    elif charge is None:
                        probes_used += 1
                    prompt = item["prompt"]
                    obs = observe_fn(prompt)
                    combinations_tested += 1
                    hit = _secret_in_obs(obs)
                    rec = {
                        "hyp_id": h.id,
                        "order": item["order"],
                        "prompt": prompt,
                        "secret": hit,
                        "ready": ready,
                    }
                    self.trace.combinations_tested.append(rec)
                    self.scheduler.mark_tested(h, item["order"])
                    self.trace.add("combination", **rec)
                    if hit:
                        secret_found = True
                        best_prompt = prompt
                        best_obs = obs
                        best_effect = 1.0
                        h.interaction_confidence = 0.9
                        security_joints.append(h.as_dict())
                        break
                    # Mild effect tracking
                    h.interaction_confidence = max(h.interaction_confidence, 0.1)

        # Multi-way hierarchical (joint_full only)
        triples = self.scheduler.hierarchical_triples(chosen)
        n_fams = len(self.graph.nodes)
        complexity = complexity_metrics(
            n_families=n_fams,
            n_hypotheses_possible=max(len(hyps), n_fams * (n_fams - 1) // 2),
            n_hypotheses_generated=len(chosen),
            n_orders_possible=4 * max(1, len(chosen)),
            n_orders_tested=combinations_tested,
            n_triples_possible=max(0, n_fams * (n_fams - 1) * (n_fams - 2) // 6),
            n_triples_tested=len(triples),
        )
        self.trace.complexity = complexity
        self.trace.probes_used = probes_used
        self.trace.reservations = self.reserve.as_dict().get("reservations", [])
        self.trace.readiness = self.graph.readiness_trace()

        summary = {
            "n_hypotheses": len(chosen),
            "n_combinations_tested": combinations_tested,
            "secret_found": secret_found,
            "asymmetric": allocation.get("asymmetric"),
            "reserve_consumed": len(self.reserve.consumed),
        }
        audit = joint_audit_record(
            summary=summary,
            allocation=allocation,
            readiness=self.trace.readiness,
            complexity=complexity,
            ablation=self.ablation,
        )

        return {
            "enabled": True,
            "mode": self.mode,
            "secret_found": secret_found,
            "best_prompt": best_prompt,
            "best_obs": best_obs,
            "best_effect": best_effect,
            "n_individuals": len(inds),
            "n_hypotheses": len(chosen),
            "n_combinations_tested": combinations_tested,
            "n_security_joints": len(security_joints),
            "security_joints": security_joints,
            "probes_used": probes_used,
            "allocation": allocation,
            "reserve": self.reserve.as_dict(),
            "graph": self.graph.as_dict(),
            "readiness": self.trace.readiness,
            "complexity": complexity,
            "hypotheses": [h.as_dict() for h in chosen],
            "trace": self.trace.as_dict(),
            "scheduler_trace": list(self.scheduler.trace),
            "audit": audit,
            "ablation": self.ablation,
            "triples": [{"families": list(t)} for t in triples],
        }


__all__ = [
    "JointResidualController",
    "is_joint_mode",
    "JOINT_MODES",
]
