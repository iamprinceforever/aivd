# F2 implementation

**F2 IMPLEMENTATION COMPLETE**

**F2 EXPERIMENT NOT EXECUTED**

The frozen bank and the frozen selection were not changed. No X1, X2, or X3 run was started. The four CEL expressions were refused before compilation. The Micro sample was not generated.

| Check | Result |
|---|---|
| Suite | 1423 passed, 0 failed |
| Science diff | empty |
| F1 diff | empty |
| Bank hash | `984ebf8a66a7d6695c03d7fef75e89f20b1a839626a1337be02adabece4243a5` |
| Selection hash | `3327aa65e688f4dac151c59c8fa0d17cda219a2a47487f689e3d7f7b06f6bcbf` |
| CEL | `github.com/google/cel-go v0.29.2`, commit `97611dc314dd41c9a4827b79f5196489f8a14201` |
| Firewall | a named condition, the Micro seed, and each frozen CEL expression raise |

The CEL adapter is a Go program that calls the pinned module. Its environment binds only `input` as a string. It does not import Micro. The Micro adapter calls the existing interpreter. Neither adapter rewrites one language into the other.

Observations use the frozen statuses, plus `UNSUPPORTED_OUTPUT` for a CEL value outside the generic domain. A signature is the bank hash and the ordered canonical observations. It has no language, source, or program field. Memory stores a dimension only for a complete signature. A second copy of the same signature does not create another dimension. Language is kept in a side list and is not hashed.

X1, X2, and X3 are separate empty memories. The functions that would measure the frozen samples refuse to run. Controls C1–C6 compare an observed word with the preregistered word and stop on a mismatch. They were not measured.

Stage E's signature type was not reused. Its completeness rule accepts only `NORMAL`, which would reject a valid F2 observation. That rule was not edited. The F2 signature sits beside it.

Fixture tests called the interpreters on programs that are not the frozen sample, including `(input)` and `AT:0` on the string `qq`. Those calls are not the experiment.
