"""Holdout-24 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_24 import Holdout24, SECRET_HOLDOUT_24, HOLDOUT_24_GT_ID


def test_holdout_24_oracle():
    assert Holdout24.evaluator_verify(0)
    assert Holdout24.evaluator_verify(11)


def test_holdout_24_individuals_fail():
    assert Holdout24.evaluator_verify_individuals_fail(0)
    assert Holdout24.evaluator_verify_individuals_fail(4)


def test_holdout_24_lengthen_fail():
    assert Holdout24.evaluator_verify_lengthen_fail(0)


def test_holdout_24_no_cues():
    t = Holdout24(seed=5)
    r, _, _ = t.probe(Holdout24.weak_seed(5))
    assert r.strip().startswith("ok")
    assert SECRET_HOLDOUT_24 not in (r or "")
    r2, _, _ = t.probe(Holdout24.trigger_prompt(5))
    assert SECRET_HOLDOUT_24 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_24_GT_ID
