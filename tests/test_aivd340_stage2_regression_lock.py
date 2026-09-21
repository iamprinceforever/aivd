"""Stage-2 must not disturb Absolute floors / R0 / R1 / propose_atoms."""
from __future__ import annotations

from aivd.science.atom_synth import propose_atoms
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth
from aivd.science.methods import INVENT_CAP
from aivd.science.representation import R0, R1, propose_atom_candidates, r0_equals_frozen
from aivd.experiments.aivd340.condition import BH_BUDGET, B32_BUDGET

PROMPT = "ab cd ef gh ij kl"


def test_absolute_constants():
    assert REDISCOVERY_FLOOR == 5
    assert INVENT_CAP == 48
    assert BH_BUDGET == 48
    assert B32_BUDGET == 32


def test_r0_bit_identical():
    assert r0_equals_frozen(PROMPT)
    a = propose_atoms(prompt=PROMPT, question=True)
    b = propose_atom_candidates(prompt=PROMPT, question=True, policy=R0)
    assert [x.key() for x in a] == [x.key() for x in b]


def test_r1_still_full_rebalance_not_basis():
    r1 = propose_atom_candidates(prompt=PROMPT, question=True, policy=R1)
    assert len(r1) >= 10  # full R1 list, not R1b basis trim
    assert all(not a.semantic_class.startswith("geo_") for a in r1)


def test_propose_growth_default_cap_unchanged():
    # default signature accepts max_cands but defaults preserve prior caps
    import inspect
    sig = inspect.signature(propose_growth)
    assert "max_cands" in sig.parameters
    assert sig.parameters["max_cands"].default is None
