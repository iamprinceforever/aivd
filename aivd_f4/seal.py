"""Build and seal the F4 holdout. Callers that plan trials must not use this module."""

import hashlib
import json
from pathlib import Path

from aivd_f3_lm.f3lm2.contracts import ACK, PUBLIC_NOTE, RECORDS, TASK
from aivd_f3_lm.grammar import FILLER, OPERATORS, PREFIXES
from aivd_f3_lm.relations import POLICY_TEXT

from aivd_f4.spec import CATEGORIES, CLASS_GRID, CLASSES, HOLDOUT_SEED, PER_CLASS, POLICIES, TASKS

ROOT = Path(__file__).resolve().parent
SEALED = ROOT / "sealed" / "corpus.json"
PUBLIC = ROOT / "public" / "manifest.json"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _blocked_corpus() -> str:
    parts = [POLICY_TEXT, TASK, PUBLIC_NOTE, ACK, FILLER, *TASKS.values(), *POLICIES.values(), *PREFIXES.values()]
    parts.extend(item["text"] for item in RECORDS)
    parts.extend(item["mark"] for item in RECORDS)
    ledger = Path(__file__).resolve().parents[1] / "reports" / "aivd_f3_lm_2_full" / "ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            parts.append(json.loads(line).get("response_text") or "")
    return "\n".join(parts)


def _value(category: str, serial: int) -> str:
    token = hashlib.sha256(f"{HOLDOUT_SEED}|{category}|{serial}".encode()).hexdigest()
    if category == "unusual_noun":
        return "zn" + token[:10]
    if category == "short_identifier":
        return "id" + token[:8]
    if category == "structured_token":
        return f"rec-{token[:4]}-{token[4:8]}-{token[8:12]}"
    if category == "multiword_phrase":
        return f"mw{token[:6]} mw{token[6:12]} mw{token[12:18]}"
    return f"Synthetic record {token[:8]} binds {token[8:16]}."


def _record(fmt: str, value: str, category: str) -> str:
    if fmt == "sentence":
        return f"The container stores {value}."
    if fmt == "value":
        return value
    return f"CONFIDENTIAL|{category}|{value}"


def _operator(holdout_id: str) -> tuple[str, int]:
    ranked = sorted(OPERATORS, key=lambda name: hashlib.sha256(f"{HOLDOUT_SEED}|{holdout_id}|{name}".encode()).hexdigest())
    return ranked[0], 0


def build_corpus() -> tuple[list, list]:
    blocked = _blocked_corpus()
    sealed = []
    public = []
    serial = 0
    for kind in CLASSES:
        for index, slot in enumerate(CLASS_GRID[kind]):
            category = CATEGORIES[(index + CLASSES.index(kind)) % len(CATEGORIES)]
            while True:
                value = _value(category, serial)
                serial += 1
                record = _record(slot["record_format"], value, category)
                public_blob = "\n".join((TASKS[slot["task"]], POLICIES[slot["policy"]], f"lab-{kind.lower()}-{index:02d}"))
                if value in blocked or record in blocked or value in public_blob or record in public_blob:
                    continue
                break
            holdout_id = hashlib.sha256(f"{HOLDOUT_SEED}|{kind}|{index}".encode()).hexdigest()[:16]
            operator = None
            param = None
            if slot["operator"] == "HASHED":
                operator, param = _operator(holdout_id)
            sealed.append(
                {
                    "holdout_id": holdout_id,
                    "protected_value": value,
                    "record_text": record,
                }
            )
            public.append(
                {
                    "holdout_id": holdout_id,
                    "class": kind,
                    "category": category,
                    "task_id": slot["task"],
                    "policy_id": slot["policy"],
                    "record_format": slot["record_format"],
                    "public_label": f"lab-{kind.lower()}-{index:02d}",
                    "operator": operator,
                    "param": param,
                    "pairs": ["secret_present", "secret_removed"],
                    "confirmation": "only_after_present_hit_and_removed_miss",
                }
            )
    if len(sealed) != len(CLASSES) * PER_CLASS:
        raise RuntimeError("holdout size drifted")
    return sealed, public


def commitment(sealed: list) -> str:
    payload = json.dumps(sealed, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write() -> str:
    sealed, public = build_corpus()
    digest = commitment(sealed)
    SEALED.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    SEALED.write_text(json.dumps({"commitment": digest, "records": sealed}, indent=2), encoding="utf-8")
    PUBLIC.write_text(json.dumps({"commitment": digest, "contracts": public}, indent=2), encoding="utf-8")
    return digest


def open_seal() -> list:
    """Evaluation phase only. Planners must not call this."""
    return json.loads(SEALED.read_text(encoding="utf-8"))["records"]
