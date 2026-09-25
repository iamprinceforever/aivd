# Execution contract

This is a contract for a later experiment. It was not coded.

An adapter may implement `execute(program, probe) -> observation`. The observation carries a status, an output, and the probe index. The statuses are:

| Status | Meaning |
|---|---|
| VALID_OUTPUT | The interpreter ran and produced a value different from the input. |
| VALID_IDENTITY | The interpreter ran and produced the input. |
| EXECUTION_FAILURE | The interpreter raised. |
| INVALID_EXECUTION | There was no evaluation, or a fallback replaced an empty result. |
| AMBIGUOUS | The adapter cannot tell an evaluated identity from a fallback or an encoding failure. |

`AMBIGUOUS` is not Stage E's `AMBIGUOUS_COPY`. A complete signature contains only `VALID_OUTPUT` and `VALID_IDENTITY`. The other three statuses mint nothing.

The engine may see the probe id, the status, and the output. It may not see an AST, an operator, a class, a benchmark, or a target. Two languages share a dimension only when those observations match. Language identity is not an input to that match.

No probe bank was frozen. The Micro banks stay where they are.
