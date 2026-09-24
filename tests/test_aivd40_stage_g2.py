"""Source-E selection tests. They do not treat public corpora as Source-A."""

from __future__ import annotations

from pathlib import Path

import pytest

from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.experiments.aivd40.stage_g2.commit import commitment, selection_preimage
from aivd.experiments.aivd40.stage_g2.constants import BANK_HASH, SAMPLE_CAP, SOURCES
from aivd.experiments.aivd40.stage_g2.micro_key import NotMicroKey, parse_micro_key
from aivd.experiments.aivd40.stage_g2.sample import enumerate_checkout, select_population
from aivd.science.micro import Micro

ROOT = Path(__file__).resolve().parents[1]
NEEDLES = (
    "doubled-odd",
    "doubled-even",
    "reverse-each",
    "ODDSTRIDE",
    "historical secret",
    "critical pair",
)


def _write_population(directory: Path, count: int) -> None:
    for index, body in enumerate(generate_bodies(b"g2-fixture", count)):
        (directory / f"p{index}.txt").write_text(body.key())
    (directory / "note.sl").write_text("(set-logic LIA)\n")
    (directory / "blob.bin").write_bytes(b"\0\1\2")


def test_micro_keys_roundtrip_and_reject_other_text():
    for body in generate_bodies(b"g2-fixture", 12):
        assert parse_micro_key(body.key()).key() == body.key()
    with pytest.raises(NotMicroKey):
        parse_micro_key("(set-logic LIA)")
    with pytest.raises(NotMicroKey):
        parse_micro_key("AT:0 ")


def test_sampling_is_deterministic_deduped_and_separated():
    population = [
        {"key": body.key(), "key_sha256": str(index), "path_sha256": "p"}
        for index, body in enumerate(generate_bodies(b"g2-fixture", 6))
    ]
    # Real hashes, not the placeholder above.
    from aivd.experiments.aivd40.stage_g2.sample import _sha

    population = [{"key": row["key"], "key_sha256": _sha(row["key"]), "path_sha256": "p"} for row in population]
    first = select_population(population, b"seed", "E1", 3)
    second = select_population(population, b"seed", "E1", 3)
    other = select_population(population, b"seed", "E2", 3)
    assert [row["key_sha256"] for row in first] == [row["key_sha256"] for row in second]
    assert len(first) == 3
    assert {row["key_sha256"] for row in first} != {row["key_sha256"] for row in other}


def test_enumeration_does_not_replace_an_incompatible_file(tmp_path: Path):
    _write_population(tmp_path, 4)
    inventory = enumerate_checkout(tmp_path)
    assert inventory["compatible_files"] == 4
    assert inventory["unique_programs"] == 4
    assert inventory["incompatible_files"] == 2
    selected = select_population(inventory["population"], b"seed", "E1", SAMPLE_CAP)
    assert len(selected) == 4
    blob = " ".join(row["key_sha256"] for row in selected)
    assert "(set-logic" not in blob


def test_commitment_binds_the_bank_and_detects_tamper():
    preimage = selection_preimage(
        protocol_version="aivd-4.0-stage-g2-1",
        source_id="E1",
        repository="https://example.invalid/corpus",
        commit="abc",
        seed_name="seed",
        sample_cap=SAMPLE_CAP,
        bank_hash=BANK_HASH,
        translator_version="identity-micro-key-v0",
        selected_key_sha256=["aa"],
    )
    bound = commitment(preimage)
    changed = dict(preimage)
    changed["bank_hash"] = "0" * 64
    assert commitment(changed) != bound
    changed = dict(preimage)
    changed["selected_key_sha256"] = ["bb"]
    assert commitment(changed) != bound
    other = dict(preimage)
    other["source_id"] = "E2"
    assert commitment(other) != bound


def test_pins_are_full_shas_and_sources_are_not_merged():
    commits = [row["commit"] for row in SOURCES]
    assert len(commits) == len(set(commits)) == 4
    assert all(len(commit) == 40 for commit in commits)
    assert [row["source_id"] for row in SOURCES] == ["E1", "E2", "E3", "E4"]


def test_no_target_strings_and_science_is_untouched():
    folder = ROOT / "aivd" / "experiments" / "aivd40" / "stage_g2"
    for path in folder.rglob("*.py"):
        text = path.read_text()
        for needle in NEEDLES:
            assert needle not in text
    import subprocess

    diff = subprocess.check_output(
        ["git", "diff", "b1b7106", "HEAD", "--", "aivd/science"],
        cwd=ROOT,
        text=True,
    )
    assert diff.strip() == ""
    assert Micro("TOK").key() == "TOK"
