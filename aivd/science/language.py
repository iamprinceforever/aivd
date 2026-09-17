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
from aivd.science.micro import Micro, apply_micro, canonicalize_micro
from aivd.science.operators import join_prompt, split_prompt


STATES = (
    "CANDIDATE",
    "VALIDATED",
    "LEASED",
    "ACTIVE",
    "PROMOTED",
    "REVOKED",
    "RETIRED",
)


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
    state: str = "CANDIDATE"
    parent_language: int = 0
    reason: str = ""


class ExperimentLanguage:
    """L_t: atoms, invented atoms, programs, failed regions."""

    def __init__(self) -> None:
        self.generation = 0
        self.language_id = "L0"
        self.parent_language = "L0"
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
        self.capability_state: dict[str, str] = {}
        self.reuse_history: list[dict[str, str]] = []
        self.retirement_history: list[str] = []
        self.known_boundaries: list[str] = []
        self.unresolved_questions: list[str] = []
        self.validation_evidence: dict[str, str] = {}
        self.growth_count = 0
        self.edges: list[dict[str, str]] = []

    def state_of(self, name: str) -> str:
        return self.capability_state.get(name, "")

    def program_keys(self) -> set[str]:
        return {r.body_key for r in self.records if r.kind in ("composition", "program") and r.body_key}

    def add_atom(self, atom: InventedAtom, *, grow: bool = True) -> bool:
        k = atom.key()
        if any(a.key() == k for a in self.invented):
            self.duplicates.append(k)
            self.events.append({"event": "language_duplicate", "key": k})
            return False
        self.invented.append(atom)
        self.fn_of[atom.name()] = make_fn(atom)
        self.capability_state[atom.name()] = "CANDIDATE"
        if grow:
            self._bump(atom, kind="atom", reason="materialize")
        else:
            rec = LanguageRecord(
                eid=atom.name(),
                kind="atom",
                generation=self.generation,
                deps=atom.deps or atom.lower_level_dependencies,
                novelty=atom.novelty,
                semantic_class=atom.semantic_class,
                provenance=atom.provenance,
                body_key=k,
                state="CANDIDATE",
                parent_language=self.generation,
                reason="candidate",
            )
            self.records.append(rec)
            self.events.append({"event": "language_candidate", "eid": atom.name(), "kind": "atom"})
        return True

    def promote(self, atom: InventedAtom, *, reason: str = "validated", evidence: str = "") -> bool:
        name = atom.name()
        if name not in self.capability_state and not any(a.name() == name for a in self.invented):
            self.add_atom(atom, grow=False)
        st = self.capability_state.get(name, "CANDIDATE")
        if st == "PROMOTED":
            return False
        self.capability_state[name] = "PROMOTED"
        self.validation_evidence[name] = evidence or reason
        self._bump(atom, kind="atom", reason=reason, state="PROMOTED")
        self.events.append({
            "event": "language_promote",
            "eid": name,
            "generation": str(self.generation),
            "reason": reason,
        })
        self.edges.append({
            "rel": "derived_from",
            "src": f"L{self.generation}",
            "dst": f"L{max(0, self.generation - 1)}",
        })
        self.edges.append({"rel": "validated_by", "src": name, "dst": reason})
        return True

    def _bump(self, atom: InventedAtom, *, kind: str, reason: str, state: str = "ACTIVE") -> None:
        parent = self.generation
        self.generation += 1
        self.parent_language = self.language_id
        self.language_id = f"L{self.generation}"
        rec = LanguageRecord(
            eid=atom.name(),
            kind=kind,
            generation=self.generation,
            deps=atom.deps or atom.lower_level_dependencies,
            novelty=atom.novelty,
            semantic_class=atom.semantic_class,
            provenance=atom.provenance,
            body_key=atom.key(),
            state=state,
            parent_language=parent,
            reason=reason,
        )
        self.records.append(rec)
        self.events.append({
            "event": "language_extend",
            "eid": atom.name(),
            "generation": str(self.generation),
            "kind": kind,
            "reason": reason,
        })

    def add_primitive_from_atom(self, atom: InventedAtom) -> LanguageRecord:
        self.generation += 1
        self.parent_language = f"L{self.generation - 1}"
        self.language_id = f"L{self.generation}"
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
            state="PROMOTED",
            parent_language=self.generation - 1,
            reason="atom_to_primitive",
        )
        self.records.append(rec)
        self.primitives.append(eid)
        self.fn_of[eid] = make_fn(atom)
        self.capability_state[eid] = "PROMOTED"
        self.edges.append({"rel": "depends_on", "src": eid, "dst": atom.name()})
        self.events.append({"event": "language_extend", "eid": eid, "kind": "primitive"})
        return rec

    def add_capability_from_primitive(self, prim: LanguageRecord) -> LanguageRecord:
        self.generation += 1
        self.parent_language = f"L{self.generation - 1}"
        self.language_id = f"L{self.generation}"
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
            state="PROMOTED",
            parent_language=self.generation - 1,
            reason="primitive_to_capability",
        )
        self.records.append(rec)
        self.operators.append(eid)
        if prim.eid in self.fn_of:
            self.fn_of[eid] = self.fn_of[prim.eid]
        self.capability_state[eid] = "PROMOTED"
        self.edges.append({"rel": "depends_on", "src": eid, "dst": prim.eid})
        self.events.append({"event": "language_extend", "eid": eid, "kind": "substrate"})
        return rec

    def compose(self, a: InventedAtom, b: InventedAtom) -> Callable[[str], str]:
        fa, fb = make_fn(a), make_fn(b)
        eid = ("cmp_" + a.name() + "_" + b.name())[:48]
        parent = self.generation
        self.generation += 1
        self.parent_language = f"L{parent}"
        self.language_id = f"L{self.generation}"
        rec = LanguageRecord(
            eid=eid,
            kind="composition",
            generation=self.generation,
            deps=(a.name(), b.name()),
            novelty="NEW_COMPOSITIONAL_CAPABILITY",
            semantic_class=a.semantic_class + "+" + b.semantic_class,
            provenance=a.provenance + b.provenance + ("compose",),
            body_key=a.key() + "|" + b.key(),
            state="PROMOTED",
            parent_language=parent,
            reason="compose",
        )
        self.records.append(rec)
        self.programs.append(eid)
        self.capability_state[eid] = "PROMOTED"
        self.growth_count += 1
        self.edges.append({"rel": "uses", "src": eid, "dst": a.name()})
        self.edges.append({"rel": "uses", "src": eid, "dst": b.name()})
        self.edges.append({"rel": "depends_on", "src": eid, "dst": a.name()})

        def fn(p: str, _fa=fa, _fb=fb) -> str:
            return _fb(_fa(p))

        self.fn_of[eid] = fn
        self.events.append({"event": "language_compose", "eid": eid, "a": a.name(), "b": b.name()})
        return fn

    def add_program(self, atom: InventedAtom, *, reason: str = "growth") -> bool:
        k = atom.key()
        if k in self.program_keys() or any(a.key() == k for a in self.invented):
            self.duplicates.append(k)
            return False
        self.invented.append(atom)
        self.fn_of[atom.name()] = make_fn(atom)
        parent = self.generation
        self.generation += 1
        self.parent_language = f"L{parent}"
        self.language_id = f"L{self.generation}"
        rec = LanguageRecord(
            eid=atom.name(),
            kind="program",
            generation=self.generation,
            deps=atom.parent or atom.lower_level_dependencies,
            novelty=atom.novelty,
            semantic_class=atom.semantic_class,
            provenance=atom.provenance,
            body_key=k,
            state="PROMOTED",
            parent_language=parent,
            reason=reason,
        )
        self.records.append(rec)
        self.programs.append(atom.name())
        self.capability_state[atom.name()] = "PROMOTED"
        self.growth_count += 1
        for dep in rec.deps:
            self.edges.append({"rel": "uses", "src": atom.name(), "dst": dep})
            self.edges.append({"rel": "depends_on", "src": atom.name(), "dst": dep})
        self.events.append({
            "event": "language_grow",
            "eid": atom.name(),
            "generation": str(self.generation),
            "reason": reason,
        })
        return True

    def mark_reuse(self, name: str, *, useful: bool = False) -> None:
        self.reuse_history.append({"eid": name, "useful": "1" if useful else "0"})
        self.events.append({"event": "language_reuse", "eid": name, "useful": str(useful)})

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
        out.extend("program " + p for p in self.programs)
        return out

    def cannot_express(self) -> list[str]:
        have = {a.semantic_class for a in self.invented}
        regions = [
            ("char_index_glue", "intra-token char-index glue"),
            ("char_stride", "intra-token character stride"),
            ("char_project", "intra-token character projection"),
        ]
        return [label for key, label in regions if key not in have]

    def graph(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": r.eid,
                    "kind": r.kind,
                    "generation": r.generation,
                    "state": r.state,
                    "semantic_class": r.semantic_class,
                }
                for r in self.records
            ],
            "edges": list(self.edges[-48:]),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "language_id": self.language_id,
            "parent_language": self.parent_language,
            "capability_state": dict(self.capability_state),
            "atoms": [
                {
                    "atom_id": a.atom_id,
                    "body": _micro_to_dict(a.body),
                    "semantic_class": a.semantic_class,
                    "novelty": a.novelty,
                    "why": a.why,
                    "proposal_index": a.proposal_index,
                    "parent": list(a.parent),
                    "provenance": list(a.provenance),
                }
                for a in self.invented
            ],
            "programs": list(self.programs),
            "reuse_history": list(self.reuse_history),
        }

    def restore(self, snap: dict[str, Any]) -> None:
        from aivd.science.atom import InventedAtom as IA
        self.generation = int(snap.get("generation") or 0)
        self.language_id = str(snap.get("language_id") or f"L{self.generation}")
        self.parent_language = str(snap.get("parent_language") or "L0")
        self.capability_state = dict(snap.get("capability_state") or {})
        self.programs = list(snap.get("programs") or [])
        self.reuse_history = list(snap.get("reuse_history") or [])
        self.invented = []
        self.fn_of = {}
        for row in snap.get("atoms") or []:
            body = _dict_to_micro(row.get("body") or {})
            if body is None:
                continue
            atom = IA(
                atom_id=str(row.get("atom_id") or ""),
                body=body,
                why=str(row.get("why") or ""),
                novelty=str(row.get("novelty") or ""),
                semantic_class=str(row.get("semantic_class") or ""),
                parent=tuple(row.get("parent") or ()),
                provenance=tuple(row.get("provenance") or ()),
                proposal_index=int(row.get("proposal_index") or 0),
            )
            self.invented.append(atom)
            self.fn_of[atom.name()] = make_fn(atom)

    def describe(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "L_t": self.generation,
            "language_id": self.language_id,
            "parent_language": self.parent_language,
            "base_atoms": list(self.base_atoms),
            "invented_atoms": [a.name() for a in self.invented],
            "invented_classes": [a.semantic_class for a in self.invented],
            "programs": list(self.programs),
            "primitives": list(self.primitives),
            "operators": list(self.operators),
            "rejected": list(self.rejected),
            "duplicates": list(self.duplicates),
            "capability_state": dict(self.capability_state),
            "growth_count": self.growth_count,
            "reuse": list(self.reuse_history[-12:]),
            "can_express": self.can_express(),
            "cannot_express": self.cannot_express(),
            "graph": self.graph(),
            "records": [
                {
                    "eid": r.eid,
                    "kind": r.kind,
                    "generation": r.generation,
                    "deps": list(r.deps),
                    "novelty": r.novelty,
                    "semantic_class": r.semantic_class,
                    "provenance": list(r.provenance),
                    "state": r.state,
                    "reason": r.reason,
                }
                for r in self.records
            ],
        }


def _micro_to_dict(m: Micro) -> dict[str, Any]:
    return {
        "op": m.op,
        "args": list(m.args),
        "kids": [_micro_to_dict(k) for k in m.kids],
    }


def _dict_to_micro(d: dict[str, Any]) -> Micro | None:
    if not d or not d.get("op"):
        return None
    kids = tuple(k for k in (_dict_to_micro(x) for x in (d.get("kids") or [])) if k is not None)
    return canonicalize_micro(Micro(str(d["op"]), tuple(d.get("args") or ()), kids))


def apply_composed(prompt: str, fns: list[Callable[[str], str]]) -> str:
    out = prompt
    for fn in fns:
        out = fn(out)
    toks = split_prompt(out)
    return join_prompt(toks) if toks else out


__all__ = ["ExperimentLanguage", "LanguageRecord", "apply_composed", "STATES"]
