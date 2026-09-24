"""Build a sealed Source-D corpus. Plaintext stays off the public object."""

from __future__ import annotations

import json
from dataclasses import dataclass

from aivd.behavior.discovery.constants import DISCOVERY_BANK_HASH
from aivd.behavior.sealed_corpus.codec import dump_micro, load_micro
from aivd.behavior.sealed_corpus.constants import (
    CORPUS_SIZE,
    GENERATION_SEED,
    GRAMMAR_VERSION,
    PROTOCOL_VERSION,
    SOURCE_CLASS,
)
from aivd.behavior.sealed_corpus.crypto import canonical, commit, decrypt, encrypt, sha256_hex
from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.science.micro import Micro


@dataclass(frozen=True)
class PublicCommitment:
    commitment: str
    protocol_version: str
    grammar_version: str
    corpus_size: int
    handles: tuple[str, ...]
    bank_hash: str
    source_class: str

    def as_dict(self) -> dict[str, object]:
        return {
            "bank_hash": self.bank_hash,
            "commitment": self.commitment,
            "corpus_size": self.corpus_size,
            "grammar_version": self.grammar_version,
            "handles": list(self.handles),
            "protocol_version": self.protocol_version,
            "source_class": self.source_class,
        }


@dataclass
class SealedCorpus:
    public: PublicCommitment
    ciphertext: bytes
    preimage: dict[str, object]
    _seed: bytes

    def list_handles(self) -> tuple[str, ...]:
        return self.public.handles

    def verify(self) -> bool:
        return (
            commit(self.preimage) == self.public.commitment
            and self.preimage["ciphertext_sha256"] == sha256_hex(self.ciphertext)
            and self.preimage["generation_seed_sha256"] == sha256_hex(self._seed)
        )

    def decrypt_bodies(self) -> dict[str, Micro]:
        rows = json.loads(decrypt(self._seed, self.ciphertext).decode())
        return {str(row["opaque_handle"]): load_micro(row["tree"]) for row in rows}


def build_corpus(seed: bytes = GENERATION_SEED, size: int = CORPUS_SIZE) -> SealedCorpus:
    bodies = generate_bodies(seed, size)
    handles = tuple(f"sd_{index:06d}" for index in range(1, size + 1))
    rows = [
        {"opaque_handle": handle, "order": index, "tree": dump_micro(body)}
        for index, (handle, body) in enumerate(zip(handles, bodies))
    ]
    ciphertext = encrypt(seed, json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    preimage = {
        "bank_hash": DISCOVERY_BANK_HASH,
        "ciphertext_sha256": sha256_hex(ciphertext),
        "corpus_size": size,
        "generation_seed_sha256": sha256_hex(seed),
        "grammar_version": GRAMMAR_VERSION,
        "handles": list(handles),
        "protocol_version": PROTOCOL_VERSION,
        "source_class": SOURCE_CLASS,
    }
    public = PublicCommitment(
        commitment=commit(preimage),
        protocol_version=PROTOCOL_VERSION,
        grammar_version=GRAMMAR_VERSION,
        corpus_size=size,
        handles=handles,
        bank_hash=DISCOVERY_BANK_HASH,
        source_class=SOURCE_CLASS,
    )
    sealed = SealedCorpus(public=public, ciphertext=ciphertext, preimage=preimage, _seed=seed)
    if not sealed.verify():
        raise RuntimeError("commitment did not bind the corpus just built")
    return sealed


def public_bytes(corpus: SealedCorpus) -> bytes:
    return canonical(corpus.public.as_dict())
