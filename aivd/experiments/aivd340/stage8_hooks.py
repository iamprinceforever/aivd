"""Stage-8 live hooks — replace ONLY _keep step-6; instrument A–I.

BASELINE: original grow.propose_growth (unmodified step-6).
Repair families: propose_growth clone with step-6 → step6_equivalence.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

from aivd.science.atom import (
    LEVEL_PROGRAM,
    NOVELTY_NEW_PROGRAM,
    InventedAtom,
    semantic_class_of,
)
from aivd.science.micro import apply_micro, canonicalize_micro, micro_name, validate_micro
from aivd.science.operators import split_prompt

_tls = threading.local()


def _ctx() -> dict[str, Any]:
    d = getattr(_tls, "ctx", None)
    if d is None:
        d = {}
        _tls.ctx = d
    return d


def get_recorder():
    return _ctx().get("recorder")


def get_family() -> str:
    return _ctx().get("family") or "BASELINE"


def propose_growth_stage8(
    language: Any,
    *,
    identity: str,
    leftover: int,
    any_class: bool = False,
    max_cands: int | None = None,
):
    """Bit-identical to grow.propose_growth except step-6 equivalence policy."""
    from aivd.science.grow import cat_self_body, tokens_shorter
    from aivd.experiments.aivd340.stage8_repairs.adapter import step6_equivalence

    family = get_family()
    recorder = get_recorder()
    bank = _ctx().get("banks") or {}
    core = bank.get("core")
    reserve = bank.get("reserve")
    budget = _ctx().get("budget")
    cache = _ctx().get("cache")

    if leftover < 3:
        return []
    promoted = [
        a
        for a in getattr(language, "invented", [])
        if getattr(language, "state_of", lambda _n: "")(a.name()) == "PROMOTED"
    ]
    if not promoted:
        return []
    known_keys = {a.key() for a in language.invented}
    known_keys.update(getattr(language, "program_keys", lambda: set())())
    behaviors: dict[str, str] = {}
    body_map: dict[str, Any] = {}
    try:
        for a in promoted:
            behaviors[a.key()] = apply_micro(identity, a.body)
            body_map[a.key()] = a.body
    except Exception:
        pass
    out: list[InventedAtom] = []

    def _keep(body, *, why: str, parent: tuple[str, ...], cls: str, idx: int) -> None:
        body2 = canonicalize_micro(body)
        if body2 is None:
            return
        k = body2.key()
        if k in known_keys:
            return
        if validate_micro(body2, n_tokens=max(2, len(split_prompt(identity)))) is not None:
            return
        try:
            got = apply_micro(identity, body2)
        except Exception:
            return
        if got == identity or not got:
            return
        # ---- STEP 6 ONLY (integration_spec) ----
        if family == "BASELINE":
            # Unmodified singleton identity rule
            if got in behaviors.values():
                if recorder is not None:
                    recorder.equiv_decision(
                        family="BASELINE",
                        candidate_key=k,
                        label="duplicate",
                        action="reject",
                        apply_micro_calls=0,
                        ambiguity_state=None,
                        compared_keys=list(behaviors.keys()),
                        comparisons=[],
                    )
                return
            if recorder is not None:
                recorder.equiv_decision(
                    family="BASELINE",
                    candidate_key=k,
                    label="retain",
                    action="keep",
                    apply_micro_calls=0,
                    ambiguity_state=None,
                    compared_keys=[],
                    comparisons=[],
                )
        else:
            assert core is not None and reserve is not None and budget is not None and cache is not None
            dec = step6_equivalence(
                body2,
                got,
                behaviors,
                body_map,
                family=family,
                identity=identity,
                core=core,
                reserve=reserve,
                budget=budget,
                cache=cache,
                recorder=recorder,
            )
            if dec.action == "reject":
                return
        # ---- step 7 keep ----
        atom = InventedAtom(
            atom_id=("cmp_" + micro_name(body2).removeprefix("atom_"))[:48],
            body=body2,
            origin="language_growth",
            why=why,
            novelty=NOVELTY_NEW_PROGRAM,
            level=LEVEL_PROGRAM,
            semantic_class=cls or semantic_class_of(body2),
            parent=parent,
            lower_level_dependencies=parent,
            proposal_index=idx,
            provenance=(
                "observation",
                "promoted_atom",
                "language_extension_hypothesis",
                "growth_program",
            ),
            cost=1,
        )
        known_keys.add(k)
        behaviors[k] = got
        body_map[k] = body2
        out.append(atom)

    for atom in reversed(promoted):
        if atom.semantic_class != "char_project":
            continue
        try:
            got = apply_micro(identity, atom.body)
        except Exception:
            continue
        if not tokens_shorter(identity, got):
            continue
        body = cat_self_body(atom.body)
        if body is None:
            continue
        _keep(
            body,
            why="projection shortened tokens; glue the projection to itself",
            parent=(atom.name(),),
            cls="char_index_glue",
            idx=int(getattr(atom, "proposal_index", 0) or 0),
        )
        cap = int(max_cands) if max_cands is not None else (4 if any_class else 2)
        if len(out) >= (2 if not any_class else cap) and not any_class:
            break

    cap = int(max_cands) if max_cands is not None else (4 if any_class else 2)
    if any_class:
        for i, atom in enumerate(promoted):
            if atom.semantic_class == "char_project":
                continue
            try:
                got = apply_micro(identity, atom.body)
            except Exception:
                continue
            if not tokens_shorter(identity, got):
                continue
            body = cat_self_body(atom.body)
            if body is None:
                continue
            _keep(
                body,
                why="shortening class unused as a self-glue; glue the transform to itself",
                parent=(atom.name(),),
                cls=atom.semantic_class or semantic_class_of(body),
                idx=i,
            )
            if len(out) >= cap:
                break

    return out[:cap]


def install_hooks(*, family: str, recorder, core, reserve, budget, cache) -> None:
    import aivd.science.designer as designer_mod
    import aivd.science.grow as grow_mod
    import aivd.science.representation as rep_mod

    ctx = _ctx()
    ctx["family"] = family
    ctx["recorder"] = recorder
    ctx["banks"] = {"core": core, "reserve": reserve}
    ctx["budget"] = budget
    ctx["cache"] = cache

    if ctx.get("_installed"):
        return

    orig_propose = grow_mod.propose_growth
    orig_rep_propose = rep_mod.propose_growth
    orig_pick = grow_mod.pick_generation_action
    orig_pgc = rep_mod.propose_growth_candidates

    def wrapped_propose(language, *, identity, leftover, any_class=False, max_cands=None):
        return propose_growth_stage8(
            language,
            identity=identity,
            leftover=leftover,
            any_class=any_class,
            max_cands=max_cands,
        )

    def wrapped_pgc(language, *, identity, leftover, any_class=False, policy="R0"):
        # Mirror representation.propose_growth_candidates but call our propose_growth
        from aivd.science import representation as R

        if policy == "R0":
            return wrapped_propose(
                language, identity=identity, leftover=leftover, any_class=False
            )
        if policy == "R1":
            return wrapped_propose(
                language, identity=identity, leftover=leftover, any_class=True
            )
        # R1b path — unchanged max_cands semantics from representation
        max_cands = 6
        return wrapped_propose(
            language,
            identity=identity,
            leftover=leftover,
            any_class=True,
            max_cands=max_cands,
        )

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
        rec = get_recorder()
        if rec is not None and action and action[0] == "grow" and action[1] is not None:
            rec.note_selected(action[1].key())
        elif rec is not None and action and action[0] == "compose" and action[1] is not None:
            a, b = action[1]
            rec.emit(event="select_compose", a=a.key(), b=b.key())
        return action

    grow_mod.propose_growth = wrapped_propose
    rep_mod.propose_growth = wrapped_propose
    rep_mod.propose_growth_candidates = wrapped_pgc
    grow_mod.pick_generation_action = wrapped_pick
    designer_mod.propose_growth = wrapped_propose
    designer_mod.propose_growth_candidates = wrapped_pgc
    designer_mod.pick_generation_action = wrapped_pick

    ctx["_installed"] = True
    ctx["_orig"] = {
        "propose": orig_propose,
        "rep_propose": orig_rep_propose,
        "pick": orig_pick,
        "pgc": orig_pgc,
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
    grow_mod.propose_growth = orig["propose"]
    rep_mod.propose_growth = orig["rep_propose"]
    rep_mod.propose_growth_candidates = orig["pgc"]
    grow_mod.pick_generation_action = orig["pick"]
    designer_mod.propose_growth = orig["propose"]
    designer_mod.propose_growth_candidates = orig["pgc"]
    designer_mod.pick_generation_action = orig["pick"]
    ctx.clear()


@contextmanager
def stage8_context(*, family: str, recorder, core, reserve, budget, cache) -> Iterator[None]:
    install_hooks(
        family=family, recorder=recorder, core=core, reserve=reserve, budget=budget, cache=cache
    )
    try:
        yield
    finally:
        uninstall_hooks()
