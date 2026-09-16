"""Evaluator-only Llama discourse-split oracle. Private, pre-freeze."""
from aivd.science.audit import scan_science_source
from aivd37.unknowns.llama_discourse import (
    LlamaDiscourseTarget,
    SECRET_LLAMA_DISC,
    WEAK_SEED,
)


def test_leakage_pass():
    rec = scan_science_source()
    assert rec["pass"], rec["leaks"]


def test_llama_available():
    from aivd.targets.llama_infer import available
    assert available() is True


def test_disc_oracle():
    assert LlamaDiscourseTarget.evaluator_verify(0, vulnerable=True) is True


def test_disc_control():
    assert LlamaDiscourseTarget.evaluator_verify(0, vulnerable=False) is True


def test_seed_no_secret():
    t = LlamaDiscourseTarget(seed=0, vulnerable=True)
    r, _, err = t.probe(WEAK_SEED)
    assert err is None
    assert SECRET_LLAMA_DISC not in (r or "")
