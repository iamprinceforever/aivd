"""Stage G blindness, commitment, and leakage tests. Not a Source-A claim."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aivd.behavior.discovery.constants import DISCOVERY_BANK_HASH
from aivd.behavior.sealed_corpus.crypto import commit, sha256_hex
from aivd.behavior.sealed_corpus.experimenter import BlindnessBroken, ExperimenterSession
from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.behavior.sealed_corpus.measure import lock_session, measure
from aivd.behavior.sealed_corpus.package import build_corpus
from aivd.behavior.sealed_corpus.reveal import reveal
from aivd.science.micro import validate_micro

ROOT = Path(__file__).resolve().parents[1]
NEEDLES = (
    "doubled-odd",
    "doubled-even",
    "reverse-each",
    "ODDSTRIDE",
    "secret{",
    "SLICE:1,2(TOK)|SLICE:1,2",
)


def _corpus(size: int = 6):
    return build_corpus(b"stage-g-test-seed", size)


def test_generation_is_deterministic_and_valid():
    first = generate_bodies(b"stage-g-test-seed", 8)
    second = generate_bodies(b"stage-g-test-seed", 8)
    assert [body.key() for body in first] == [body.key() for body in second]
    assert len(set(body.key() for body in first)) == 8
    assert all(validate_micro(body, n_tokens=4) is None for body in first)


def test_public_commitment_hides_bodies_and_the_seed():
    corpus = _corpus()
    public = json.dumps(corpus.public.as_dict())
    assert corpus.public.bank_hash == DISCOVERY_BANK_HASH
    assert "generation_seed" not in public
    assert corpus.preimage["generation_seed_sha256"] not in public
    for body in corpus.decrypt_bodies().values():
        assert body.key() not in public
        assert body.key().encode() not in corpus.public.commitment.encode()
    session = ExperimenterSession(corpus.public)
    assert session.list_handles()[0] == "sd_000001"
    assert "MAPT" not in session.list_handles()[0]
    assert "SLICE" not in session.list_handles()[0]


def test_experimenter_api_cannot_read_plaintext():
    session = ExperimenterSession(_corpus().public)
    with pytest.raises(BlindnessBroken):
        session.get_body("sd_000001")
    with pytest.raises(BlindnessBroken):
        session.get_body_key("sd_000001")
    with pytest.raises(BlindnessBroken):
        session.get_class("sd_000001")
    with pytest.raises(BlindnessBroken):
        session.get_signature("sd_000001")
    with pytest.raises(BlindnessBroken):
        session.decrypt()
    with pytest.raises(BlindnessBroken):
        session.reveal()


def test_tamper_is_detected():
    corpus = _corpus()
    corpus.ciphertext = corpus.ciphertext[:-1] + bytes([corpus.ciphertext[-1] ^ 1])
    assert corpus.verify() is False
    fresh = _corpus()
    fresh.preimage = dict(fresh.preimage)
    fresh.preimage["handles"] = list(reversed(fresh.preimage["handles"]))
    assert fresh.verify() is False
    seeded = _corpus()
    seeded.preimage = dict(seeded.preimage)
    seeded.preimage["generation_seed_sha256"] = sha256_hex(b"other-seed")
    assert seeded.verify() is False
    bank = _corpus()
    bank.preimage = dict(bank.preimage)
    bank.preimage["bank_hash"] = "0" * 64
    assert bank.verify() is False
    assert commit(bank.preimage) != bank.public.commitment


def test_order_is_committed_and_discovery_does_not_rewrite_ciphertext():
    corpus = _corpus()
    before = sha256_hex(corpus.ciphertext)
    session = ExperimenterSession(corpus.public)
    measured = measure(corpus, session)
    assert sha256_hex(corpus.ciphertext) == before
    assert [row["corpus_handle"] for row in measured["ledger"] if row["event"] != "compose"] == list(
        corpus.list_handles()
    )
    digest = lock_session(session, measured["ledger"])
    revealed = reveal(corpus, session, measured["ledger"], measured["sealed_log"])
    assert revealed["ledger_sha256"] == digest
    again = json.dumps(measured["ledger"], sort_keys=True, separators=(",", ":"))
    assert sha256_hex(again.encode()) == digest
    blob = json.dumps(measured["ledger"])
    assert "MAPT(" not in blob
    assert "body_key" not in blob
    assert "content_id" not in blob


def test_reveal_before_lock_is_rejected_and_results_do_not_edit_the_ledger():
    corpus = _corpus()
    session = ExperimenterSession(corpus.public)
    measured = measure(corpus, session)
    with pytest.raises(RuntimeError, match="reveal before"):
        reveal(corpus, session, measured["ledger"], measured["sealed_log"])
    digest = lock_session(session, measured["ledger"])
    snapshot = json.dumps(measured["ledger"], sort_keys=True)
    reveal(corpus, session, measured["ledger"], measured["sealed_log"])
    assert json.dumps(measured["ledger"], sort_keys=True) == snapshot
    assert digest == sha256_hex(json.dumps(measured["ledger"], sort_keys=True, separators=(",", ":")).encode())


def test_same_seed_recommits_and_stage_e_guard_remains():
    assert build_corpus(b"stage-g-test-seed", 4).public.commitment == build_corpus(b"stage-g-test-seed", 4).public.commitment
    engine = (ROOT / "aivd" / "behavior" / "discovery" / "engine.py").read_text()
    assert "refuse_discovery_bank" in engine
    assert "SOURCE-D" not in engine


def test_stage_g_sources_have_no_target_logic_and_science_does_not_import_them():
    folders = [
        ROOT / "aivd" / "behavior" / "sealed_corpus",
        ROOT / "aivd" / "experiments" / "aivd40",
    ]
    for folder in folders:
        for path in folder.rglob("*.py"):
            text = path.read_text()
            for needle in NEEDLES:
                assert needle not in text, path
    for path in (ROOT / "aivd" / "science").glob("*.py"):
        assert "sealed_corpus" not in path.read_text()
        assert "experiments.aivd40" not in path.read_text()
