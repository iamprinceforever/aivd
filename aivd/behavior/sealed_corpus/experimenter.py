"""Experimenter surface. It cannot decrypt."""

from __future__ import annotations

from aivd.behavior.sealed_corpus.package import PublicCommitment


class BlindnessBroken(RuntimeError):
    pass


class ExperimenterSession:
    def __init__(self, public: PublicCommitment) -> None:
        self.commitment = public.commitment
        self.handles = public.handles
        self.bank_hash = public.bank_hash
        self.protocol_version = public.protocol_version
        self.corpus_size = public.corpus_size
        self.source_class = public.source_class
        self.locked = False

    def list_handles(self) -> tuple[str, ...]:
        return self.handles

    def public_metadata(self) -> dict[str, object]:
        return {
            "bank_hash": self.bank_hash,
            "commitment": self.commitment,
            "corpus_size": self.corpus_size,
            "handles": list(self.handles),
            "protocol_version": self.protocol_version,
            "source_class": self.source_class,
        }

    def get_body(self, handle: str) -> None:
        raise BlindnessBroken(handle)

    def get_body_key(self, handle: str) -> None:
        raise BlindnessBroken(handle)

    def get_class(self, handle: str) -> None:
        raise BlindnessBroken(handle)

    def get_signature(self, handle: str) -> None:
        raise BlindnessBroken(handle)

    def decrypt(self) -> None:
        raise BlindnessBroken("decrypt")

    def reveal(self) -> None:
        raise BlindnessBroken("reveal before lock is not an experimenter action")
