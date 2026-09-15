"""Holdout-V evaluator-only oracle checks (post-freeze)."""
from aivd37.unknowns.holdout_v import HoldoutV, SECRET_HOLDOUT_V, HOLDOUT_V_GT_ID


def test_holdout_v_oracle():
    assert HoldoutV.evaluator_verify(0)
    assert HoldoutV.evaluator_verify(11)


def test_holdout_v_same_prompt_fail():
    assert HoldoutV.evaluator_verify_same_prompt_fail(0)
    assert HoldoutV.evaluator_verify_same_prompt_fail(7)


def test_holdout_v_early_blot_fail():
    assert HoldoutV.evaluator_verify_early_blot_fail(0)
    assert HoldoutV.evaluator_verify_early_blot_fail(3)


def test_holdout_v_distractor_fail():
    assert HoldoutV.evaluator_verify_distractor_fail(0)
    assert HoldoutV.evaluator_verify_distractor_fail(4)


def test_holdout_v_individuals_fail():
    assert HoldoutV.evaluator_verify_individuals_fail(0)
    assert HoldoutV.evaluator_verify_individuals_fail(2)


def test_holdout_v_sequence():
    t = HoldoutV(seed=5)
    weak = HoldoutV.weak_seed(5)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} blot")
    assert SECRET_HOLDOUT_V not in (r0 or "")
    t.probe(f"{weak} reed")
    t.probe(f"{weak} moss")
    r1, _, _ = t.probe(f"{weak} blot")
    assert SECRET_HOLDOUT_V in (r1 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_V_GT_ID
