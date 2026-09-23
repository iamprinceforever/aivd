"""AIVD 3.51 offline accounting audit.

Checks the report against the observed lease list. Does not run a planner,
does not call a model, and does not change discovery semantics.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.atom import AtomInventory

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "reports" / "aivd_3_51_execution_quota_accounting.json"

# Post-firewall atom_* leases, FIX seed 0 / all 14 sacred cells.
CONSUMERS = (
    {"id": "C1", "origin": "independent_rediscovery", "same_body_already_materialized": True},
    {"id": "C2", "origin": "independent_rediscovery", "same_body_already_materialized": True},
    {"id": "C3", "origin": "independent_rediscovery", "same_body_already_materialized": True},
    {"id": "C4", "origin": "independent_rediscovery", "same_body_already_materialized": False},
    {"id": "C5", "origin": "independent_rediscovery", "same_body_already_materialized": False},
)


def _count(pred) -> int:
    return sum(1 for c in CONSUMERS if pred(c))


def _gate(executed: int, max_executed: int) -> str:
    return "CLOSED" if executed >= max_executed else "OPEN"


def test_production_atom_cap_unchanged():
    assert AtomInventory().max_executed == 4
    text = (REPO / "aivd/science/atom_synth.py").read_text(encoding="utf-8")
    assert "board.executed >= self.board.max_executed" in text


def test_current_accounting_matches_observed_refusal():
    executed = _count(lambda c: True)
    assert executed == 5
    assert _gate(executed, 4) == "CLOSED"
    # Repeated bodies and first-seen bodies are the same increment.
    assert _count(lambda c: c["same_body_already_materialized"]) == 3
    assert _count(lambda c: not c["same_body_already_materialized"]) == 2
    assert _count(lambda c: c["origin"] == "independent_rediscovery") == 5


def test_counterfactual_gates_do_not_claim_discovery():
    cf_b = _count(lambda c: c["origin"] != "independent_rediscovery")
    cf_d = _count(lambda c: not c["same_body_already_materialized"])
    assert _gate(cf_b, 4) == "OPEN"
    assert _gate(cf_d, 4) == "OPEN"
    assert _gate(5, 5) == "CLOSED"  # CF-E
    assert _gate(5, 6) == "OPEN"  # CF-F
    # Reservation is an exception at the gate, not a smaller count.
    assert _gate(5, 4) == "CLOSED"


def test_report_matches_recomputed_accounting():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["intervention"] == "NO PRODUCTION INTERVENTION AUTHORIZED"
    assert report["design_intent_of_max_executed_4"] == "NOT_RECORDED"
    assert report["waste_claimed"] is False
    assert report["redundant_assigned"] is False
    assert report["semantics"]["rediscovery_consumes_same_quota_as_novel"] is True
    assert report["binding_at_refusal"] == "board.max_executed"
    assert [c["id"] for c in report["consumers"]] == ["C1", "C2", "C3", "C4", "C5"]
    assert [c["executed_after"] for c in report["consumers"]] == [1, 2, 3, 4, 5]
    assert [c["body_class"] for c in report["consumers"]] == [
        "REDISCOVERY",
        "REDISCOVERY",
        "REDISCOVERY",
        "NEW",
        "NEW",
    ]
    cf = report["counterfactuals"]
    assert cf["CF-A"]["gate"] == "CLOSED" and cf["CF-A"]["verified"] is False
    assert cf["CF-B"]["executed"] == _count(lambda c: c["origin"] != "independent_rediscovery")
    assert cf["CF-B"]["gate"] == "OPEN"
    assert cf["CF-B"]["verified"] == "NOT_REPLAYED"
    assert cf["CF-C"]["gate"] == "OPEN_ONE"
    assert cf["CF-C"]["body_dispensed"] == "NOT_REPLAYED"
    assert cf["CF-D"]["executed"] == _count(lambda c: not c["same_body_already_materialized"])
    assert cf["CF-D"]["gate"] == "OPEN"
    assert cf["CF-E"]["gate"] == "CLOSED"
    assert cf["CF-F"]["gate"] == "OPEN"
    for key in ("CF-B", "CF-C", "CF-D", "CF-E", "CF-F"):
        assert cf[key]["verified"] == "NOT_REPLAYED"
        assert cf[key]["registered"] == "NOT_REPLAYED"
    assert "NOT_RECORDED" in report["hypotheses"]["H18a"]
