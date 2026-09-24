"""Execute a body on a bank with apply_micro only."""

from __future__ import annotations

from aivd.behavior.discovery.constants import DISCOVERY_BANK_HASH, DISCOVERY_PROBES
from aivd.behavior.discovery.errors import DiscoveryBankSealed
from aivd.behavior.discovery.signature import BehavioralSignature, ProbeResult, bank_hash
from aivd.science.micro import apply_micro

_DISCOVERY_PROBE_SET = frozenset(DISCOVERY_PROBES)


def refuse_discovery_bank(probes: tuple[str, ...]) -> None:
    if bank_hash(probes) == DISCOVERY_BANK_HASH or any(p in _DISCOVERY_PROBE_SET for p in probes):
        raise DiscoveryBankSealed(
            "the frozen discovery bank is not executed by fixture or harness code"
        )


def execute_body(body: object, probes: tuple[str, ...], *, allow_discovery_bank: bool = False) -> BehavioralSignature:
    if not allow_discovery_bank:
        refuse_discovery_bank(probes)
    digest = bank_hash(probes)
    results: list[ProbeResult] = []
    for index, probe in enumerate(probes):
        results.append(_one(body, index, probe))
    return BehavioralSignature(bank_hash=digest, results=tuple(results))


def execute_sequential(
    first: object,
    second: object,
    probes: tuple[str, ...],
    *,
    allow_discovery_bank: bool = False,
) -> tuple[BehavioralSignature, int]:
    """b after a: apply_micro(apply_micro(probe, first), second). Returns signature and call count."""
    if not allow_discovery_bank:
        refuse_discovery_bank(probes)
    digest = bank_hash(probes)
    results: list[ProbeResult] = []
    calls = 0
    for index, probe in enumerate(probes):
        try:
            mid = apply_micro(probe, first)
            calls += 1
        except Exception:
            calls += 1
            results.append(ProbeResult(index, None, "EXECUTION_FAILURE"))
            continue
        try:
            out = apply_micro(mid, second)
            calls += 1
        except Exception:
            calls += 1
            results.append(ProbeResult(index, None, "EXECUTION_FAILURE"))
            continue
        results.append(_status(index, probe, out))
    return BehavioralSignature(bank_hash=digest, results=tuple(results)), calls


def _one(body: object, index: int, probe: str) -> ProbeResult:
    try:
        out = apply_micro(probe, body)
    except Exception:
        return ProbeResult(index, None, "EXECUTION_FAILURE")
    return _status(index, probe, out)


def _status(index: int, probe: str, out: object) -> ProbeResult:
    if not isinstance(out, str):
        return ProbeResult(index, None, "EXECUTION_FAILURE")
    if out == probe:
        return ProbeResult(index, out, "AMBIGUOUS_COPY")
    return ProbeResult(index, out, "NORMAL")
