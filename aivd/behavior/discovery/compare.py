"""Finite-bank comparison. Not a claim of semantic equivalence."""

from __future__ import annotations

from aivd.behavior.discovery.signature import BehavioralSignature

OBSERVED_EQUIVALENT = "OBSERVED_EQUIVALENT"
OBSERVED_DISTINCT = "OBSERVED_DISTINCT"
INSUFFICIENT = "INSUFFICIENT"


def compare(left: BehavioralSignature, right: BehavioralSignature) -> str:
    if left.bank_hash != right.bank_hash or len(left.results) != len(right.results):
        return INSUFFICIENT
    if not left.complete() or not right.complete():
        return INSUFFICIENT
    differed = False
    for a, b in zip(left.results, right.results):
        if a.index != b.index or a.output != b.output:
            differed = True
    return OBSERVED_DISTINCT if differed else OBSERVED_EQUIVALENT
