"""Signature memory. Lookup is not by body key or family."""

from __future__ import annotations

from dataclasses import dataclass, field

from aivd.behavior.discovery.constants import PROTOCOL_VERSION
from aivd.behavior.discovery.signature import BehavioralSignature, content_id


@dataclass
class BehavioralDimension:
    handle: str
    content_id: str
    bank_hash: str
    signature: BehavioralSignature
    representative: str
    parents: tuple[str, ...]
    epoch: int
    event: str
    observations: list[str] = field(default_factory=list)
    security: str = "UNEVALUATED"
    version: str = PROTOCOL_VERSION


class BehavioralMemory:
    def __init__(self) -> None:
        self.epoch = 1
        self._dimensions: list[BehavioralDimension] = []
        self._by_content: dict[str, BehavioralDimension] = {}

    def dimensions(self) -> tuple[BehavioralDimension, ...]:
        return tuple(self._dimensions)

    def find_content(self, signature: BehavioralSignature) -> BehavioralDimension | None:
        if signature.bank_hash is None:
            return None
        found = self._by_content.get(content_id(signature))
        if found is None or found.bank_hash != signature.bank_hash:
            return None
        return found

    def add(self, dimension: BehavioralDimension) -> None:
        if dimension.content_id in self._by_content:
            raise RuntimeError("rediscovery must not create a second dimension")
        self._dimensions.append(dimension)
        self._by_content[dimension.content_id] = dimension

    def firewall(self) -> None:
        self.epoch += 1
        self._dimensions = []
        self._by_content = {}
