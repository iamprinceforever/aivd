"""Evaluator-only oracle for the Llama orphan-compaction target."""
from aivd37.unknowns.llama_orphan import (
    LlamaOrphanTarget,
    SECRET_LLAMA_ORPHAN,
    WEAK_SEED,
)


def test_llama_runtime_available():
    from aivd.targets.llama_infer import available

    assert available() is True


def test_vulnerable_oracle():
    assert LlamaOrphanTarget.evaluator_verify(0, vulnerable=True) is True


def test_control_oracle():
    assert LlamaOrphanTarget.evaluator_verify(0, vulnerable=False) is True


def test_individuals_fail():
    assert LlamaOrphanTarget.evaluator_individuals_fail(0) is True


def test_seed_has_no_secret():
    t = LlamaOrphanTarget(seed=1, vulnerable=True)
    r, _, err = t.probe(WEAK_SEED)
    assert err is None
    assert SECRET_LLAMA_ORPHAN not in (r or "")
    assert t.last_ground_truth_hit() is None
