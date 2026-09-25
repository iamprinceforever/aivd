# Candidate selection

Hash: `3327aa65e688f4dac151c59c8fa0d17cda219a2a47487f689e3d7f7b06f6bcbf`

The hash is SHA-256 of the canonical selection JSON, without the hash field. The bodies were not generated.

Micro uses the existing generator `generate_bodies`, seed `aivd-4.2-micro-v1`, canonical deduplication, generator order, and the first 8 programs. They are not chosen to resemble a CEL expression.

CEL is not sampled. The set is every expression in `E ::= input | E + E` with at most 5 nodes, over the string binding `input`. Canonical sources, in lexicographic order:

1. `(input + input) + input`
2. `input`
3. `input + (input + input)`
4. `input + input`

There is no seed that changes this set. Nothing is dropped because it looks novel, equivalent, or familiar.

The public controls are separate from both samples:

| Id | What is declared | Expected |
|---|---|---|
| C1 | Micro `TOK` and CEL `input`, both the identity behavior | same dimension |
| C2 | CEL `input` and CEL `input + input` | distinct dimensions |
| C3 | CEL `input` measured twice | same dimension |
| C4 | Micro `TOK` and Micro `REV(REV(TOK))`, evaluated as written | same dimension if the behavior matches |
| C5 | CEL `missing`, which is not bound | no dimension |
| C6 | any signature with an `AMBIGUOUS`, `INVALID_EXECUTION`, `EXECUTION_FAILURE`, or `UNSUPPORTED_OUTPUT` probe | no dimension |

C4 must not be canonicalized away before it is evaluated. If the run collapses it, that is reported. It is not repaired.
