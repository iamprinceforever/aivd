import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "aivd_endgame" / "BLIND_FEATURE_TABLE.md"
FORENSICS = ROOT / "aivd_endgame" / "FORENSICS.md"
TABLE_HASH = "f47cdf067f313dcc13d9730dec83e0a3628a55ad83c0bfe64dd8d3f4606a5cfa"


def test_blind_table_is_frozen_and_unlabeled():
    text = TABLE.read_text(encoding="utf-8")
    assert hashlib.sha256(text.encode()).hexdigest() == TABLE_HASH
    assert "CROSS_TURN_CARRY" not in text
    assert "protected_value" not in text
    assert TABLE_HASH in FORENSICS.read_text(encoding="utf-8")
