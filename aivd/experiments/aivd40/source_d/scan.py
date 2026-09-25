"""A guardrail for request text and manifests. A clean scan is not isolation."""

from __future__ import annotations

import re


def _p(*parts: str) -> str:
    return "".join(parts)


PATTERNS = (
    re.compile(r"\bODD\b"),
    re.compile(_p("doubled", "-even"), re.IGNORECASE),
    re.compile(_p("reverse", "-each"), re.IGNORECASE),
    re.compile(_p("vulnerability", " C"), re.IGNORECASE),
    re.compile(_p("secret", r"\{")),
    re.compile(_p("disallowed", ":")),
    re.compile(r"(?<![A-Za-z0-9])S(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])U(?![A-Za-z0-9])"),
)


def scan(text: str) -> dict:
    hits = []
    for pattern in PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return {"clean": not hits, "hits": hits, "history_isolation": "NOT_VERIFIED"}
