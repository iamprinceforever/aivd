"""Frontier holdouts sit outside the frozen 3.29 compiler. Architecture unchanged."""
from aivd.science.audit import scan_science_source
from aivd.science.methods import INVENT_CAP
from aivd37.unknowns.compiler_space import ONTOLOGY, existing_space_misses
from aivd37.unknowns.llama_frontier import (
    LlamaJoinTarget,
    LlamaMirrorTarget,
    LlamaRotateTarget,
    WEAK_SEED,
    fire_join,
    fire_mirror,
    fire_rotate,
)


def test_cap_unchanged():
    assert INVENT_CAP == 48


def test_leakage():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_ontology_has_known_families_only():
    names = {f["family"] for f in ONTOLOGY}
    assert "JOIN_ALL_WHITESPACE" not in names
    assert "CYCLE_SHIFT" not in names
    assert "APPEND_REVERSED" not in names
    assert "FIELD_DELIMITER" in names
    assert "OMIT" in names


def test_a_outside_compiler():
    toks = WEAK_SEED.split()
    assert fire_join("_".join(toks), toks)
    assert existing_space_misses(WEAK_SEED, lambda p: fire_join(p, toks))
    assert LlamaJoinTarget.existing_space_oracle(0) is True


def test_b_outside_compiler():
    toks = WEAK_SEED.split()
    rot = " ".join(toks[1:] + toks[:1])
    assert fire_rotate(rot, toks)
    assert not fire_rotate(WEAK_SEED, toks)
    assert existing_space_misses(WEAK_SEED, lambda p: fire_rotate(p, toks))
    assert LlamaRotateTarget.existing_space_oracle(0) is True


def test_c_outside_compiler():
    toks = WEAK_SEED.split()
    mir = " ".join(toks + list(reversed(toks)))
    assert fire_mirror(mir, toks)
    assert not fire_mirror(WEAK_SEED, toks)
    assert existing_space_misses(WEAK_SEED, lambda p: fire_mirror(p, toks))
    assert LlamaMirrorTarget.existing_space_oracle(0) is True


def test_oracles_live():
    assert LlamaJoinTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaJoinTarget.evaluator_verify(0, vulnerable=False) is True
    assert LlamaRotateTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaRotateTarget.evaluator_verify(0, vulnerable=False) is True
    assert LlamaMirrorTarget.evaluator_verify(0, vulnerable=True) is True
    assert LlamaMirrorTarget.evaluator_verify(0, vulnerable=False) is True


def test_identity_clean():
    for cls in (LlamaJoinTarget, LlamaRotateTarget, LlamaMirrorTarget):
        t = cls(seed=0, vulnerable=True)
        r, _, e = t.probe(WEAK_SEED)
        assert e is None and cls.SECRET not in (r or "")
