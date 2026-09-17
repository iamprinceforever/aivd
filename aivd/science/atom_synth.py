"""Question-directed atom invention. Not a random mutator.

Invoked only after 3.32 substrate operators fail to distinguish remaining
hypotheses. Candidates are micro-language programs, not holdout names
and not an expansion of the 3.32 atom catalog.
"""
from __future__ import annotations

from typing import Any

from aivd.science.atom import (
    NOVELTY_DUPLICATE,
    NOVELTY_EXISTING_ATOM,
    InventedAtom,
    AtomInventory,
    LEVEL_INVENTED_ATOM,
    LEVEL_LANGUAGE_EXTENSION,
    classify_atom,
    make_fn,
    semantic_class_of,
)
from aivd.science.micro import (
    Micro,
    apply_micro,
    canonicalize_micro,
    micro_name,
    validate_micro,
)
from aivd.science.operators import split_prompt


def propose_atoms(
    *,
    prompt: str,
    question: bool,
    n_tokens: int | None = None,
) -> list[InventedAtom]:
    """Deterministic, bounded candidate set from intra-token geometry.

    After 3.32 (token-opaque glue / stride / fold), remaining computational
    classes are: char-index glue, character stride, character projection.
    Not a catalog of named historical plants.
    """
    if not question:
        return []
    toks = split_prompt(prompt)
    n = n_tokens if n_tokens is not None else len(toks)
    if n < 2:
        return []
    if not any(len(t) >= 2 for t in toks):
        return []
    why = "discriminate residual after 3.32 operators exhausted"
    tok = Micro("TOK")
    last = Micro("AT", (-1,))
    first = Micro("AT", (0,))
    raw: list[Micro] = [
        # Char-index glue: each token concatenated with a positional char.
        Micro("MAPT", kids=(Micro("CAT", kids=(tok, last)),)),
        # Intra-token character stride.
        Micro("MAPT", kids=(Micro("SLICE", (0, 2), kids=(tok,)),)),
        Micro("MAPT", kids=(Micro("CAT", kids=(last, tok)),)),
        Micro("MAPT", kids=(Micro("SLICE", (1, 2), kids=(tok,)),)),
        Micro("MAPT", kids=(last,)),
        Micro("MAPT", kids=(Micro("CAT", kids=(tok, first)),)),
        Micro("MAPT", kids=(Micro("CAT", kids=(first, last)),)),
        Micro("MAPT", kids=(Micro("SLICE", (0, 3), kids=(tok,)),)),
    ]
    out: list[InventedAtom] = []
    seen: set[str] = set()
    for body in raw:
        body2 = canonicalize_micro(body)
        if body2 is None:
            continue
        if validate_micro(body2, n_tokens=n) is not None:
            continue
        k = body2.key()
        if k in seen:
            continue
        seen.add(k)
        pid = micro_name(body2)
        out.append(InventedAtom(
            atom_id=pid,
            body=body2,
            why=why,
            origin="atom_synth",
            depth=body2.depth(),
            complexity=body2.nodes(),
            predicted="intra-token transform the 3.32 atoms cannot name",
            cost=1,
            semantic_class=semantic_class_of(body2),
            parent=tuple(sorted({body2.op} | {k.op for k in body2.kids})),
            lower_level_dependencies=("micro",),
            proposal_index=len(out),
            provenance=(
                "observation",
                "unresolved_question",
                "3.32_operators_insufficient",
                "atom_capability_hypothesis",
                "micro_candidate",
            ),
        ))
    return out[:8]


class AtomSynthesizer:
    def __init__(
        self,
        *,
        filter_novelty: bool = True,
        require_question: bool = True,
    ) -> None:
        self.board = AtomInventory()
        self.op_of: dict[str, InventedAtom] = {}
        self.family_id = "synth.atom"
        self.filter_novelty = bool(filter_novelty)
        self.require_question = bool(require_question)

    def plan(
        self,
        *,
        prompt: str,
        question: bool,
        known_ops: set[str],
    ) -> list[InventedAtom]:
        if self.require_question and not question:
            self.board.without_question += 1
            self.board.farming += 1
            self.board.events.append({"event": "atom_blocked", "why": "no_unresolved_question"})
            return []
        if self.board.generated >= self.board.max_generated and not self.board.remaining:
            self.board.farming += 1
            return []
        if self.board.remaining or self.board.materialized:
            return list(self.board.remaining)
        self.board.language_hypotheses += 1
        raw = propose_atoms(prompt=prompt, question=True)
        n = len(split_prompt(prompt))
        kept: list[InventedAtom] = []
        known_keys = set(self.board.seen)
        probes = (prompt, "ab cd efg hij")
        behaviors: dict[str, str] = {}
        for atom in raw:
            self.board.generated += 1
            k = atom.key()
            if k in self.board.seen:
                self.board.duplicates += 1
                continue
            if validate_micro(atom.body, n_tokens=n) is not None:
                self.board.validation_fail += 1
                continue
            try:
                got = apply_micro(prompt, atom.body)
            except Exception:
                self.board.validation_fail += 1
                continue
            if got == prompt:
                self.board.validation_fail += 1
                self.board.seen.add(k)
                continue
            try:
                g2 = apply_micro(probes[1], atom.body)
            except Exception:
                self.board.validation_fail += 1
                continue
            if not g2:
                self.board.validation_fail += 1
                continue
            nov = classify_atom(
                atom,
                n_tokens=n,
                known_ops=known_ops,
                known_keys=known_keys,
                identity=prompt,
                filter_novelty=self.filter_novelty,
                known_behaviors=behaviors,
            )
            if nov in (NOVELTY_DUPLICATE, NOVELTY_EXISTING_ATOM):
                self.board.duplicates += 1
                self.board.seen.add(k)
                self.board.events.append({"event": "atom_duplicate", "key": k, "novelty": nov})
                continue
            level = LEVEL_LANGUAGE_EXTENSION if nov == "INVENTED_ATOM" else LEVEL_INVENTED_ATOM
            atom = InventedAtom(
                atom_id=atom.atom_id,
                body=atom.body,
                origin=atom.origin,
                why=atom.why,
                depth=atom.depth,
                complexity=atom.complexity,
                novelty=nov,
                level=level,
                predicted=atom.predicted,
                cost=atom.cost,
                parent=atom.parent,
                semantic_class=atom.semantic_class,
                lower_level_dependencies=atom.lower_level_dependencies,
                provenance=atom.provenance + ("semantic_validation", "promotion"),
                validation=("structural", "execution", "semantic", "repro"),
                proposal_index=atom.proposal_index,
            )
            self.board.seen.add(k)
            known_keys.add(k)
            behaviors[k] = got
            self.board.validation_ok += 1
            kept.append(atom)
            self.board.events.append({
                "event": "atom_validate",
                "key": k,
                "novelty": nov,
                "level": level,
                "name": atom.name(),
                "semantic_class": atom.semantic_class,
            })
            if len(kept) >= self.board.max_generated:
                break
        self.board.remaining = list(kept)
        return list(kept)

    def next_atom(self) -> InventedAtom | None:
        if self.board.executed >= self.board.max_executed:
            return None
        if not self.board.remaining:
            return None
        return self.board.remaining.pop(0)

    def make_fn(self, atom: InventedAtom):
        return make_fn(atom)

    def telemetry(self) -> dict[str, Any]:
        return self.board.telemetry()


__all__ = ["AtomSynthesizer", "propose_atoms"]
