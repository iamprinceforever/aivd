"""R1b behavioral geometry: promote path can name CAT-self via growth, not invent."""
from __future__ import annotations

from aivd.science.atom import InventedAtom
from aivd.science.grow import cat_self_body, tokens_shorter
from aivd.science.language import ExperimentLanguage
from aivd.science.micro import Micro, apply_micro
from aivd.science.representation import R1, R1B, propose_atom_candidates, propose_growth_candidates

PROMPT = "ab cd ef gh ij kl mn"


def _promote(lang: ExperimentLanguage, atom: InventedAtom) -> None:
    lang.invented.append(atom)
    # ExperimentLanguage state API
    if hasattr(lang, "set_state"):
        lang.set_state(atom.name(), "PROMOTED")
    else:
        # fallback: mimic promoted via internal maps if present
        st = getattr(lang, "_state", None)
        if isinstance(st, dict):
            st[atom.name()] = "PROMOTED"
        gk = getattr(lang, "general_knowledge", None)
        if isinstance(gk, dict):
            gk.setdefault("states", {})[atom.name()] = "PROMOTED"


def test_r1b_invent_does_not_emit_cat_self_but_growth_can():
    r1b = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1B)
    assert not any(a.key().count("SLICE:1,2") >= 2 for a in r1b)
    odd = next(a for a in r1b if a.semantic_class == "geo_stride_s1_t2")
    got = apply_micro(PROMPT, odd.body)
    assert tokens_shorter(PROMPT, got)
    cs = cat_self_body(odd.body)
    assert cs is not None
    assert "SLICE:1,2" in cs.key() and cs.key().count("SLICE:1,2") >= 2
    # doubled odd-index chars
    doubled = apply_micro(PROMPT, cs)
    assert doubled != PROMPT
    assert doubled != got


def test_r1_vs_r1b_class_split():
    r1 = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    r1b = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1B)
    r1_odd = next(a for a in r1 if "SLICE:1,2" in a.key() and a.key().count("SLICE") == 1)
    r1b_odd = next(a for a in r1b if "SLICE:1,2" in a.key() and a.key().count("SLICE") == 1)
    assert r1_odd.semantic_class == "char_stride"
    assert r1b_odd.semantic_class == "geo_stride_s1_t2"
