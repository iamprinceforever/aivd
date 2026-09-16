"""Design the next experiment to discriminate remaining hypotheses.

3.21: keep a LIVE informative state. When a continuation collapses,
do not chain the dead prompt. Invent a new method from the live state
and keep spending remaining budget.
"""
from __future__ import annotations

from typing import Any

from aivd.epistemic.types import ExperimentProposal
from aivd.science.contrast import Contrast, contrast
from aivd.science.hypotheses import HypothesisBoard
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.commit import CommitmentBoard
from aivd.science.families import FamilyInventory
from aivd.science.synth import InterventionSynthesizer
from aivd.science.primitive_synth import PrimitiveSynthesizer
from aivd.science.gap import (
    compile_from_harvest,
    compile_from_structure,
    compile_record_forms,
    compile_field_delims,
    compile_one_field,
    field_family_spec,
    gap_hypothesis,
    harvest_unseen_chars,
)
from aivd.science.operators import BATTERY, apply_operator, apply_sequence, split_prompt


class ScienceDesigner:
    """Hypothesis → experiment. Residual tokens are not the search."""

    def __init__(self, *, seed_prompt: str, seed: int = 0, max_new: int = 16, mode: str = "off"):
        self.seed_prompt = seed_prompt
        self.seed = int(seed)
        self.max_new = int(max_new)
        self.mode = str(mode or "off")
        self.allow_intra = any(v in self.mode for v in ("3_24", "3_25", "3_26", "3_27", "3_28", "3_29", "3_30", "3_31"))
        self.allow_gap = any(v in self.mode for v in ("3_25", "3_26", "3_27", "3_28", "3_29", "3_30", "3_31"))
        self.allow_struct = any(v in self.mode for v in ("3_26", "3_27", "3_28", "3_29", "3_30", "3_31"))
        self.allow_commit = any(v in self.mode for v in ("3_27", "3_28", "3_29", "3_30", "3_31"))
        self.allow_wave2 = "3_28" in self.mode and "3_29" not in self.mode and "3_30" not in self.mode and "3_31" not in self.mode
        self.allow_lazy = "3_29" in self.mode or "3_30" in self.mode or "3_31" in self.mode
        self.allow_synth = "3_30" in self.mode or "3_31" in self.mode
        self.allow_prim = "3_31" in self.mode
        self.allow_prim_lease = self.allow_prim and "nolease" not in self.mode
        self.allow_prim_lazy = self.allow_prim and "nolazy" not in self.mode
        self.wave2_compiled = False
        self.families = FamilyInventory()
        self.synthesizer = InterventionSynthesizer()
        self.prim_synth = PrimitiveSynthesizer()
        self.field_spec: dict | None = None
        self.failure_class: str | None = None
        self.commitments = CommitmentBoard()
        self.ontology_insufficient = False
        self.harvested_texts: list[str] = []
        self.abstract_dimensions: list[Any] = []
        self.gap_compiled = False
        self.board = HypothesisBoard(seed=seed)
        self.tested: set[str] = set()
        self.seq = 0
        self.supported_ops: list[str] = []
        self.trap_ops: list[str] = []
        self.last_prompt = seed_prompt
        self.last_ops: list[str] = []
        self.history: list[dict[str, Any]] = []
        self.content_tokens: list[str] = []
        self.recent_tokens: list[str] = []
        self.live_prompt = seed_prompt
        self.live_ops: list[str] = []
        self.live_metric = 0.0
        self.live_error = ""
        self.collapsed = False
        self.tried_on_live: set[str] = set()
        self.inventor = MethodInventor()
        self.methods_log: list[dict[str, str]] = []
        self.hot_indices: list[int] = []
        self.identity_prompt = seed_prompt
        self.representation_gap = False
        self.board = HypothesisBoard(seed=seed)
        self.tested: set[str] = set()
        self.seq = 0
        self.supported_ops: list[str] = []
        self.trap_ops: list[str] = []
        self.last_prompt = seed_prompt
        self.last_ops: list[str] = []
        self.history: list[dict[str, Any]] = []
        self.content_tokens: list[str] = []
        self.recent_tokens: list[str] = []
        self.live_prompt = seed_prompt
        self.live_ops: list[str] = []
        self.live_metric = 0.0
        self.live_error = ""
        self.collapsed = False
        self.tried_on_live: set[str] = set()
        self.inventor = MethodInventor()
        self.methods_log: list[dict[str, str]] = []
        for op in BATTERY:
            self.board.add(
                f"op:{op}",
                f"security-relevant behavior is gated by operator {op}",
                [op],
                prior=0.35,
                why="generic structural edit; competing, not assumed",
            )

    @property
    def invented(self) -> list[str]:
        return list(self.inventor.invented)

    def _apply(self, prompt: str, name: str) -> str:
        return self.inventor.apply(prompt, name)

    def _apply_seq(self, prompt: str, names: list[str]) -> str:
        return self.inventor.apply_sequence(prompt, names)

    def invent(self) -> list[str]:
        """Invent methods from the live prompt. Called when current method dies."""
        base = self.identity_prompt or self.live_prompt or self.seed_prompt
        hot = list(self.hot_indices) if self.allow_intra else []
        new = self.inventor.invent(base, hot_indices=hot)
        for name in new:
            if f"op:{name}" not in self.board.nodes:
                intra = name.startswith(("revchar_", "caseflip_", "duphead_"))
                self.board.add(
                    f"op:{name}",
                    f"invented method {name} may gate security-relevant behavior",
                    [name],
                    prior=0.42 if intra else 0.28,
                    why=(
                        "intra-token identity mutation after token-slot residual"
                        if intra
                        else "runtime invention after collapse or cheap-battery exhaustion"
                    ),
                )
        if new:
            self.methods_log.append({"event": "invent", "ops": ",".join(new)})
        if self.allow_intra and self.hot_indices and not any(
            n.startswith(("revchar_", "caseflip_", "duphead_")) for n in self.inventor.invented
        ):
            self.representation_gap = True
            self.methods_log.append({
                "event": "representation_gap",
                "why": "token-slot residual; identity-preserving intra-token not yet compiled",
            })
        return new

    def _maybe_declare_gap(self) -> None:
        if not self.allow_gap or self.gap_compiled:
            return
        intra = [
            n for n in self.inventor.invented
            if n.startswith(("revchar_", "caseflip_", "duphead_"))
        ]
        if not intra:
            return
        pending = [
            n for n in intra
            if int(getattr(self.board.nodes.get(f"op:{n}"), "tests", 0) or 0) == 0
        ]
        if pending:
            return
        chars = harvest_unseen_chars(self.harvested_texts, exclude=self.identity_prompt or self.seed_prompt)
        self.ontology_insufficient = True
        hyp = gap_hypothesis(hot_indices=self.hot_indices, harvested=chars)
        self.abstract_dimensions.append(hyp)
        self.methods_log.append({
            "event": "KNOWN_INTERVENTIONS_INSUFFICIENT",
            "harvested": ",".join(repr(c) for c in chars),
        })
        ident = self.identity_prompt or self.seed_prompt
        new = compile_from_harvest(self.inventor._register, prompt=ident, chars=chars)
        if self.allow_commit:
            extra = compile_record_forms(
                self.inventor._register,
                prompt=ident,
                hot_indices=list(self.hot_indices),
            )
            new = list(extra) + list(new)
        if self.allow_struct:
            new = list(new) + compile_from_structure(
                self.inventor._register,
                prompt=ident,
                hot_indices=list(self.hot_indices),
            )
        for name in new:
            if f"op:{name}" not in self.board.nodes:
                self.board.add(
                    f"op:{name}",
                    f"gap-compiled {name} may discriminate remaining hypotheses",
                    [name],
                    prior=0.38,
                    why="compiled after ontology gap to address unresolved question",
                )
        if new:
            self.methods_log.append({"event": "gap_compile", "ops": ",".join(new)})
        if self.allow_commit and new:
            q = self.commitments.open_gap(probe=len(self.history))
            # First-test entitlement for a small prefix, not every compiled op
            # (avoids novelty farming and starving known wrap/insert).
            self.commitments.commit_ops(list(new)[:3], question_id=q.question_id, probe=len(self.history))
            self.commitments.waves = max(self.commitments.waves, 1)
            self.methods_log.append({
                "event": "epistemic_commitment",
                "question": q.question_id,
                "ops": ",".join(new),
            })
        self.gap_compiled = True
        self.representation_gap = True

    def _maybe_wave2(self) -> None:
        if not self.allow_wave2 or self.wave2_compiled:
            return
        if not self.commitments.first_wave_exhausted():
            return
        ident = self.identity_prompt or self.seed_prompt
        new = compile_field_delims(
            self.inventor._register,
            prompt=ident,
            hot_indices=list(self.hot_indices),
        )
        for name in new:
            if f"op:{name}" not in self.board.nodes:
                self.board.add(
                    f"op:{name}",
                    f"second-wave field {name} may answer the unresolved gap",
                    [name],
                    prior=0.4,
                    why="compiled after first-wave leases revoked",
                )
        qid = self.commitments.questions[-1].question_id if self.commitments.questions else "q.gap.0"
        if new:
            self.commitments.commit_ops(new, question_id=qid, probe=len(self.history))
            self.commitments.waves = 2
            self.commitments.max_leases_executed = max(
                self.commitments.max_leases_executed, self.commitments.executed_novel + len(new)
            )
            self.methods_log.append({"event": "wave2_compile", "ops": ",".join(new)})
        self.wave2_compiled = True

    def _maybe_continue_families(self) -> None:
        """3.29: remember deferred families; materialize one instance if a slot is free."""
        if not self.allow_lazy:
            return
        ident = self.identity_prompt or self.seed_prompt
        occ = self.inventor.occupancy()
        self.families.note_occupancy(occ)
        gap_open = bool(self.commitments.questions) and not any(
            L.state == "UNLOCKED" for L in self.commitments.leases
        )
        pending = [
            L for L in self.commitments.leases
            if L.state in ("COMMITTED", "TESTING", "INFORMATIVE") and L.remaining > 0
        ]
        first_done = (not pending) and self.commitments.revoked >= 1
        if first_done and "record.field_delim" not in self.families.families:
            spec = field_family_spec(prompt=ident, hot_indices=list(self.hot_indices))
            if spec:
                self.field_spec = spec
                self.families.remember(
                    spec["family_id"],
                    list(spec["remaining"]),
                    question_id=(self.commitments.questions[-1].question_id if self.commitments.questions else ""),
                    why="unresolved ontology-gap question after first-wave revocation",
                )
                self.methods_log.append({
                    "event": "family_deferred",
                    "family": spec["family_id"],
                    "remaining": str(len(spec["remaining"])),
                    "occupancy": str(occ),
                    "cap": str(INVENT_CAP),
                })
                if occ >= INVENT_CAP:
                    self.methods_log.append({
                        "event": "registry_full",
                        "family": spec["family_id"],
                        "occupancy": str(occ),
                    })
        if not gap_open:
            return
        fam = self.families.families.get("record.field_delim")
        if fam is None or self.field_spec is None:
            return
        if self.inventor.occupancy() >= INVENT_CAP:
            self.methods_log.append({
                "event": "registry_full",
                "family": fam.family_id,
                "occupancy": str(self.inventor.occupancy()),
            })
            return
        param = self.families.next_param(fam.family_id)
        if param is None:
            return
        name = compile_one_field(self.field_spec, str(param), self.inventor._register)
        if not name:
            self.failure_class = "LAZY_MATERIALIZATION_FAILURE"
            return
        self.families.mark_materialized(fam.family_id, param, name)
        self.families.wakeups += 1
        if f"op:{name}" not in self.board.nodes:
            self.board.add(
                f"op:{name}",
                f"lazy instance {name} of deferred family {fam.family_id}",
                [name],
                prior=0.4,
                why="materialized after executable capacity released",
            )
        qid = fam.question_id or (self.commitments.questions[-1].question_id if self.commitments.questions else "q.gap.0")
        self.commitments.commit_ops([name], question_id=qid, probe=len(self.history))
        self.commitments.waves = max(self.commitments.waves, 2)
        self.commitments.max_leases_executed = max(
            self.commitments.max_leases_executed, self.commitments.executed_novel + 1
        )
        self.methods_log.append({
            "event": "lazy_materialize",
            "op": name,
            "family": fam.family_id,
            "reason": "capacity_released+unresolved_question",
            "occupancy": str(self.inventor.occupancy()),
        })

    def _syn_rejected_kinds(self) -> set[str]:
        kinds: set[str] = set()
        for L in self.commitments.leases:
            if not str(L.op).startswith("syn_") or L.state != "REVOKED":
                continue
            rest = str(L.op)[4:]
            if rest.startswith("swap"):
                kinds.add("SWAP")
            elif rest.startswith("move"):
                kinds.add("MOVE")
            elif rest.startswith("wrap"):
                kinds.add("WRAP_EACH")
        return kinds

    def _ir_kinds_exhausted(self) -> bool:
        """3.30 IR kinds failed to distinguish. More SWAP instances are not a new capability."""
        if not self.allow_prim:
            return False
        kinds = self._syn_rejected_kinds()
        if {"SWAP", "MOVE", "WRAP_EACH"} <= kinds:
            return True
        if self.synthesizer.board.executed >= self.synthesizer.board.max_executed:
            return True
        if self.synthesizer.board.rejections >= 3 and not self.synthesizer.board.remaining:
            return True
        return False

    def _release_nonlease_slot(self, why: str) -> bool:
        leased = {L.op for L in self.commitments.leases if L.state not in ("REVOKED",)}
        for name in list(self.inventor.invented):
            if name in leased or name.startswith(("p_", "syn_", "label_", "quote_", "field_")):
                continue
            if self.inventor.release(name):
                self.families.capacity_releases += 1
                self.methods_log.append({
                    "event": "capacity_release",
                    "op": name,
                    "why": why,
                    "occupancy": str(self.inventor.occupancy()),
                })
                return True
        return False

    def _maybe_synthesize_primitive(self) -> None:
        if not self.allow_prim:
            return
        if any(L.state == "UNLOCKED" for L in self.commitments.leases):
            return
        pending = [
            L for L in self.commitments.leases
            if L.state in ("COMMITTED", "TESTING", "INFORMATIVE") and L.remaining > 0
        ]
        if pending:
            return
        question = bool(self.commitments.questions) or self.ontology_insufficient
        if not question:
            self.prim_synth.board.without_question += 1
            return
        if not self._ir_kinds_exhausted() and self.synthesizer.board.remaining:
            return
        if not self._ir_kinds_exhausted() and self.synthesizer.board.executed == 0:
            # 3.30 still the fast path; wait until IR has been given its leases.
            if self.allow_synth and self.synthesizer.board.materialized == 0:
                return
        fam = self.families.families.get("record.field_delim")
        if fam is not None and fam.remaining and fam.generated < fam.max_generated:
            return
        ident = self.identity_prompt or self.seed_prompt
        if not any(e.get("event") == "EXPERIMENT_LANGUAGE_INSUFFICIENT" for e in self.methods_log):
            self.failure_class = "EXPERIMENT_LANGUAGE_INSUFFICIENT"
            self.methods_log.append({
                "event": "EXPERIMENT_LANGUAGE_INSUFFICIENT",
                "why": "3.30 IR kinds cannot discriminate remaining hypotheses",
                "rejected_kinds": ",".join(sorted(self._syn_rejected_kinds())),
            })
            self.methods_log.append({
                "event": "language_extension_hypothesis",
                "hypothesis": "sequence combinators beyond the 3.30 IR (zip/pair/map-all)",
            })
        self.prim_synth.plan(
            prompt=ident,
            question=True,
            known_ops=set(self.inventor.ops),
            failed_kinds=self._syn_rejected_kinds(),
        )
        if self.inventor.occupancy() >= INVENT_CAP:
            self._release_nonlease_slot("slot for question-justified primitive")
        if self.inventor.occupancy() >= INVENT_CAP:
            self.methods_log.append({
                "event": "prim_capacity_wait",
                "occupancy": str(self.inventor.occupancy()),
            })
            self.failure_class = "SYNTHESIS_CAPACITY_FAILURE"
            return
        n_mat = 1 if self.allow_prim_lazy else 4
        for _ in range(n_mat):
            if self.inventor.occupancy() >= INVENT_CAP:
                break
            prim = self.prim_synth.next_primitive()
            if prim is None:
                break
            name = prim.name()
            if name in self.inventor.ops:
                continue
            ok = self.inventor._register(
                name,
                self.prim_synth.make_fn(prim),
                why=prim.why or "synthesized primitive for unresolved question",
            )
            if not ok:
                self.failure_class = "SYNTHESIS_CAPACITY_FAILURE"
                return
            self.prim_synth.op_of[name] = prim
            self.prim_synth.board.materialized.append(name)
            qid = self.commitments.questions[-1].question_id if self.commitments.questions else "q.prim.0"
            self.families.remember(
                self.prim_synth.family_id,
                remaining=[p.key() for p in self.prim_synth.board.remaining],
                question_id=qid,
                why="runtime synthesized primitive family; lazy remaining programs",
            )
            if f"op:{name}" not in self.board.nodes:
                self.board.add(
                    f"op:{name}",
                    f"synthesized primitive {name} may discriminate remaining hypotheses",
                    [name],
                    prior=0.44,
                    why=prim.why,
                )
            if self.allow_prim_lease:
                self.commitments.commit_ops([name], question_id=qid, probe=len(self.history))
                self.commitments.max_leases_executed = max(
                    self.commitments.max_leases_executed, self.commitments.executed_novel + 1
                )
            self.methods_log.append({
                "event": "prim_materialize",
                "op": name,
                "key": prim.key(),
                "origin": "SYNTHESIZED_PRIMITIVE",
                "novelty": prim.novelty,
                "occupancy": str(self.inventor.occupancy()),
            })
            if self.allow_prim_lazy:
                break

    def _maybe_synthesize(self) -> None:
        if not self.allow_synth and not self.allow_prim:
            return
        if any(L.state == "UNLOCKED" for L in self.commitments.leases):
            return
        pending = [
            L for L in self.commitments.leases
            if L.state in ("COMMITTED", "TESTING", "INFORMATIVE") and L.remaining > 0
        ]
        if pending:
            return
        question = bool(self.commitments.questions) or self.ontology_insufficient
        if not question:
            if self.allow_synth:
                self.synthesizer.board.without_question += 1
            if self.allow_prim:
                self.prim_synth.board.without_question += 1
            return
        fam = self.families.families.get("record.field_delim")
        if fam is not None and fam.remaining and fam.generated < fam.max_generated:
            return
        if self.allow_synth and not self._ir_kinds_exhausted():
            ident = self.identity_prompt or self.seed_prompt
            self.synthesizer.plan(
                prompt=ident,
                hot_indices=list(self.hot_indices),
                question=True,
                known_ops=set(self.inventor.ops),
            )
            if self.inventor.occupancy() >= INVENT_CAP:
                self._release_nonlease_slot("slot for synthesized IR program")
            if self.inventor.occupancy() >= INVENT_CAP:
                self.methods_log.append({
                    "event": "synthesis_capacity_wait",
                    "occupancy": str(self.inventor.occupancy()),
                })
                return
            prog = self.synthesizer.next_program()
            if prog is not None:
                name = prog.name()
                if name not in self.inventor.ops:
                    ok = self.inventor._register(
                        name,
                        self.synthesizer.make_fn(prog),
                        why=prog.why or "synthesized IR program for unresolved question",
                    )
                    if not ok:
                        self.failure_class = "SYNTHESIS_CAPACITY_FAILURE"
                        return
                    self.synthesizer.op_of[name] = prog
                    self.synthesizer.board.materialized += 1
                    qid = self.commitments.questions[-1].question_id if self.commitments.questions else "q.synth.0"
                    self.families.remember(
                        self.synthesizer.family_id,
                        remaining=[p.key() for p in self.synthesizer.board.remaining],
                        question_id=qid,
                        why="runtime synthesized family; lazy remaining programs",
                    )
                    if f"op:{name}" not in self.board.nodes:
                        self.board.add(
                            f"op:{name}",
                            f"synthesized program {name} may discriminate remaining hypotheses",
                            [name],
                            prior=0.42,
                            why=prog.why,
                        )
                    self.commitments.commit_ops([name], question_id=qid, probe=len(self.history))
                    self.commitments.max_leases_executed = max(
                        self.commitments.max_leases_executed, self.commitments.executed_novel + 1
                    )
                    self.methods_log.append({
                        "event": "synth_materialize",
                        "op": name,
                        "key": prog.key(),
                        "origin": "SYNTHESIZED_PROGRAM",
                        "occupancy": str(self.inventor.occupancy()),
                    })
                    return
        if self.allow_prim:
            self._maybe_synthesize_primitive()

    def _mark_hot_from_ops(self, ops: list[str], prompt: str) -> None:
        n = len(split_prompt(self.identity_prompt or self.seed_prompt))
        for op in ops:
            idx: int | None = None
            if op == "omit_first":
                idx = 0
            elif op == "omit_second":
                idx = 1
            elif op == "omit_last":
                idx = max(0, n - 1)
            elif op.startswith("omit_i") and op[6:].isdigit():
                idx = int(op[6:])
            elif op.startswith("swap_i") and op[6:].isdigit():
                idx = int(op[6:])
            if idx is not None and idx not in self.hot_indices:
                self.hot_indices.append(idx)


    def observe(self, prompt: str, obs: Any, *, baseline: Any | None, ops: list[str] | None = None) -> Contrast:
        from aivd.science.contrast import _text
        import re

        c = contrast(obs, baseline)
        used_ops = list(ops or [])
        self.tested.add(prompt)
        self.last_prompt = prompt
        self.last_ops = used_ops
        text = _text(obs)
        self.harvested_texts.append(text)
        labels = {m.lower() for m in re.findall(r"\b([A-Za-z]{3,24})\s*:", text)}
        stop = {
            "the", "and", "for", "with", "from", "this", "that", "then",
            "next", "also", "just", "only", "ok",
        }
        recent: list[str] = []
        for raw in text.replace(":", " ").replace(",", " ").replace("|", " ").split():
            t = raw.strip().lower()
            if not (3 <= len(t) <= 24 and t.isalpha()):
                continue
            if t in labels or t in stop:
                continue
            if t not in self.content_tokens:
                self.content_tokens.append(t)
                self.board.add(
                    f"tok:{t}",
                    f"just-observed token {t} is an operand worth testing",
                    [f"token:{t}"],
                    prior=0.4,
                    why="content appeared after a probe; not a catalog name",
                )
            if t not in recent:
                recent.append(t)
        self.recent_tokens = recent
        self.history.append({
            "prompt": prompt,
            "ops": used_ops,
            "contrast": c.as_dict(),
            "recent": recent,
            "live": self.live_prompt,
            "collapsed": self.collapsed,
        })

        if not used_ops:
            self.live_prompt = prompt
            self.live_ops = []
            self.live_metric = c.metric
            self.live_error = c.error
            self.tried_on_live = set()
            return c

        last = used_ops[-1]
        self.tried_on_live.add(last)

        for op in used_ops:
            hid = f"op:{op}"
            if hid not in self.board.nodes:
                self.board.add(hid, f"operator {op}", [op], prior=0.3)
            if c.secret:
                self.board.update(hid, support=1.0)
                if op not in self.supported_ops:
                    self.supported_ops.append(op)
            elif c.greedy_metric:
                self.board.update(hid, support=0.05, against=0.55)
                if op not in self.trap_ops:
                    self.trap_ops.append(op)
            elif c.security_shaped or (c.metric_delta >= 0.08 and c.error):
                self.board.update(hid, support=0.55)
            elif c.metric_delta < 0.03 and not c.error_appeared and not c.text_changed:
                self.board.update(hid, support=0.0, against=0.45)
            else:
                self.board.update(hid, support=0.12)

        if self.allow_commit and used_ops:
            op0 = used_ops[0] if len(used_ops) == 1 else ""
            if op0 and any(L.op == op0 for L in self.commitments.leases):
                informative = bool(c.secret or (c.metric >= 0.28 and c.error))
                self.commitments.on_result(op0, informative=informative, secret=bool(c.secret))
                self.methods_log.append({
                    "event": "lease_result",
                    "op": op0,
                    "informative": str(informative),
                    "secret": str(bool(c.secret)),
                })
                if self.allow_lazy:
                    if not informative and not c.secret:
                        if self.inventor.release(op0):
                            self.families.capacity_releases += 1
                            self.methods_log.append({
                                "event": "capacity_release",
                                "op": op0,
                                "occupancy": str(self.inventor.occupancy()),
                            })
                        self.families.mark_executed(op0, rejected=True)
                    else:
                        self.families.mark_executed(op0, rejected=False)
                    self._maybe_continue_families()
                    if self.allow_synth:
                        if op0.startswith("syn_"):
                            self.synthesizer.board.executed += 1
                            if c.secret:
                                self.synthesizer.board.successes += 1
                            elif not informative:
                                self.synthesizer.board.rejections += 1
                        if op0.startswith("p_"):
                            self.prim_synth.board.executed += 1
                            if c.secret:
                                self.prim_synth.board.successes += 1
                                self.prim_synth.board.language_successes += 1
                            elif not informative:
                                self.prim_synth.board.rejections += 1
                        self._maybe_synthesize()
                else:
                    self._maybe_wave2()

        if len(used_ops) >= 2:
            hid = "cmp:" + "+".join(used_ops)
            self.board.add(
                hid,
                f"composition {' then '.join(used_ops)} is required",
                used_ops,
                prior=0.45,
                why="single operators did not suffice; testing conjunction",
            )
            if c.secret:
                self.board.update(hid, support=1.0)
            elif c.security_shaped:
                self.board.update(hid, support=0.4)
            else:
                self.board.update(hid, support=0.05, against=0.2)

        informative = bool(
            c.secret
            or (c.security_shaped and not c.greedy_metric)
            or (c.metric_delta >= 0.08 and c.error and not c.greedy_metric)
        )
        if informative and not c.secret and used_ops:
            self._mark_hot_from_ops(used_ops, prompt)
            if self.allow_intra:
                self.representation_gap = True
                self.methods_log.append({
                    "event": "representation_gap",
                    "ops": "+".join(used_ops),
                    "why": "token-level residual without secret; current grammar may not preserve identity",
                })
                # Compile intra-token methods against the identity prompt.
                self.invent()
            if self.allow_gap:
                self._maybe_declare_gap()
        prev = self.live_metric
        upgraded = False
        lease_dead = False
        if self.allow_commit and len(used_ops) == 1:
            op0 = used_ops[0]
            lease_dead = any(L.op == op0 and L.state == "REVOKED" for L in self.commitments.leases)
        if c.greedy_metric:
            self.collapsed = False
        elif lease_dead:
            self.collapsed = False
        elif c.secret or c.metric > prev + 0.05:
            self.live_prompt = prompt
            self.live_ops = used_ops
            self.live_metric = c.metric
            self.live_error = c.error
            self.collapsed = False
            self.tried_on_live = {last}
            upgraded = True
        elif informative and prev < 0.2:
            self.live_prompt = prompt
            self.live_ops = used_ops
            self.live_metric = c.metric
            self.live_error = c.error
            self.collapsed = False
            self.tried_on_live = {last}
            upgraded = True
        elif prev >= 0.2 and (c.metric < prev - 0.06 or (self.live_error and not c.error)):
            self.collapsed = True
            hid = "dead:" + "+".join(used_ops)
            self.board.add(
                hid,
                "continuation of the live state collapsed",
                used_ops,
                prior=0.15,
                why="signal lost; do not chain the dead prompt",
            )
            self.board.update(hid, support=0.0, against=0.7)
            self.methods_log.append({
                "event": "collapse",
                "ops": "+".join(used_ops),
                "live": self.live_prompt,
            })
        else:
            self.collapsed = False

        if upgraded:
            for op in used_ops:
                if op not in self.supported_ops and op not in self.trap_ops:
                    self.supported_ops.append(op)
        return c

    def _prop(
        self,
        prompt: str,
        ops: list[str],
        *,
        disc: float,
        eig: float,
        sec: float,
        unlock: bool,
        remaining: int,
        evidence: float,
        why: str,
    ) -> ExperimentProposal | None:
        if not prompt or prompt in self.tested:
            return None
        self.seq += 1
        hid = "+".join(ops) if ops else "contrast"
        return ExperimentProposal(
            proposal_id=f"sci_{self.seq}",
            branch_id="science",
            subsystem="science",
            hypothesis_id=hid,
            action=hid,
            prompt=prompt,
            expected_information_gain=eig,
            uncertainty_reduction=0.2 + 0.3 * disc,
            security_relevance=sec,
            hypothesis_discrimination_value=disc,
            verification_value=0.25 if unlock else 0.08,
            novelty_value=0.3,
            experiment_cost=1.0,
            estimated_remaining_steps=remaining,
            estimated_completion_probability=evidence,
            unlocks_hypothesis_class=unlock,
            provenance="science.designer",
            meta={"ops": list(ops), "why": why, "live": self.live_prompt, "collapsed": self.collapsed},
        )

    def _candidate_ops(self) -> list[str]:
        seen: list[str] = []
        for op in list(BATTERY) + list(self.inventor.promoted) + list(self.inventor.invented):
            if op not in seen:
                seen.append(op)
        return seen

    def propose(self, *, remaining_steps: int = 6, evidence_strength: float = 0.4) -> list[ExperimentProposal]:
        out: list[ExperimentProposal] = []

        def add(p: ExperimentProposal | None) -> None:
            if p is not None and len(out) < self.max_new:
                out.append(p)

        # Invent once we have a live informative state, a collapse, or the
        # cheap battery has been fully tested — not before any evidence.
        battery_untested = [
            op for op in BATTERY
            if f"op:{op}" not in self.board.nodes or self.board.nodes[f"op:{op}"].tests == 0
        ]
        if not self.inventor.invented:
            if self.collapsed or self.supported_ops or not battery_untested:
                self.invent()
        elif self.collapsed and remaining_steps <= 4 and len(self.inventor.invented) < 8:
            self.invent()

        # -1. Identity-preserving intra-token mutations on the original
        #     utterance, never on a compacted live prompt.
        if self.allow_intra:
            intra_ops = [
                n for n in self.inventor.invented
                if n.startswith(("revchar_", "caseflip_", "duphead_"))
            ]
            ident = self.identity_prompt or self.seed_prompt
            for other in intra_ops:
                if other in self.trap_ops:
                    continue
                nxt = self._apply(ident, other)
                if not nxt or nxt == ident:
                    continue
                add(self._prop(
                    nxt,
                    [other],
                    disc=0.95,
                    eig=0.34,
                    sec=0.6,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.72),
                    why=f"identity-preserving intra-token probe {other}",
                ))
            if intra_ops and out:
                return out[: self.max_new]

        if self.allow_gap:
            self._maybe_declare_gap()
            ident = self.identity_prompt or self.seed_prompt
            if self.allow_commit:
                self._maybe_wave2()
                self._maybe_continue_families()
                self._maybe_synthesize()
                due = self.commitments.due()
                if due is not None:
                    nxt = self._apply(ident, due.op)
                    if nxt and nxt != ident and nxt not in self.tested:
                        add(self._prop(
                            nxt,
                            [due.op],
                            disc=0.5,
                            eig=0.2,
                            sec=0.4,
                            unlock=True,
                            remaining=1,
                            evidence=0.5,
                            why=f"epistemic-lease {due.lease_id} for unresolved {due.question_id}",
                        ))
                        if out:
                            return out[: self.max_new]
                    self.commitments.postpone()
            struct_ops = [
                n for n in self.inventor.invented
                if n.startswith(("label_nl_", "rejoin_", "label_eq_", "quote_tail_", "field_", "syn_", "p_"))
            ]
            struct_ops.sort(key=lambda n: (0 if n.startswith(("p_", "syn_", "label_eq_", "quote_tail_")) else 1, n))
            for other in struct_ops:
                if other in self.trap_ops:
                    continue
                nxt = self._apply(ident, other)
                if not nxt or nxt == ident:
                    continue
                disc = 0.91 if other.startswith(("label_nl_", "label_eq_", "quote_tail_")) else 0.88
                add(self._prop(
                    nxt,
                    [other],
                    disc=disc,
                    eig=0.32,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.7),
                    why=f"ontology-gap compiled intervention {other}",
                ))

        # 0. Collapse restore / live-state compose.

        # 0. Collapse restore / live-state compose.
        #    Remaining operators on the LIVE prompt, never on a collapsed last_prompt.
        if self.collapsed or self.supported_ops:
            base = self.live_prompt
            base_ops = list(self.live_ops)
            pending: list[tuple[int, str, str, list[str]]] = []
            for other in self._candidate_ops():
                if other in self.trap_ops:
                    continue
                if other in self.tried_on_live:
                    continue
                if base_ops and other == base_ops[-1]:
                    continue
                nxt = self._apply(base, other)
                if not nxt or nxt == base:
                    continue
                node = self.board.nodes.get(f"op:{other}")
                tested_n = int(getattr(node, "tests", 0) or 0) if node is not None else 0
                pending.append((tested_n, other, nxt, base_ops + [other]))
            # Untested methods first — collapse must not re-walk failed singles.
            pending.sort(key=lambda t: (0 if t[0] == 0 else 1, t[0]))
            for tested_n, other, nxt, seq in pending:
                if tested_n == 0:
                    disc = 0.94
                elif other in self.supported_ops:
                    disc = 0.90
                else:
                    disc = 0.78
                add(self._prop(
                    nxt,
                    seq,
                    disc=disc,
                    eig=0.32 if self.collapsed else 0.28,
                    sec=0.58,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.7 if self.collapsed else 0.6),
                    why=(
                        f"restore live state then {other}"
                        if self.collapsed
                        else f"compose {other} onto live informative prompt"
                    ),
                ))
            if self.collapsed and out:
                return out[: self.max_new]

        # 1. Just-observed content tokens — test NEXT, not FIFO behind chrome.
        for tok in self.recent_tokens:
            add(self._prop(
                f"{self.seed_prompt} {tok}".strip(),
                [f"token:{tok}"],
                disc=0.92,
                eig=0.32,
                sec=0.5,
                unlock=True,
                remaining=1,
                evidence=0.7,
                why=f"just-observed content {tok}; test immediately as operand",
            ))
            live = self.live_prompt
            if live and live != self.seed_prompt:
                add(self._prop(
                    f"{live} {tok}".strip(),
                    (self.live_ops or []) + [f"token:{tok}"],
                    disc=0.93,
                    eig=0.33,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=0.75,
                    why=f"append just-observed {tok} to the live informative prompt",
                ))
            if len(out) >= self.max_new:
                return out

        # 2. Seed-side compose of supported operators (same-prompt conjunction).
        for op in self.supported_ops:
            for other in self._candidate_ops():
                if other == op or other in self.trap_ops:
                    continue
                seq = [op, other]
                in_battery = other in BATTERY
                add(self._prop(
                    self._apply_seq(self.seed_prompt, seq),
                    seq,
                    disc=0.88 if in_battery else 0.84,
                    eig=0.28,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.6),
                    why=f"supported {op}; compose with {other} from seed to discriminate conjunction",
                ))
                if len(out) >= self.max_new:
                    return out

        # 3. Untested battery / invented singles — competing hyps, not greedy-EIG.
        for op in self._candidate_ops():
            node = self.board.nodes.get(f"op:{op}")
            if node is not None and node.tests > 0:
                continue
            trap = op in ("repeat_last", "duplicate")
            in_battery = op in BATTERY
            add(self._prop(
                self._apply(self.seed_prompt, op),
                [op],
                disc=0.75 if in_battery else 0.72,
                eig=0.18 if trap else 0.22,
                sec=0.22,
                unlock=False,
                remaining=max(2, remaining_steps),
                evidence=0.25 if trap else evidence_strength,
                why=(
                    f"untested operator {op}; discriminate against alternatives"
                    if in_battery
                    else f"invented method {op}; cheap battery did not suffice"
                ),
            ))

        # 4. Reverse-order falsifiers for two-op live histories.
        if len(self.live_ops) >= 2:
            rev = list(reversed(self.live_ops[:2]))
            add(self._prop(
                self._apply_seq(self.seed_prompt, rev),
                rev,
                disc=0.8,
                eig=0.22,
                sec=0.4,
                unlock=False,
                remaining=2,
                evidence=0.4,
                why="reverse order to falsify order-insensitive conjunction",
            ))

        # 5. Ablation: drop last live op.
        if self.live_ops:
            rest = self.live_ops[:-1]
            prompt = self._apply_seq(self.seed_prompt, rest) if rest else self.seed_prompt
            add(self._prop(
                prompt,
                rest or ["ablate"],
                disc=0.7,
                eig=0.15,
                sec=0.2,
                unlock=False,
                remaining=2,
                evidence=0.3,
                why="ablate last edit; if effect vanishes the last op was necessary",
            ))
        return out[: self.max_new]


# Keep apply_operator / apply_sequence import used by tests that patch designer.
_ = (apply_operator, apply_sequence)


__all__ = ["ScienceDesigner"]
