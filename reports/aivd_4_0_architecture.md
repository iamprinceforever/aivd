# AIVD 4.0 architecture

Status: design audit only. No engine. No production change.

The question is whether AIVD can create a persistent behavioral dimension from what a generated program does, without being told the dimension in advance. Family labels, lease metrics, and the secret substring do not answer that question. They stay where they are.

## What exists

A generated microprogram is a `Micro` tree. `apply_micro` runs it. If the tree yields no tokens, `apply_micro` returns the original prompt. That fallback is an executor property. It is not a behavior.

`semantic_class_of` labels a tree by which operators it contains. Any tree with `SLICE` is `char_stride`. That label is a family name. It is not a signature.

Live composition admission runs `b(a(identity))` on one string and rejects the result when it is empty or equal to the identity, to `a(identity)`, or to `b(identity)`. Pairs are chosen because their family labels differ. `behavioral_equivalent` compares two bodies on two fixed probes and is not called by live discovery.

`informative` is `secret OR (metric >= 0.28 AND error)`. `secret` is the substring `secret{` or `disallowed:` in the observation text. `representation_gap` is a boolean on that same observation. It can call `invent()`. None of the three reads program outputs.

`board.max_executed` counts completed atom leases after the firewall reset. It is an execution quota, not a behavioral depth.

`GenerationRecord` and the firewall epoch record where a body came from. They do not record what the body does on a probe bank.

## Reuse, without changing it

- `Micro` and `apply_micro` are the deterministic executor. The new engine calls them. It does not replace them.
- Body keys and `GenerationRecord` are provenance for the program. A dimension points at them. It does not rewrite them.
- The firewall epoch is a boundary. Behavioral memory for a fresh plant starts empty. Memory from before a firewall is not evidence inside the new epoch.
- `semantic_class_of` remains the family label, reported beside a dimension, never used to build a signature or to decide novelty.

## Leave untouched

Until a later reviewed integration, do not change:

- `semantic_class_of`
- the lease formula and the `0.28` constant
- the secret substring and verification
- `representation_gap` and `computational_usefulness`
- `max_executed`, `invent_cap`, and the episode budget
- the live identity-string composition check
- proposal order, ranking, and scoring
- firewall reset
- `GenerationRecord`

The doubled-odd body `MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))` is not a component, not a seed, and not a probe.

## New subsystem

The engine is a separate package. It is not a branch inside `ScienceDesigner.observe`. Working name: `aivd.behavior`. Nothing in `aivd/science` imports it in this phase.

```
program body
    |
    v
BehavioralExperiment     frozen bank, apply_micro only
    |
    v
BehavioralSignature      ordered outputs, no family label
    |
    v
BehavioralDistance       OBSERVED_EQUIVALENT | OBSERVED_DISTINCT | INSUFFICIENT_EVIDENCE
    |
    v
BehavioralMemory         dimensions, not classes
    |
    v
BehavioralNoveltyFrontier
    |
    v
growth over bodies whose dimensions are already in memory
    |
    v
same experiment, same bank
    |
    v
new dimension or known observation

Security characterization is a later reader of a dimension.
It does not write the signature.
```

Replacing `semantic_class_of` with a signature, and leaving the rest of the loop alone, is not this subsystem.

## Data

`BehavioralSignature` holds the bank hash, the ordered probe identifiers, and for each probe the output string, its length, and a status: `OK` or `EXECUTOR_FALLBACK` when `apply_micro` returned the input unchanged because the program produced nothing. The fallback is recorded. It is not rewritten into a fake output. No model text is stored here.

`BehavioralDimension` holds an id, the signature, one representative body key, the discovery context (epoch, generation id if one exists), the probes that distinguish it from its nearest stored dimension, a finite-bank confidence that is only `OBSERVED`, parent dimension ids, and the body keys that were composed to produce it. Confidence is not a probability of being a vulnerability.

`BehavioralMemory` is a set of dimensions plus the observations that matched them. Lookup is by comparison against stored signatures, not by family label and not by body key. Two different keys with `OBSERVED_EQUIVALENT` signatures are one dimension.

## Breakthrough, versus a patch

A breakthrough is a dimension created from execution, stored, and then used as a parent of a later composition whose own signature is a second new dimension, with the held-out body absent from every discovery input, and with security left unset by that novelty.

These are not breakthroughs: the known odd body materializes, `informative` becomes true, `max_executed` is raised, or `char_stride` is split by a hand-written odd/even rule.

## Implementation, after review

0. This document. No code.
1. Offline benchmark on already recorded bodies. The engine may not import plant secrets.
2. Twin run: the current path unchanged, the new path beside it. No shared mutable state.
3. Mock recursive growth. Depth is not a parameter. A composition is admitted only when its signature is distinct. The sequence of dimensions is whatever the bank and the budget produce.
4. Fresh plant only after 1–3. No mid-run retune. No target injection. Model calls stay in the existing plant. Behavior experiments do not spend `board.executed`.
5. Held-out security evaluation in a module the engine does not import.

## Can it discover an unknown dimension?

The mechanism can. A program whose outputs differ from every stored signature on the frozen bank becomes a dimension, and nothing in that step needs the dimension's name. The mechanism cannot promise that the bank separates the behavior a later auditor cares about. If the held-out behavior collides with a stored signature, the engine will treat it as known. That is a false merge of a finite bank, not a reason to add a special case.
