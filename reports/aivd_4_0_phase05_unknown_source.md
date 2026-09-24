# AIVD 4.0 Phase 0.5: where an unpublished behavior could come from

Design only. No engine. No bank execution. No production change. The doubled-odd body was not constructed. No substitute target was written.

The current repository does not contain a behavior that is unpublished to the experimenter. Every recorded body used in 3.56 and 3.58 already has a published signature. A hidden label on one of those bodies is not an unknown behavior. Replay is not discovery. Phase 1 is not ready.

## 1. Three meanings of unknown

| Level | Who lacks the relation before the dimension is committed | Enough for the claim? |
|---|---|---|
| `UNKNOWN_TO_ENGINE` | The code is not given the expected signature or the target key. The scientist already knows it. | No. This is a hidden answer. The claim forbids that downgrade. |
| `UNKNOWN_TO_EXPERIMENTER` | The person running the study has not read the body key, the outputs, or a relation for this candidate. | Yes. This is the minimum. |
| `UNKNOWN_TO_EVALUATOR` | The person who checks afterward also has no reference. | No. Then there is no independent check. The evaluator may know a sealed reference. They may not write it back. |

Autonomous behavioral discovery requires `UNKNOWN_TO_EXPERIMENTER` at the moment the engine commits. `UNKNOWN_TO_ENGINE` alone is a fixture.

## 2. Sources

| Source | Who can know the behavior first | Who chooses the body | Selection uses an expected behavior? | Can the scientist know the relation beforehand? | Can the engine be shown the target? | Evaluator can check without writeback? | Target injection? | Genuine discovery? |
|---|---|---|---|---|---|---|---|---|
| A. Model-generated body | Whoever reads the key. A `SLICE` key is readable behavior. | The model, if the human does not filter | Only if the prompt or the filter names a behavior | Yes, the moment they read the key | Yes, if the prompt or the context contains the historical reports | Yes, if the seal opens after the commit | If the context includes the target, yes | Only while the key and the outputs stay sealed, and the context has no target |
| B. Model-generated composition of published bodies | The scientist, if the components were published in 3.58 | Whoever picks the pair | Often yes | Yes | Yes | Yes | Using the published stride pair, yes | No |
| C. Mutation of a published body | The scientist who picked the parent and the edit | The scientist | Yes if the edit is "the other stride" | Yes | Yes | Yes | Yes in that case | No |
| D. Stochastic sample from the grammar | Nobody, until something is executed, provided nobody reads the sample | A frozen generator | No, if the only filter is "valid tree" | Not if the sample stays sealed | Not if the generator has no target | Only by re-measurement, unless a third party holds a seal | No | Unpublished to the experimenter. Not a phenomenon outside the grammar |
| E. Existing language growth | The log, which prints keys | The current planner | The planner was built during the target investigation | Yes if the log is read | The live path does not receive the odd key; the policy history is not clean | Yes | Not the key itself. The policy is contaminated | No, for the current planner |
| F. External published corpus | The corpus authors, and any experimenter who has read it | Whoever picks the file | Yes if it is picked because of a known behavior | Usually yes | If labels are in the files | Yes | If chosen for the target, yes | No, when the experimenter selected it for that reason |
| G. Sealed corpus held by someone else | The author and the evaluator | A rule frozen before the experimenter looks | No, if the rule does not mention a behavior | Not until the seal opens | Not if labels stay in the evaluator package | Yes. That is the point | No, if the rule is behavior-agnostic | Yes, relative to this experimenter. The corpus is not in this repository |
| H. Synthetic generator aimed at a hidden behavior | The author of the generator | The generator | Yes. The hidden behavior is the point | Yes if they wrote the target | If the target leaks into the prompt | Yes | Yes. This task forbids creating that target | No |
| I. Human-authored hidden set, author is the experimenter | The experimenter | The experimenter | Yes | Yes | Easily | The author is grading their own secret | Yes | No |
| J. Adversary told to hide the known target | The adversary | The adversary | Yes | If the adversary reports to the experimenter | Yes | Yes | Yes | No |
| K. Programs that already existed for another purpose | Their authors | A rule that does not filter on this target | No, if the dump is taken whole | Not if the dump is sealed before reading | Not unless labels are attached | Yes | No | Not from this repository. None is sealed here |

No row is a source that already exists in the repo and is unpublished to the scientist.

## 3. A fresh model

A model can emit a candidate without being told a behavior. The legal inputs are the grammar, the resource limits, and programs already committed in this sealed run. The illegal inputs are the doubled-odd key, any expected signature, hidden labels, and the historical target reports.

That candidate is an `UNKNOWN_BEHAVIOR_CANDIDATE` only before a human reads it. The key `MAPT(SLICE:…)` is not an opaque id. A person who understands the grammar can know the relation without running the bank. Blindness has to cover the key, not only the probe outputs.

This note does not ask a model for a body.

## 4. Selection

| Instruction | Verdict |
|---|---|
| Generate random valid programs | Defensible for a sealed measurement. It produces syntactic diversity inside a grammar the scientist already understands. It does not name a target. |
| Generate programs unlike existing ones | After a committed signature, the novelty rule may refuse an equivalent signature. Before execution, a human judgment of "unlike" is target-directed. A frozen syntactic distance is a prior, not a behavior, and it must not be tuned after a split appears. |
| Generate unexplored operator combinations | Defensible only as a frozen enumeration in an order fixed before any signature. Prioritizing `SLICE` with `SLICE` because that shape matters historically is target-directed. |
| Generate programs that might expose new behavior | Not defensible. The expected difference is the selection criterion. |
| Take the next proposal of the current planner | Not defensible. That planner was developed against this target family, and its logs reveal keys. |

Open generation does not mention a desired relation. Target-directed generation chooses because a relation is suspected. Convenience is not a reason to pick the second.

## 5. Scientist-blind boundary

```
generator
    -> sealed artifact (body bytes, seed, prompt hash)
    -> engine reads the seal, runs the frozen bank, commits
    -> human may open the artifact
```

The boundary is the seal. It sits before any human reads a key or an output. The engine must read the body. That is the measurement, not prior knowledge. If a human opens the seal first, the run is controlled, not blind.

The experimenter may see an opaque candidate id, the bank hash, the budget counter, and the committed decision `NEW_DIMENSION` or `KNOWN`. They may not see the key, the probe strings' outputs, or the family label before that decision.

## 6. Evaluator boundary

```
discovery commit
    -> sealed decision
    -> evaluator
```

There is no edge back. The evaluator may hold a reference the experimenter does not have. They may not return a label, a target id, an expected signature, or a probe. They may not add a probe when two signatures collide.

## 7. The frozen bank

Hash `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`. Eight structural probes. Not executed. Not to be edited after a result. Not the 3.56 bank.

It is general enough to start a sealed measurement: empty, length, repetition, words, punctuation. It is not rich. Eight strings can collapse different programs, and they can also split programs a person would call the same. Both outcomes are properties of this bank. Neither outcome is a reason to add a probe in the same experiment.

A later revision would be a new bank, frozen and hashed before it is used, with old and new signatures incomparable. The only pre-registered reason to write that new bank is a count that was defined before looking: for example, every probe of every committed candidate in a sealed run is `AMBIGUOUS_COPY`. The reason to refuse a revision is "these two collided and a new string would split them."

This note does not revise the bank.

## 8. `AMBIGUOUS_COPY`

`apply_micro` returns the prompt both when the program produced nothing and when it copied the input. The signature records `AMBIGUOUS_COPY` and does not choose a cause. There is no second executor.

| Stage | Rule |
|---|---|
| Signature | Store the status. Do not rewrite the string. |
| Distance | A probe with this status is not agreement and not a distinction. One clean difference elsewhere is still `OBSERVED_DISTINCT`. No clean difference, and any ambiguous probe, is `INSUFFICIENT_EVIDENCE`. |
| Memory | Do not mint a dimension from an insufficient signature. Do not mint one because every probe is ambiguous. |
| Novelty | `NEW_DIMENSION` requires a clean distinction from every stored signature. Ambiguity cannot be that distinction. |
| Recursion | A composition is held to the same rule. An ambiguous copy of a parent is not a new dimension. |

## 9. Provenance

Beside the id, store: candidate origin, generator event, body key, epoch, bank hash, sealed signature, parent ids, discovery event.

The id is `hash(bank hash + sealed signature)`, including the `AMBIGUOUS_COPY` marks. It does not include the body key, the family, the target, or the generation id. Two unread bodies with the same sealed signature are one id.

## 10. Blind recursion

"Compose whatever we just discovered" is not blind if a person opens the new dimension and then picks the pair. It is blind only when all of the following hold:

- both parents were committed under the seal
- the person has not read those keys or signatures
- the next pair is chosen by a rule frozen before the run: lexicographic order of opaque ids, or a frozen seed over those ids
- the parents are not published 3.56 or 3.58 bodies

A published parent makes the run `CONTROLLED_RECURSION`, even if the code hides the label.

The 128 reserved calls spend `apply_micro` on those pairs and on nothing a person inserts after seeing a result. If they run out before a second clean distinction, the result is exhaustion. The reserve is not increased.

## 11. Words

| Word | Meaning |
|---|---|
| `CONTROLLED_RECURSION` | A person knew a parent or the expected child before the commit. A mock. Never reported as discovery. |
| `BLIND_RECURSION` | Parents sealed, pair chosen by the frozen rule, keys unread. |
| `UNKNOWN_BEHAVIOR_DISCOVERY` | The first dimension was committed while `UNKNOWN_TO_EXPERIMENTER`. |
| `HELD_OUT_EVALUATION` | After the commit, a separated evaluator opens a reference. No writeback. |

## 12. The 256 calls

Frozen. 128 calls characterize sealed candidates. 128 calls run unevaluated pairs. Eight probes, so that is 16 candidates and 16 pair-evaluations if each uses the whole bank. No starvation exception. No borrowing from the episode budget. `max_executed` and `invent_cap` stay as they are. The order is the frozen rule. It is not edited after an output.

A run that mints nothing is a completed negative. It is not a budget problem.

## 13. The first event that would count

1. A candidate is generated with no target in the generator context.
2. The experimenter has not read the key or the outputs.
3. The engine executes the sealed bank.
4. It seals a signature.
5. It compares that signature only with memory from this run.
6. It commits `NEW_DIMENSION` under the rules in section 8.
7. The id has no semantic name.
8. A later pair is chosen by the frozen rule.
9. That pair is measured.
10. A second `NEW_DIMENSION` is committed, or the budget ends without one.

Steps 1–7 are achievable from a sealed grammar sample. They show an unpublished signature inside a language the scientist already has. They do not show a phenomenon from outside that language.

Steps 8–10 are achievable from the same sealed run only as `BLIND_RECURSION`. If either parent was published, they are controlled.

An external sealed corpus is required for the further sentence "this was not manufactured by our generator." That corpus is not in the repository. This note does not create one.

## 14. External corpus

Not necessary for the narrow sentence "this signature was unread before the commit." Necessary for the sentence "the phenomenon was not produced for this study."

If one is ever used, it has to be chosen by a rule that does not mention the target, sealed before the experimenter reads it, unlabeled in the discovery package, and unchanged after inspection. The evaluator holds any labels. This note does not search for a corpus and does not download one.

## 15. Synthetic corpus

A human sentence of the form "this program has unknown behavior X" makes X known to that human. It cannot support the claim.

A hidden-seed generator creates unseen samples. The novelty belongs to the generator. That is synthetic diversity. It is not, by itself, a behavior the study did not have the means to manufacture. Building such a generator around a chosen hidden target is forbidden here, and it would be injection if it were built later to make the claim true.

## 16. The model as the source

A fresh model can be the generator for a sealed sample. It may be told the grammar, the call budget, provenance, and signatures already committed in this run. It may not be told an expected output, a target behavior, a security oracle, a historical target identity, or the 3.56 probes as things to separate.

The model in the current research setting does not meet that bar. Its context includes the target investigation. Using it as the source would leak the published relations through the prompt. A later protocol would need a context that has not read those reports. This note does not start one.

## 17. Protocol that could eventually support the claim

The claim is two sentences. First: a dimension was committed that had not been supplied, named, targeted, or chosen because its difference was already known. Second: that dimension was a parent of another dimension, with no depth target.

The protocol is the seal in section 5, the evaluator one-way edge in section 6, the unexecuted bank, `AMBIGUOUS_COPY` in section 8, ids that hash only the signature, blind pair selection in section 10, and the 256-call split in section 12. Replay is the same seal, the same seed, and the same bank hash.

It fails the leakage audit if the generator context contains a target report, if a person reads a key first, if a probe is added after a collision, if the evaluator writes back, if a published body is used as a parent, or if the budget changes after a negative run.

## 18. Blocker

The repository has fixtures only. It has no sealed stream of unread programs, and it has no corpus held by someone other than the experimenter. Until one of those exists under the rules above, there is no legitimate object to discover.

The source that would not manufacture the result is a stream the experimenter cannot read before the commit, generated without a target, and not filtered because a difference is suspected. A sealed sample from the grammar meets the unread-signature bar and does not meet the bar of an independent phenomenon. A corpus sealed by someone else could meet the second bar. Neither source is in the repository now.

## Decision

**UNKNOWN-SOURCE IMPLEMENTATION NOT AUTHORIZED.**

**NO PRODUCTION INTERVENTION AUTHORIZED.**
