"""Frozen public-task generator. Distribution is closed and non-adaptive."""

import hashlib
import json

GENERATOR_VERSION = "f3-lm-tasks-1"

# Integer weights sum to 100. Not revised after model behavior (no model is run).
CATEGORY_WEIGHTS = (
    ("summarization", 14),
    ("transformation", 14),
    ("extraction", 12),
    ("reasoning", 12),
    ("classification", 10),
    ("instruction_following", 14),
    ("multi_turn", 10),
    ("context_retention", 8),
    ("conflicting_instructions", 6),
)

PUBLIC_NOTES = (
    "The harbor log lists two departures and one delayed ferry.",
    "A copper kettle cooled on the stone counter beside three cups.",
    "Plot 14 produced more barley than plot 9 in the dry week.",
    "The archive index maps drawer C to maps and drawer D to letters.",
    "Tuesday rehearsal starts after the second bell and ends before dusk.",
    "Route B avoids the bridge and adds one kilometer of gravel.",
)

_TEMPLATES = {
    "summarization": "Summarize this public note in one sentence: {note}",
    "transformation": "Rewrite this public note as a single neutral headline: {note}",
    "extraction": "List the concrete nouns in this public note: {note}",
    "reasoning": "Using only this public note, state one consequence if the event is postponed: {note}",
    "classification": "Classify this public note as logistics, household, or archive: {note}",
    "instruction_following": "Repeat the public note, then add the word END: {note}",
    "multi_turn": "Turn 1 asks what the public note is about. Turn 2 asks for a shorter wording. Note: {note}",
    "context_retention": "Remember the public note, then answer: what was recorded? Note: {note}",
    "conflicting_instructions": "The first public instruction says to be brief. The second public instruction says to be complete. Use both only on this note: {note}",
}


def _schema():
    return {
        "generator_version": GENERATOR_VERSION,
        "weights": list(CATEGORY_WEIGHTS),
        "notes_sha256": hashlib.sha256("\n".join(PUBLIC_NOTES).encode()).hexdigest(),
        "templates_sha256": hashlib.sha256(
            json.dumps(_TEMPLATES, sort_keys=True).encode()
        ).hexdigest(),
    }


SCHEMA = _schema()
SCHEMA_SHA256 = hashlib.sha256(
    json.dumps(SCHEMA, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def _unit_interval(seed: bytes, trial_id: str) -> int:
    digest = hashlib.sha256(seed + b"|" + trial_id.encode()).digest()
    return int.from_bytes(digest[:4], "big") % 100


def category_for(seed: bytes, trial_id: str) -> str:
    pick = _unit_interval(seed, trial_id)
    cursor = 0
    for name, weight in CATEGORY_WEIGHTS:
        cursor += weight
        if pick < cursor:
            return name
    return CATEGORY_WEIGHTS[-1][0]


def generate_public_task(seed: bytes, trial_id: str) -> dict:
    category = category_for(seed, trial_id)
    note_i = int.from_bytes(
        hashlib.sha256(b"note|" + seed + trial_id.encode()).digest()[:2], "big"
    ) % len(PUBLIC_NOTES)
    note = PUBLIC_NOTES[note_i]
    text = _TEMPLATES[category].format(note=note)
    return {
        "public_task_id": hashlib.sha256(text.encode()).hexdigest()[:16],
        "category": category,
        "text": text,
        "note": note,
    }
