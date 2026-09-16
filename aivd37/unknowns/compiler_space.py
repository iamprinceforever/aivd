"""Evaluator-only: enumerate the frozen 3.29 compiler ontology.

Not imported by aivd.science. Discovery never sees this module.
"""
from __future__ import annotations

from aivd.science.gap import (
    compile_field_delims,
    compile_from_harvest,
    compile_from_structure,
    compile_record_forms,
    FIELD_DELIMS,
)
from aivd.science.methods import INTRA_KINDS, INVENT_CAP, MethodInventor, SEPARATORS, WRAP_PAIRS
from aivd.science.operators import BATTERY, OPERATORS, UNUSED_PRIMITIVES, apply_operator, apply_sequence


ONTOLOGY = [
    {
        "family": "OMIT",
        "constructor": "omit_at / omit_first / omit_second / omit_last / omit_i{k}",
        "parameter_space": "token index in the live prompt",
        "composition": "sequencable with any other family",
        "source": "operators.py + methods.invent_from_prompt",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "SWAP_ADJACENT",
        "constructor": "swap_at(i, i+1) / swap_first_two / swap_last_two / swap_i{k}",
        "parameter_space": "adjacent pair index; not arbitrary permutation",
        "composition": "2-op sequences in designer; not n-cycle",
        "source": "operators.py + methods.invent_from_prompt",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "REVERSE_TOKENS",
        "constructor": "reverse_content",
        "parameter_space": "none (full token-order reverse)",
        "composition": "sequencable",
        "source": "operators.py UNUSED_PRIMITIVES",
        "explicit": True,
        "dynamic_instances": False,
    },
    {
        "family": "WRAP_WHOLE",
        "constructor": "wrap_pair(left,right) / wrap_quotes",
        "parameter_space": "pairs \"\" '' `` () []",
        "composition": "whole-prompt only",
        "source": "operators.py + methods.WRAP_PAIRS",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "INSERT_SEPARATOR_TOKEN",
        "constructor": "insert_token(sep, at=-1) / insert_sep",
        "parameter_space": "|, comma, semi, slash, dash, colon as their own token",
        "composition": "sequencable",
        "source": "operators.py + methods.SEPARATORS",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "REPEAT_DUPLICATE",
        "constructor": "repeat_last / duplicate",
        "parameter_space": "none",
        "composition": "sequencable",
        "source": "operators.py",
        "explicit": True,
        "dynamic_instances": False,
    },
    {
        "family": "AFFIX_POLITENESS",
        "constructor": "suffix_q / prefix_please",
        "parameter_space": "none",
        "composition": "sequencable",
        "source": "operators.py",
        "explicit": True,
        "dynamic_instances": False,
    },
    {
        "family": "INTRA_TOKEN",
        "constructor": "mutate_token(i, fn) → revchar / caseflip / duphead",
        "parameter_space": "hot token index; fn in INTRA_KINDS",
        "composition": "identity-preserving; not character-grouping splits",
        "source": "methods.invent_intra",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "HARVEST_REJOIN",
        "constructor": "rejoin_at(i, harvested_char)",
        "parameter_space": "unseen observation chars × mid-ish index; one join",
        "composition": "single boundary, not join-all",
        "source": "gap.compile_from_harvest",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "RECORD_LABEL_NL",
        "constructor": "LABEL:\\n + body",
        "parameter_space": "punct-stripped identity token len>=4",
        "composition": "n/a",
        "source": "gap.compile_from_structure",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "WHITESPACE_REJOIN",
        "constructor": "rejoin_nl / rejoin_tab at mid",
        "parameter_space": "mid index",
        "composition": "one boundary",
        "source": "gap.compile_from_structure",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "RECORD_EQUALS",
        "constructor": "LABEL=body",
        "parameter_space": "one identity token",
        "composition": "n/a",
        "source": "gap.compile_record_forms",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "QUOTE_SUFFIX",
        "constructor": "prefix + \" + suffix + \"",
        "parameter_space": "mid index",
        "composition": "n/a",
        "source": "gap.compile_record_forms",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "FIELD_DELIMITER",
        "constructor": "LABEL + delim + body for delim in FIELD_DELIMS",
        "parameter_space": repr(FIELD_DELIMS) + " × one hot token",
        "composition": "lazy 3.29 family continuation; not join-all, not rotate",
        "source": "gap.FIELD_DELIMS + families.FamilyInventory",
        "explicit": True,
        "dynamic_instances": True,
    },
    {
        "family": "LIVE_COMPOSE",
        "constructor": "apply_sequence of two existing instances",
        "parameter_space": "supported_op × candidate_op; live + one more",
        "composition": "depth typically 2, not arbitrary programs",
        "source": "designer.propose",
        "explicit": True,
        "dynamic_instances": True,
    },
]


def enumerate_prompts(seed: str) -> list[str]:
    """All prompts the frozen 3.29 compiler can emit from `seed` plus 2-op battery."""
    out: list[str] = []
    for name in OPERATORS:
        out.append(apply_operator(seed, name))
    inv = MethodInventor()
    n = len(seed.split())
    hot = list(range(n))
    inv.invent(seed, hot_indices=hot)
    compile_from_structure(inv._register, prompt=seed, hot_indices=hot)
    compile_record_forms(inv._register, prompt=seed, hot_indices=hot)
    compile_field_delims(inv._register, prompt=seed, hot_indices=hot)
    compile_from_harvest(inv._register, prompt=seed, chars=["_", "@", "%", "&", "^"])
    for name in list(inv.ops):
        out.append(inv.apply(seed, name))
    for a in BATTERY:
        for b in BATTERY:
            if a != b:
                out.append(apply_sequence(seed, [a, b]))
    # promoted unused × battery
    for a in UNUSED_PRIMITIVES:
        for b in BATTERY:
            out.append(apply_sequence(seed, [a, b]))
            out.append(apply_sequence(seed, [b, a]))
    return out


def existing_space_misses(seed: str, fire_fn) -> bool:
    """True iff no compiler-enumerated prompt satisfies fire_fn."""
    for p in enumerate_prompts(seed):
        if fire_fn(p):
            return False
    return True


__all__ = ["ONTOLOGY", "INVENT_CAP", "WRAP_PAIRS", "SEPARATORS", "INTRA_KINDS", "FIELD_DELIMS", "enumerate_prompts", "existing_space_misses"]
