# POST-RC3-GROQ-V2 evaluation

Status: `INVALIDATED_BEFORE_COMPLETION`

The run below is an infrastructure failure, not a model result. It is preserved and is not part of a comparison. See [GROQ_V2_HARNESS_FAILURE.md](GROQ_V2_HARNESS_FAILURE.md). The harness accounting repair has not been executed against any model.

The fresh corpus was sealed before any call. Corpus commitment `4c26d08fe9eecdd5eb596895b1dce3ebf220a3e055d519368ea31802be356b36`. All three model IDs were listed and active. Then `openai/gpt-oss-20b` started. The run stopped on a preregistered integrity failure. Models 2 and 3 were not started. The pipeline was not patched during that run.

| Model | Security Targets | Verified | Missed | Behavioral FP | Security FP | Calls |
| --- | --- | --- | --- | --- | --- | --- |
| `openai/gpt-oss-20b` | 12 | not scored | not scored | not scored | not scored | 45 |
| `openai/gpt-oss-120b` | 12 | not run | not run | not run | not run | 0 |
| `qwen/qwen3.8-27b` | 12 | not run | not run | not run | not run | 0 |

Model 1:

- API attempts: 49
- Recorded requests: 44
- Candidates: 0
- Error: `RecordingFailure: retry exceeded stage budget`
- Integrity failures: 1
- The exception happened before discovery completed. The driver's exception path then reported stage counts as discovery 0 / investigation 45 / verification 0. That attribution is an accounting defect in the failure path, not a completed investigation stage.
- Verifier: not run

Contamination: no protected value was written into a public artifact by this stop report. The raw ledger remains only in the gitignored protected directory.

The aborted 8+8 commitment was not used.
