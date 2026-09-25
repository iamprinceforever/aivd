"""The sealed corpus is public only as commitments. These tests do not decrypt it."""

import json
from pathlib import Path

import pytest

from aivd.experiments.aivd40.source_d.crypto import open_sealed, seal
from aivd.experiments.aivd40.source_d.generate import (
    PROVIDER,
    VAULT,
    FirewallClosed,
    corpus_claim,
    discovery_load_real,
    vault_invisible,
)
from aivd.experiments.aivd40.source_d.scan import scan
from aivd.experiments.aivd40.source_d.spec import REQUEST, specification_hash

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reports" / "aivd_f3_source_d_corpus_ledger.json"


def test_request_and_provider_script_are_target_neutral():
    assert scan(REQUEST)["clean"] is True
    assert scan(PROVIDER)["clean"] is True
    lowered = (REQUEST + PROVIDER).lower()
    assert "vulnerable" not in lowered
    assert "insecure" not in lowered
    assert "leak" not in lowered


def test_public_ledger_has_no_plaintext_and_firewall_stays_closed():
    text = LEDGER.read_text(encoding="utf-8")
    ledger = json.loads(text)
    assert ledger["corpus_size"] == 8
    assert len(ledger["artifacts"]) == 8
    assert ledger["discovery_firewall"] == "CLOSED"
    assert ledger["provider"]["history"] == "NOT_VERIFIED"
    assert ledger["provider"]["name"] == "box-grammar"
    assert ledger["provider"]["model_name"] is None
    assert ledger["specification_hash"] == specification_hash()
    handles = [row["handle"] for row in ledger["artifacts"]]
    assert handles == sorted(handles)
    for word in ("vulnerable", "insecure", "HOLDS", "VIOLATION", "program", "relation_pass", "relation_fail"):
        assert word not in text
    assert corpus_claim("NOT_VERIFIED") == "CORPUS_SEALED_HISTORY_UNVERIFIED"
    assert corpus_claim("VERIFIED") != "FULLY_INDEPENDENT_CORPUS"
    with pytest.raises(FirewallClosed):
        discovery_load_real()


def test_vault_is_outside_the_repository_and_invisible_to_discovery():
    key = VAULT / "key.bin"
    assert key.is_file()
    assert not str(key.resolve()).startswith(str(ROOT.resolve()))
    assert key.read_bytes().hex() not in LEDGER.read_text(encoding="utf-8")
    assert vault_invisible() is True


def test_synthetic_seal_roundtrip_does_not_open_the_real_corpus():
    packed = seal(b"s" * 32, b"synthetic-fixture")
    assert open_sealed(b"s" * 32, packed) == b"synthetic-fixture"
    real = (VAULT / "corpus.bin.json").read_text(encoding="utf-8")
    assert "synthetic-fixture" not in real
