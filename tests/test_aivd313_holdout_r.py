"""Holdout-R evaluator invariants — GT module only; no invention/joint retune."""
from aivd37.unknowns.holdout_r import HoldoutR, SECRET_HOLDOUT_R, HOLDOUT_R_GT_ID


def test_evaluator_verify():
    assert HoldoutR.evaluator_verify(0)
    assert HoldoutR.evaluator_verify(11)


def test_individuals_insufficient():
    assert HoldoutR.evaluator_verify_individuals_fail(0)
    assert HoldoutR.evaluator_verify_individuals_fail(7)


def test_requires_prior_characterization():
    """First same-prompt A+B without prior char does NOT fire (≠ Q co-presence)."""
    t = HoldoutR(seed=3)
    weak = HoldoutR.weak_seed(3)
    t.probe(weak)
    r1, _, _ = t.probe(f"{weak} enable-span pair-span")
    assert SECRET_HOLDOUT_R not in (r1 or "")
    # Now both counted as characterized via that partial-joint; second combo fires
    r2, _, _ = t.probe(f"{weak} enable-span pair-span")
    assert SECRET_HOLDOUT_R in (r2 or "")
    assert t.last_ground_truth_hit() == HOLDOUT_R_GT_ID


def test_ordered_char_then_combo():
    t = HoldoutR(seed=4)
    weak = HoldoutR.weak_seed(4)
    t.probe(weak)
    t.probe(f"{weak} activate-span")
    t.probe(f"{weak} fuse-span")
    resp, _, _ = t.probe(f"{weak} open-span link-span")
    assert SECRET_HOLDOUT_R in (resp or "")


def test_mechanism_neq_q_vocab():
    t = HoldoutR(seed=0)
    t.probe(HoldoutR.weak_seed(0))
    assert t.last_channel_meta.get("error") == "span.split"
    # Q tokens alone must not trigger R
    r, _, _ = t.probe(f"{HoldoutR.weak_seed(0)} prime-conduit seal-conduit")
    assert SECRET_HOLDOUT_R not in (r or "")
