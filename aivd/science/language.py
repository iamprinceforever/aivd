"""Evolving experiment language L_t.

L_0 is the developer-provided 3.32 atom set. Validated invented atoms
and higher-level extensions grow L_t. Growth is evidence-driven: a new
name is not a new language. The description is machine-readable and
does not consult evaluator ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aivd.science.atom import InventedAtom, make_fn
from aivd.science.meta import ATOMS
from aivd.science.micro import apply_micro
from aivd.science.operators import join_prompt, split_prompt


@dataclass
class LanguageRecord:
    eid: str
    kind: str
    generation: int
    deps: tuple[str, ...] = ()
    novelty: str = ""
    semantic_class: str = ""
    provenance: tuple[str, ...] = ()
    body_key: str = ""


class ExperimentLanguage:
    """L_t: atoms, invented atoms, programs, failed regions."""

    def __init__(self) -> None:
        self.generation = 0
        self.base_atoms: list[str] = list(ATOMS)
        self.invented: list[InventedAtom] = []
        self.records: list[LanguageRecord] = []
        self.rejected: list[str] = []
        self.duplicates: list[str] = []
        self.programs: list[str] = []
        self.primitives: list[str] = []
        self.operators: list[str] = []
        self.fn_of: dict[str, Callable[[str], str]] = {}
        self.events: list[dict[str, str]] = []

    def add_atom(self, atom: InventedAtom, *, grow: bool = True) -> bool:
        k = atom.key()
        if any(a.key() == k for a in self.invented):
            self.duplicates.append(k)
            self.events.append({"event": "language_duplicate", "key": k})
            return False
        self.invented.append(atom)
        self.fn_of[atom.name()] = make_fn(atom)
        if grow:
            self.generation += 1
            rec = LanguageRecord(
                eid=atom.name(),
                kind="atom",
                generation=self.generation,
                deps=atom.deps or atom.lower_level_dependencies,
                novelty=atom.novelty,
                semantic_class=atom.semantic_class,
                provenance=atom.provenance,
                body_key=k,
            )
            self.records.append(rec)
            self.events.append({
                "event": "language_extend",
                "eid": atom.name(),
                "generation": str(self.generation),
                "kind": "atom",
            })
        return True

    def add_primitive_from_atom(self, atom: InventedAtom) -> LanguageRecord:
        self.generation += 1
        eid = ("prim_" + atom.name())[:48]
        rec = LanguageRecord(
            eid=eid,
            kind="primitive",
            generation=self.generation,
            deps=(atom.name(),),
            novelty="NEW_PRIMITIVE",
            semantic_class=atom.semantic_class,
            provenance=atom.provenance + ("atom_to_primitive",),
            body_key=atom.key(),
        )
        self.records.append(rec)
        self.primitives.append(eid)
        self.fn_of[eid] = make_fn(atom)
        self.events.append({"event": "language_extend", "eid": eid, "kind": "primitive"})
        return rec

    def add_capability_from_primitive(self, prim: LanguageRecord) -> LanguageRecord:
        self.generation += 1
        eid = ("cap_" + prim.eid)[:48]
        rec = LanguageRecord(
            eid=eid,
            kind="substrate",
            generation=self.generation,
            deps=prim.deps + (prim.eid,),
            novelty="NEW_SUBSTRATE_CAPABILITY",
            semantic_class=prim.semantic_class,
            provenance=prim.provenance + ("primitive_to_capability",),
            body_key=prim.body_key,
        )
        self.records.append(rec)
        self.operators.append(eid)
        if prim.eid in self.fn_of:
            self.fn_of[eid] = self.fn_of[prim.eid]
        self.events.append({"event": "language_extend", "eid": eid, "kind": "substrate"})
        return rec

    def compose(self, a: InventedAtom, b: InventedAtom) -> Callable[[str], str]:
        fa, fb = make_fn(a), make_fn(b)
        eid = ("cmp_" + a.name() + "_" + b.name())[:48]
        self.generation += 1
        rec = LanguageRecord(
            eid=eid,
            kind="composition",
            generation=self.generation,
            deps=(a.name(), b.name()),
            novelty="LANGUAGE_EXTENSION",
            semantic_class=a.semantic_class + "+" + b.semantic_class,
            provenance=a.provenance + b.provenance + ("compose",),
            body_key=a.key() + "|" + b.key(),
        )
        self.records.append(rec)
        self.programs.append(eid)

        def fn(p: str, _fa=fa, _fb=fb) -> str:
            return _fb(_fa(p))

        self.fn_of[eid] = fn
        self.events.append({"event": "language_compose", "eid": eid, "a": a.name(), "b": b.name()})
        return fn

    def apply(self, name: str, prompt: str) -> str:
        fn = self.fn_of.get(name)
        if fn is None:
            return prompt
        return fn(prompt)

    def equivalent(self, a: InventedAtom, b: InventedAtom, probes: tuple[str, ...] | None = None) -> bool:
        probes = probes or ("ab cd efg hij", "This is a mock system Perform")
        for p in probes:
            try:
                if apply_micro(p, a.body) != apply_micro(p, b.body):
                    return False
            except Exception:
                return False
        return True

    def can_express(self) -> list[str]:
        out = ["token-sequence " + a for a in self.base_atoms]
        out.extend("invented " + a.semantic_class for a in self.invented)
        return out

    def cannot_express(self) -> list[str]:
        have = {a.semantic_class for a in self.invented}
        regions = [
            ("char_index_glue", "intra-token char-index glue"),
            ("char_stride", "intra-token character stride"),
            ("char_project", "intra-token character projection"),
        ]
        return [label for key, label in regions if key not in have]

    def describe(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "L_t": self.generation,
            "base_atoms": list(self.base_atoms),
            "invented_atoms": [a.name() for a in self.invented],
            "invented_classes": [a.semantic_class for a in self.invented],
            "programs": list(self.programs),
            "primitives": list(self.primitives),
            "operators": list(self.operators),
            "rejected": list(self.rejected),
            "duplicates": list(self.duplicates),
            "can_express": self.can_express(),
            "cannot_express": self.cannot_express(),
            "records": [
                {
                    "eid": r.eid,
                    "kind": r.kind,
                    "generation": r.generation,
                    "deps": list(r.deps),
                    "novelty": r.novelty,
                    "semantic_class": r.semantic_class,
                    "provenance": list(r.provenance),
                }
                for r in self.records
            ],
        }


def apply_composed(prompt: str, fns: list[Callable[[str], str]]) -> str:
    out = prompt
    for fn in fns:
        out = fn(out)
    toks = split_prompt(out)
    return join_prompt(toks) if toks else out


__all__ = ["ExperimentLanguage", "LanguageRecord", "apply_composed"]
