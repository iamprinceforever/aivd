"""One authorized pass over the frozen F2 samples. It does not edit the protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from aivd.behavior.sealed_corpus.grammar import generate_bodies
from aivd.experiments.aivd40.stage_4_2.cel_exec import execute as execute_cel
from aivd.experiments.aivd40.stage_4_2.firewall import AUTHORIZED
from aivd.experiments.aivd40.stage_4_2.freeze import (
    BANK_HASH,
    CEL_COMMIT,
    CEL_VERSION,
    MICRO_SAMPLE_SIZE,
    MICRO_SEED,
    SELECTION_HASH,
    require_bank,
    require_selection,
)
from aivd.experiments.aivd40.stage_4_2.micro_exec import execute as execute_micro
from aivd.experiments.aivd40.stage_4_2.observation import (
    BehavioralMemory,
    BehavioralObservation,
    BehavioralSignature,
    make_signature,
)
from aivd.science.micro import Micro

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports" / "aivd_f2_execution"
os.environ[AUTHORIZED] = "1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _measure_micro(program: Micro, probes: list[dict]) -> tuple[BehavioralObservation, ...]:
    return tuple(execute_micro(program, probe["value"]) for probe in probes)


def _measure_cel(expression: str, probes: list[dict]) -> tuple[BehavioralObservation, ...]:
    return tuple(execute_cel(expression, probe["value"]) for probe in probes)


def _pack(rows: tuple[BehavioralObservation, ...]) -> list[dict]:
    return [{"canonical": row.canonical, "status": row.status} for row in rows]


def _remember(memory: BehavioralMemory, signature: BehavioralSignature, handle: str, language: str) -> str:
    if not signature.complete():
        return "INSUFFICIENT"
    before = set(memory.dimensions())
    memory.add(signature, handle, language)
    if signature.content_id() not in before:
        return "NEW_OBSERVED_BEHAVIOR"
    return "OBSERVED_EQUIVALENT"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    binary = Path("/tmp/aivd-f2-celbin")
    if binary.exists():
        binary.unlink()
    science = subprocess.check_output(
        ["git", "diff", "--stat", "HEAD", "--", "aivd/science", "aivd/experiments/aivd40/f1"],
        cwd=ROOT,
        text=True,
    )
    if science.strip():
        raise SystemExit("science or F1 differs from HEAD")
    bank = require_bank()
    selection = require_selection()
    probes = bank["probes"]
    sources = tuple(selection["cel"]["sources"])
    bodies = generate_bodies(MICRO_SEED.encode(), MICRO_SAMPLE_SIZE)
    keys = tuple(body.key() for body in bodies)
    micro_hash = _sha("\n".join(keys))
    cel_hash = _sha("\n".join(sources))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    _dump(
        OUT / "pre_run.json",
        {
            "bank_hash": BANK_HASH,
            "cel_commit": CEL_COMMIT,
            "cel_sample_hash": cel_hash,
            "cel_version": CEL_VERSION,
            "design_commit": "3cedb97a853a71bad8d0b4289bf82cd1d12d32b7",
            "f1_diff": "empty",
            "firewall": "authorized for this process only",
            "implementation_commit": "e3ae322832cb704ecdd8226f1a80b8927935a5cb",
            "micro_sample_hash": micro_hash,
            "parent_head": head,
            "probe_count": len(probes),
            "science_diff": "empty",
            "selection_hash": SELECTION_HASH,
        },
    )
    micro_handles = [f"m{index:02d}" for index in range(len(bodies))]
    cel_handles = [f"c{index:02d}" for index in range(len(sources))]
    micro_rows = [_measure_micro(body, probes) for body in bodies]
    cel_rows = [_measure_cel(source, probes) for source in sources]
    micro_sigs = [make_signature(BANK_HASH, rows) for rows in micro_rows]
    cel_sigs = [make_signature(BANK_HASH, rows) for rows in cel_rows]

    def condition(pairs: list[tuple[str, str, BehavioralSignature]]) -> dict:
        memory = BehavioralMemory()
        events = []
        for handle, language, signature in pairs:
            events.append(
                {
                    "event": _remember(memory, signature, handle, language),
                    "handle": handle,
                    "signature": signature.content_id(),
                }
            )
        return {"dimensions": list(memory.dimensions()), "events": events}

    x1_pairs = [(handle, "micro", sig) for handle, sig in zip(micro_handles, micro_sigs)]
    x2_pairs = [(handle, "cel", sig) for handle, sig in zip(cel_handles, cel_sigs)]
    x1 = condition(x1_pairs)
    x2 = condition(x2_pairs)
    x3 = condition(x1_pairs + x2_pairs)
    equivalents = []
    distinct = []
    for m_handle, m_sig in zip(micro_handles, micro_sigs):
        for c_handle, c_sig in zip(cel_handles, cel_sigs):
            pair = {"cel": c_handle, "micro": m_handle}
            if not m_sig.complete() or not c_sig.complete():
                pair["relation"] = "INSUFFICIENT"
                distinct.append(pair)
                continue
            if m_sig.content_id() == c_sig.content_id():
                pair["relation"] = "OBSERVATIONALLY_EQUIVALENT_ON_FROZEN_BANK"
                equivalents.append(pair)
            else:
                pair["relation"] = "DISTINCT_ON_FROZEN_BANK"
                distinct.append(pair)
    ledger = []
    for handle, rows in list(zip(micro_handles, micro_rows)) + list(zip(cel_handles, cel_rows)):
        for index, row in enumerate(rows):
            ledger.append(
                {
                    "canonical": row.canonical,
                    "handle": handle,
                    "probe_index": index,
                    "status": row.status,
                }
            )
    ledger_bytes = json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode()
    ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    _dump(OUT / "ledger.json", {"hash": ledger_hash, "rows": ledger})
    _dump(OUT / "lock.json", {"ledger_hash": ledger_hash, "order": "ledger file written before reveal"})
    reveal = {
        "cel": [{"handle": handle, "source": source} for handle, source in zip(cel_handles, sources)],
        "micro": [{"handle": handle, "source": key} for handle, key in zip(micro_handles, keys)],
    }
    _dump(OUT / "reveal.json", reveal)
    controls = _controls(probes, micro_sigs, cel_sigs, sources)
    replay = _replay(probes, bodies, sources, micro_rows, cel_rows, controls)
    _dump(
        OUT / "primary.json",
        {
            "cel_sample_hash": cel_hash,
            "controls": controls,
            "cross_language_distinct": distinct,
            "cross_language_equivalent": equivalents,
            "ledger_hash": ledger_hash,
            "micro_sample_hash": micro_hash,
            "replay": replay,
            "x1": x1,
            "x2": x2,
            "x3": x3,
        },
    )


def _controls(probes, micro_sigs, cel_sigs, sources) -> list[dict]:
    results = []
    tok = execute_micro(Micro("TOK"), probes) if False else _measure_micro(Micro("TOK"), probes)
    identity = _measure_cel("input", probes)
    doubled = _measure_cel("input + input", probes)
    missing = _measure_cel("missing", probes)
    nested = _measure_micro(Micro("REV", (), (Micro("REV", (), (Micro("TOK"),)),)), probes)
    tok_sig = make_signature(BANK_HASH, tok)
    identity_sig = make_signature(BANK_HASH, identity)
    doubled_sig = make_signature(BANK_HASH, doubled)
    missing_sig = make_signature(BANK_HASH, missing)
    nested_sig = make_signature(BANK_HASH, nested)
    plan = [
        ("C1", "same", tok_sig, identity_sig),
        ("C2", "distinct", identity_sig, doubled_sig),
        ("C3", "same", identity_sig, make_signature(BANK_HASH, _measure_cel("input", probes))),
        ("C4", "same", tok_sig, nested_sig),
    ]
    stopped = False
    for name, expect, left, right in plan:
        if stopped:
            results.append({"control": name, "result": "NOT_RUN"})
            continue
        if not left.complete() or not right.complete():
            observed = "incomplete"
        elif left.content_id() == right.content_id():
            observed = "same"
        else:
            observed = "distinct"
        passed = observed == expect
        results.append({"control": name, "observed": observed, "result": "PASS" if passed else "FAIL"})
        stopped = not passed
    if not stopped:
        memory = BehavioralMemory()
        created = memory.add(missing_sig, "c5", "cel")
        passed = created is None
        results.append({"control": "C5", "result": "PASS" if passed else "FAIL"})
        stopped = not passed
    else:
        results.append({"control": "C5", "result": "NOT_RUN"})
    if not stopped:
        memory = BehavioralMemory()
        blocked = make_signature(BANK_HASH, (BehavioralObservation("AMBIGUOUS", None),))
        passed = memory.add(blocked, "c6", "fixture") is None
        results.append({"control": "C6", "result": "PASS" if passed else "FAIL"})
    else:
        results.append({"control": "C6", "result": "NOT_RUN"})
    results.append(
        {
            "observations": {
                "c2_right": _pack(doubled),
                "c4_nested": _pack(nested),
                "c5_missing": _pack(missing),
                "identity": _pack(identity),
                "tok": _pack(tok),
            }
        }
    )
    return results


def _replay(probes, bodies, sources, micro_rows, cel_rows, controls) -> dict:
    failed = any(item.get("result") == "FAIL" for item in controls if "result" in item)
    if failed:
        return {"result": "NOT_RUN", "reason": "a control failed"}
    for body, rows in zip(bodies, micro_rows):
        again = _measure_micro(body, probes)
        if _pack(again) != _pack(rows):
            return {"result": "REPLAY_MISMATCH"}
    for source, rows in zip(sources, cel_rows):
        again = _measure_cel(source, probes)
        if _pack(again) != _pack(rows):
            return {"result": "REPLAY_MISMATCH"}
    return {"result": "MATCH"}


if __name__ == "__main__":
    main()
