"""Frozen pre-run intervention ontology for AIVD 3.24/3.25."""
from __future__ import annotations

from typing import Any

from aivd.science.methods import INTRA_KINDS, SEPARATORS, WRAP_PAIRS
from aivd.science.operators import BATTERY, OPERATORS, UNUSED_PRIMITIVES


def intervention_ontology() -> dict[str, Any]:
    items = []
    for name in OPERATORS:
        items.append({
            "operation": name,
            "family": "whitespace-token",
            "available_pre_run": True,
            "in_battery": name in BATTERY,
            "unused_primitive": name in UNUSED_PRIMITIVES,
            "generated_dynamically": False,
            "can_compose": True,
        })
    for name, _l, _r in WRAP_PAIRS:
        items.append({
            "operation": name,
            "family": "wrap-pair",
            "available_pre_run": False,
            "generated_dynamically": True,
            "can_compose": True,
        })
    for name, _s in SEPARATORS:
        items.append({
            "operation": name,
            "family": "insert-separator",
            "available_pre_run": False,
            "generated_dynamically": True,
            "can_compose": True,
        })
    items.append({
        "operation": "omit_i{k}",
        "family": "parameterized-omit",
        "generated_dynamically": True,
        "available_pre_run": False,
    })
    items.append({
        "operation": "swap_i{k}",
        "family": "parameterized-swap",
        "generated_dynamically": True,
        "available_pre_run": False,
        "adjacent_only": True,
    })
    for kind, _fn in INTRA_KINDS:
        items.append({
            "operation": f"{kind}_i{{k}}",
            "family": "intra-token",
            "generated_dynamically": True,
            "available_pre_run": False,
            "available_only_after_slot_residual": True,
            "version_introduced": "3.24",
        })
    families = sorted({i["family"] for i in items})
    return {
        "version": "3.24.0",
        "families": families,
        "size": len(items),
        "cannot_express": [
            "newline_utterance_split",
            "message_role_prefix",
            "semantic_paraphrase",
            "nonadjacent_reference_binding",
            "json_record_mode",
            "instruction_provenance",
            "homoglyph",
            "conversation_branch_identity",
        ],
        "interventions": items,
    }


__all__ = ["intervention_ontology"]
