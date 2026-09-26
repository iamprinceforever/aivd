import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_unretained_first_call_invalidates_and_old_targets_stay():
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_1_7b_execution.json").read_text(encoding="utf-8"))
    assert report["classification"] == "F3-LM QWEN3 1.7B EXPERIMENT INVALIDATED"
    assert report["retained_outputs"] == 0
    assert report["rerun_after_defect"] is False
    four = json.loads((ROOT / "reports" / "aivd_f3_lm_qwen3_4b_target.json").read_text(encoding="utf-8"))
    assert four["admission"] == "DENIED"
    assert four["model_loaded"] is False
    eight = json.loads((ROOT / "reports" / "aivd_f3_lm_1_1_execution.json").read_text(encoding="utf-8"))
    assert eight["classification"] == "F3-LM-1.1 EXPERIMENT INVALIDATED"
