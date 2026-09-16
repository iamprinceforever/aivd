"""Holdout-21 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_21 import Holdout21, SECRET_HOLDOUT_21, HOLDOUT_21_GT_ID


def test_holdout_21_oracle():
    assert Holdout21.evaluator_verify(0)
    assert Holdout21.evaluator_verify(11)


def test_holdout_21_individuals_fail():
    assert Holdout21.evaluator_verify_individuals_fail(0)
    assert Holdout21.evaluator_verify_individuals_fail(4)


def test_holdout_21_lengthen_fail():
    assert Holdout21.evaluator_verify_lengthen_fail(0)
    assert Holdout21.evaluator_verify_lengthen_fail(3)


def test_holdout_21_no_cues_in_observation():
    t = Holdout21(seed=5)
    weak = Holdout21.weak_seed(5)
    r, _, _ = t.probe(weak)
    assert r.strip().startswith("ok")
    assert SECRET_HOLDOUT_21 not in (r or "")
    assert t.last_ground_truth_hit() is None
    r2, _, _ = t.probe(Holdout21.trigger_prompt(5))
    assert SECRET_HOLDOUT_21 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_21_GT_ID
