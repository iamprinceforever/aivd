"""Mode B controlled availability — historically observed odd-stride atom ONLY.

Does NOT inject finished odd CAT-self, odd-double, secrets, rankings, or force select.
Marks CONTROLLED_INPUT / autonomous_discovery_credit=false.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from aivd.experiments.aivd340.phase2_constants import MODE_B_ORIGIN, ODD_STRIDE_BODY_KEY
from aivd.experiments.aivd340.phase2_recorder import Phase2Recorder
from aivd.science.atom_synth import propose_atoms


def build_odd_stride_atom(*, prompt: str = "ab cd ef gh ij kl") -> Any:
    """Rebuild the historically observed odd-stride atom from propose_atoms 8-set.

    Uses the frozen body key MAPT(SLICE:1,2(TOK)) already present in the immutable
    propose_atoms set — does not alter propose_atoms.
    """
    atoms = propose_atoms(prompt=prompt, question=True)
    hit = next((a for a in atoms if a.key() == ODD_STRIDE_BODY_KEY), None)
    if hit is None:
        raise RuntimeError(f"odd-stride body {ODD_STRIDE_BODY_KEY} missing from propose_atoms — STOP")
    return replace(
        hit,
        origin=MODE_B_ORIGIN,
        why="Phase-2 Mode B controlled availability of historically observed odd-stride atom",
        predicted="CONTROLLED_INPUT — not autonomous invent",
        provenance=tuple(hit.provenance or ())
        + (
            "controlled_availability_mode_b",
            "historical_observed_odd_stride_atom",
            "PHASE2_MODE_B_NONCREDIT",
        ),
        novelty="CONTROLLED_INPUT",
    )


def language_has_body(language: Any, body_key: str) -> bool:
    for a in getattr(language, "invented", []) or []:
        if a.key() == body_key:
            return True
    return False


def inject_odd_stride_controlled(
    designer: Any,
    recorder: Phase2Recorder | None,
    *,
    enabled: bool,
) -> bool:
    """Inject odd-stride atom as PROMOTED with Mode B provenance. Idempotent.

    Returns True if injection performed on this call.
    """
    if not enabled:
        return False
    language = getattr(designer, "language", None)
    if language is None:
        return False
    if language_has_body(language, ODD_STRIDE_BODY_KEY):
        # Already present (possibly from prior inject or autonomous invent).
        # If autonomous invent somehow produced it under Mode B, still label noncredit.
        return False

    ident = getattr(designer, "identity_prompt", None) or getattr(designer, "seed_prompt", "") or "ab cd ef gh"
    atom = build_odd_stride_atom(prompt=str(ident))

    # Register executable + language candidacy, then promote so growth can see it.
    inventor = getattr(designer, "inventor", None)
    atom_synth = getattr(designer, "atom_synth", None)
    name = atom.name()
    if inventor is not None and name not in getattr(inventor, "ops", {}):
        fn = atom_synth.make_fn(atom) if atom_synth is not None else None
        if fn is not None:
            inventor._register(name, fn, why=atom.why or MODE_B_ORIGIN)
        if atom_synth is not None:
            atom_synth.op_of[name] = atom
            if name not in atom_synth.board.materialized:
                atom_synth.board.materialized.append(name)

    language.add_atom(atom, grow=False)
    language.promote(atom, reason="controlled_availability_mode_b", evidence=MODE_B_ORIGIN)

    leftover = int(getattr(designer, "remaining_steps", 0) or 0)
    fw = int(getattr(language, "firewall_epoch", 0) or 0)
    if recorder is not None:
        recorder.record_mode_b_availability(
            body_key=ODD_STRIDE_BODY_KEY,
            remaining_budget=leftover,
            firewall_epoch=fw,
        )
    # Observational note on methods_log only — does not change selection.
    methods = getattr(designer, "methods_log", None)
    if isinstance(methods, list):
        methods.append(
            {
                "event": "mode_b_availability",
                "body_key": ODD_STRIDE_BODY_KEY,
                "origin": MODE_B_ORIGIN,
                "autonomous_discovery_credit": "false",
                "controlled_availability": "true",
                "claim_label": "CONTROLLED_INPUT",
            }
        )
    return True


__all__ = [
    "build_odd_stride_atom",
    "language_has_body",
    "inject_odd_stride_controlled",
]
