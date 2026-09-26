import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_load_failure_is_invalidated_and_old_result_remains():
    report = json.loads((ROOT / "reports" / "aivd_f3_lm_1_1_execution.json").read_text(encoding="utf-8"))
    assert report["classification"] == "F3-LM-1.1 EXPERIMENT INVALIDATED"
    assert report["calls_completed"] == 0
    old = json.loads((ROOT / "reports" / "aivd_f3_lm_execution.json").read_text(encoding="utf-8"))
    assert old["classification"] == "F3-LM EXPERIMENT INVALIDATED"
    grammar = (ROOT / "aivd_f3_lm" / "grammar.py").read_text(encoding="utf-8")
    assert "ROLE_PERMUTE" in grammar
