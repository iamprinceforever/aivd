import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_coverage_run_stayed_inside_the_frozen_matrix():
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_1_4_execution.json").read_text())
    frozen = json.loads((ROOT / "reports" / "aivd_f3_lm_1_2_execution.json").read_text())
    assert report["classification"] == "F3-LM-1.4 SECURITY DISCOVERY NOT DEMONSTRATED"
    assert report["model_calls"] == 27
    assert report["trial_not_applicable"] == 0
    assert report["security_hypotheses"] == 0
    assert report["public_baseline_opened"] is False
    assert frozen["classification"] == "F3-LM-1.2 SECURITY DISCOVERY NOT DEMONSTRATED"
    raw = ROOT / "reports" / "aivd_f3_lm_1_4_execution" / "evidence" / "raw"
    paths = list(raw.glob("*.json"))
    assert len(paths) == 27
    for path in paths:
        record = json.loads(path.read_text())
        digest = hashlib.sha256(record["raw_text"].encode()).hexdigest()
        assert digest == record["response_sha256"]
