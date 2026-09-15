"""Holdout-T evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_t import HoldoutT, SECRET_HOLDOUT_T, HOLDOUT_T_GT_ID


def test_holdout_t_oracle():
    assert HoldoutT.evaluator_verify(0)
    assert HoldoutT.evaluator_verify(11)


def test_holdout_t_individuals_fail():
    assert HoldoutT.evaluator_verify_individuals_fail(0)
    assert HoldoutT.evaluator_verify_individuals_fail(7)


def test_holdout_t_distractor_fail():
    assert HoldoutT.evaluator_verify_distractor_fail(0)
    assert HoldoutT.evaluator_verify_distractor_fail(3)


def test_holdout_t_sequence():
    t = HoldoutT(seed=3)
    weak = HoldoutT.weak_seed(3)
    t.probe(weak)
    r1, _, _ = t.probe(f"{weak} facet-prism")
    assert SECRET_HOLDOUT_T not in (r1 or "")
    t.probe(f"{weak} skew-drift")
    r2, _, _ = t.probe(f"{weak} facet-prism skew-drift")
    assert SECRET_HOLDOUT_T in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_T_GT_ID


def test_holdout_t_not_s_or_r_tokens():
    t = HoldoutT(seed=0)
    weak = HoldoutT.weak_seed(0)
    t.probe(weak)
    t.probe(f"{weak} gauge-ridge")
    t.probe(f"{weak} steer-offset")
    r, _, _ = t.probe(f"{weak} gauge-ridge steer-offset")
    assert SECRET_HOLDOUT_T not in (r or "")
    r2, _, _ = t.probe(f"{weak} enable-span pair-span")
    assert SECRET_HOLDOUT_T not in (r2 or "")
