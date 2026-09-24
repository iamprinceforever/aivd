# AIVD 4.0 Phase-1 integrity audit

Design audit only. The engine was not implemented. Production code was not modified. The doubled-odd body was not constructed. No body was executed on the proposed discovery bank.

**Phase 1 implementation is not authorized.**

The proposed benchmark can check whether a program computes signatures and comparisons. It cannot show that AIVD discovered an unknown behavioral dimension. Every case already has a published relation. Running the engine on those cases and matching the published relation is a fixture, not discovery.

## 1. Benchmark leakage

The expectation column is what a human already knows from 3.56 and 3.58. It is not what the engine should be told.

| Case | Inputs | Expected relation | Source of that expectation | Leakage | Allowed as |
|---|---|---|---|---|---|
| Own-body rediscovery | `MAPT(SLICE:0,2(TOK))` twice | Same signature, one dimension | Same body, by construction | Low for a fixture. The expected id equality is known before the run. | Development fixture only |
| Same-family stride pair | `MAPT(SLICE:0,2(TOK))`, `MAPT(SLICE:1,2(TOK))` | Distinct on the 3.56 bank, 7 of 12 probes. Both labeled `char_stride`. | 3.56, after the odd/even question was already the object of study | High if this pair is the evidence of discovery. Selecting the pair encodes the historical question. | Historical fixture. Not a discovery input |
| Even-stride double | `MAPT(CAT(SLICE:0,2(TOK)\|SLICE:0,2(TOK)))` against `MAPT(SLICE:0,2(TOK))` | Distinct on 11 of 12, same family | 3.57 | High for a discovery claim. The composition and the difference are published. | Historical fixture |
| Two sequential programs | The two `cmp_…` programs from the 3.54 log, against their components and against each other | Distinct from components and from each other | 3.58 | High. The outputs were the previous measurement. | Historical fixture |
| Same-family pair | Any two recorded `char_stride` keys | Often distinct; the interesting pair is the stride pair above | 3.56 labels and outputs | The label is known. Using it as the oracle would be contamination. | Fixture, and only if the oracle is the outputs, not the label |
| Different-family pair | For example `MAPT(AT:-1)` and a `char_stride` body | Distinct on the 3.56 bank. No recorded distinct keys share a signature. | 3.56 | A test that expects "different label implies different dimension" leaks the label into the oracle. | Not allowed as an oracle. See section 8 |
| `informative=false` lease | The two compose leases | Signature still exists; the flag must not merge or split it | 3.54 log plus 3.58 signatures | The false flag is known. That is the point of a negative test. It is not a behavior. | Contamination fixture |

Nothing in this table is safe to call autonomous discovery. The doubled-odd key is not a row, and it stays unconstructed.

## 2. Fixture versus discovery

A development fixture may carry a known expected relation, in the test, outside the engine. The engine still receives only a body, the bank, and memory.

A discovery input carries no expected relation, no family label, no informative bit, and no target key. The human who chose it also does not already know the signature.

Phase 1 as written has fixtures only. Every recorded body used above already has a published signature. There is no recorded body left whose behavior is unknown to this research program. Computing a known answer automatically is not discovery.

What Phase 1 can establish, separately:

| Claim | Phase 1 |
|---|---|
| A. Signature correctness | Yes, as a fixture, on a sealed bank |
| B. Observed equivalence | Yes, as the rediscovery fixture |
| C. Observed distinction | Yes, as a historical replay. Not as a new finding |
| D. New-dimension creation | Only in the weak sense: the rule mints an id when every comparison is a distinction the fixture already expected. That tests the rule. It does not test discovery |
| E. Recursive discovery of an unknown behavior | No |

## 3. Recursion

The mock asks for a parent link and a later dimension. The bodies are recorded programs whose differences are already published. A human can know, before the engine runs, which compositions are distinct on the historical bank.

If the test names behavior C, its signature, its body, or its parents, the mock is a scripted result. If the test only checks structural facts after the run — a parent list that points at real ids, a signature hash that does not contain a body key, no depth field — and the expected signature of C is not an engine input, the mock is still a **controlled recursion demonstration**. The bodies were chosen because they differ.

It is not unknown behavior discovery. The audit does not weaken that line.

## 4. Blind holdout

A code-blind holdout is possible. One recorded body is withheld from the fixture's expected-answer table. The engine receives the executable body, the frozen bank, and memory. A separate evaluator, which the engine does not import, may later compare the stored id with a sealed reference. The evaluator writes nothing back.

A scientist-blind holdout is not possible inside the recorded set. The signatures were published in 3.56 and 3.58. Withholding the label from the code does not make the behavior unknown.

The doubled-odd body is not eligible to be that holdout. Constructing it would create the answer. Phase 1 must not claim unknown-target discovery.

## 5. Bank

Rules that stand: the bank is written before execution, hashed before execution, immutable during the run, not extended because two signatures collided, and not built from a target output.

The 3.56 bank, hash prefix `4238cefe4c7ea07e`, is safe for a labeled historical replay and unsafe for an autonomous-discovery claim. It contains `ab cd efg hij`, the probe on which the odd and even strides were shown to differ.

The discovery bank below was specified from structural categories. It was not executed against any body. It was not kept or dropped because of a collision. The empty string is the one overlap with the historical list. Empty input is a structural case, not a target probe. The other seven strings are not in the 3.56 list.

| Order | Probe | Category |
|---|---|---|
| 1 | empty | empty |
| 2 | `q` | one character |
| 3 | `mn` | two characters |
| 4 | `zzzz` | repetition |
| 5 | `token` | one word |
| 6 | `one two` | two words |
| 7 | `hello, world` | punctuation |
| 8 | `alpha beta gamma delta` | longer line |

Bank hash: `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`.

This hash is not evidence that the bank separates anything. No such measurement was made. Adding a probe after a collision remains forbidden.

## 6. Executor

The only execution primitive for a signature is `apply_micro`.

`apply_micro` returns the original prompt when the input has no tokens, when evaluation yields no tokens, or when every token is empty. The caller cannot see which path was taken. A program that truly copies the input also returns the prompt.

So a signature that only stores the return string cannot mark `EXECUTOR_FALLBACK`. Calling `eval_micro` and reimplementing the truncation and join would be a second executor. It can drift from `apply_micro`. That is not allowed in Phase 1.

Required status when the output string equals the probe: `AMBIGUOUS_COPY`. It is not a fallback bit, and it is not by itself a new dimension. An exception on a probe makes that probe incomparable. The comparison is `INSUFFICIENT_EVIDENCE` if any probe is incomparable and no probe differs. An exception is not a dimension.

Replay is a byte compare of the sealed output list and this status list, under one bank hash.

## 7. Collisions

On a finite bank, two different programs can share a signature. Under a sealed bank that event is `OBSERVED_EQUIVALENT`. It is not universal sameness. The protocol does not add a probe to break the tie.

On the 3.56 bank, no two distinct recorded keys shared a signature. That fact is about that bank only. It was not remeasured on the new bank. It must not be assumed there.

A false split would be two signatures for one deterministic behavior. The controls are: one bank hash, one call to `apply_micro` per probe, no model text, and `AMBIGUOUS_COPY` used the same way on every replay. A split that remains after those controls is an observed distinction on this bank, not a license to merge by family name.

## 8. Memory

One sealed signature is one dimension id. Many body keys may attach to it. A second run of the same body adds an observation, not an id. Memory lives for one epoch. A firewall epoch starts empty. An id from the previous epoch is not a hit.

The id is a hash of the bank hash plus the ordered outputs and statuses. It must not contain the body key, an operator name, a family label, or a target id. Provenance stores those beside the id.

The rediscovery fixture is allowed to check that two runs share an id. That check lives in the test, not in the id.

## 9. Family labels

Same family, different outputs: `MAPT(SLICE:0,2(TOK))` and `MAPT(SLICE:1,2(TOK))` are both `char_stride`, and they differ on the historical bank. An implementation that merges on the family label fails this fixture. The design's novelty rule does not consult the label, so the design passes this side.

Different family, same outputs: not in the recorded set. Zero distinct keys collided on the 3.56 bank. This audit did not build a pair to fill the gap. A Phase 1 claim that the engine was shown to ignore labels on an equivalent different-family pair would be false. The rule as written would ignore the label if such a pair appeared. The fixture does not exist. Do not synthesize one, and do not construct the doubled-odd body to serve as one.

## 10. Informative, secret, gap

Those three values are not inputs to the signature, the distance, the id, or the novelty rule. The contamination fixture is the 3.54 compose lease: `informative=false`, `secret=false`, and a 3.58 signature that still exists. The false flag must not delete the signature and must not merge it with a component.

`informative=false` does not mean behaviorally uninteresting. The design already says this. A test that drops a body because the lease was false fails the fixture.

## 11. Security

```
behavior
  -> dimension
  -> security characterization, later, not in Phase 1
  -> candidate, only if that later stage says so
  -> existing verifier
```

No edge from a new dimension to verified, to secret, or to informative. The behavior engine does not call the verifier. Phase 1 does not run the security stage. A dimension minted in Phase 1 is not a finding.

## 12. Resources

These stay separate:

| Counter | Phase 1 |
|---|---|
| Episode budget | Untouched. Not spent by a behavior call |
| `max_executed` | Untouched |
| `invent_cap` | Untouched |
| Firewall floor | Untouched |
| Behavior-call budget | New. Frozen here, before any execution on the new bank |

Frozen budget: **256** calls to `apply_micro`. The number is 8 probes times 32 program slots. It was not chosen from a signature. Half of the 256 is reserved for unevaluated pairs. That fraction was not chosen from a result. Neither number may be edited after outputs are seen.

Proposal order and ranking are untouched. The behavior path does not write `methods_log`.

## 13. Recursion and depth

There is no depth parameter. The stop is: no unevaluated pair whose components are already in memory, or the 256 calls are spent.

The reserved half does not name a depth. It can still starve a second dimension by spending calls on bodies already stored. If the run stops with budget exhausted and no parent link, the result is starvation or exhaustion. It is not "recursion failed" and it is not a reason to change the fraction.

A passing controlled demonstration is a parent link produced under these stops. It is not evidence of an unknown behavior.

## 14. Provenance

Stored beside the id: representative body key, parent ids, generation id if one exists, epoch, bank hash, discovery event.

Not inside the id: body key, generation id, family label, target identifier.

A parent id that was not minted in this epoch, or a body key that was not executed, fails integrity. The engine does not invent a parent to make a chain look deep.

## 15. Claim matrix

| Claim | Tested in Phase 1? | Evidence | Safe claim | Overclaim |
|---|---|---|---|---|
| Deterministic signatures | Only after a redesigned fixture run | Replay of one sealed bank | Same inputs, same output list | A signature is a behavior's identity |
| Observed equivalence | Fixture | Two runs, one id | Same outputs on this bank | The programs are the same function |
| Observed distinction | Historical fixture | A published pair, replayed | They differed on this bank | The engine discovered the difference |
| Rediscovery collapse | Fixture | Second run adds no id | The rule did not mint a second id | The engine recognized a known behavior in the wild |
| New dimension creation | Weak fixture | Id minted from a known distinction | The rule has a branch that mints an id | A new behavior was discovered |
| Recursive growth | Controlled mock at most | A parent link under the frozen budget | A composition can be stored as a child of two ids | Unknown recursive discovery |
| Unknown-target discovery | No | No blind unknown body exists in the recorded set | Not claimed | The engine found a behavior it was not shown |
| Security relevance | No | Security stage is not in Phase 1 | Not claimed | A dimension is security-relevant |
| Vulnerability discovery | No | Verifier is not called | Not claimed | A dimension is a finding |

## 16. Breakthrough

The minimum evidence for "AIVD has autonomous behavioral discovery" is all of:

- a dimension whose name, target key, and expected signature were not supplied
- the body was not chosen because its difference was already published
- the dimension is in memory
- a later composition uses it without a scripted parent list
- that composition's signature is a different dimension
- security is still unset

Phase 1 cannot produce that evidence. The recorded set is already published. A mock that checks a parent link on those bodies is a controlled demonstration. Saying otherwise would be the overclaim.

## 17. What has to change before implementation

1. Phase 1 tests are named development fixtures or historical replays. They are not discovery runs.
2. Discovery evaluation uses the bank hashed above, or a later bank frozen the same way. It does not use the 3.56 list.
3. Equal-to-input status is `AMBIGUOUS_COPY`. No second executor. No claimed fallback bit.
4. The stride pair, the even double, and the two sequential programs stay out of any discovery claim.
5. Recursion language in tests says controlled demonstration.
6. The different-family equivalent case stays absent. It is not filled by a synthesized body.
7. The budget stays 256 and the unevaluated share stays one half, unless a later protocol freezes a different pair before execution.
8. Dimension ids hash only the bank and the signature.

Until those are the Phase 1 rules, implementation is not authorized.

## Decision

**PHASE 1 IMPLEMENTATION NOT AUTHORIZED.**

**NO PRODUCTION INTERVENTION AUTHORIZED.**
