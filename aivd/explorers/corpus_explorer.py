from __future__ import annotations

from typing import Any

from aivd.explorers.corpus_data import VULN_CORPUS


class CorpusExplorer:
    name = "corpus"

    def __init__(self, seed: int = 42):
        self._i = 0
        self.corpus = list(VULN_CORPUS)

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        item = self.corpus[self._i % len(self.corpus)]
        self._i += 1
        return item

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        return
