"""Thin observational hooks — log pool/score/rank/select WITHOUT changing semantics.

Monkeypatches designer-imported symbols so return values / order / scores stay identical.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

from aivd.experiments.aivd340.phase2_constants import MODE_B_ORIGIN
from aivd.experiments.aivd340.phase2_mode_b import inject_odd_stride_controlled
from aivd.experiments.aivd340.phase2_recorder import Phase2Recorder, candidate_entry

_tls = threading.local()


def _ctx() -> dict[str, Any]:
    d = getattr(_tls, "ctx", None)
    if d is None:
        d = {}
        _tls.ctx = d
    return d


def get_active_recorder() -> Phase2Recorder | None:
    return _ctx().get("recorder")


def _parent_id(atom: Any) -> str | None:
    parents = getattr(atom, "parent", None) or ()
    if not parents:
        return None
    if isinstance(parents, (list, tuple)):
        return ",".join(str(p) for p in parents)
    return str(parents)


def _origin_of(atom: Any) -> str | None:
    return getattr(atom, "origin", None)


def _score_for_growth(atom: Any, promoted_names: list[str]) -> float:
    """Mirror pick_generation_action parent_rank as a score (lower parent_rank = better).

    Score = -parent_rank so higher is better for ranking tables; does not alter selector.
    """
    parents = getattr(atom, "parent", ()) or ()
    idxs = [promoted_names.index(p) if p in promoted_names else 99 for p in parents]
    parent_rank = min(idxs) if idxs else 99
    return float(-parent_rank)


def _ties_from_scores(body_keys: list[str], scores: list[float | None]) -> list[dict[str, Any]]:
    buckets: dict[float, list[str]] = {}
    for bk, sc in zip(body_keys, scores):
        if sc is None:
            continue
        buckets.setdefault(float(sc), []).append(bk)
    out = []
    for sc, keys in sorted(buckets.items(), key=lambda kv: -kv[0]):
        if len(keys) > 1:
            out.append({"score": sc, "body_keys": keys})
    return out


def install_hooks(*, recorder: Phase2Recorder, mode_b_inject: bool) -> None:
    """Install observational wrappers on designer-bound imports. Idempotent per call site."""
    import aivd.science.designer as designer_mod
    import aivd.science.grow as grow_mod
    import aivd.science.lifecycle as life_mod
    import aivd.science.representation as rep_mod

    ctx = _ctx()
    ctx["recorder"] = recorder
    ctx["mode_b_inject"] = bool(mode_b_inject)
    ctx["mode_b_done"] = False

    if ctx.get("_installed"):
        return

    orig_pick = grow_mod.pick_generation_action
    orig_propose_growth = rep_mod.propose_growth_candidates
    orig_rank = life_mod.rank_atoms
    orig_next_gen = designer_mod.ScienceDesigner._maybe_next_generation
    orig_maybe_grow = designer_mod.ScienceDesigner._maybe_grow

    def wrapped_propose_growth_candidates(language, *, identity, leftover, any_class=False, policy="R0"):
        return orig_propose_growth(
            language, identity=identity, leftover=leftover, any_class=any_class, policy=policy
        )

    def wrapped_pick_generation_action(
        language,
        *,
        growth_cands,
        compose_pair,
        leftover,
        greedy=False,
        always_invent=False,
    ):
        rec = get_active_recorder()
        promoted_names = [
            a.name()
            for a in getattr(language, "invented", [])
            if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
            and not str(a.name()).startswith("cmp_")
        ]
        # Build observational ranking mirroring selector inputs (parent_rank).
        scored: list[tuple[Any, float]] = []
        for g in growth_cands or []:
            scored.append((g, _score_for_growth(g, promoted_names)))
        # Stable sort by score desc then original order — observational only; selector unchanged.
        order_idx = {id(g): i for i, g in enumerate(growth_cands or [])}
        ranked = sorted(scored, key=lambda t: (-t[1], order_idx.get(id(t[0]), 0)))
        candidates = []
        ranking_keys = []
        scores_list: list[float | None] = []
        for rank_i, (g, sc) in enumerate(ranked, start=1):
            bk = g.key()
            ranking_keys.append(bk)
            scores_list.append(sc)
            parents = getattr(g, "parent", ()) or ()
            candidates.append(
                candidate_entry(
                    candidate_id=str(getattr(g, "name", lambda: bk)()),
                    body_key=bk,
                    origin=_origin_of(g),
                    parent_id=_parent_id(g),
                    representation_id=str((_ctx().get("recorder") or Phase2Recorder()).representation_id),
                    growth_or_composition_op="CAT_SELF",
                    score=sc,
                    rank=rank_i,
                )
            )
        # Compose pair as optional pool entry marker (not scored by growth ranker).
        if compose_pair is not None:
            a, b = compose_pair
            ck = f"COMPOSE({getattr(a, 'key', lambda: a.name())()}|{getattr(b, 'key', lambda: b.name())()})"
            candidates.append(
                candidate_entry(
                    candidate_id=ck,
                    body_key=ck,
                    origin="compose_pair",
                    parent_id=f"{a.name()},{b.name()}",
                    representation_id=str((_ctx().get("recorder") or Phase2Recorder()).representation_id),
                    growth_or_composition_op="COMPOSE",
                    score=None,
                    rank=None,
                )
            )

        ties = _ties_from_scores(ranking_keys, scores_list)
        if rec is not None:
            rec.record_pre_selection(
                candidates=candidates,
                ranking_ordered_body_keys=ranking_keys,
                ties=ties,
                selection_rule_id="pick_generation_action",
                tie_break_rule_id="parent_rank_then_growth_order",
                remaining_budget=leftover,
                firewall_epoch=int(getattr(language, "firewall_epoch", 0) or 0),
                generation_id=f"growth-{int(getattr(language, 'growth_count', 0) or 0)}",
                event_kind="grow",
                extra={"n_growth_cands": len(growth_cands or []), "has_compose": bool(compose_pair)},
            )

        action = orig_pick(
            language,
            growth_cands=growth_cands,
            compose_pair=compose_pair,
            leftover=leftover,
            greedy=greedy,
            always_invent=always_invent,
        )

        if rec is not None:
            selected_id = None
            selected_bk = None
            rejected = []
            if action is None:
                pass
            elif action[0] == "grow" and action[1] is not None:
                selected_id = action[1].name()
                selected_bk = action[1].key()
            elif action[0] == "compose" and action[1] is not None:
                a, b = action[1]
                selected_id = f"compose:{a.name()}+{b.name()}"
                selected_bk = f"COMPOSE({a.key()}|{b.key()})"
            elif action[0] == "safety":
                selected_id = "safety"
                selected_bk = None
            for c in candidates:
                if c["body_key"] != selected_bk:
                    cat = "NOT_SELECTED_OTHER"
                    if c.get("rank") is not None and selected_bk is not None:
                        # if selected was grow and this had worse rank
                        cat = "LOW_RANK" if (c.get("rank") or 99) > 1 else "TIE_LOST"
                    if c.get("growth_or_composition_op") == "COMPOSE" and action and action[0] == "grow":
                        cat = "NOT_SELECTED_OTHER"
                    rejected.append(
                        {
                            "candidate_id": c["candidate_id"],
                            "body_key": c["body_key"],
                            "rejection_category": cat,
                            "rejection_reason": "selector_chose_other",
                        }
                    )
            rec.record_post_selection(
                selected_candidate_id=selected_id,
                selected_body_key=selected_bk,
                rejected_candidates=rejected,
                remaining_budget=leftover,
                firewall_epoch=int(getattr(language, "firewall_epoch", 0) or 0),
                generation_id=f"growth-{int(getattr(language, 'growth_count', 0) or 0)}",
                action=(action[0] if action else "none"),
            )
        return action

    def wrapped_rank_atoms(atoms, *, rejected_classes, leftover, invariant_ready, greedy=False):
        ranked = orig_rank(
            atoms,
            rejected_classes=rejected_classes,
            leftover=leftover,
            invariant_ready=invariant_ready,
            greedy=greedy,
        )
        rec = get_active_recorder()
        if rec is not None and ranked is not None:
            candidates = []
            ranking_keys = []
            scores: list[float | None] = []
            for rank_i, a in enumerate(ranked, start=1):
                bk = a.key()
                ranking_keys.append(bk)
                # Observational mirror of lifecycle expected value is not re-derived;
                # use rank position as ordinal score only for tables.
                sc = float(-rank_i)
                scores.append(sc)
                candidates.append(
                    candidate_entry(
                        candidate_id=a.name(),
                        body_key=bk,
                        origin=_origin_of(a),
                        parent_id=_parent_id(a),
                        representation_id=rec.representation_id,
                        growth_or_composition_op="INVENT",
                        score=sc,
                        rank=rank_i,
                    )
                )
            rec.record_pre_selection(
                candidates=candidates,
                ranking_ordered_body_keys=ranking_keys,
                ties=_ties_from_scores(ranking_keys, scores),
                selection_rule_id="rank_atoms",
                tie_break_rule_id="proposal_index",
                remaining_budget=leftover,
                event_kind="invent",
                extra={"rejected_classes": sorted(str(x) for x in (rejected_classes or set()))},
            )
        return ranked

    def _maybe_inject(self: Any) -> None:
        c = _ctx()
        if c.get("mode_b_inject") and not c.get("mode_b_done"):
            did = inject_odd_stride_controlled(self, get_active_recorder(), enabled=True)
            if did:
                c["mode_b_done"] = True

    def wrapped_maybe_next_generation(self):
        _maybe_inject(self)
        return orig_next_gen(self)

    def wrapped_maybe_grow(self):
        _maybe_inject(self)
        return orig_maybe_grow(self)

    # Patch source modules AND designer-bound names.
    grow_mod.pick_generation_action = wrapped_pick_generation_action
    rep_mod.propose_growth_candidates = wrapped_propose_growth_candidates
    life_mod.rank_atoms = wrapped_rank_atoms
    designer_mod.pick_generation_action = wrapped_pick_generation_action
    designer_mod.propose_growth_candidates = wrapped_propose_growth_candidates
    designer_mod.rank_atoms = wrapped_rank_atoms
    designer_mod.ScienceDesigner._maybe_next_generation = wrapped_maybe_next_generation
    designer_mod.ScienceDesigner._maybe_grow = wrapped_maybe_grow

    ctx["_installed"] = True
    ctx["_orig"] = {
        "pick": orig_pick,
        "propose_growth": orig_propose_growth,
        "rank": orig_rank,
        "next_gen": orig_next_gen,
        "maybe_grow": orig_maybe_grow,
    }


def uninstall_hooks() -> None:
    import aivd.science.designer as designer_mod
    import aivd.science.grow as grow_mod
    import aivd.science.lifecycle as life_mod
    import aivd.science.representation as rep_mod

    ctx = _ctx()
    orig = ctx.get("_orig")
    if not orig:
        ctx.clear()
        return
    grow_mod.pick_generation_action = orig["pick"]
    rep_mod.propose_growth_candidates = orig["propose_growth"]
    life_mod.rank_atoms = orig["rank"]
    designer_mod.pick_generation_action = orig["pick"]
    designer_mod.propose_growth_candidates = orig["propose_growth"]
    designer_mod.rank_atoms = orig["rank"]
    designer_mod.ScienceDesigner._maybe_next_generation = orig["next_gen"]
    designer_mod.ScienceDesigner._maybe_grow = orig["maybe_grow"]
    ctx.clear()


@contextmanager
def observational_session(
    recorder: Phase2Recorder,
    *,
    mode_b_inject: bool = False,
) -> Iterator[Phase2Recorder]:
    install_hooks(recorder=recorder, mode_b_inject=mode_b_inject)
    try:
        yield recorder
    finally:
        uninstall_hooks()


__all__ = [
    "install_hooks",
    "uninstall_hooks",
    "observational_session",
    "get_active_recorder",
]
