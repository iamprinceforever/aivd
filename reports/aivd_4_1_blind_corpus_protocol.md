# AIVD 4.1 blind external corpus protocol

Design only. No corpus was gathered. No candidate was generated. The discovery bank was not executed. The doubled-odd body was not constructed. Production code was not modified.

This repository cannot be the corpus provider. The experimenter is the person who already knows the published signatures. A file they write, a model they prompt, or a planner they run is not an external source. An independent sealed corpus is required, and it is not here.

## 1. Trust model

Three roles. One person must not hold two of them.

| Role | May see before the discovery receipt is recorded | Must not see |
|---|---|---|
| Corpus provider | The candidates, the generator, the commitment key | The discovery memory while it is being written |
| Discovery experimenter | The commitment, the bank hash, the budget, opaque handles, the receipt | Body keys, programs, outputs, relations, target labels |
| Evaluator | A sealed copy of the corpus and any reference the provider also sealed | Nothing that would let them send a label back |

The discovery engine may read a candidate. That is the measurement. The human experimenter must not. If the experimenter runs the process that decrypts the corpus, they can print the keys. Cryptography does not make an operator blind. The process that opens candidates has to run where the experimenter cannot observe it. The experimenter submits the frozen rules and receives a receipt.

## 2. Providers

No provider is chosen. Nobody is contacted.

| Model | Independence | Provenance | Reproducible later | Secrecy | Later reference | Contamination |
|---|---|---|---|---|---|---|
| Independent researcher | High if they have not worked on this target | Their record of how the candidates were made | Only if their generator and seed are sealed and later revealed | High if they keep the bodies | Yes, they can hold the originals | High if they have read the AIVD target reports |
| Independent group | Same, with more than one witness to the commitment time | A group log | Same | Same | Yes | Same risk, shared across the group |
| Sealed benchmark maintainer | High if the benchmark predates this study and was not built for it | The benchmark's own history | Yes, if a version is named | High until release | The published version is the reference | Low if it predates the target. High if it was filtered for this study |
| Cryptographic commitment alone | Does not create independence. It only binds bytes | The hash binds what was committed, not why | Yes, after reveal | Fails if the experimenter can enumerate the bytes | The reveal is the reference | A hash of a contaminated corpus is still contaminated |
| Generator run by this study | None. It was produced for the study | Local | Yes | Fails. The operator can read it | The operator already knows it | Certain |
| Trusted third party | Only as good as the separation | Their log | If they keep the generator seal | High if they run the discovery process | Yes | High if the instructions mention a target |

A commitment is not a provider. A provider is a party who holds candidates the experimenter does not.

## 3. Commitment

Four objects. None of them is implemented here.

The commitment is a hash the experimenter may see. It binds corpus identity, order, count, a provider timestamp, a generator hash, and an environment hash. It must not be a list of per-candidate hashes. This grammar is small and bounded (`MAX_NODES` 8, `MAX_DEPTH` 4). A list of body hashes can be inverted by enumeration. A single hash of a short tuple may be invertible too. The commitment therefore binds a ciphertext, not a plaintext the experimenter can search.

The sealed corpus is that ciphertext plus the commitment. The key is held by the provider and the evaluator. The experimenter does not have it.

The discovery manifest is the only thing the engine's operator, inside the sealed environment, passes out: opaque handles, decision codes, budget consumed, and a hash of the internal log. No key, no output string, no content hash.

The reveal package is opened after the receipt is recorded. It contains the ordered bodies, the generator identity, the seed, the mapping from opaque handles to bodies, and the internal log. Replay happens then, not before.

## 4. Key blindness

`MAPT(SLICE:…)` is a description, not an opaque id. The experimenter must not see it before the receipt exists.

```
provider ciphertext
    -> process the experimenter cannot observe
    -> engine reads the body
    -> signature, including AMBIGUOUS_COPY marks
    -> content id stays inside the seal
    -> receipt: opaque handle and decision code only
```

The content id remains `hash(bank hash + sealed signature)`. It is stored in the sealed log so that later replay can check it. It is not printed on the receipt. Anyone who can enumerate the grammar and who knows the public bank can turn that hash back into a signature. Putting it on the receipt would open the seal.

Opaque handles are random inside the sealed process, or they are the committed order index. They are not a hash of the body and not a hash of the signature.

The corpus stays closed until the receipt hash is recorded outside the experimenter's control.

## 5. Where candidates may come from

| Source | "Not produced for this study" |
|---|---|
| Programs that already existed for another purpose, taken whole | Yes, if the set predates the request and was not filtered |
| A benchmark version that predates this protocol | Yes, under the same condition |
| A grammar sample made by a separated party before this request | Yes |
| A grammar sample commissioned for this protocol | No. It can still be scientist-blind. It is synthetic diversity made for the study |
| The same AIVD grammar, sampled by the experimenter | No. It is not an independent source |
| A model prompted by the experimenter | No |
| A model prompted by a separated provider who was not told the target | Scientist-blind only. Produced for the study if the prompt exists because of the study |
| Programs written by the experimenter | No |
| Programs written by a separated author who was not told the target | Scientist-blind. Independent only if they were not written for this study |

Using the AIVD grammar does not make a separated sampler into an independent phenomenon. It makes an independent draw from a hypothesis class this project already published. That draw can support scientist-blind discovery. It cannot support the sentence "the phenomenon was not produced for this AIVD study."

## 6. Target independence

The provider is not asked to find the doubled-odd behavior, to avoid it, to find security bugs, to find novel behavior, or to reproduce historical AIVD targets. The request is target-neutral: a fixed set, already ordered, with no behavioral filter.

If the provider knows the historical target and generates around it, the corpus is contaminated and is not used. A declaration that they did not do so is evidence. It is not proof.

## 7. Reproduction without early reveal

The provider seals the generator version, the environment hash, and the seed. The seed stays with the ciphertext. The experimenter does not receive it. A seed that regenerates the candidates would let the experimenter build the corpus before the run.

After reveal, a third party can rerun the generator and rehash the corpus. Agreement with the commitment is the reproducibility check. Before reveal, reproducibility is the provider's and the evaluator's property, not the experimenter's.

## 8. Order

The order is part of the commitment. The experimenter does not reorder, drop, or prefer a candidate. They cannot, if they cannot see the keys.

If the corpus is larger than the budget, the prefix is the committed order until 128 characterization calls are spent. That rule is frozen here. It is not a selection after inspection.

Streaming is allowed only if the commitment names the full ordered list before the first candidate is opened. A stream that is extended after a result is a different corpus.

## 9. Bank

Hash `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`. It stays frozen. It is not revised after a sealed candidate is seen. No probe is added because two signatures collide. The 3.56 bank is not discovery evidence.

## 10. `AMBIGUOUS_COPY`

When `apply_micro` returns the probe, the sealed record stores `AMBIGUOUS_COPY` for that probe. The cause is not inferred. There is no second executor.

That mark is not agreement and not a distinction. A signature with no clean difference does not mint a dimension, including the case where every probe is ambiguous. One clean difference from every stored signature can still mint a dimension. The ambiguous probes do not supply that difference.

The receipt does not list the marks. They stay in the sealed log.

## 11. Budget

256 calls to `apply_micro`. 128 characterize candidates in committed order. 128 evaluate pairs chosen by the frozen rule. Eight probes, so that is at most 16 full characterizations and 16 full pair runs.

The episode budget, `max_executed`, and `invent_cap` are not this counter. They stay untouched. When the 256 are spent, the run stops. A negative result does not increase the counter.

## 12. Reveal

The evaluator holds the originals, the provenance, and any reference. None of that enters the discovery process.

After the receipt is recorded:

1. The sealed log is copied to the evaluator. They do not edit it.
2. They check the commitment, the order, the budget, and that no receipt field contains a key or an output.
3. They may then publish the reveal package.
4. They do not change memory, content ids, signatures, pair choices, or decision codes.

A reference that says a candidate matches a historical body is an evaluation sentence. It is not written into the discovery record.

## 13. Blind recursion

The pair rule is frozen before any candidate is opened.

Inside the sealed process, parents are dimensions committed in this run. The next pair is the next unused pair in lexicographic order of opaque handles. The rule does not read a family label, an operator name, a key, or a human judgment.

Ordering by opaque handle does not mean "compose the interesting one." It does decide which pairs fit in 128 calls. That bias is arbitrary and precommitted. It is acceptable. Changing the order after a dimension appears is not.

A published 3.56 or 3.58 body is not an eligible parent. Using one makes the run controlled recursion.

The experimenter does not pick the pair. They only see that a pair slot was consumed.

## 14. Independence

These can be checked later: commitment time before the experimenter received bodies, a provider declaration that the request was target-neutral, a generator hash, a sealed seed, a repository the experimenter did not write, and a pre-registration time.

Together they support this claim: the bytes were bound before the experimenter could read them, and the provider states they were not aimed at the historical target.

They do not prove what the provider was thinking. A corpus aimed at the target and then hashed is still aimed at the target. The protocol rejects a corpus when that aim is known or later shown. It does not pretend a hash prevents it.

## 15. Frozen before opening

The bank and its hash. The signature fields, including `AMBIGUOUS_COPY`. Distance: clean difference, agreement, or insufficient. The content-id formula, kept inside the seal. Opaque handles on the receipt. Memory cleared at the epoch boundary. The pair rule in section 13. The 256 calls and the 128 reserve. Stop on no eligible pair or on budget exhaustion. No writeback. No probe added after a collision. Success and failure as below.

None of these is tuned after a key or an output is seen.

## 16. The event that would count

A candidate was committed before the experimenter saw it. It was not selected for the known target. The sealed process measured it on the frozen bank, stored a signature, compared it only with memory from this run, and committed a new dimension under the ambiguity rule. The dimension has no semantic name on the receipt. A later pair was chosen by the frozen rule. That pair produced a second new dimension, or the budget ended first. Security is unset. The verifier is not called.

If the candidates were created for this study, the event is scientist-blind discovery inside a supplied class. It becomes independent-source discovery only if section 5's stronger source is the one that was sealed.

## 17. Claim hierarchy

| Term | Evidence required | Must not be used for |
|---|---|---|
| Fixture validation | A known relation, checked outside the engine | Discovery |
| Historical replay | 3.56 or 3.58, labeled as replay | Discovery |
| Synthetic diversity | Samples from a grammar this project already has | An independent phenomenon |
| Sealed-corpus discovery | A commitment the experimenter could not invert, receipt before reveal | A vulnerability |
| Scientist-blind discovery | Section 16, and the experimenter did not read keys | "Not produced for this study" |
| Independent-source discovery | Section 5's pre-existing or separated, non-commissioned source | A security finding |
| Recursive blind discovery | A second dimension from the frozen pair rule, parents from this run only | A scripted mock |
| Security discovery | A later stage, after the seal, not fed back | Verification |
| Verified vulnerability | The existing verifier, unchanged | Anything this protocol emits |

A weaker row does not inherit a stronger name.

## 18. The corpus is invalid if

The experimenter sees a key or an output early. The provider targets the historical vulnerability. Selection is target-directed. Order changes after inspection. The bank changes. The evaluator writes a label, a target id, an expected signature, or a probe into discovery. An ambiguous copy mints a dimension. A historical body is relabeled as unknown. Controlled recursion is reported as discovery. The experimenter operates the decrypting process and the receipt still claims scientist-blindness.

## 19. Before any implementation

An independent provider has to exist, and this repository is not that provider. A commitment to ciphertext has to exist before the experimenter can read bodies. The discovery process has to run where that experimenter cannot observe it. The frozen list in section 15 has to be the rules of that run. None of those conditions holds now.

Until they do, there is no corpus to discover from, and there is no engine to build.

**BLIND-CORPUS IMPLEMENTATION NOT AUTHORIZED.**

**NO PRODUCTION INTERVENTION AUTHORIZED.**
