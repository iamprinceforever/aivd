"""CrossSignalController — Level-5 cross-signal co-exploration.

Pipeline:
residual weak signal → cross-signal hypothesis → bidirectional co-explore →
characterize both → INTERACTION_READY (needs relation support) → reserved combo →
CF verification.

Config defaults OFF. No Holdout special-casing.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.cross_signal.audit import (
    anti_mapping_benchmark_spec,
    cross_signal_audit_record,
    scan_cross_signal_source,
)
from aivd.cross_signal.coexplore import (
    coexplore_bidirectional,
    compose_cross_prompts,
    hypothesize_cross_signals,
    _secret_in_obs,
)
from aivd.cross_signal.graph import RelationGraph
from aivd.cross_signal.memory import CrossSignalMemory
from aivd.cross_signal.relation import RelationState
from aivd.cross_signal.reserve import CrossSignalReserve
from aivd.cross_signal.scheduler import (
    CROSS_SIGNAL_MODES,
    CrossSignalScheduler,
    is_cross_signal_mode,
)
from aivd.cross_signal.signals import ActionSignal, ResidualSignal
from aivd.cross_signal.traces import CrossSignalTrace
from aivd.cross_signal.validation import validate_counterfactuals
from aivd.invention.intervention_space import Intervention


ObserveFn = Callable[[str], Any]


def _family_of(inv: Intervention) -> str:
    return (inv.meta or {}).get("family_id") or "unknown"


def _stem_of(inv: Intervention) -> str:
    seq = inv.sequence or []
    if not seq:
        return ""
    tok = str(seq[0])
    return tok.split("-")[0] if "-" in tok else tok[:8]


def _build_signals_from_individuals(
    individuals: list[Intervention],
    *,
    residual_context: dict[str, Any] | None = None,
    individual_effects: dict[str, float] | None = None,
) -> tuple[list[ResidualSignal], list[ActionSignal], dict[str, list[Intervention]]]:
    """Split individuals into residual-leaning vs action-leaning signals (general heuristics)."""
    ctx = residual_context or {}
    effects = dict(individual_effects or {})
    residual_text = str(
        ctx.get("error") or ctx.get("error_text") or ctx.get("residual_text") or ""
    )
    residual_toks = set()
    import re
    for t in re.split(r"[^a-zA-Z]+", residual_text.lower()):
        if len(t) >= 3:
            residual_toks.add(t)

    by_family: dict[str, list[Intervention]] = {}
    for inv in individuals or []:
        by_family.setdefault(_family_of(inv), []).append(inv)

    residuals: list[ResidualSignal] = []
    actions: list[ActionSignal] = []
    # Always seed at least one residual signal from context
    base_r = ResidualSignal(
        channel="error" if residual_text else "residual",
        residual_text=residual_text or "residual",
        strength=float(ctx.get("unexplained") or 0.3),
    )
    if residual_text or ctx.get("unexplained"):
        base_r.observe(strength=base_r.strength, unexplained=float(ctx.get("unexplained") or 0.0))
    residuals.append(base_r)

    fam_to_side: dict[str, str] = {}
    for fam, invs in by_family.items():
        # Residual-leaning if family tokens share residual vocabulary
        share = 0
        for inv in invs:
            for tok in inv.sequence or []:
                parts = str(tok).lower().replace("_", "-").split("-")
                if residual_toks & set(parts):
                    share += 1
        mean_eff = 0.0
        for inv in invs:
            mean_eff += float(effects.get(inv.id) or inv.effect or inv.security or 0.0)
        mean_eff /= max(1, len(invs))

        if share > 0 or mean_eff < 0.08:
            # Treat as residual-side evidence carrier
            r = ResidualSignal(
                channel=f"family:{fam}",
                residual_text=residual_text or fam,
                strength=max(0.05, mean_eff + 0.1 * share),
            )
            r.meta["family_id"] = fam
            r.observe(strength=r.strength)
            residuals.append(r)
            fam_to_side[fam] = "residual"
        # Always also register as action region (underexplored stem side)
        a = ActionSignal(
            family_id=fam,
            stem=_stem_of(invs[0]),
            region=fam,
            strength=mean_eff,
        )
        for inv in invs:
            a.observe(
                effect=float(effects.get(inv.id) or inv.effect or 0.0),
                variant="|".join(inv.sequence or []) or inv.id,
            )
        actions.append(a)
        if fam not in fam_to_side:
            fam_to_side[fam] = "action"

    return residuals, actions, by_family


class CrossSignalController:
    """Discover and exploit residual↔action cross-signal relationships."""

    def __init__(
        self,
        *,
        mode: str = "off",
        seed: int = 0,
        max_hypotheses: int = 6,
        max_combinations: int = 4,
        reserve_fraction: float = 0.25,
        ablation: str | None = None,
        total_budget: int | None = None,
        memory_path: str | None = None,
    ):
        self.mode = str(mode or "off").lower().strip()
        self.seed = int(seed)
        self.max_hypotheses = int(max_hypotheses)
        self.max_combinations = int(max_combinations)
        self.reserve_fraction = float(reserve_fraction)
        self.ablation = ablation
        self.total_budget = total_budget
        self.graph = RelationGraph()
        self.reserve = CrossSignalReserve(0)
        self.memory = CrossSignalMemory(memory_path)
        self.trace = CrossSignalTrace(mode=self.mode)
        self.scheduler = CrossSignalScheduler(
            mode=self.mode if is_cross_signal_mode(self.mode) else "cross_signal",
            seed=self.seed,
            ablation=ablation,
            max_hypotheses=self.max_hypotheses,
            max_combinations=self.max_combinations,
        )

    @property
    def enabled(self) -> bool:
        return is_cross_signal_mode(self.mode)

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
        self.trace = CrossSignalTrace(mode=self.mode)
        self.graph = RelationGraph()
        if not self.enabled:
            return {
                "enabled": False,
                "secret_found": False,
                "best_prompt": None,
                "n_hypotheses": 0,
                "n_combinations_tested": 0,
                "trace": self.trace.as_dict(),
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
                "complexity": {},
            }

        residuals, actions, by_family = _build_signals_from_individuals(
            inds,
            residual_context=residual_context,
            individual_effects=individual_effects,
        )
        for r in residuals:
            self.graph.add_residual(r)
            self.memory.remember_residual(r)
        for a in actions:
            self.graph.add_action(a)
            self.memory.remember_action(a)

        # HYPOTHESIZE (pruned — not brute Cartesian)
        if self.ablation == "no_relation":
            hyps = []
        else:
            hyps = hypothesize_cross_signals(
                residuals=residuals,
                actions=actions,
                max_hypotheses=self.max_hypotheses * 2,
            )
        # Track considered vs pruned at graph level
        n_possible = max(1, len(residuals) * len(actions))
        self.graph.pairs_considered = n_possible
        self.graph.pairs_pruned = max(0, n_possible - len(hyps))

        chosen = self.scheduler.select_hypotheses(hyps, budget=self.max_hypotheses)
        for h in chosen:
            self.graph.add_hypothesis(h)
            self.memory.remember_hypothesis(h)
        self.trace.hypotheses = [h.as_dict() for h in chosen]
        self.trace.add("hypotheses", n=len(chosen), possible=n_possible)

        total = int(budget if budget is not None else (self.total_budget or 8))
        if self.ablation == "no_reserve":
            rf = 0.0
        else:
            rf = self.reserve_fraction
        reserve_slots = max(0, int(round(total * rf)))
        char_budget = max(0, total - reserve_slots)
        self.reserve = CrossSignalReserve(reserve_slots)
        self.trace.add("budget", total=total, reserve=reserve_slots, characterize=char_budget)

        for h in chosen:
            if self.ablation == "no_reserve":
                break
            self.reserve.reserve(h, reason="cross_evi")
        self.trace.reservations = list(self.reserve.reservations)

        best_prompt = None
        best_obs = None
        best_effect = 0.0
        secret_found = False
        probes_used = 0
        combinations_tested = 0
        security_hits: list[dict[str, Any]] = []

        def _charge_wrap() -> bool:
            nonlocal probes_used
            if charge is not None:
                ok = charge()
                if ok:
                    probes_used += 1
                return ok
            probes_used += 1
            return True

        # Allocate char budget across chosen hyps (asymmetric toward uncertain action)
        per_hyp = max(1, char_budget // max(1, len(chosen))) if chosen else 0

        # CO-EXPLORE
        if self.ablation != "combo_only":
            for h in chosen:
                if secret_found:
                    break
                if per_hyp <= 0:
                    break
                r_fam = (h.residual.meta or {}).get("family_id") if h.residual else None
                a_fam = h.action.family_id if h.action else None
                r_invs = list(by_family.get(r_fam) or inds[:2])
                a_invs = list(by_family.get(a_fam) or inds[-2:])
                alloc_r = max(1, per_hyp // 2)
                alloc_a = max(1, per_hyp - alloc_r)
                # Prefer spending more on underexplored action side
                if h.action and h.action.uncertainty > 0.5:
                    alloc_a = max(alloc_a, alloc_r)
                cex = coexplore_bidirectional(
                    seed_prompt,
                    h,
                    residual_interventions=r_invs,
                    action_interventions=a_invs,
                    observe_fn=observe_fn,
                    graph=self.graph,
                    alloc_residual=alloc_r,
                    alloc_action=alloc_a,
                    charge=_charge_wrap,
                )
                self.trace.add(
                    "coexplore",
                    hyp=h.id,
                    state=cex.get("state"),
                    ready=cex.get("interaction_ready"),
                    link=cex.get("link_score"),
                    probes=cex.get("probes"),
                )
                self.reserve.revise(h)
                self.memory.remember_hypothesis(h)
                if cex.get("secret_found"):
                    secret_found = True
                    best_prompt = cex.get("best_prompt")
                    best_obs = cex.get("best_obs")
                    best_effect = 1.0

        # COMBINATION when relation-supported (not mere visits)
        if not secret_found and self.ablation != "no_combo":
            for h in chosen:
                if secret_found:
                    break
                ready = h.interaction_ready or h.state == RelationState.SUPPORTED.value
                soft = (
                    h.state in (RelationState.PLAUSIBLE.value, RelationState.SUPPORTED.value)
                    and float(h.cross_evi) >= 0.3
                    and self.reserve.can_test_combination()
                )
                # Visits alone are insufficient
                visits_only = (
                    (h.residual and h.residual.n_observations > 0)
                    and (h.action and h.action.n_probes > 0)
                    and h.state in (RelationState.UNSEEN.value, RelationState.WEAK.value)
                )
                if visits_only and not ready and self.ablation != "force_combo":
                    self.trace.add("not_ready_visits_only", hyp=h.id, state=h.state)
                    continue
                if not ready and not soft and self.ablation != "force_combo":
                    self.trace.add("not_ready", hyp=h.id, state=h.state)
                    continue

                r_fam = (h.residual.meta or {}).get("family_id") if h.residual else None
                a_fam = h.action.family_id if h.action else None
                r_inv = (by_family.get(r_fam) or inds)[0]
                a_inv = (by_family.get(a_fam) or inds)[-1]
                orders = self.scheduler.select_orders(h, max_orders=self.max_combinations)
                prompts = compose_cross_prompts(
                    seed_prompt, r_inv, a_inv, orders=tuple(orders),
                )
                for item in prompts:
                    if not self.reserve.consume(h.id) and self.ablation != "force_combo":
                        if not self.reserve.can_test_combination():
                            break
                    if charge is not None and not _charge_wrap():
                        break
                    elif charge is None:
                        probes_used += 1
                    prompt = item["prompt"]
                    obs = observe_fn(prompt)
                    combinations_tested += 1
                    self.graph.mark_tested(h.id)
                    hit = _secret_in_obs(obs)
                    rec = {
                        "hyp_id": h.id,
                        "order": item["order"],
                        "prompt": prompt,
                        "secret": hit,
                        "ready": ready,
                        "state": h.state,
                    }
                    self.trace.combinations_tested.append(rec)
                    self.scheduler.mark_tested(h, item["order"])
                    self.trace.add("combination", **rec)
                    if hit:
                        secret_found = True
                        best_prompt = prompt
                        best_obs = obs
                        best_effect = 1.0
                        h.n_support += 1
                        h.advance(cf_pass=True)
                        security_hits.append(h.as_dict())
                        break

                # CF validation (when budget remains)
                if not secret_found and self.ablation not in ("no_cf", "combo_only"):
                    distractor = None
                    for fam, invs in by_family.items():
                        if fam not in (r_fam, a_fam) and invs:
                            distractor = invs[0]
                            break
                    cf = validate_counterfactuals(
                        seed_prompt,
                        h,
                        residual_inv=r_inv,
                        action_inv=a_inv,
                        distractor_inv=distractor,
                        observe_fn=observe_fn,
                        charge=_charge_wrap,
                    )
                    self.trace.add("cf", hyp=h.id, **{k: cf[k] for k in (
                        "cf_pass", "cf_consistency", "state", "probes",
                    ) if k in cf})
                    self.reserve.revise(h)
                    if cf.get("secret_in_joint"):
                        secret_found = True
                        best_prompt = f"{seed_prompt} {' '.join(r_inv.sequence or [])} {' '.join(a_inv.sequence or [])}".strip()
                        best_effect = 1.0
                        security_hits.append(h.as_dict())

        complexity = self.graph.complexity()
        self.trace.complexity = complexity
        self.trace.probes_used = probes_used
        self.trace.reservations = self.reserve.as_dict().get("reservations", [])
        self.memory.save()

        summary = {
            "n_hypotheses": len(chosen),
            "n_combinations_tested": combinations_tested,
            "secret_found": secret_found,
            "n_supported": len(self.graph.supported()),
            "reserve_consumed": len(self.reserve.consumed),
            "brute_force": complexity.get("brute_force"),
        }
        audit = cross_signal_audit_record(
            summary=summary,
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
            "n_security_hits": len(security_hits),
            "security_hits": security_hits,
            "probes_used": probes_used,
            "reserve": self.reserve.as_dict(),
            "graph": self.graph.as_dict(),
            "complexity": complexity,
            "hypotheses": [h.as_dict() for h in chosen],
            "trace": self.trace.as_dict(),
            "scheduler_trace": list(self.scheduler.trace),
            "memory": self.memory.as_dict(),
            "audit": audit,
            "ablation": self.ablation,
            "anti_mapping_spec": anti_mapping_benchmark_spec(),
        }


__all__ = [
    "CrossSignalController",
    "is_cross_signal_mode",
    "CROSS_SIGNAL_MODES",
    "scan_cross_signal_source",
]
