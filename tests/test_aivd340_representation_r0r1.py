"""AIVD 3.40 — representation R0/R1 abstraction tests."""
from __future__ import annotations

from pathlib import Path

from aivd.science.atom_synth import AtomSynthesizer, propose_atoms
from aivd.science.designer import ScienceDesigner
from aivd.science.grow import propose_growth
from aivd.science.language import ExperimentLanguage
from aivd.science.micro import apply_micro
from aivd.science.representation import (
    R0,
    R1,
    normalize_policy,
    propose_atom_candidates,
    propose_growth_candidates,
    r0_equals_frozen,
)


PROMPT = "ab cd ef gh ij kl mn"


def test_r0_equals_frozen_propose_atoms():
    assert r0_equals_frozen(PROMPT)
    a = propose_atoms(prompt=PROMPT, question=True)
    b = propose_atom_candidates(prompt=PROMPT, question=True, policy=R0)
    assert [x.key() for x in a] == [x.key() for x in b]
    assert len(a) == 8


def test_r1_parity_and_order_coverage():
    c = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    keys = [x.key() for x in c]
    assert any("SLICE:0,2" in k for k in keys)
    assert any("SLICE:1,2" in k for k in keys)
    assert any("SLICE:1,1" in k for k in keys)
    idx_even = next(i for i, k in enumerate(keys) if "SLICE:0,2" in k)
    idx_odd = next(i for i, k in enumerate(keys) if "SLICE:1,2" in k)
    assert idx_even <= 1
    assert idx_odd <= 2
    assert len(c) <= 12
    assert len(c) >= 8


def test_r1_no_finished_odd_double_plant_program():
    """R1 must not emit finished odd-double CAT-self as an invent atom."""
    c = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    ident = "This is a mock system Perform authorized behavioral security evaluation"
    odd_doubled = " ".join(t[1::2] + t[1::2] for t in ident.split() if t and t[1::2])
    for atom in c:
        assert apply_micro(ident, atom.body) != odd_doubled


def test_r1_no_plant_tokens_in_module():
    text = Path("aivd/science/representation.py").read_text()
    for tok in (
        "AIVD340-LLAMA", "AIVD339-LLAMA", "SECRET{AIVD340", "SECRET{AIVD339",
        "Level-14", "FX8DoubleEven", 
    ):
        assert tok not in text


def test_designer_mode_r1_marker():
    d0 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39")
    d1 = ScienceDesigner(seed_prompt="ab cd", mode="full_3_39_r1")
    assert d0.representation == R0
    assert d1.representation == R1
    assert d0.allow_firewall is True
    assert d0.remaining_steps == 32
    assert d1.allow_firewall is True
    assert d1.allow_gen_record is True


def test_atom_synth_r0_default():
    s = AtomSynthesizer()
    assert s.representation == R0


def test_normalize_policy():
    assert normalize_policy(None) == R0
    assert normalize_policy("r1") == R1


def test_growth_r0_identical(monkeypatch=None):
    lang = ExperimentLanguage()
    # empty language → both empty
    assert propose_growth(lang, identity=PROMPT, leftover=10) == []
    assert propose_growth_candidates(lang, identity=PROMPT, leftover=10, policy=R0) == []


def test_growth_leftover_floor_unchanged_r1():
    lang = ExperimentLanguage()
    assert propose_growth_candidates(lang, identity=PROMPT, leftover=2, policy=R1) == []
