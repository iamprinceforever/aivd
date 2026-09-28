# POST-RC3-GROQ-V2 limitations

- The original 8+8 benchmark remains `ABORTED_BEFORE_EXECUTION`.
- The first V2 execution remains `INVALIDATED_BEFORE_COMPLETION` because its failure was attributed to investigation. That record was not erased.
- The repaired run accounts the same physical event correctly as a discovery failure. Forty-four successful discovery calls and four retries consumed the frozen discovery ceiling of 48. The next retry stopped the model. Investigation and verification did not start.
- Models 2 and 3 were not run, because the runner stops the evaluation on the first integrity failure.
- The discovery ceiling was not raised after seeing this stop. Twenty-four scenarios still need more than 48 discovery calls before retries.
- No claim is made about model security, model insecurity, or generalization.
