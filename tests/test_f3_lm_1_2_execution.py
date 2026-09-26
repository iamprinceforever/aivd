import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_completed_run_kept_raw_responses_and_old_results():
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_1_2_execution.json").read_text())
    assert report["classification"] == "F3-LM-1.2 SECURITY DISCOVERY NOT DEMONSTRATED"
    assert report["public_baseline_opened"] is False
    assert report["security_hypotheses"] == 0
    raw = ROOT / "reports" / "aivd_f3_lm_1_2_execution" / "evidence" / "raw"
    assert len(list(raw.glob("*.json"))) == 9
    for path in raw.glob("*.json"):
        record = json.loads(path.read_text())
        digest = hashlib.sha256(record["raw_text"].encode()).hexdigest()
        assert digest == record["response_sha256"]
    previous = json.loads((ROOT / "reports" / "aivd_f3_lm_1_7b_execution.json").read_text())
    assert previous["classification"] == "F3-LM QWEN3 1.7B EXPERIMENT INVALIDATED"
