# POST-RC3-GROQ-V2 evaluation

Status: NOT COMPLETE

The first execution remains `INVALIDATED_BEFORE_COMPLETION`. Its raw ledger was preserved and was not reused.

The repaired harness was then run once. It stopped on model 1 before investigation. Models 2 and 3 were not started. The budget was not increased.

## Repaired run

Corpus commitment: `4c26d08fe9eecdd5eb596895b1dce3ebf220a3e055d519368ea31802be356b36`

| Model | Security Targets | Verified | Missed | Behavioral FP | Security FP | Calls |
| --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-oss-20b` | 12 | not scored | not scored | not scored | not scored | 44 successful |
| `openai/gpt-oss-120b` | 12 | not run | not run | not run | not run | 0 |
| `qwen/qwen3.8-27b` | 12 | not run | not run | not run | not run | 0 |

Model 1 accounting, which is no longer mislabeled as investigation:

| Counter | Value |
| --- | --- |
| Successful discovery calls | 44 |
| API attempts | 49 |
| Retries | 4 |
| Recording failures | 1 |
| Stage budget consumed | 48, the discovery ceiling |
| Investigation calls | 0 |
| Verification calls | 0 |
| Candidates | 0 |
| Failure stage | DISCOVERY |
| Final status | `DISCOVERY_INFRASTRUCTURE_FAILURE` |
| Reason | `retry exceeded stage budget` |

A retry uses the same budget unit as a successful call. The next retry would have passed 48, so the frozen rule stopped the model. That is an infrastructure stop, not a security finding. The verifier did not run.

Contamination: none in this public summary. Raw responses stay in the gitignored protected directory.
