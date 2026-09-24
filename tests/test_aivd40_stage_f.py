"""Stage F does not discover. It rejects substitutes and does not execute."""

from __future__ import annotations

import pytest

from aivd.behavior.discovery.constants import DISCOVERY_BANK_HASH, PROTOCOL_VERSION
from aivd.behavior.discovery.errors import BlindnessBroken
from aivd.behavior.discovery.stage_f import (
    WAITING,
    ExperimenterView,
    assess_corpus,
    bind_measurement_environment,
    run_stage_f,
)
from aivd.science import micro


def _seal(**overrides):
    envelope = {
        "provider_id": "external-provider",
        "commitment": "commit-opaque",
        "ciphertext": b"\x01\x02",
        "candidate_count": 4,
        "order_commitment": "order-opaque",
        "bank_hash": DISCOVERY_BANK_HASH,
        "protocol_version": PROTOCOL_VERSION,
        "source_class": "A",
        "timestamp": "2020-01-01T00:00:00Z",
        "manufactured_in_repository": False,
    }
    envelope.update(overrides)
    return envelope


def test_missing_corpus_waits_and_does_not_execute(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("apply_micro must not run")

    monkeypatch.setattr(micro, "apply_micro", fail)
    result = run_stage_f(None)
    assert result["status"] == WAITING
    assert result["discovery_performed"] is False
    assert result["apply_micro_calls"] == 0
    assert result["claim"] is None


def test_structurally_complete_seal_still_does_not_execute(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("apply_micro must not run")

    monkeypatch.setattr(micro, "apply_micro", fail)
    result = run_stage_f(_seal())
    assert result["structurally_complete"] is True
    assert result["accepted_for_execution"] is False
    assert result["discovery_performed"] is False
    assert result["status"] == WAITING


@pytest.mark.parametrize(
    "overrides",
    [
        {"source_class": "B"},
        {"source_class": "C"},
        {"manufactured_in_repository": True},
        {"locally_generated": True},
        {"planner_generated": True},
        {"historical_bodies": True},
        {"target_directed": True},
        {"filtered_for_study": True},
        {"body_keys": ["MAPT(TOK)"]},
        {"plaintext": "visible"},
        {"seed": "reconstruct"},
        {"bank_hash": "0" * 64},
    ],
)
def test_substitutes_and_leaks_are_rejected(overrides):
    result = assess_corpus(_seal(**overrides))
    assert result["structurally_complete"] is False
    assert result["discovery_performed"] is False
    assert result["accepted_for_execution"] is False


def test_experimenter_cannot_read_plaintext():
    view = ExperimenterView(commitment="commit-opaque", handles=("h-0001",))
    assert view.commitment == "commit-opaque"
    with pytest.raises(BlindnessBroken):
        _ = view.plaintext
    with pytest.raises(BlindnessBroken):
        _ = view.seed
    with pytest.raises(BlindnessBroken):
        bind_measurement_environment()
