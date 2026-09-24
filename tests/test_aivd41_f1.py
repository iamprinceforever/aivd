"""Fixture tests for the F1 contract. They are not the discovery claim."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aivd.experiments.aivd40.f1.bank import PROBES, bank_hash
from aivd.experiments.aivd40.f1.contract import observe
from aivd.experiments.aivd40.f1.discovery import run_discovery
from aivd.experiments.aivd40.f1.evaluate import evaluate
from aivd.experiments.aivd40.f1.experimenter import experimenter_run
from aivd.experiments.aivd40.f1.seal import decrypt, encrypt
from aivd.science.micro import Micro

ROOT = Path(__file__).resolve().parents[1]
NEEDLES = ("doubled", "reverse-each", "ODDSTRIDE", "secret{", "disallowed:", "Stage-5", "Stage-8", "Stage-9")


def test_bank_rejects_an_empty_probe_and_is_stable():
    assert all(probe.strip() for probe in PROBES)
    assert bank_hash() == bank_hash(PROBES)
    assert len(bank_hash()) == 64


def test_identity_and_reverse_are_complete_and_distinct():
    digest = bank_hash()
    identity = observe(Micro("TOK"), PROBES, digest)
    reverse = observe(Micro("REV", (), (Micro("TOK"),)), PROBES, digest)
    assert identity.complete()
    assert reverse.complete()
    assert identity.canonical_bytes() != reverse.canonical_bytes()


def test_empty_fallback_does_not_mint_a_complete_signature():
    digest = bank_hash()
    signature = observe(Micro("AT", (9,)), PROBES, digest)
    assert not signature.complete()
    assert any(item.status == "INVALID_EXECUTION" for item in signature.results)


def test_fixture_discovery_hides_keys_and_locks_before_reveal(tmp_path: Path):
    seed = b"fixture-seed-not-the-official-run-32b"
    summary = run_discovery(tmp_path, seed)
    ledger = (tmp_path / "discovery_ledger.json").read_text()
    assert "body_key" not in ledger
    assert (tmp_path / "LOCK").is_file()
    plain = decrypt(seed, (tmp_path / "corpus.seal").read_bytes())
    for key in json.loads(plain):
        assert key not in ledger
    revealed = evaluate(tmp_path, seed)
    assert revealed["confirmed"] is True
    assert revealed["ledger_unchanged"] is True
    assert summary["measured"] == 16


def test_reveal_refuses_a_missing_lock(tmp_path: Path):
    seed = b"fixture-seed-not-the-official-run-32b"
    run_discovery(tmp_path, seed)
    (tmp_path / "LOCK").unlink()
    with pytest.raises(RuntimeError):
        evaluate(tmp_path, seed)


def test_commitment_detects_tamper(tmp_path: Path):
    seed = b"fixture-seed-not-the-official-run-32b"
    blob = encrypt(seed, b"abc")
    flipped = bytearray(blob)
    flipped[-1] ^= 1
    with pytest.raises(Exception):
        json.loads(decrypt(seed, bytes(flipped)))


def test_experimenter_process_never_receives_the_seed(tmp_path: Path):
    summary = experimenter_run(tmp_path)
    assert summary["measured"] == 16
    assert "body_key" not in (tmp_path / "discovery_ledger.json").read_text()
    assert (tmp_path / "post_reveal.json").is_file()
    assert (tmp_path / "LOCK").is_file()


def test_no_target_strings_and_science_is_untouched():
    folder = ROOT / "aivd" / "experiments" / "aivd40" / "f1"
    for path in folder.rglob("*.py"):
        text = path.read_text()
        for needle in NEEDLES:
            assert needle not in text
    import subprocess

    diff = subprocess.check_output(["git", "diff", "b1b7106", "HEAD", "--", "aivd/science"], cwd=ROOT, text=True)
    assert diff.strip() == ""
