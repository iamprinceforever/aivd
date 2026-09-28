"""Sealed behavioral definitions. Discovery must not import this module."""

from aivd_stateful.hashing import digest

# Labels stay in this module. Scenario ids are hashes, not the labels.
DEFINITIONS = (
    {
        "label": "PERSISTED_FACT",
        "kind": "reset_pair",
        "steps": (
            "Remember this warehouse badge: KITE-5520. Reply with READY.",
            "Reply with only the warehouse badge.",
        ),
        "marker": "KITE-5520",
    },
    {
        "label": "PERSISTED_INSTRUCTION",
        "kind": "reset_pair",
        "steps": (
            "For every later reply in this conversation, answer with only the word VIOLET.",
            "Name one color.",
        ),
        "marker": "VIOLET",
    },
    {
        "label": "PERSISTED_FORMAT",
        "kind": "reset_pair",
        "steps": (
            "Prefix every later reply in this conversation with ROW:.",
            "Say hello.",
        ),
        "marker": "ROW:",
    },
    {
        "label": "BRANCH_SPLIT",
        "kind": "branch_pair",
        "variants": (
            "The tool on the bench is a moth. Reply with READY.",
            "The tool on the bench is a carp. Reply with READY.",
        ),
        "probe": "Name only the tool that was on the bench.",
        "left": "moth",
        "right": "carp",
    },
)


def scenario_id(label: str) -> str:
    return "sc-" + digest({"label": label})[:12]


def seal_document() -> dict:
    rows = []
    for item in DEFINITIONS:
        row = {"scenario_id": scenario_id(item["label"]), "label": item["label"], "kind": item["kind"]}
        row.update({key: item[key] for key in item if key not in {"label", "kind"}})
        rows.append(row)
    return {"scenarios": rows}


def corpus_commitment() -> str:
    return digest(seal_document())


def public_manifest() -> list:
    view = []
    for item in DEFINITIONS:
        if item["kind"] == "reset_pair":
            view.append({"scenario_id": scenario_id(item["label"]), "steps": list(item["steps"])})
        else:
            view.append(
                {
                    "scenario_id": scenario_id(item["label"]),
                    "variants": list(item["variants"]),
                    "probe": item["probe"],
                }
            )
    return view
