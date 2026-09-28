# POST-RC3-GROQ-V2 harness failure

Classification: `INVALIDATED_BEFORE_COMPLETION`

This is an infrastructure failure. It is not a model-quality result and it is not part of any model comparison. The historical execution record is unchanged.

## What happened

`openai/gpt-oss-20b` stopped during discovery.

| Counter | Historical value |
| --- | --- |
| `session.calls` | 45 |
| Persisted request records | 44 |
| API attempts | 49 |
| Extra retries | 4 |
| Candidates | 0 |
| Investigation | not started |
| Verification | not started |

The raised error was `RecordingFailure: retry exceeded stage budget`.

## Actual stage

`DISCOVERY`

The exception path in `aivd_post_rc3/driver.py` then did:

```python
stage_calls["investigation"] = stage_calls["investigation"] or max(session.calls - stage_calls["discovery"], 0)
```

Discovery had not returned, so `stage_calls["discovery"]` was still 0. The 45 calls were therefore reported as investigation. That attribution was wrong.

## Root cause

Two accounting bugs:

1. A retry consumes the same stage-budget unit as a successful call (`Budget.charge` increments `turn_executions`). The extra retries on the last discovery invocation crossed the discovery ceiling. The session raised before that invocation was persisted.
2. The driver exception handler did not know the active stage. It assigned every not-yet-closed call to investigation.

`session.calls` also incremented before a response was persisted, so the failing invocation was counted as a call even though it was not a successful response.

## Fix

The frozen POST-RC3 driver and session are left byte-for-byte in place so the aborted V1 preregistration still matches. The repaired path is `aivd_post_rc3_v2.session.V2Session` and `aivd_post_rc3_v2.driver`.

- Every attempt record has exactly one stage.
- A retry's `retry_of` is the original attempt of the same logical call and the same stage.
- Successful responses, API attempts, retries, recording failures, and stage-budget units are separate counters.
- A recording failure is not a successful call.
- `FAILURE_STAGE` is the stage that was active when the exception was raised.
- An unfinished discovery run cannot be reported as completed discovery, investigation, or verification.

Budget policy, unchanged: a successful call and each retry consume one stage-budget unit. They are no longer allowed to change stage.

## Regression fixtures

1. Two discovery successes, then a transport failure with two failed retries. Status `DISCOVERY_INFRASTRUCTURE_FAILURE`. Discovery calls 2. Discovery attempts 5. Investigation 0. Verification 0.
2. Discovery complete, one investigation success, then an investigation recording failure. Status `INVESTIGATION_INFRASTRUCTURE_FAILURE`.
3. Discovery and investigation complete, one verification success, then a verification recording failure. Status `VERIFICATION_INFRASTRUCTURE_FAILURE`.
4. A retry that exhausts the discovery budget stays a discovery failure.
5. The repaired `run_model` exception path, with a stub transport, keeps the same discovery failure on discovery.

## Not done

No model was called. The 12+12 corpus was not modified. RC3 was not modified. The three-model evaluation was not restarted.
