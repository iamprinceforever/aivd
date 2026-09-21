"""Stage-7 body resolution — extends Stage-5 resolve without mutating it."""
from __future__ import annotations

from aivd.experiments.aivd340.stage5_equiv_audit import resolve_body as stage5_resolve_body
from aivd.experiments.aivd340.stage6_constants import IDENTITY_DEFAULT
from aivd.science.atom_synth import propose_atoms
from aivd.science.grow import cat_self_body
from aivd.science.micro import Micro, canonicalize_micro


def _micro_at(i: int) -> Micro:
    return canonicalize_micro(Micro("MAPT", kids=(Micro("AT", (i,)),)))  # type: ignore[return-value]


def _micro_slice(start: int, step: int) -> Micro:
    return canonicalize_micro(  # type: ignore[return-value]
        Micro("MAPT", kids=(Micro("SLICE", (start, step), kids=(Micro("TOK"),)),))
    )


def _cat2(left: Micro, right: Micro) -> Micro:
    return canonicalize_micro(  # type: ignore[return-value]
        Micro("MAPT", kids=(Micro("CAT", kids=(left.kids[0], right.kids[0])),))
    )


def resolve_body(body_key: str) -> Micro:
    """Resolve Stage-7 frozen body keys without mutating grow / Stage-5."""
    try:
        return stage5_resolve_body(body_key)
    except KeyError:
        pass

    atoms = {a.key(): a.body for a in propose_atoms(prompt=IDENTITY_DEFAULT, question=True)}
    if body_key in atoms:
        return atoms[body_key]

    # Direct AT / SLICE constructors
    if body_key.startswith("MAPT(AT:") and body_key.endswith(")"):
        inner = body_key[len("MAPT(AT:") : -1]
        return _micro_at(int(inner))
    if body_key.startswith("MAPT(SLICE:") and "(TOK))" in body_key:
        # MAPT(SLICE:start,step(TOK))
        mid = body_key[len("MAPT(SLICE:") : -len("(TOK))")]
        start_s, step_s = mid.split(",", 1)
        return _micro_slice(int(start_s), int(step_s))

    # CAT-self via parent
    cat_self_parents = {
        "MAPT(CAT(AT:0|AT:0))": _micro_at(0),
        "MAPT(CAT(AT:1|AT:1))": _micro_at(1),
        "MAPT(CAT(AT:2|AT:2))": _micro_at(2),
        "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))": _micro_slice(0, 2),
        "MAPT(CAT(SLICE:0,3(TOK)|SLICE:0,3(TOK)))": _micro_slice(0, 3),
        "MAPT(CAT(SLICE:0,4(TOK)|SLICE:0,4(TOK)))": _micro_slice(0, 4),
    }
    if body_key in cat_self_parents:
        cat = cat_self_body(cat_self_parents[body_key])
        assert cat is not None and cat.key() == body_key
        return cat

    # Cross-CAT constructors
    cross = {
        "MAPT(CAT(AT:0|AT:-1))": (_micro_at(0), _micro_at(-1)),
        "MAPT(CAT(AT:-1|AT:0))": (_micro_at(-1), _micro_at(0)),
        "MAPT(CAT(AT:1|AT:-1))": (_micro_at(1), _micro_at(-1)),
        "MAPT(CAT(AT:-1|AT:1))": (_micro_at(-1), _micro_at(1)),
        "MAPT(CAT(AT:0|AT:1))": (_micro_at(0), _micro_at(1)),
        "MAPT(CAT(AT:1|AT:0))": (_micro_at(1), _micro_at(0)),
        "MAPT(CAT(AT:2|AT:-1))": (_micro_at(2), _micro_at(-1)),
        "MAPT(CAT(SLICE:0,2(TOK)|AT:-1))": (_micro_slice(0, 2), _micro_at(-1)),
        "MAPT(CAT(AT:-1|SLICE:0,2(TOK)))": (_micro_at(-1), _micro_slice(0, 2)),
    }
    if body_key in cross:
        left, right = cross[body_key]
        out = _cat2(left, right)
        assert out.key() == body_key
        return out

    raise KeyError(f"unresolvable Stage-7 body_key: {body_key}")


def resolve_token(token: str) -> Micro:
    t = token.strip()
    if t == "IDENTICAL_MICRO_TWICE":
        return resolve_body("MAPT(AT:0)")
    if t == "IDENTICAL_AT0_TWICE":
        return resolve_body("MAPT(AT:0)")
    if t == "IDENTICAL_AT2_TWICE":
        return resolve_body("MAPT(AT:2)")
    if t == "S6_REPLAY_TD01":
        return resolve_body("MAPT(AT:-1)")
    if t.startswith("RE_CAT_SELF(") and t.endswith(")"):
        inner = t[len("RE_CAT_SELF(") : -1]
        parent = resolve_body(inner)
        cat = cat_self_body(parent)
        if cat is None:
            raise RuntimeError(f"RE_CAT_SELF failed for {inner}")
        return cat
    return resolve_body(t)
