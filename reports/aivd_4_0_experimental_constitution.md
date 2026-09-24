# AIVD 4.0 experimental constitution

Pre-registration freeze. Research protocol only. No implementation, no corpus, no bank execution, no model call, and no production change.

Frozen at commit `afe3acdf83be4427e76d82f4537880ddf4eb99e6`. This document does not authorize an experiment. The independent sealed corpus does not exist. The repository must not manufacture one.

Two phrases in the freeze request are fixed here so they cannot be read against the seal.

The receipt may name a dimension only by an opaque handle minted inside the seal. The content id, `hash(bank hash + sealed signature)`, stays inside the seal. A signature hash can be searched. Putting it on the receipt would open the corpus.

The signature schema has a place for a genuine empty output. `apply_micro` does not reveal that case. When the returned string equals the probe, the status is `AMBIGUOUS_COPY` and nothing else. No second executor is added to split that case.

## 1. Boundary

Recorded bodies are published fixtures. Bodies generated inside this project are scientist-blind at best, and otherwise synthetic diversity. The strongest independence claim requires programs that already existed, taken whole, unfiltered, and sealed before this experimenter can read them. A substitute corpus written here is forbidden.

## 2. Roles

Exactly three. One person holds one role.

| Role | Holds | Does not do |
|---|---|---|
| Provider | Candidate bytes, order, count, ciphertext, provenance. Declares the acquisition was target-neutral. | Does not see discovery memory while it is written. |
| Experimenter | Commitment and receipt. Submits the frozen rules. | Does not see plaintext, does not hold the decryption key, and does not watch the process that does. |
| Evaluator | A sealed reference copy. Records the receipt, then opens. | Does not write labels, probes, or expected signatures back into discovery. |

The measurement process may read plaintext. The experimenter may not. If decryption runs where the experimenter can observe it, the run is not scientist-blind.

## 3. Seal

A body hash is not a seal. The grammar is small enough to enumerate. A signature hash is not a seal. Finite signatures can be searched.

The commitment binds ciphertext, corpus order, count, a provider timestamp, and provenance hashes. The experimenter receives the commitment, opaque handles, the receipt, and decision codes. They do not receive a plaintext body, a body key, the content id, a plaintext signature, or a seed that regenerates the corpus.

## 4. Sources

| Source | Frozen claim |
|---|---|
| A. Programs that already existed, taken whole, not filtered for this experiment | Independent-source discovery |
| B. Programs commissioned for this study | Scientist-blind discovery only |
| C. The same grammar, sampled inside this project | Synthetic diversity |

Source C is not an independent phenomenon, not independently existing behavior, and not an external novelty source.

## 5. Provider

The provider is not asked to find or avoid the doubled-odd behavior, to find vulnerabilities, novel behavior, or security-relevant behavior, or to reproduce or avoid historical AIVD targets. The request is target-neutral.

Before the experimenter has access, the provider commits the candidate bytes, the order, the count, the ciphertext, and the provenance metadata. Their statement of neutrality is a record of procedure. It is not proof of intent.

## 6. Bank

Hash `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`. Frozen before any corpus is acquired. Not modified after opening. Not enlarged because two signatures collided. Not chosen from candidate behavior. No target-derived probe. The 3.56 bank is historical replay only.

## 7. Executor

The only primitive is `apply_micro`. There is no second executor.

`output == input` is `AMBIGUOUS_COPY`. That status is not `OBSERVED_EQUIVALENT`, not `OBSERVED_DISTINCT`, and not a new dimension. An exception is an execution failure. It does not create a dimension.

## 8. Signature

A signature is the ordered results on the frozen bank. Each probe keeps one status: normal output, `AMBIGUOUS_COPY`, or execution failure. A genuine empty output would be a fourth status. This executor cannot show it, so that status is not recorded.

The signature does not include model text, `informative`, `secret`, `representation_gap`, `semantic_class_of`, or the body key.

## 9. Dimension id

Inside the seal, the content id is `hash(bank hash + sealed signature)`. It does not depend on the body key, an operator name, the family, a generation id, a target id, or the provider id.

Many bodies may share one content id. A second body with the same sealed signature is another observation, not another dimension. The public name of that dimension, on the receipt, is an opaque handle. It is not the content id.

## 10. Novelty

Compare the sealed signature with every dimension in the current epoch. Each comparison is exactly one of `OBSERVED_EQUIVALENT`, `OBSERVED_DISTINCT`, or `INSUFFICIENT`.

A new observed behavior requires a distinction from every stored dimension and no insufficient comparison. An ambiguous probe is not a distinction and not an agreement. If any comparison is insufficient and none is a clean distinction, nothing is minted. The bank is not edited to break a tie.

## 11. Memory

Empty at the start of an epoch. Kept during the epoch. Cleared at the firewall. Not carried across the firewall. A published historical body is not a parent. Blind recursion uses only dimensions from eligible sealed candidates in this epoch.

## 12. Recursion

The pair rule is frozen before the corpus is opened. It uses opaque handles, the precommitted order, and discovery state this protocol allows. It does not read a body key, an operator, an expected output, a target relation, or security relevance.

A new dimension becomes a parent only because that rule selects it. There is no depth target. There is no researcher choice after a result.

## 13. Resources

256 calls to `apply_micro`. 128 are reserved for unevaluated pairs. 128 remain for the rest of the protocol. Frozen before opening.

Not part of this budget, and not to be changed: the episode budget, `max_executed`, `invent_cap`, the firewall, proposal order, and ranking. No starvation exception. No increase. No reallocation after a result.

## 14. Security

Discovery does not set `secret`, `informative`, `verified`, or vulnerability. A new dimension is not a finding. The behavior engine does not call the verifier. Security characterization starts only after the discovery receipt is immutable. Verification stays with the existing verifier.

## 15. Leakage

Discovery may read candidate plaintext, the frozen bank, memory of this epoch, and provenance the protocol permits. It may not read target labels, historical target reports, evaluator labels, provider annotations, expected signatures, secret strings, the doubled-odd identity, or evaluation answers. Evaluator output does not flow back.

## 16. Receipt

The receipt is finalized before the evaluator opens the corpus. It may contain opaque handles, decision codes, the opaque dimension handle, the bank hash, and the protocol version. It must not contain a plaintext body, a body key, the content id, a plaintext signature, or an evaluator label.

The evaluator then opens the sealed copy. Evaluation does not alter discovery state.

## 17. Claims

| Term | What it means |
|---|---|
| Fixture validation | The implementation matches a known example. |
| Historical replay | A documented 3.56 or 3.58 result is reproduced. |
| Synthetic diversity | The candidate was generated inside this project. |
| Scientist-blind discovery | Hidden from the experimenter before measurement, and produced for this study. |
| Independent-source discovery | The source predates the study or otherwise exists apart from it, and was sealed before inspection. |
| Blind recursive discovery | A sealed candidate mints a dimension, the frozen pair rule reuses it, and a second distinct dimension appears without a target-directed choice. |
| Security discovery | A later, separate characterization says the behavior is security-relevant. |
| Verified finding | The existing verifier confirms it. |

These are not interchangeable. A weaker result does not take a stronger name.

## 18. The event that would count

All twelve, together. Candidate bytes are held independently. They are sealed before the experimenter sees them. They were not selected for the known target. The experimenter does not know the body key. The engine measures the frozen bank. The signature is not already in memory. A dimension is created with no semantic name. The frozen rule, not a person, sends it into recursion. A later measurement produces another distinct dimension. Security stays unset until its own stage. The evaluator checks the sealed reference without writing back. No discovery rule changes after the corpus is opened.

Only that class of event supports the strongest autonomous-discovery claim.

## 19. Never that claim

A 3.56 replay. A 3.58 replay. Same-family stride separation. A hidden label. A hidden expected answer. A model candidate aimed at the target. A candidate from the current planner. An internal random program. Controlled mock recursion. Synthetic recursion. A composition of known bodies. A reconstruction of the doubled-odd body. A probe added after a collision. A candidate generated because of the target.

## 20. Immutable before opening

The bank hash. The signature format. The `AMBIGUOUS_COPY` rule. The comparison semantics. The content-id formula and the rule that it stays inside the seal. Memory. The pair rule. The recursion rule. The 256 calls and the 128/128 split. The stopping condition. The leakage rules. The evaluator boundary. The claim hierarchy. The success criterion in section 18. The failures in section 19.

No parameter moves after a candidate is inspected.

## 21. Decision

The corpus is not in this repository, and it must not be manufactured here. Implementation is not authorized. Bank execution is not authorized. Sacred execution is not authorized. Construction of the doubled-odd body is not authorized. Production changes are not authorized.

The only later prerequisite is a provider, who is not this experimenter, holding an independently existing corpus under this seal.

**IMPLEMENTATION NOT AUTHORIZED.**

**NO PRODUCTION INTERVENTION AUTHORIZED.**
