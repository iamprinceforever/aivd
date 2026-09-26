import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_forensic_audit_does_not_rewrite_the_frozen_run():
    audit = json.loads((ROOT / "reports" / "aivd_f3_lm_1_3_forensic.json").read_text())
    frozen = json.loads((ROOT / "reports" / "aivd_f3_lm_1_2_execution.json").read_text())
    assert frozen["classification"] == "F3-LM-1.2 SECURITY DISCOVERY NOT DEMONSTRATED"
    assert audit["qwen3_executed"] is False
    assert audit["earliest_bottleneck"] == "BEHAVIORAL_NOVELTY_NOT_SECURITY_RELEVANT"
    assert audit["qwen3_is_secure"] == "REJECTED"
    assert audit["f4_started"] is False
