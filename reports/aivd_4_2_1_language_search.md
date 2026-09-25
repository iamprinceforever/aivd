# Language B search

**F2 STATUS: READY_FOR_LANGUAGE_B_DESIGN**

No adapter was written. No probe bank was frozen. X1, X2, and X3 were not run. No language was invented in this repository.

The search looked for a public interpreter that already executes a program on an input. It did not look for security behavior, for Micro, or for a language that would make a known target succeed. Pins were taken from `git ls-remote` on 2026-09-25. They are not floating names.

Three candidates meet the requirements. They are not ranked. A later authorization may use any one of them. It may not use more than the contract already stated: the adapter executes, and the behavioral engine sees only a probe, a status, and an output.

## Accepted

| Language | Pin | License | How a program runs |
|---|---|---|---|
| CEL | `google/cel-go` tag `v0.29.2`, commit `97611dc314dd41c9a4827b79f5196489f8a14201`. Spec `google/cel-spec` tag `v0.25.3`, commit `ba58ae5007845f3a1279b488cdeb79645ce958bb` | Apache-2.0 | `cel.Program.Eval` on an input activation. The project documents evaluation as side-effect free. No solver. |
| JMESPath | `jmespath/jmespath.py` tag `1.1.0`, commit `6ff419a8b171d055a9bfc6904605bceb8b7a80ef` | MIT. Copyright 2013, Amazon.com, Inc. or its affiliates | `jmespath.search(expression, data)` walks the expression against one JSON value. No solver. |
| Starlark | `google/starlark-go` commit `89a6a09411d5c7a33409dc050c2fecdf8f4eca8f`. No release tags were listed | BSD-3-Clause. Copyright 2017, The Bazel Authors | `starlark.ExecFile`, then `starlark.Call` with the input as an argument. No solver. |

None of these is translated into Micro. None depends on AIVD. The first public release date of each project is `NOT_RECORDED` here, apart from the JMESPath copyright year.

Starlark is deterministic only if the predeclared environment has no clock and no I/O. That is a constraint on the adapter, not a property of every possible Starlark embedding. CEL's spec tag is older than the interpreter tag. Those are the remaining uncertainties. They do not reject the candidates.

A generic input is not frozen. CEL can take a binding, JMESPath a JSON value, and Starlark a function argument. Those are not Micro token strings. The probe model waits until one language is authorized.

## Rejected

| Candidate | Pin inspected | Reason |
|---|---|---|
| E1 synthesis benchmark dataset | `c02d18c3608b164ff09cc5cad3c02f98f9c1ef21` | Examples, not an interpreter. |
| E2 SyGuS | `13c8deb68a873635879c9a69bc78caebd340f646` | Specifications. A solver would search. |
| E3 SyGuS-Comp14 | `c56409093597c4c1f358b42a9b0db8dfefe52040` | Specifications plus search programs. |
| E4 PROSE | `50cc38f602fffe14073953cf128825ea8d92b188` | SDK samples, not a small interpreter. |
| jq | `jqlang/jq` tag `jq-1.8.2`, commit `34f7186b86743a083a589741b6cea95293524108`. MIT-style grant, copyright 2012 Stephen Dolan | The C interpreter is too large to audit here. A program can also read further input, so determinism is not a property of the language as a whole. |
| Jsonnet | `google/jsonnet` commit `2ef32abf3d5c7a0a7699ccb3043936ce0e244ed2` | Apache-2.0. The C++ evaluator is too large to audit here, and import can read files. |
| Brainfuck | `fabianishere/brainfuck` tag `2.7.3`, commit `59415237188ff94ec7b0d8ebb32420aab4309c11` | The program runs, but no license file was found. Unclear license. |
| CPython | not pinned | The execution surface is too large to audit in this stage. |
| Dafny | not pinned | Checking a program uses a solver. That is not the required interpreter. |

Translating any rejected candidate into Micro would still be invalid. An internal toy language was not created.
