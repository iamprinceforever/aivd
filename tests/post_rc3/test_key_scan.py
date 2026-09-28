"""No gsk_… key in tracked files, reports or ledgers. The key is never printed."""

from aivd_post_rc3.key_scan import GSK_PATTERN, assert_no_gsk, key_present_in_env, scan_for_gsk


def test_repository_contains_no_groq_key():
    assert scan_for_gsk() == []


def test_pattern_detects_synthetic_key(tmp_path):
    f = tmp_path / "leak.json"
    fake = "gsk_" + "A1b2C3d4E5f6G7h8I9j0K1l2"  # synthetic, assembled at runtime
    f.write_text('{"x":"' + fake + '"}')
    hits = scan_for_gsk([f])
    assert hits == [str(f)]
    try:
        assert_no_gsk([f])
    except AssertionError as exc:
        assert fake not in str(exc)  # never echo the key
    else:
        raise AssertionError("not detected")


def test_short_or_prefix_only_not_flagged(tmp_path):
    f = tmp_path / "ok.txt"
    f.write_text("gsk_ short gsk_abc")
    assert scan_for_gsk([f]) == []


def test_key_presence_reports_boolean_only(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert key_present_in_env() is False
    monkeypatch.setenv("GROQ_API_KEY", "dummy-not-a-key")
    assert key_present_in_env() is True


def test_no_literal_key_in_harness_source():
    from pathlib import Path
    for p in list(Path("aivd_post_rc3").glob("*.py")) + list(Path("scripts").glob("post_rc3_*")):
        assert not GSK_PATTERN.search(p.read_text()), p
