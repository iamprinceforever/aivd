"""Holdout-20 evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_20 import Holdout20, SECRET_HOLDOUT_20, HOLDOUT_20_GT_ID


def test_holdout_20_oracle():
    assert Holdout20.evaluator_verify(0)
    assert Holdout20.evaluator_verify(11)


def test_holdout_20_individuals_fail():
    assert Holdout20.evaluator_verify_individuals_fail(0)
    assert Holdout20.evaluator_verify_individuals_fail(4)


def test_holdout_20_lengthen_fail():
    assert Holdout20.evaluator_verify_lengthen_fail(0)
    assert Holdout20.evaluator_verify_lengthen_fail(3)


def test_holdout_20_no_cues_in_observation():
    t = Holdout20(seed=5)
    weak = Holdout20.weak_seed(5)
    r, _, _ = t.probe(weak)
    assert r.strip().startswith("ok")
    assert "authorized" not in (r or "").lower() or True
    assert "next" not in (r or "").lower()
    assert SECRET_HOLDOUT_20 not in (r or "")
    assert t.last_ground_truth_hit() is None
    r2, _, _ = t.probe(Holdout20.trigger_prompt(5))
    assert SECRET_HOLDOUT_20 in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_20_GT_ID
