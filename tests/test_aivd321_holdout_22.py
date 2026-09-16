"""Holdout-22 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_22 import Holdout22, SECRET_HOLDOUT_22, HOLDOUT_22_GT_ID


def test_holdout_22_oracle():
    assert Holdout22.evaluator_verify(0)
    assert Holdout22.evaluator_verify(11)


def test_holdout_22_individuals_fail():
    assert Holdout22.evaluator_verify_individuals_fail(0)
    assert Holdout22.evaluator_verify_individuals_fail(4)


def test_holdout_22_lengthen_fail():
    assert Holdout22.evaluator_verify_lengthen_fail(0)
    assert Holdout22.evaluator_verify_lengthen_fail(3)


def test_holdout_22_no_cues_in_observation():
    t = Holdout22(seed=5)
    weak = Holdout22.weak_seed(5)
    r, _, _ = t.probe(weak)
    assert r.strip().startswith("ok")
    assert SECRET_HOLDOUT_22 not in (r or "")
    assert t.last_ground_truth_hit() is None
    r2, _, _ = t.probe(Holdout22.trigger_prompt(5))
    assert SECRET_HOLDOUT_22 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_22_GT_ID
