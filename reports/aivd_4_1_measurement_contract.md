# Measurement contract

This contract does not rewrite Stage E. `AMBIGUOUS_COPY` still means `out == probe` there, and an incomplete signature still mints nothing.

Phase 0 showed that one label was covering three events. The F1 observation separates them:

| State | When |
|---|---|
| VALID_OUTPUT | The program was evaluated and the joined output differs from the probe. |
| VALID_IDENTITY | The program was evaluated and the joined output is the probe. |
| INVALID_EXECUTION | There was no token to evaluate, or evaluation produced no nonempty token and the executor would have returned the probe as a fallback. |
| EXECUTOR_FAILURE | The executor raised. |
| AMBIGUOUS | Evaluation and `apply_micro` disagree. |

A signature is complete only when every probe is `VALID_OUTPUT` or `VALID_IDENTITY`. A fallback is not recorded as an output, and it does not create a dimension. The dimension id is the hash of the bank and the observations. It is not the body key.
