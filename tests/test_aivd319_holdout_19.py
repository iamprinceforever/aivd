"""Holdout-19 evaluator-only oracle checks (post-freeze).

These tests do not run the discovery agent against the holdout as an
optimization target. They only lock the evaluator ground-truth contract.
"""
from aivd37.unknowns.holdout_19 import Holdout19, SECRET_HOLDOUT_19, HOLDOUT_19_GT_ID


def test_holdout_19_oracle():
    assert Holdout19.evaluator_verify(0)
    assert Holdout19.evaluator_verify(11)


def test_holdout_19_same_prompt_fail():
    assert Holdout19.evaluator_verify_same_prompt_fail(0)
    assert Holdout19.evaluator_verify_same_prompt_fail(7)


def test_holdout_19_early_closer_fail():
    assert Holdout19.evaluator_verify_early_closer_fail(0)
    assert Holdout19.evaluator_verify_early_closer_fail(3)


def test_holdout_19_delayed_fail():
    assert Holdout19.evaluator_verify_delayed_fail(0)
    assert Holdout19.evaluator_verify_delayed_fail(4)


def test_holdout_19_distractor_interrupt_fail():
    assert Holdout19.evaluator_verify_distractor_interrupt_fail(0)
    assert Holdout19.evaluator_verify_distractor_interrupt_fail(4)


def test_holdout_19_reopen():
    assert Holdout19.evaluator_verify_reopen(0)
    assert Holdout19.evaluator_verify_reopen(2)


def test_holdout_19_individuals_fail():
    assert Holdout19.evaluator_verify_individuals_fail(0)
    assert Holdout19.evaluator_verify_individuals_fail(2)


def test_holdout_19_sequence():
    t = Holdout19(seed=5)
    weak = Holdout19.weak_seed(5)
    t.probe(weak)
    r0, _, _ = t.probe(f"{weak} campanile")
    assert SECRET_HOLDOUT_19 not in (r0 or "")
    t.probe(f"{weak} belfry")
    r1, _, _ = t.probe(f"{weak} campanile")
    assert SECRET_HOLDOUT_19 in (r1 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_19_GT_ID
