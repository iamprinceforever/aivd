"""Offline intermediate-representation test (EXISTING operators only).

Never inserts intermediates into autonomous discovery.
"""
from __future__ import annotations

from typing import Any

from aivd.experiments.aivd340.stage4_constants import (
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    U_GOOD_BODY_KEY,
    U_GOOD_CAT_SELF_BODY_KEY,
)
from aivd.science.atom_synth import propose_atoms
from aivd.science.grow import cat_self_body
from aivd.science.language import ExperimentLanguage
from aivd.science.micro import apply_micro


def _atom_by_key(body_key: str, prompt: str = "ab cd ef gh ij kl") -> Any:
    atoms = propose_atoms(prompt=prompt, question=True)
    hit = next((a for a in atoms if a.key() == body_key), None)
    if hit is None:
        raise RuntimeError(f"body {body_key} missing from propose_atoms 8-set")
    return hit


def offline_ir_path(
    *,
    start_body_key: str,
    target_body_key: str,
    prompt: str = "ab cd ef gh ij kl",
) -> dict[str, Any]:
    """Test whether EXISTING cat_self_body yields target in one step.

    Multi-step compose exploration is recorded but does not invent new operators.
    inserted_into_autonomous MUST remain false.
    """
    start = _atom_by_key(start_body_key, prompt=prompt)
    cat = cat_self_body(start.body)
    single_step = bool(cat is not None and cat.key() == target_body_key)
    path_steps: list[dict[str, Any]] = []
    if cat is not None:
        path_steps.append(
            {
                "op": "cat_self_body",
                "input_keys": [start_body_key],
                "output_key": cat.key(),
            }
        )
    path_found = single_step
    # Optional: note behavioral identity with other single-step products (analysis only)
    behavior_note = None
    if cat is not None:
        try:
            behavior_note = apply_micro(prompt, cat)
        except Exception as e:
            behavior_note = f"apply_fail:{e}"

    return {
        "start_body_key": start_body_key,
        "target_body_key": target_body_key,
        "operators_allowed": ["cat_self_body", "compose"],
        "path_found": path_found,
        "path_steps": path_steps,
        "single_step_cat_self": single_step,
        "inserted_into_autonomous": False,
        "claim_label": "OFFLINE_IR",
        "cat_self_output_key": None if cat is None else cat.key(),
        "behavior_on_prompt": behavior_note,
        "autonomous_discovery_credit": False,
    }


def offline_ir_control_b(*, seed: int = 0) -> dict[str, Any]:
    r = offline_ir_path(
        start_body_key=ODD_STRIDE_BODY_KEY,
        target_body_key=ODD_CAT_SELF_BODY_KEY,
    )
    r["seed"] = seed
    r["control_id"] = "B"
    r["condition_id"] = "S4-IR-B"
    return r


def offline_ir_control_a(*, seed: int = 0) -> dict[str, Any]:
    r = offline_ir_path(
        start_body_key=U_GOOD_BODY_KEY,
        target_body_key=U_GOOD_CAT_SELF_BODY_KEY,
    )
    r["seed"] = seed
    r["control_id"] = "A"
    r["condition_id"] = "S4-IR-A"
    return r


def language_with_promoted(body_keys: list[str], prompt: str = "ab cd ef gh ij kl") -> ExperimentLanguage:
    """Build a language with selected propose_atoms bodies PROMOTED (evaluator setup)."""
    lang = ExperimentLanguage()
    atoms = propose_atoms(prompt=prompt, question=True)
    by_key = {a.key(): a for a in atoms}
    for bk in body_keys:
        a = by_key.get(bk)
        if a is None:
            raise RuntimeError(f"missing body {bk}")
        lang.add_atom(a, grow=False)
        lang.promote(a, reason="stage4_evaluator_setup", evidence="OFFLINE_IR_OR_OBS")
    return lang


__all__ = [
    "offline_ir_path",
    "offline_ir_control_a",
    "offline_ir_control_b",
    "language_with_promoted",
]
