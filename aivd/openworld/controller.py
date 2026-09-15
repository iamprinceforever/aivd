"""OpenWorldController — observation-harvested representation + generative experiments.

Pipeline: OBSERVE → features → primitive discovery → representation → hypothesis
→ generative operator composition → experiment → observe → representation update.

Default off. Disabled ≈ 3.16. No ACTION_STEMS dump. Protected experiment floor.
Predict before experiment. Falsify noncausal. Invent-without-execute hard guard.
"""
from __future__ import annotations

from typing import Any, Callable

from aivd.invention.intervention_space import Intervention
from aivd.openworld.budget import (
    OpenWorldBudget,
    invent_without_execute_guard,
    protected_floor,
)
from aivd.openworld.diagnostics import diagnose_openworld, success_levels
from aivd.openworld.experiment import predict_experiment, rank_experiments
from aivd.openworld.features import extract_features
from aivd.openworld.generator import generate_from_representation, info_acquisition_from_rep
from aivd.openworld.memory import OpenWorldMemory
from aivd.openworld.primitives import harvest_primitives, primitive_tokens
from aivd.openworld.representation import representation_from_primitives
from aivd.openworld.scheduler import is_openworld_mode
from aivd.reasoning.efficiency import compute_efficiency
from aivd.reasoning.information_gain import update_uncertainty


ObserveFn = Callable[[str], Any]


def _secret_in_obs(obs: Any) -> bool:
    text = ""
    if obs is None:
        return False
    if hasattr(obs, "out_text"):
        text = obs.out_text or ""
    elif isinstance(obs, dict):
        text = str(obs.get("out_text") or obs.get("text") or "")
    else:
        text = str(obs)
    t = text.lower()
    return "secret{" in t or "disallowed:" in t


def _security_signal(obs: Any, baseline: Any | None = None) -> float:
    if obs is None:
        return 0.0
    if _secret_in_obs(obs):
        return 1.0
    feat = extract_features(obs, baseline=baseline)
    score = 0.0
    if feat.error:
        score += 0.35
    if feat.metric:
        score += min(0.4, float(feat.metric))
    if feat.state_changed:
        score += 0.2
    return min(1.0, score)


def _prompt_of(seed: str, inv: Intervention) -> str:
    toks = " ".join(str(t) for t in (inv.sequence or []))
    return f"{seed} {toks}".strip()


class OpenWorldController:
    """Open-world behavioral representation + generative experimentation."""

    def __init__(
        self,
        *,
        mode: str = "off",
        seed: int = 0,
        max_steps: int = 32,
        max_candidates: int = 24,
        floor_fraction: float = 0.40,
        ablation: str | None = None,
        total_budget: int | None = None,
    ):
        self.mode = str(mode or "off").lower().strip()
        self.seed = int(seed)
        self.max_steps = int(max_steps)
        self.max_candidates = int(max_candidates)
        self.floor_fraction = float(floor_fraction)
        self.ablation = ablation
        self.total_budget = int(total_budget if total_budget is not None else max_steps)
        self.charge_ok = 0
        self.charge_fail = 0
        self.memory = OpenWorldMemory()
        self.total_predicted_ig = 0.0
        self.total_actual_ig = 0.0

    @property
    def enabled(self) -> bool:
        return is_openworld_mode(self.mode)

    def run(
        self,
        seed_prompt: str,
        *,
        observe_fn: ObserveFn,
        residual_context: dict[str, Any] | None = None,
        individuals: list[Intervention] | None = None,
        charge: Callable[[], bool] | None = None,
        budget: int | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "mode": self.mode,
                "openworld_enabled": False,
                "tested_candidates": 0,
                "generated_candidates": 0,
                "secret_found": False,
            }

        total = int(budget if budget is not None else self.total_budget)
        abl = (self.ablation or "").lower()
        frac = 0.0 if abl == "no_floor" else self.floor_fraction
        floor = protected_floor(total, fraction=frac, min_n=0 if abl == "no_floor" else 4)
        bgt = OpenWorldBudget(total=total, reserved_floor=floor)
        ctx = dict(residual_context or {})
        unexplained = float(ctx.get("unexplained") or 0.8)
        u0 = unexplained

        def _charge() -> bool:
            if charge is not None:
                ok = charge()
                if not ok:
                    self.charge_fail += 1
                    return False
                # sync local used
                bgt.charge(1)
                self.charge_ok += 1
                return True
            ok = bgt.charge(1)
            if not ok:
                self.charge_fail += 1
                return False
            self.charge_ok += 1
            return True

        baseline = None
        try:
            if _charge():
                baseline = observe_fn(seed_prompt)
        except Exception as e:
            ctx["observe_error"] = str(e)

        secret_found = _secret_in_obs(baseline)
        best_prompt = seed_prompt if secret_found else None
        best_obs = baseline if secret_found else None
        best_effect = 1.0 if secret_found else 0.0
        tested_keys: set[str] = set()
        effects_seen: set[int] = set()
        n_state_changes = 0
        n_hyp_resolved = 0
        n_hyps = 0
        state_pending: list[str] = []
        transition_pending: list[tuple[str, str]] = []
        tested_kinds: dict[str, int] = {}
        latencies: list[float] = []
        executed_recs: list[dict[str, Any]] = []

        prims = harvest_primitives(
            baseline, residual_context=ctx if "no_harvest" not in abl else {"error": ctx.get("error")},
        )
        if "no_harvest" in abl:
            # closed: residual error tokens only
            prims = harvest_primitives(None, residual_context={"error": ctx.get("error"), "error_text": ctx.get("error_text")})
        self.memory.primitives_seen = primitive_tokens(prims, skip_distractor=False)

        if secret_found:
            # still return a full record
            pass
        else:
            # Iterate: represent → generate → execute (floor-protected)
            max_iter = min(self.max_steps, total + 2)
            for it in range(max_iter):
                if secret_found or bgt.remaining() <= 0:
                    break
                guard = invent_without_execute_guard(
                    generated=bgt.generated, tested=bgt.tested,
                    remaining=bgt.remaining(),
                )
                if guard["halt_generate"] or (abl != "invent_spam" and bgt.halt_generate):
                    bgt.halt_generate = True

                feats = {}
                if baseline is not None:
                    bf = extract_features(baseline)
                    feats = {"metric": bf.metric, "out_len": float(bf.out_len)}
                rep = representation_from_primitives(prims, features=feats)
                rep.n_distinct_effects = len(effects_seen)
                rep.n_state_changes = n_state_changes
                n_hyps = max(n_hyps, len(rep.relations) + len(rep.tokens()))
                suff = rep.sufficient()

                cands: list[Intervention] = []
                if not bgt.halt_generate:
                    extra_st = list(state_pending) if "no_state" not in abl else []
                    extra_tr = list(transition_pending) if "no_transition" not in abl else []
                    cands = generate_from_representation(
                        rep, ablation=self.ablation, max_new=self.max_candidates,
                        extra_state_repeats=extra_st, extra_transitions=extra_tr,
                    )
                    if individuals:
                        cands = list(individuals) + cands
                    if (not suff.get("sufficient")) or (bgt.tested < 1 and not cands):
                        cands = info_acquisition_from_rep(rep, ctx, max_new=4) + cands
                    bgt.note_generated(len(cands))
                else:
                    # STOP GENERATE → execute best already queued via pending
                    extra_st = list(state_pending)
                    extra_tr = list(transition_pending)
                    cands = generate_from_representation(
                        rep, ablation=self.ablation, max_new=min(8, self.max_candidates),
                        extra_state_repeats=extra_st, extra_transitions=extra_tr,
                    )

                if self.mode == "openworld_random" or abl == "random":
                    import random as _rnd
                    rng = _rnd.Random(self.seed + it)
                    rng.shuffle(cands)
                    recs = [predict_experiment(c, tested_kinds=tested_kinds) for c in cands[: bgt.remaining()]]
                elif abl == "no_predict":
                    recs = [predict_experiment(c, tested_kinds=tested_kinds) for c in cands[: bgt.remaining()]]
                else:
                    recs = [
                        predict_experiment(
                            c, tested_kinds=tested_kinds, n_open_hyps=max(2, n_hyps),
                            state_pending=bool(state_pending or transition_pending),
                        )
                        for c in cands
                    ]
                    recs = rank_experiments(recs, budget=min(8, bgt.remaining()))

                progressed = False
                for rec in recs:
                    if secret_found or bgt.remaining() <= 0:
                        break
                    inv = rec.intervention
                    if inv is None:
                        continue
                    key = "|".join(inv.sequence or [])
                    # Allow STATE re-probe of the same sequence (first-class)
                    state_repeat = rec.grammar_kind == "STATE" and key in tested_keys
                    trans_follow = rec.grammar_kind == "TRANSITION"
                    if state_repeat and tested_kinds.get("STATE", 0) >= 3:
                        continue
                    if trans_follow and tested_kinds.get("TRANSITION", 0) >= 8:
                        continue
                    if key in tested_keys and not (state_repeat or trans_follow):
                        continue
                    if state_repeat:
                        key = key + f"|repeat{tested_kinds.get('STATE', 0)}"
                    if trans_follow:
                        key = key + f"|tr{tested_kinds.get('TRANSITION', 0)}|{key}"
                    if key in tested_keys:
                        continue
                    if not _charge():
                        # Hard guard: do not invent-spam after charge fail
                        bgt.halt_generate = True
                        break
                    import time as _time
                    t0 = _time.perf_counter()
                    prompt = _prompt_of(seed_prompt, inv)
                    obs = observe_fn(prompt)
                    latencies.append(_time.perf_counter() - t0)
                    tested_keys.add(key)
                    bgt.note_tested(1)
                    progressed = True
                    if "no_harvest" not in abl:
                        prims = harvest_primitives(obs, residual_context=ctx, existing=prims)
                    else:
                        prims = harvest_primitives(None, residual_context={"error": ctx.get("error"), "error_text": ctx.get("error_text")}, existing=prims)
                    self.memory.primitives_seen = primitive_tokens(prims, skip_distractor=False)
                    feat = extract_features(obs, baseline=baseline)
                    effect = _security_signal(obs, baseline)
                    # Noncausal falsification: metric-only bump without error/state/secret
                    if abl != "no_falsify":
                        if feat.metric >= 0.3 and not feat.error and not feat.has_secret and not feat.state_changed:
                            effect = min(effect, 0.05)
                            n_hyp_resolved += 1  # distractor hyp falsified as causal
                    effects_seen.add(int(round(effect * 10)))
                    if feat.state_changed:
                        n_state_changes += 1
                    u_after = update_uncertainty(unexplained, effect, predicted_positive=rec.predicted_positive)
                    ig = max(0.0, unexplained - u_after)
                    unexplained = min(unexplained, u_after)
                    self.total_predicted_ig += float(rec.predicted_ig)
                    self.total_actual_ig += float(ig)
                    rec.executed = True
                    rec.effect = effect
                    rec.actual_ig = ig
                    rec.informative = ig > 0.01 or effect > 0.15 or feat.state_changed
                    tested_kinds[rec.grammar_kind] = tested_kinds.get(rec.grammar_kind, 0) + 1
                    seq0 = (inv.sequence or ["?"])[0]
                    self.memory.record_chain(
                        observation_id=f"obs_{it}",
                        feature_id=f"feat_{it}",
                        hyp_id=rec.grammar_kind or "h",
                        operator_id=seq0,
                        experiment_id=f"exp_{key}",
                        outcome_id=f"out_{it}",
                    )
                    self.memory.record_outcome(key=key, effect=effect, ig=ig, kind=rec.grammar_kind)
                    executed_recs.append(rec.as_dict())
                    if effect > 0.15:
                        n_hyp_resolved += 1
                        # STATE: token changed something → re-apply
                        if seq0 and seq0 not in state_pending:
                            state_pending.append(seq0)
                        # TRANSITION: after A, try other primitives as B
                        for other in primitive_tokens(prims)[:6]:
                            if other != seq0:
                                pair = (seq0, other)
                                if pair not in transition_pending:
                                    transition_pending.append(pair)
                    if effect > best_effect:
                        best_effect = effect
                        best_prompt = prompt
                        best_obs = obs
                    if _secret_in_obs(obs):
                        secret_found = True
                        best_prompt = prompt
                        best_obs = obs
                        best_effect = 1.0
                        break
                if not progressed:
                    # no new experiment executed this round
                    if bgt.tested == 0 and self.charge_fail >= 2:
                        bgt.starvation = True
                        break
                    if bgt.remaining() <= 0:
                        break
                    # avoid infinite no-progress loops
                    if it > 2 and bgt.tested > 0 and not state_pending and not transition_pending:
                        break
                    # if we have pending state/transition, continue
                    if not state_pending and not transition_pending and bgt.tested > 0:
                        # SEARCH_DEAD_END recovery: one more info-acq then stop
                        if it > 0:
                            break

        if bgt.tested == 0 and bgt.generated > 0:
            bgt.starvation = True

        mean_ig = (self.total_actual_ig / bgt.tested) if bgt.tested else 0.0
        add = 0
        if baseline is not None:
            add = 1
        if prims:
            add = max(add, 2)
        if bgt.generated > 0:
            add = max(add, 4)
        if bgt.tested > 0:
            add = max(add, 5)
        if secret_found:
            add = max(add, 8)
        u_drop = max(0.0, u0 - unexplained)
        act, disc = add, 0
        if bgt.tested > 0:
            disc = 1
        if mean_ig > 0.02 or u_drop > 0.05:
            disc = max(disc, min(act, 3 + int(3 * min(1.0, mean_ig * 5))))
        if secret_found:
            disc = act
        disc = min(disc, act)
        eff = compute_efficiency(
            probes=bgt.used, tested=bgt.tested, theoretical=max(64, bgt.generated),
            generated=bgt.generated, total_actual_ig=self.total_actual_ig,
            total_predicted_ig=self.total_predicted_ig, n_hypotheses=n_hyps,
            n_hyp_resolved=n_hyp_resolved, add=add, secret_found=secret_found,
            u_before=u0, u_after=unexplained,
        )
        # Override activity/discovery with our split
        from aivd.reasoning.efficiency import DiscoveryEfficiency
        eff = DiscoveryEfficiency(
            discovery_efficiency=eff.discovery_efficiency,
            hypothesis_efficiency=eff.hypothesis_efficiency,
            information_efficiency=eff.information_efficiency,
            search_reduction=eff.search_reduction,
            activity_depth=int(act),
            discovery_depth=int(disc),
            activity_without_discovery=bool(act > 0 and disc <= 1 and not secret_found),
        )
        suff_final = representation_from_primitives(prims).sufficient()
        diag = diagnose_openworld(
            n_primitives=len(primitive_tokens(prims)),
            generated=bgt.generated, tested=bgt.tested, mean_ig=mean_ig,
            u_drop=u_drop, secret_found=secret_found, charge_fail=self.charge_fail,
            representation_ok=bool(suff_final.get("sufficient")),
        )
        informative = bool(mean_ig > 0.01 or u_drop > 0.02 or secret_found or bgt.tested > 0 and best_effect > 0.15)
        security_rel = bool(secret_found or best_effect >= 0.5)
        levels = success_levels(
            representable=len(primitive_tokens(prims)) > 0,
            generatable=bgt.generated > 0,
            executable=bgt.tested > 0,
            informative=informative,
            hyp_discrimination=n_hyp_resolved > 0,
            security_relevant=security_rel,
            reproduced_verified=bool(secret_found),
        )
        first_broken = None
        if bgt.tested == 0:
            first_broken = "EXPERIMENT"
        elif not secret_found:
            first_broken = diag.get("first_broken_capability") or "VERIFY"

        return {
            "enabled": True,
            "openworld_enabled": True,
            "mode": self.mode,
            "best_prompt": best_prompt,
            "best_obs": best_obs,
            "best_effect": best_effect,
            "secret_found": secret_found,
            "probes_used": bgt.used,
            "budget": bgt.as_dict(),
            "add": add,
            "activity_depth": int(act),
            "discovery_depth": int(disc),
            "tested_candidates": bgt.tested,
            "generated_candidates": bgt.generated,
            "n_primitives": len(primitive_tokens(prims)),
            "primitives": primitive_tokens(prims),
            "representable": len(primitive_tokens(prims)) > 0,
            "generatable": bgt.generated > 0,
            "executable": bgt.tested > 0,
            "informative": informative,
            "n_hypotheses": n_hyps,
            "mean_actual_ig": mean_ig,
            "efficiency": eff.as_dict(),
            "diagnostics": diag,
            "success_levels": levels,
            "starvation": bgt.starvation,
            "first_broken_transition": first_broken,
            "bottleneck": {
                "earliest": "EXPERIMENT" if bgt.starvation else (diag.get("first_broken_capability") or "UNKNOWN-LIMIT"),
                "codes": diag.get("codes"),
            },
            "charge_ok": self.charge_ok,
            "charge_fail": self.charge_fail,
            "provenance": self.memory.as_dict(),
            "representation": suff_final,
            "experiments": executed_recs[:32],
            "mean_latency_s": (sum(latencies) / len(latencies)) if latencies else 0.0,
            "ablation": self.ablation,
            "brute_force": False,
            "theoretical_candidates": max(64, bgt.generated),
        }


__all__ = ["OpenWorldController"]
