"""Tree serialization for the sealed package. Not a public identifier."""

from __future__ import annotations

from aivd.science.micro import Micro


def dump_micro(body: Micro) -> dict[str, object]:
    return {"op": body.op, "args": list(body.args), "kids": [dump_micro(kid) for kid in body.kids]}


def load_micro(payload: dict[str, object]) -> Micro:
    kids = tuple(load_micro(kid) for kid in payload["kids"])  # type: ignore[index]
    args = tuple(payload["args"])  # type: ignore[arg-type]
    return Micro(str(payload["op"]), args, kids)
