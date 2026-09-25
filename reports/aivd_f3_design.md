# F3 design

**F3 DESIGN COMPLETE**

**F3 IMPLEMENTATION NOT AUTHORIZED**

**F3 EXPERIMENT NOT AUTHORIZED**

F1 and F2 stay as they were. This document does not reinterpret them. Nothing here was implemented or run.

## Question

The question is not whether AIVD can find a named vulnerability. It is whether a behavior can be found without that vulnerability being supplied, and whether a separate, pre-registered relation can then say that the behavior breaks a security property, tightly enough that an independent verifier can reproduce the relation without being told the answer.

Four words stay separate:

| Word | Meaning |
|---|---|
| Behavior | A complete signature from the existing behavioral engine. It has no security label. |
| Hypothesis | A claim that one frozen relation fails for that signature in a sealed context. |
| Evidence | The locked inputs, outputs, and hashes that the claim points at. |
| Verification | A second party recomputes the relation. Their verdict does not re-enter discovery. |

A new dimension is not a finding. A different output is not a violation.

## Unknown

| Level | Enough for F3? |
|---|---|
| Hidden from the engine, known to the experimenter | No |
| Unread by the experimenter before the lock | Necessary, not sufficient |
| Unread by the evaluator | No. The evaluator must be able to recompute |
| Not written down in this repository's historical reports | Necessary, not sufficient |
| The artifact was not produced for this study | Required for the strong claim |

Hiding a string, a label, or an expected output does not make a behavior unknown.

## Property

Two relations are pre-registered. Neither names a bug.

**Non-interference.** An artifact declares zero or more channels with role `public` or `private`. The roles are interface marks, not a judgment that a leak exists. If there is no private channel, the relation is `NOT_APPLICABLE`. If there is one, the public projection must be identical across every sealed pair that changes only the private channel. `N = 4` pairs, and all 4 must differ before a violation is recorded. One differing pair is not enough. The outputs are not scanned for marker text.

**Policy equality.** If, and only if, the artifact arrives with a policy already attached, two principals the policy treats the same way must get the same observation of the same resource. If no policy is attached, the relation is `NOT_APPLICABLE`. This experiment does not invent a policy in order to create a miss.

Any other family, including one that needs a target-shaped oracle, is out. The legacy plant check that looks for a marker substring is a rejected oracle. It is not an F3 mechanism.

F2's string programs have no channels and no principals. On that corpus every relation is `NOT_APPLICABLE`. Those dimensions remain behaviors. They are not promoted.

## Reference

The reference is the relation above, not a desired output. What is known before discovery is the relation, the size `N = 4`, and the rule that missing structure means not applicable. What is unknown is which behaviors will appear and whether any sealed pair will fail the relation. The test is differential execution of one discovered behavior. A false positive is a public difference caused by something other than the private channel, which is why every pair has to move only that channel, and why a single pair cannot mint a hypothesis.

The reference becomes the vulnerability if someone writes "the public output must not equal this particular extract." That sentence is forbidden.

## From a new behavior to a hypothesis

The behavioral search never reads a security bit. After a signature is complete, a separate step asks only the two relations. The outcomes are:

| Observation | Hypothesis |
|---|---|
| `NOT_APPLICABLE` | none |
| relation holds | none |
| relation fails on all 4 pairs | one hypothesis |

The hypothesis names the signature, the relation id, and the context handles. It does not name a target. No new probe is added after a failure. Security does not change which behavior is explored next. A later composition may use a behavior as a parent for behavioral reasons only.

## Controls

Negative, and these would have to pass before any positive claim:

- A novel behavior with no private channel, including the F2 distinctions, yields no hypothesis.
- Two behaviors that both ignore the private channel but differ on public input are a behavioral difference and not a violation.

Positive controls are pipeline tests only. They are labeled, stored in a separate memory, and omitted from the discovery ledger and from any unknownness claim. This repository must not build one. A positive control is not evidence that an unknown issue was found.

## Verifier

The verifier receives the behavior, the context handles, the sealed payloads, and the relation id. The verifier does not receive AIVD's verdict, a score, a target name, or an expected answer. The verifier recomputes the relation. Agreement with AIVD is not the definition of success. Sending the verdict back into discovery invalidates the run.

F4, which is not authorized here, would require that independent recomputation, a negative control that stays clean, and a result that does not depend on a marker string. "The verifier agreed" is not F4.

## Package

Discovery locks, in order: signature id, relation id, context handles, output hashes, environment, timestamps. Plaintext payloads and the hypothesis text stay sealed until that lock. Verification writes a second package. The two are not merged.

## Sources

| Source | What it can support |
|---|---|
| A. An artifact that already existed, sealed by someone else, with roles assigned as interface structure | The strong claim, if the provider did not select it for a leak |
| B. An artifact commissioned for this study | Unknown to the experimenter only if still sealed. It does not support "not produced for this study." A commission that asks for a vulnerability is manufactured |
| C. Sealed output of a generator this project wrote | Unknown to the engine. The author of the generator is not blind |
| D. Another model's output | Same limit as C unless the model and the sample already existed and were not prompted for a vulnerability |

Self-generated data is not independent. The F2 sample is not a security corpus.

## Leakage

The discovery path must not read historical reports, marker checks, the positive-control identity, the verifier's verdict, or an expected answer. The experimenter must not read sealed payloads before the lock. The evaluator must not write a verdict back. Candidate generation must not be scored by a security relation.

## Hypothesis tree

| Id | Disposition in this design |
|---|---|
| H-F3-1 Novelty alone creates false findings | Real risk. Blocked only if a hypothesis requires a failed relation. Not yet tested |
| H-F3-2 A property can be judged without asking whether the behavior is new | Required by the design. A known behavior may fail and a new one may hold. Not tested |
| H-F3-3 A generic relation can connect behavior to security | Proposed: non-interference and policy equality. Untested |
| H-F3-4 Differential execution can be evidence | This is the proposed measurement. It is not a finding by itself |
| H-F3-5 The engine can form a hypothesis without the target | Possible only under the source and leakage rules. Not shown |
| H-F3-6 An independent party can recompute the claim | Specified, not run |
| H-F3-REJECT The result is leakage or a label applied afterward | Any such path invalidates the run |

## Success and failure

Success requires all ten: the behavior was not supplied as a target; it was not pre-labeled; the relation is not a hidden oracle; the hypothesis comes from the relation failing; negative controls stay clean; the behavior is reproduced by the verifier; the verifier judges the relation rather than AIVD's label; no historical target is evidence; the locked package is sufficient to reconstruct the claim; no marker string is the decider.

Failure is any of: a marker oracle, a probe added after a miss, novelty promoted to a finding, a positive control counted as discovery, a reference that names the forbidden output, a verdict returned to search, a historical body used as a seed, or a self-generated corpus described as independent.

## Attacks considered

| Attack | Result |
|---|---|
| The reference names the forbidden output | Closed. The reference is equality across private variants, or it is not applicable |
| A control teaches the historical target | Closed. No positive control is constructed here, and a future one cannot enter the discovery memory |
| The generator is aimed at a leak | Closed. Search priority is behavioral. Security does not rank it |
| The experimenter reconstructs a leak from a self-generated program | Open for sources C and D. Those sources cannot carry the strong claim |
| The verifier is handed the conclusion | Closed. The verifier recomputes and does not return a verdict |
| Every new signature becomes a finding | Closed. No channel means not applicable. The F2 distinctions are the negative example |
| One accidental difference becomes a finding | Closed. All 4 sealed pairs must differ, and only the private channel may change |
| A historical body is copied in as a candidate | Closed as a rule. There is no corpus yet in which to enforce it |
| A positive control shares a memory with the unknown run | Closed. Separate memory, no claim |
| The hypothesis step adds a probe after a miss | Closed. The sealed pairs are fixed before measurement |

No attack required a change to the question. The attacks that remain open restrict which sources are allowed to count.

## Blocker

This repository does not contain an artifact that already had public and private channels, or an attached policy, assigned independently of a vulnerability and unread by the experimenter. The F2 programs do not become that artifact by being wrapped in a channel invented here. Inventing the channel would invent the result.

Until such an artifact is supplied from outside, F3 cannot be run.

## Unresolved

Whether a provider can assign channel roles without quietly selecting for a leak is an audit question, not something this repository can certify. Whether these two relations miss entire classes of security failure is accepted. Adding a relation later, after a result, is not allowed. `N = 4` is a pre-registered conservative rule, not a number fit to data, because there is no data.
