import hashlib
from pathlib import Path

from aivd_f3_lm.qwen3_runtime import F3_LM_EXECUTION_AUTHORIZED

ROOT = Path(__file__).resolve().parents[1]


def test_execution_stopped_before_inference():
    template = (ROOT / "freeze" / "qwen3" / "template").read_text(encoding="utf-8")
    assert 'eq .Role "developer"' not in template
    assert 'eq .Role "user"' in template
    assert F3_LM_EXECUTION_AUTHORIZED is False
    ledger = ROOT / "reports" / "aivd_f3_lm_execution" / "ledger.json"
    digest = hashlib.sha256(ledger.read_bytes()).hexdigest()
    report = (ROOT / "reports" / "aivd_f3_lm_execution.json").read_text(encoding="utf-8")
    assert digest in report
    assert "EXPERIMENT INVALIDATED" in report
    assert "qwen" not in (ROOT / "aivd_f3_lm" / "grammar.py").read_text(encoding="utf-8").lower()
