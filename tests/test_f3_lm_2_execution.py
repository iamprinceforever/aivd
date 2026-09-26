import json
from pathlib import Path

from aivd_f3_lm.f3lm2.evaluate import controls, violates
from aivd_f3_lm.f3lm2.generate import generate_contracts

ROOT = Path(__file__).resolve().parents[1]


def test_execution_stopped_before_any_model_call():
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_2_execution.json").read_text())
    frozen = json.loads((ROOT / "reports" / "aivd_f3_lm_1_4_execution.json").read_text())
    assert report["classification"] == "F3-LM-2 EXPERIMENT INVALIDATED"
    assert report["qwen3_executed"] is False
    assert report["model_calls"] == 0
    assert report["oracle_modified"] is False
    assert report["stop_reason"].startswith("N3")
    assert frozen["model_calls"] == 27
    denied = [contract for contract in generate_contracts() if contract["authorization"] == "DENIED"]
    assert len(denied) == 5
    assert all(not violates(contract, controls(contract)["N3"]["output"]) for contract in denied)
