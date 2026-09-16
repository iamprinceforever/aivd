"""EpistemicController — OBSERVE → propose → GLOBAL ARBITER → execute → update.

Default off ≈ 3.17. Authoritative mode replaces sequential leftover ownership
with one global 32-slot allocator. Shadow mode records arbiter vs legacy
without changing execution.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.epistemic.arbiter import GlobalEpistemicArbiter
from aivd.epistemic.branch import Branch
from aivd.epistemic.diagnostics import report
from aivd.epistemic.memory import roundtrip
from aivd.epistemic.proposers import (
    AxisProposer,
    InventionProposer,
    OpenWorldProposer,
    ResidualProposer,
    _secret_in_obs,
    actual_ig_from_obs,
    security_signal,
)
from aivd.epistemic.scheduler import is_authoritative, is_epistemic_mode, is_shadow_mode
from aivd.epistemic.types import BranchState, ExperimentProposal
from aivd.openworld.diagnostics import diagnose_openworld, success_levels
from aivd.reasoning.efficiency import compute_efficiency, DiscoveryEfficiency


ObserveFn = Callable[[str], Any]


class EpistemicController:
    def __init__(
        self,
        *,
        mode: str = "off",
        seed: int = 0,
        max_steps: int = 32,
        max_candidates: int = 24,
        ablation: str | None = None,
        total_budget: int | None = None,
        policy: str | None = None,
    ):
        self.mode = str(mode or "off").lower().strip()
        self.seed = int(seed)
        self.max_steps = int(max_steps)
        self.max_candidates = int(max_candidates)
        self.ablation = ablation
        self.total_budget = int(total_budget if total_budget is not None else max_steps)
        self.policy = policy or ("greedy_eig" if "greedy" in (ablation or "") else "completion_value")
        self.charge_ok = 0
        self.charge_fail = 0

    @property
    def enabled(self) -> bool:
        return is_epistemic_mode(self.mode)

    @property
    def shadow(self) -> bool:
        return is_shadow_mode(self.mode)

    @property
    def authoritative(self) -> bool:
        return is_authoritative(self.mode)

    def run(
        self,
        seed_prompt: str,
        *,
        observe_fn: ObserveFn,
        residual_context: dict[str, Any] | None = None,
        charge: Callable[[], bool] | None = None,
        budget: int | None = None,
        extra_proposals: Callable[[dict[str, Any]], list[ExperimentProposal]] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "mode": self.mode,
                "epistemic_enabled": False,
                "openworld_enabled": False,
                "tested_candidates": 0,
                "generated_candidates": 0,
                "secret_found": False,
            }

        from aivd.science.scheduler import is_science_mode
        if is_science_mode(self.mode):
            from aivd.science.controller import ScienceController
            sci = ScienceController(
                mode=self.mode,
                seed=self.seed,
                max_steps=self.max_steps,
                max_candidates=self.max_candidates,
                total_budget=int(budget if budget is not None else self.total_budget),
            )
            return sci.run(
                seed_prompt,
                observe_fn=observe_fn,
                charge=charge,
                budget=budget,
                residual_context=residual_context,
            )

        total = int(budget if budget is not None else self.total_budget)
        arb = GlobalEpistemicArbiter(
            total=total,
            seed=self.seed,
            shadow=self.shadow,
            policy=self.policy,
        )
        ctx = dict(residual_context or {})
        unexplained = float(ctx.get("unexplained") or 0.8)
        u0 = unexplained

        ow_p = OpenWorldProposer(seed=self.seed, max_new=min(8, self.max_candidates), ablation=self.ablation)
        inv_p = InventionProposer(seed=self.seed, max_new=6)
        ax_p = AxisProposer(max_new=6)
        res_p = ResidualProposer(max_new=6)

        arb.register_branch(Branch(branch_id="openworld", subsystem="openworld", estimated_remaining_steps=5))
        arb.register_branch(Branch(branch_id="invention", subsystem="invention", estimated_remaining_steps=6, evidence_strength=0.22))
        arb.register_branch(Branch(branch_id="residual", subsystem="residual", estimated_remaining_steps=4, evidence_strength=0.35))
        arb.register_branch(Branch(branch_id="axis", subsystem="axis", estimated_remaining_steps=8, evidence_strength=0.18))

        def _charge() -> bool:
            if charge is not None:
                ok = charge()
            else:
                ok = arb.ledger.can_spend(1)
            if not ok:
                self.charge_fail += 1
                return False
            self.charge_ok += 1
            return True

        baseline = None
        if _charge():
            baseline = observe_fn(seed_prompt)
            # If an outer charge() already billed the env interaction, still
            # record it on the global ledger when we own the counter.
            if charge is None:
                arb.ledger.charge(1, subsystem="observe", branch_id="residual", proposal_id="seed")
            else:
                # Outer pipeline already charged; mirror into ledger used count
                # only if the ledger is empty so diagnostics stay consistent.
                if arb.ledger.used == 0:
                    arb.ledger.used = min(arb.ledger.total, arb.ledger.used + 1)

        secret_found = _secret_in_obs(baseline)
        best_prompt = seed_prompt if secret_found else None
        best_obs = baseline if secret_found else None
        best_effect = 1.0 if secret_found else 0.0
        generated = 0
        tested = 0
        executed: list[dict[str, Any]] = []

        ow_p.observe_update(baseline, residual_context=ctx)
        res_p.harvest(baseline)
        if ctx.get("axes"):
            ax_p.set_axes(list(ctx.get("axes") or []))
        else:
            try:
                from aivd37.unknowns.open_axes import generate_open_axes
                axes = generate_open_axes(
                    residual_channels=list(ctx.get("security_shaped_residuals") or ctx.get("residual_channels") or []),
                    max_axes=8,
                )
                ax_p.set_axes([a.axis for a in axes])
            except Exception:
                ax_p.set_axes(["authorization_sequence", "sparse_structure"])

        max_iter = min(self.max_steps, total + 2)
        for _it in range(max_iter):
            if secret_found or arb.ledger.remaining() <= 0:
                break
            proposals: list[ExperimentProposal] = []
            b_ow = arb.registry.get("openworld")
            b_inv = arb.registry.get("invention")
            b_res = arb.registry.get("residual")
            b_ax = arb.registry.get("axis")
            if b_ow and b_ow.viable():
                proposals.extend(ow_p.propose(
                    seed_prompt=seed_prompt, remaining_steps=b_ow.estimated_remaining_steps,
                    evidence_strength=b_ow.evidence_strength,
                ))
            if b_inv and b_inv.viable():
                proposals.extend(inv_p.propose(
                    seed_prompt=seed_prompt, residual_context=ctx,
                    remaining_steps=b_inv.estimated_remaining_steps,
                    evidence_strength=b_inv.evidence_strength,
                ))
            if b_res and b_res.viable():
                proposals.extend(res_p.propose(
                    seed_prompt=seed_prompt, remaining_steps=b_res.estimated_remaining_steps,
                    evidence_strength=b_res.evidence_strength,
                ))
            if b_ax and b_ax.viable() and (self.ablation or "") != "no_axis":
                proposals.extend(ax_p.propose(
                    seed_prompt=seed_prompt, remaining_steps=b_ax.estimated_remaining_steps,
                    evidence_strength=b_ax.evidence_strength,
                ))
            if extra_proposals is not None:
                proposals.extend(extra_proposals({
                    "seed": seed_prompt, "remaining": arb.ledger.remaining(), "step": arb.step,
                    "registry": arb.registry,
                }) or [])
            generated += len(proposals)
            if not proposals:
                break
            dec = arb.decide(proposals)
            chosen = dec.selected
            if chosen is None:
                break
            if not _charge():
                break
            obs = observe_fn(chosen.prompt)
            tested += 1
            effect = security_signal(obs, baseline)
            secret = _secret_in_obs(obs)
            # Noncausal metric-only bump
            if (self.ablation or "") != "no_falsify":
                if _metric_only(obs) and not secret:
                    effect = min(effect, 0.05)
            ig, u_after = actual_ig_from_obs(unexplained, effect)
            redundant = (chosen.action in (ow_p.tested_keys | inv_p.tested | res_p.tested | ax_p.tested))
            falsified = bool(effect < 0.02 and chosen.expected_information_gain > 0.5 and ig < 0.01)
            # If outer charge already billed, still commit_execution which charges ledger.
            # Avoid double-count: when charge callback exists, temporarily allow ledger
            # to track used even if it would exceed — we already billed outside.
            if charge is not None:
                # Outer pipeline billed this probe; record without a second env call.
                if arb.ledger.used >= arb.ledger.total:
                    pass
            ok = arb.commit_execution(
                chosen,
                actual_ig=ig,
                uncertainty_before=unexplained,
                uncertainty_after=u_after,
                effect=effect,
                secret=secret,
                falsified=falsified,
                redundant=redundant,
                cost=float(chosen.experiment_cost or 1.0),
            )
            if not ok and charge is not None:
                # Outer billed; force-record branch update only
                arb.ledger.used = min(arb.ledger.total, arb.ledger.used)
            unexplained = min(unexplained, u_after)
            ow_p.observe_update(obs, residual_context=ctx)
            ow_p.tested_keys.add(str((chosen.meta or {}).get("key") or chosen.action))
            if chosen.hypothesis_id:
                ow_p.tested_kinds[chosen.hypothesis_id] = ow_p.tested_kinds.get(chosen.hypothesis_id, 0) + 1
            inv_p.tested.add(chosen.action)
            res_p.tested.add(chosen.prompt)
            res_p.harvest(obs)
            ax_p.tested.add(chosen.prompt)
            executed.append({
                "proposal_id": chosen.proposal_id,
                "branch_id": chosen.branch_id,
                "subsystem": chosen.subsystem,
                "prompt": chosen.prompt,
                "expected_ig": chosen.expected_information_gain,
                "actual_ig": ig,
                "effect": effect,
                "secret": secret,
                "score": chosen.score.as_dict(),
            })
            if effect > best_effect:
                best_effect = effect
                best_prompt = chosen.prompt
                best_obs = obs
            if secret:
                secret_found = True
                best_prompt = chosen.prompt
                best_obs = obs
                best_effect = 1.0
                break

        starvation = tested == 0 and generated > 0
        mean_ig = (sum(e["actual_ig"] for e in executed) / tested) if tested else 0.0
        add = 1 if baseline is not None else 0
        if generated:
            add = max(add, 4)
        if tested:
            add = max(add, 5)
        if secret_found:
            add = max(add, 8)
        disc = 0
        if tested:
            disc = 1
        u_drop = max(0.0, u0 - unexplained)
        if mean_ig > 0.02 or u_drop > 0.05:
            disc = max(disc, min(add, 3 + int(3 * min(1.0, mean_ig * 5))))
        if secret_found:
            disc = add
        disc = min(disc, add)
        eff = compute_efficiency(
            probes=max(tested, arb.ledger.used), tested=tested, theoretical=max(64, generated),
            generated=generated, total_actual_ig=sum(e["actual_ig"] for e in executed),
            total_predicted_ig=sum(float(e["expected_ig"]) for e in executed),
            n_hypotheses=len(arb.registry.branches), n_hyp_resolved=sum(1 for e in executed if e["effect"] > 0.15),
            add=add, secret_found=secret_found, u_before=u0, u_after=unexplained,
        )
        eff = DiscoveryEfficiency(
            discovery_efficiency=eff.discovery_efficiency,
            hypothesis_efficiency=eff.hypothesis_efficiency,
            information_efficiency=eff.information_efficiency,
            search_reduction=eff.search_reduction,
            activity_depth=int(add),
            discovery_depth=int(disc),
            activity_without_discovery=bool(add > 0 and disc <= 1 and not secret_found),
        )
        informative = bool(mean_ig > 0.01 or u_drop > 0.02 or secret_found or (tested > 0 and best_effect > 0.15))
        levels = success_levels(
            representable=bool(ow_p.prims or res_p.tokens),
            generatable=generated > 0,
            executable=tested > 0,
            informative=informative,
            hyp_discrimination=any(e["effect"] > 0.15 for e in executed),
            security_relevant=bool(secret_found or best_effect >= 0.5),
            reproduced_verified=bool(secret_found),
        )
        diag_ow = diagnose_openworld(
            n_primitives=len(ow_p.prims), generated=generated, tested=tested,
            mean_ig=mean_ig, u_drop=u_drop, secret_found=secret_found,
            charge_fail=self.charge_fail, representation_ok=bool(ow_p.prims),
        )
        pipe = report(
            arb.ledger, arb.registry, arb.book, arb.shadow_log,
            verified=secret_found, secret_found=secret_found,
            unresolved_invisible=not secret_found and best_effect < 0.15,
        )
        ckpt = roundtrip(arb.checkpoint())
        return {
            "enabled": True,
            "epistemic_enabled": True,
            "openworld_enabled": False,
            "mode": self.mode,
            "shadow": self.shadow,
            "authoritative": self.authoritative,
            "best_prompt": best_prompt,
            "best_obs": best_obs,
            "best_effect": best_effect,
            "secret_found": secret_found,
            "probes_used": arb.ledger.used,
            "budget": arb.ledger.as_dict(),
            "add": add,
            "activity_depth": int(add),
            "discovery_depth": int(disc),
            "tested_candidates": tested,
            "generated_candidates": generated,
            "n_primitives": len(ow_p.prims),
            "primitives": list(res_p.tokens)[:16],
            "representable": bool(ow_p.prims or res_p.tokens),
            "generatable": generated > 0,
            "executable": tested > 0,
            "informative": informative,
            "n_hypotheses": len(arb.registry.branches),
            "mean_actual_ig": mean_ig,
            "efficiency": eff.as_dict(),
            "diagnostics": {**diag_ow, **pipe},
            "success_levels": levels,
            "starvation": starvation,
            "first_broken_transition": "EXPERIMENT" if starvation else ("VERIFY" if not secret_found else None),
            "charge_ok": self.charge_ok,
            "charge_fail": self.charge_fail,
            "experiments": executed[:32],
            "branches": arb.registry.as_dict(),
            "reservations": arb.book.as_dict(),
            "shadow_log": arb.shadow_log.as_dict(),
            "checkpoint": ckpt,
            "brute_force": False,
            "theoretical_candidates": max(64, generated),
            "pipeline_experiment_slot_efficiency": pipe["pipeline_experiment_slot_efficiency"],
            "same_budget": arb.ledger.total == total and arb.ledger.used <= total,
        }


def _metric_only(obs: Any) -> bool:
    from aivd.epistemic.proposers import _error, _metric
    m = _metric(obs)
    return m >= 0.3 and not _error(obs) and not _secret_in_obs(obs)


__all__ = ["EpistemicController"]
