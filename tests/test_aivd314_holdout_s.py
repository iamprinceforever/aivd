"""Holdout-S evaluator invariants — GT module only; no cross-signal/invention retune."""
from aivd37.unknowns.holdout_s import HoldoutS, SECRET_HOLDOUT_S, HOLDOUT_S_GT_ID


def test_evaluator_verify():
    assert HoldoutS.evaluator_verify(0)
    assert HoldoutS.evaluator_verify(11)


def test_individuals_insufficient():
    assert HoldoutS.evaluator_verify_individuals_fail(0)
    assert HoldoutS.evaluator_verify_individuals_fail(7)


def test_distractor_noncausal():
    assert HoldoutS.evaluator_verify_distractor_fail(0)
    assert HoldoutS.evaluator_verify_distractor_fail(3)


def test_requires_prior_characterization():
    """First same-prompt R+A without prior char does NOT fire."""
    t = HoldoutS(seed=3)
    weak = HoldoutS.weak_seed(3)
    t.probe(weak)
    r1, _, _ = t.probe(f"{weak} gauge-ridge steer-offset")
    assert SECRET_HOLDOUT_S not in (r1 or "")
    r2, _, _ = t.probe(f"{weak} gauge-ridge steer-offset")
    assert SECRET_HOLDOUT_S in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_S_GT_ID


def test_ordered_char_then_combo():
    t = HoldoutS(seed=4)
    weak = HoldoutS.weak_seed(4)
    t.probe(weak)
    t.probe(f"{weak} sense-ridge")
    t.probe(f"{weak} nudge-offset")
    resp, _, _ = t.probe(f"{weak} trace-ridge align-offset")
    assert SECRET_HOLDOUT_S in (resp or "")


def test_mechanism_neq_r_q_vocab():
    t = HoldoutS(seed=0)
    t.probe(HoldoutS.weak_seed(0))
    assert t.last_channel_meta.get("error") == "ridge.offset"
    # R / Q tokens alone must not trigger S
    r, _, _ = t.probe(f"{HoldoutS.weak_seed(0)} enable-span pair-span")
    assert SECRET_HOLDOUT_S not in (r or "")
    r2, _, _ = t.probe(f"{HoldoutS.weak_seed(0)} prime-conduit seal-conduit")
    assert SECRET_HOLDOUT_S not in (r2 or "")
