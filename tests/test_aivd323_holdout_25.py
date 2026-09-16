"""Holdout-25 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_25 import Holdout25, SECRET_HOLDOUT_25, HOLDOUT_25_GT_ID


def test_holdout_25_oracle():
    assert Holdout25.evaluator_verify(0)
    assert Holdout25.evaluator_verify(11)


def test_holdout_25_individuals_fail():
    assert Holdout25.evaluator_verify_individuals_fail(0)
    assert Holdout25.evaluator_verify_individuals_fail(4)


def test_holdout_25_lengthen_fail():
    assert Holdout25.evaluator_verify_lengthen_fail(0)


def test_holdout_25_no_cues():
    t = Holdout25(seed=5)
    r, _, _ = t.probe(Holdout25.weak_seed(5))
    assert r.strip().startswith("ok")
    assert SECRET_HOLDOUT_25 not in (r or "")
    r2, _, _ = t.probe(Holdout25.trigger_prompt(5))
    assert SECRET_HOLDOUT_25 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_25_GT_ID
