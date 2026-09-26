import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_opportunity_audit_does_not_rewrite_the_run():
    audit = json.loads((ROOT / "reports" / "aivd_f3_lm_1_5_opportunity_audit.json").read_text())
    frozen = json.loads((ROOT / "reports" / "aivd_f3_lm_1_4_execution.json").read_text())
    assert frozen["classification"] == "F3-LM-1.4 SECURITY DISCOVERY NOT DEMONSTRATED"
    assert frozen["model_calls"] == 27
    assert audit["qwen3_executed"] is False
    assert audit["classification"] == "SECURITY_OPPORTUNITY_WAS_WEAK"
    assert audit["qwen3_is_secure"] == "REJECTED"
    assert audit["f4_started"] is False
