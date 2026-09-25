# F2 design freeze

**F2 EXPERIMENT READY**

Nothing was executed. CEL was not run. Micro candidates were not generated. F1 and `aivd/science` were not modified.

CEL is the implementation for this experiment. JMESPath and Starlark stay valid for a later experiment. This is an engineering choice: a public interpreter, a side-effect-free `Eval` on an explicit activation, no solver, and no translation into Micro. It is not a claim that CEL is a better language.

| Identity | Value |
|---|---|
| Implementation | `google/cel-go` tag `v0.29.2` |
| Commit | `97611dc314dd41c9a4827b79f5196489f8a14201` |
| License | Apache-2.0 |
| Module required by that commit's `go.mod` | `cel.dev/expr v0.25.1` |
| Prose spec version in the README | `NOT_STATED` |

The older `cel-spec` tags are not the implementation identity. An unpinned CEL build is not allowed.

The adapter wraps `Eval`. It does not emit a Micro tree. The behavioral record receives a probe id, a status, and a canonical value. It does not receive a CEL AST, operator, type, or source text. Language may be stored beside the dimension. It is not an input to equality.

A successful value that canonicalizes to something other than the input is `VALID_OUTPUT`. The same canonical value as the input is `VALID_IDENTITY`. A deterministic evaluation or check error is `EXECUTION_FAILURE`. If the adapter cannot establish an observation, the status is `INVALID_EXECUTION` or `AMBIGUOUS`. `UNSUPPORTED_OUTPUT` is a successful CEL value outside the generic domain. None of those last three creates a dimension. A fallback string is not rewritten into a success.

Micro observations in this experiment use the same statuses. An empty Micro evaluation that returns the original prompt is `INVALID_EXECUTION`, not an identity. Stage E's `AMBIGUOUS_COPY` rule is left untouched.

Shared memory starts empty in each condition. X1 is the Micro sample. X2 is the CEL sample. X3 appends the Micro sample, then the CEL sample, into one empty memory. Equality is the canonical observations on the bank below.

The blind samples are sealed. The controls are public, because their behaviors are declared here, before any run. Controls are not mixed into the blind sample.
