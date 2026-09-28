"""Synthetic accounting fixtures. No network and no model call."""

from aivd_post_rc3_v2.accounting import assert_invariants
from aivd_post_rc3_v2.driver import run_fixture, run_model



def test_discovery_transport_retries_stay_on_discovery(tmp_path):
    ledger = run_fixture(tmp_path / "d", [
        {"stage": "discovery", "outcome": "success"},
        {"stage": "discovery", "outcome": "success"},
        {"stage": "discovery", "outcome": "transport_failure", "retries": 2},
    ])
    assert ledger["stage_calls"] == {"discovery": 2, "investigation": 0, "verification": 0}
    assert ledger["calls"] == 2
    assert ledger["api_attempts"] == 5
    assert ledger["retry_attempts"] == 2
    assert ledger["successful_responses"] == 2
    assert ledger["recording_failures"] == 3
    assert ledger["final_status"] == "DISCOVERY_INFRASTRUCTURE_FAILURE"
    assert ledger["failure_stage"] == "discovery"
    assert ledger["failure_report"]["FAILURE_STAGE"] == "discovery"
    assert ledger["discovery_completed"] is False
    assert "investigation" not in ledger["stages_completed"]
    assert_invariants(ledger)


def test_investigation_recording_failure_does_not_become_verification(tmp_path):
    ledger = run_fixture(tmp_path / "i", [
        {"stage": "discovery", "outcome": "success"},
        {"stage": "investigation", "outcome": "success"},
        {"stage": "investigation", "outcome": "recording_failure"},
    ])
    assert ledger["stage_calls"]["discovery"] > 0
    assert ledger["stage_calls"]["investigation"] == 1
    assert ledger["stage_calls"]["verification"] == 0
    assert ledger["final_status"] == "INVESTIGATION_INFRASTRUCTURE_FAILURE"
    assert ledger["failure_stage"] == "investigation"
    assert ledger["stages_completed"] == ["discovery"]
    assert_invariants(ledger)


def test_verification_recording_failure_keeps_earlier_stages(tmp_path):
    ledger = run_fixture(tmp_path / "v", [
        {"stage": "discovery", "outcome": "success"},
        {"stage": "investigation", "outcome": "success"},
        {"stage": "verification", "outcome": "success"},
        {"stage": "verification", "outcome": "recording_failure"},
    ])
    assert ledger["stage_calls"]["verification"] == 1
    assert ledger["final_status"] == "VERIFICATION_INFRASTRUCTURE_FAILURE"
    assert ledger["stages_completed"] == ["discovery", "investigation"]
    assert ledger["discovery_completed"] is True
    assert_invariants(ledger)


def test_retry_budget_exhaustion_remains_a_discovery_failure(tmp_path):
    ledger = run_fixture(tmp_path / "b", [
        {"stage": "discovery", "outcome": "success"},
        {"stage": "discovery", "outcome": "success"},
        {"stage": "discovery", "outcome": "success", "retries": 2},
    ], budget_limit=3)
    assert ledger["stage_calls"] == {"discovery": 2, "investigation": 0, "verification": 0}
    assert ledger["final_status"] == "DISCOVERY_INFRASTRUCTURE_FAILURE"
    assert ledger["failure_report"]["FAILURE_STAGE"] == "discovery"
    assert ledger["failure_report"]["reason"] == "retry exceeded stage budget"
    assert all(item["stage"] == "discovery" for item in ledger["attempts"])
    assert_invariants(ledger)


def test_driver_exception_path_does_not_relabel_discovery(tmp_path):
    calls = {"n": 0}

    def transport(request):
        calls["n"] += 1
        transport.last_attempts = 3 if calls["n"] == 3 else 1
        if calls["n"] < 3:
            return 200, b'{"model":"openai/gpt-oss-20b","message":{"role":"assistant","content":"same"}}'
        raise TimeoutError("synthetic transport failure")

    transport.last_attempts = 1
    public = [{"scenario_id": "sc-acct", "steps": ["open the record", "follow the record"]}]
    ledger = run_model(tmp_path / "m", public, transport, model_id="openai/gpt-oss-20b",
                       corpus_commitment="fixture", discovery_seed=1)
    assert ledger["failure_stage"] == "discovery"
    assert ledger["final_status"] == "DISCOVERY_INFRASTRUCTURE_FAILURE"
    assert ledger["stage_calls"]["investigation"] == 0
    assert ledger["stage_calls"]["verification"] == 0
    assert ledger["stage_calls"]["discovery"] == 2
    assert ledger["api_attempts"] == 5
    assert ledger["discovery_completed"] is False
    assert_invariants(ledger)
