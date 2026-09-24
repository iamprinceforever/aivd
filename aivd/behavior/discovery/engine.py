"""Epoch engine. Stops on an empty frontier or on the frozen budget. No depth cap."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aivd.behavior.discovery.budget import BehavioralBudget
from aivd.behavior.discovery.compare import OBSERVED_DISTINCT, OBSERVED_EQUIVALENT, compare
from aivd.behavior.discovery.constants import FORBIDDEN_PUBLIC_CLAIMS, PROTOCOL_VERSION
from aivd.behavior.discovery.errors import BudgetExhausted
from aivd.behavior.discovery.experiment import refuse_discovery_bank
from aivd.behavior.discovery.memory import BehavioralDimension, BehavioralMemory
from aivd.behavior.discovery.signature import BehavioralSignature, ProbeResult, bank_hash, content_id
from aivd.science.micro import apply_micro

_PURPOSES = frozenset({"FIXTURE", "HISTORICAL_REPLAY"})
Runner = Callable[[str], str]


@dataclass(frozen=True)
class Observation:
    handle: str
    state: str
    opaque_dimension_handle: str | None
    content_id: str | None
    signature: BehavioralSignature
    epoch: int
    event: str
    parents: tuple[str, ...]
    purpose: str
    security: str = "UNEVALUATED"


class DiscoveryEngine:
    def __init__(self, probes: tuple[str, ...], *, purpose: str) -> None:
        if purpose not in _PURPOSES or purpose in FORBIDDEN_PUBLIC_CLAIMS:
            raise ValueError("fixture validation cannot be labeled as discovery")
        refuse_discovery_bank(probes)
        self.probes = tuple(probes)
        self.purpose = purpose
        self.budget = BehavioralBudget()
        self.memory = BehavioralMemory()
        self._runners: dict[str, Runner] = {}
        self._cost: dict[str, int] = {}
        self._dim_of: dict[str, str] = {}
        self._next_body = 0
        self._next_dim = 0
        self._apply_calls = 0
        self._done_pairs: set[tuple[str, str]] = set()

    def characterize(self, body: object) -> Observation:
        need = len(self.probes)
        if not self.budget.can_characterize(need):
            raise BudgetExhausted("characterization")
        handle = self._body_handle()
        self._runners[handle] = self._leaf(body)
        self._cost[handle] = 1
        signature, calls = self._measure(self._runners[handle])
        if calls != need:
            raise RuntimeError("a leaf must spend one call per probe")
        self.budget.charge_characterization(calls)
        return self._commit(handle, signature, event="characterize", parents=())

    def grow(self) -> list[Observation]:
        produced: list[Observation] = []
        while True:
            pending = [pair for pair in self._pairs() if pair not in self._done_pairs]
            if not pending:
                break
            first, second = pending[0]
            need = (self._cost[first] + self._cost[second]) * len(self.probes)
            if not self.budget.can_pair(need):
                break
            self._done_pairs.add((first, second))
            handle = self._body_handle()
            self._runners[handle] = self._chain(self._runners[first], self._runners[second])
            self._cost[handle] = self._cost[first] + self._cost[second]
            signature, calls = self._measure(self._runners[handle])
            self.budget.charge_pair(calls)
            parents = tuple(h for h in (self._dim_of.get(first), self._dim_of.get(second)) if h)
            produced.append(self._commit(handle, signature, event="compose", parents=parents))
        return produced

    def firewall(self) -> None:
        self.memory.firewall()
        self._dim_of = {}
        self._done_pairs = set()

    def _leaf(self, body: object) -> Runner:
        def run(probe: str) -> str:
            self._apply_calls += 1
            out = apply_micro(probe, body)
            if not isinstance(out, str):
                raise TypeError("apply_micro did not return a string")
            return out

        return run

    def _chain(self, first: Runner, second: Runner) -> Runner:
        def run(probe: str) -> str:
            return second(first(probe))

        return run

    def _measure(self, runner: Runner) -> tuple[BehavioralSignature, int]:
        start = self._apply_calls
        results: list[ProbeResult] = []
        for index, probe in enumerate(self.probes):
            try:
                out = runner(probe)
            except Exception:
                results.append(ProbeResult(index, None, "EXECUTION_FAILURE"))
                continue
            if out == probe:
                results.append(ProbeResult(index, out, "AMBIGUOUS_COPY"))
            else:
                results.append(ProbeResult(index, out, "NORMAL"))
        signature = BehavioralSignature(bank_hash=bank_hash(self.probes), results=tuple(results))
        return signature, self._apply_calls - start

    def _commit(
        self,
        handle: str,
        signature: BehavioralSignature,
        *,
        event: str,
        parents: tuple[str, ...],
    ) -> Observation:
        cid = content_id(signature) if signature.complete() else None
        state, dim_handle = self._classify(handle, signature, event, parents)
        return Observation(
            handle=handle,
            state=state,
            opaque_dimension_handle=dim_handle,
            content_id=cid,
            signature=signature,
            epoch=self.memory.epoch,
            event=event,
            parents=parents,
            purpose=self.purpose,
        )

    def _classify(
        self,
        handle: str,
        signature: BehavioralSignature,
        event: str,
        parents: tuple[str, ...],
    ) -> tuple[str, str | None]:
        if not signature.complete():
            return "INSUFFICIENT", None
        for dimension in self.memory.dimensions():
            relation = compare(signature, dimension.signature)
            if relation == OBSERVED_EQUIVALENT:
                dimension.observations.append(handle)
                self._dim_of[handle] = dimension.handle
                return "KNOWN_OBSERVATION", dimension.handle
            if relation != OBSERVED_DISTINCT:
                return "INSUFFICIENT", None
        dimension = BehavioralDimension(
            handle=self._dim_handle(),
            content_id=content_id(signature),
            bank_hash=signature.bank_hash,
            signature=signature,
            representative=handle,
            parents=parents,
            epoch=self.memory.epoch,
            event=event,
            observations=[handle],
        )
        self.memory.add(dimension)
        self._dim_of[handle] = dimension.handle
        return "NEW_DIMENSION", dimension.handle

    def _pairs(self) -> list[tuple[str, str]]:
        handles = sorted(handle for handle in self._runners if handle in self._dim_of)
        return [(left, right) for left in handles for right in handles if left != right]

    def _body_handle(self) -> str:
        self._next_body += 1
        return f"c-{self._next_body:04d}"

    def _dim_handle(self) -> str:
        self._next_dim += 1
        return f"d-{self._next_dim:04d}"


def sealed_receipt(observation: Observation) -> dict[str, str | None]:
    return {
        "opaque_handle": observation.handle,
        "discovery_state": observation.state,
        "opaque_dimension_handle": observation.opaque_dimension_handle,
        "bank_hash": observation.signature.bank_hash,
        "protocol_version": PROTOCOL_VERSION,
        "purpose": observation.purpose,
        "security": observation.security,
    }
