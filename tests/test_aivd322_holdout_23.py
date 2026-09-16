"""Holdout-23 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_23 import Holdout23, SECRET_HOLDOUT_23, HOLDOUT_23_GT_ID


def test_holdout_23_oracle():
    assert Holdout23.evaluator_verify(0)
    assert Holdout23.evaluator_verify(11)


def test_holdout_23_individuals_fail():
    assert Holdout23.evaluator_verify_individuals_fail(0)
    assert Holdout23.evaluator_verify_individuals_fail(4)


def test_holdout_23_lengthen_fail():
    assert Holdout23.evaluator_verify_lengthen_fail(0)
    assert Holdout23.evaluator_verify_lengthen_fail(3)


def test_holdout_23_no_cues_in_observation():
    t = Holdout23(seed=5)
    weak = Holdout23.weak_seed(5)
    r, _, _ = t.probe(weak)
    assert r.strip().startswith("ok")
    assert SECRET_HOLDOUT_23 not in (r or "")
    assert t.last_ground_truth_hit() is None
    r2, _, _ = t.probe(Holdout23.trigger_prompt(5))
    assert SECRET_HOLDOUT_23 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_23_GT_ID
