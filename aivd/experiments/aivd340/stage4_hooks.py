"""Stage-4 observational hooks — must NOT change growth/selection semantics.

Wraps the same symbols Phase-2 wraps; return values identical to uninstrumented.
Additionally can attach a Stage4Recorder for pool/select continuity events.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

from aivd.experiments.aivd340.phase2_mode_b import inject_odd_stride_controlled
from aivd.experiments.aivd340.stage4_recorder import Stage4Recorder

_tls = threading.local()


def _ctx() -> dict[str, Any]:
    d = getattr(_tls, "ctx", None)
    if d is None:
        d = {}
        _tls.ctx = d
    return d


def get_active_recorder() -> Stage4Recorder | None:
    return _ctx().get("recorder")


def install_hooks(
    *,
    recorder: Stage4Recorder | None,
    mode_b_inject: bool = False,
) -> None:
    import aivd.science.designer as designer_mod
    import aivd.science.grow as grow_mod
    import aivd.science.representation as rep_mod

    ctx = _ctx()
    ctx["recorder"] = recorder
    ctx["mode_b_inject"] = bool(mode_b_inject)
    ctx["mode_b_done"] = False

    if ctx.get("_installed"):
        return

    orig_pick = grow_mod.pick_generation_action
    orig_propose = rep_mod.propose_growth_candidates
    orig_next_gen = designer_mod.ScienceDesigner._maybe_next_generation
    orig_maybe_grow = designer_mod.ScienceDesigner._maybe_grow

    def wrapped_propose(language, *, identity, leftover, any_class=False, policy="R0"):
        out = orig_propose(
            language, identity=identity, leftover=leftover, any_class=any_class, policy=policy
        )
        rec = get_active_recorder()
        if rec is not None:
            rec.emit(
                event_kind="pool",
                snapshot_phase="pre_selection_pool_snapshot",
                claim_label="OBSERVED",
                remaining_budget=leftover,
                firewall_epoch=int(getattr(language, "firewall_epoch", 0) or 0),
                pool_body_keys=[g.key() for g in out],
                n_growth_cands=len(out),
                policy=policy,
            )
        return out

    def wrapped_pick(
        language,
        *,
        growth_cands,
        compose_pair,
        leftover,
        greedy=False,
        always_invent=False,
    ):
        action = orig_pick(
            language,
            growth_cands=growth_cands,
            compose_pair=compose_pair,
            leftover=leftover,
            greedy=greedy,
            always_invent=always_invent,
        )
        rec = get_active_recorder()
        if rec is not None:
            selected_bk = None
            if action and action[0] == "grow" and action[1] is not None:
                selected_bk = action[1].key()
            elif action and action[0] == "compose" and action[1] is not None:
                a, b = action[1]
                selected_bk = f"COMPOSE({a.key()}|{b.key()})"
            rec.emit(
                event_kind="select",
                snapshot_phase="post_selection_record",
                claim_label="OBSERVED",
                remaining_budget=leftover,
                firewall_epoch=int(getattr(language, "firewall_epoch", 0) or 0),
                action=None if action is None else action[0],
                selected_body_key=selected_bk,
                pool_body_keys=[g.key() for g in (growth_cands or [])],
            )
        return action

    def _maybe_inject(self: Any) -> None:
        c = _ctx()
        if c.get("mode_b_inject") and not c.get("mode_b_done"):
            # Phase-2 injector expects Phase2Recorder | None; pass None (methods_log still records).
            did = inject_odd_stride_controlled(self, None, enabled=True)
            if did:
                c["mode_b_done"] = True
                rec = get_active_recorder()
                if rec is not None:
                    from aivd.experiments.aivd340.stage4_constants import ODD_STRIDE_BODY_KEY

                    rec.controlled_injected = True
                    rec.controlled_body_key = ODD_STRIDE_BODY_KEY
                    rec.emit(
                        event_kind="controlled_presence",
                        snapshot_phase="controlled_atom_presence",
                        claim_label="CONTROLLED",
                        body_key=ODD_STRIDE_BODY_KEY,
                        remaining_budget=int(getattr(self, "remaining_steps", 0) or 0),
                        autonomous_discovery_credit=False,
                    )

    def wrapped_next(self):
        _maybe_inject(self)
        return orig_next_gen(self)

    def wrapped_grow(self):
        _maybe_inject(self)
        return orig_maybe_grow(self)

    grow_mod.pick_generation_action = wrapped_pick
    rep_mod.propose_growth_candidates = wrapped_propose
    designer_mod.pick_generation_action = wrapped_pick
    designer_mod.propose_growth_candidates = wrapped_propose
    designer_mod.ScienceDesigner._maybe_next_generation = wrapped_next
    designer_mod.ScienceDesigner._maybe_grow = wrapped_grow

    ctx["_installed"] = True
    ctx["_orig"] = {
        "pick": orig_pick,
        "propose": orig_propose,
        "next_gen": orig_next_gen,
        "maybe_grow": orig_maybe_grow,
    }


def uninstall_hooks() -> None:
    import aivd.science.designer as designer_mod
    import aivd.science.grow as grow_mod
    import aivd.science.representation as rep_mod

    ctx = _ctx()
    orig = ctx.get("_orig")
    if not orig:
        ctx.clear()
        return
    grow_mod.pick_generation_action = orig["pick"]
    rep_mod.propose_growth_candidates = orig["propose"]
    designer_mod.pick_generation_action = orig["pick"]
    designer_mod.propose_growth_candidates = orig["propose"]
    designer_mod.ScienceDesigner._maybe_next_generation = orig["next_gen"]
    designer_mod.ScienceDesigner._maybe_grow = orig["maybe_grow"]
    ctx.clear()


@contextmanager
def stage4_session(
    recorder: Stage4Recorder | None,
    *,
    mode_b_inject: bool = False,
) -> Iterator[Stage4Recorder | None]:
    install_hooks(recorder=recorder, mode_b_inject=mode_b_inject)
    try:
        yield recorder
    finally:
        uninstall_hooks()


__all__ = [
    "install_hooks",
    "uninstall_hooks",
    "stage4_session",
    "get_active_recorder",
]
