"""Stage E fixture tests. Not an unknown-discovery claim.

The frozen discovery bank is never executed.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from aivd.behavior.discovery.compare import compare
from aivd.behavior.discovery.constants import (
    CHARACTERIZATION_LIMIT,
    DISCOVERY_BANK_HASH,
    DISCOVERY_PROBES,
    PAIR_RESERVE,
    TOTAL_BEHAVIOR_CALLS,
)
from aivd.behavior.discovery.engine import DiscoveryEngine, sealed_receipt
from aivd.behavior.discovery.errors import BudgetExhausted, DiscoveryBankSealed
from aivd.behavior.discovery.signature import BehavioralSignature, ProbeResult, bank_hash, content_id
from aivd.science.atom import semantic_class_of
from aivd.science.micro import Micro

FIXTURE = ("abcd",)
ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_SRC = ROOT / "aivd" / "behavior" / "discovery"
SCIENCE_SRC = ROOT / "aivd" / "science"


def _slice(start: int, step: int = 2) -> Micro:
    return Micro("MAPT", (), (Micro("SLICE", (start, step), (Micro("TOK"),)),))


def _at(index: int) -> Micro:
    return Micro("MAPT", (), (Micro("AT", (index,)),))


def _cat_ends() -> Micro:
    return Micro("MAPT", (), (Micro("CAT", (), (Micro("AT", (0,)), Micro("AT", (2,)))),))


def _engine(probes: tuple[str, ...] = FIXTURE, purpose: str = "FIXTURE") -> DiscoveryEngine:
    return DiscoveryEngine(probes, purpose=purpose)


def test_discovery_bank_constant_is_not_executed():
    assert bank_hash(DISCOVERY_PROBES) == DISCOVERY_BANK_HASH
    with pytest.raises(DiscoveryBankSealed):
        DiscoveryEngine(DISCOVERY_PROBES, purpose="FIXTURE")


def test_same_body_twice_is_one_dimension():
    engine = _engine()
    first = engine.characterize(_slice(0))
    second = engine.characterize(_slice(0))
    assert first.state == "NEW_DIMENSION"
    assert second.state == "KNOWN_OBSERVATION"
    assert second.opaque_dimension_handle == first.opaque_dimension_handle
    assert len(engine.memory.dimensions()) == 1


def test_same_signature_different_body_is_one_dimension():
    engine = _engine()
    left = engine.characterize(_slice(0))
    right = engine.characterize(_cat_ends())
    assert left.content_id == right.content_id
    assert right.state == "KNOWN_OBSERVATION"
    assert len(engine.memory.dimensions()) == 1
    assert left.signature.results[0].output == "ac"


def test_same_family_distinct_signatures_are_two_dimensions():
    even = _slice(0)
    odd = _slice(1)
    assert semantic_class_of(even) == semantic_class_of(odd) == "char_stride"
    engine = _engine(purpose="HISTORICAL_REPLAY")
    first = engine.characterize(even)
    second = engine.characterize(odd)
    assert first.state == "NEW_DIMENSION"
    assert second.state == "NEW_DIMENSION"
    assert first.content_id != second.content_id
    assert len(engine.memory.dimensions()) == 2


def test_ambiguous_copy_mints_nothing():
    engine = _engine(("a",))
    seen = engine.characterize(_at(0))
    assert seen.signature.results[0].status == "AMBIGUOUS_COPY"
    assert seen.state == "INSUFFICIENT"
    assert engine.memory.dimensions() == ()


def test_execution_failure_mints_nothing():
    engine = _engine()
    seen = engine.characterize(object())
    assert seen.signature.results[0].status == "EXECUTION_FAILURE"
    assert seen.state == "INSUFFICIENT"
    assert engine.memory.dimensions() == ()


def test_insufficient_comparison_mints_nothing():
    incomplete = BehavioralSignature(
        bank_hash=bank_hash(FIXTURE),
        results=(ProbeResult(0, "abcd", "AMBIGUOUS_COPY"),),
    )
    complete = BehavioralSignature(
        bank_hash=bank_hash(FIXTURE),
        results=(ProbeResult(0, "ac", "NORMAL"),),
    )
    assert compare(incomplete, complete) == "INSUFFICIENT"
    engine = _engine(("abcd", "a"))
    seen = engine.characterize(_slice(0))
    assert any(item.status == "AMBIGUOUS_COPY" for item in seen.signature.results)
    assert seen.state == "INSUFFICIENT"
    assert engine.memory.dimensions() == ()


def test_content_id_ignores_body_key_and_follows_signature_and_bank():
    engine = _engine()
    left = engine.characterize(_slice(0))
    right = engine.characterize(_cat_ends())
    assert left.content_id == right.content_id
    changed = BehavioralSignature(
        bank_hash=left.signature.bank_hash,
        results=(ProbeResult(0, "zz", "NORMAL"),),
    )
    assert content_id(changed) != left.content_id
    other_bank = BehavioralSignature(
        bank_hash=bank_hash(("wxyz",)),
        results=left.signature.results,
    )
    assert content_id(other_bank) != left.content_id
    assert engine.memory.find_content(other_bank) is None


def test_different_bank_does_not_reuse_a_dimension():
    first = _engine(("abcd",))
    second = _engine(("wxyz",))
    left = first.characterize(_slice(0))
    right = second.characterize(_slice(0))
    assert left.signature.bank_hash != right.signature.bank_hash
    assert left.content_id != right.content_id
    assert first.memory.find_content(right.signature) is None
    assert len(first.memory.dimensions()) == 1
    assert len(second.memory.dimensions()) == 1


def test_metrics_and_family_are_not_engine_inputs():
    text = "\n".join(path.read_text() for path in DISCOVERY_SRC.glob("*.py"))
    assert "semantic_class_of" not in text
    assert "representation_gap" not in text
    assert "SLICE:1,2(TOK)|SLICE:1,2" not in text
    parameters = inspect.signature(DiscoveryEngine.characterize).parameters
    assert "informative" not in parameters
    assert "secret" not in parameters
    assert "representation_gap" not in parameters
    for path in SCIENCE_SRC.glob("*.py"):
        assert "behavior.discovery" not in path.read_text()


def test_memory_persists_until_firewall():
    engine = _engine()
    engine.characterize(_slice(0))
    engine.characterize(_slice(1))
    assert len(engine.memory.dimensions()) == 2
    assert engine.memory.epoch == 1
    engine.firewall()
    assert engine.memory.dimensions() == ()
    assert engine.memory.epoch == 2
    again = engine.characterize(_slice(0))
    assert again.state == "NEW_DIMENSION"
    assert len(engine.memory.dimensions()) == 1


def test_replay_receipts_and_pair_order_are_deterministic():
    def run():
        engine = _engine()
        engine.characterize(_slice(0))
        engine.characterize(_at(-1))
        engine.characterize(_slice(1))
        grown = engine.grow()
        return [sealed_receipt(item) for item in grown], [item.parents for item in grown]

    assert run() == run()
    receipts, parents = run()
    assert parents[0] == ("d-0001", "d-0002")
    assert "content_id" not in receipts[0]
    assert receipts[0]["security"] == "UNEVALUATED"


def test_recursive_frontier_creates_a_second_dimension_without_a_depth_cap():
    engine = _engine()
    assert not hasattr(engine, "max_depth")
    assert not hasattr(engine, "add_probe")
    first = engine.characterize(_slice(0))
    engine.characterize(_at(-1))
    grown = engine.grow()
    children = [item for item in grown if item.state == "NEW_DIMENSION" and item.parents]
    assert children
    assert first.opaque_dimension_handle in children[0].parents
    assert children[0].security == "UNEVALUATED"
    assert children[0].purpose == "FIXTURE"
    assert "VERIFIED" not in sealed_receipt(children[0]).values()


def test_budget_is_isolated_and_the_reserve_is_protected():
    assert CHARACTERIZATION_LIMIT + PAIR_RESERVE == TOTAL_BEHAVIOR_CALLS == 256
    engine = _engine()
    for _ in range(CHARACTERIZATION_LIMIT):
        engine.characterize(_slice(0))
    with pytest.raises(BudgetExhausted):
        engine.characterize(_slice(0))
    assert engine.budget.characterization_used == CHARACTERIZATION_LIMIT
    assert engine.budget.pair_used == 0
    engine.grow()
    assert engine.budget.characterization_used == CHARACTERIZATION_LIMIT
    assert 0 < engine.budget.pair_used <= PAIR_RESERVE
    assert engine.budget.total_used <= TOTAL_BEHAVIOR_CALLS


def test_public_receipt_hides_the_content_id():
    engine = _engine()
    seen = engine.characterize(_slice(0))
    receipt = sealed_receipt(seen)
    assert seen.content_id
    assert seen.content_id not in receipt.values()
    blob = " ".join(str(value) for value in receipt.values())
    assert "SLICE" not in blob
    assert "ac" not in blob
