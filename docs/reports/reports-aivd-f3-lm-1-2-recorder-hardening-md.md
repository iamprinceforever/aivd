# AIVD 4.0 F3-LM-1.2 Recorder Hardening

**Status:** INFRASTRUCTURE ONLY. NOT EXECUTED.  
**Recorded:** 2026-09-26  

```
PREVIOUS F3-LM-1.1 REMAINS INVALIDATED
NO NEW QWEN3 EXECUTION OCCURRED
F3-LM-1.2 EXPERIMENT NOT YET EXECUTED
F4 NOT STARTED
```

## Prior event

Commit `434a96622dd8a968ad389c14fa774903e988602d` stays unchanged. That run is `INVALIDATED_REAL_INVOCATION_NO_USABLE_OBSERVATION`: one HTTP 200 happened, thinking was off, 17 tokens were generated, and the recorder crashed on a missing `template_id` before the body was saved. That output is not recovered and is not counted.

## Repair

A model body is written to disk and hashed before any field is read. `template_id` is optional audit metadata. If it is absent the status is `MISSING_OPTIONAL` and the assistant text is still kept. Thinking text is stored separately and is not folded into the visible response. A parser exception after the raw write is `RAW_RESPONSE_PERSISTED_PARSE_FAILURE`, not data loss.

If the process stops between the raw write and normalization, restart reads the raw file, checks its hash, and normalizes it. It does not call the model. A trial is marked executed when it is submitted. A later recording failure is `RECOVERY_REQUIRED`. The same trial is not submitted again.

## Firewall

`F3_LM_EXECUTION_AUTHORIZED` remains false. `attempt_model_execution()` refuses. F3-LM-1.2 starts with an empty discovery memory and zero trials. Grammar, relations, sampling, seeds, and the interface were not changed.

```
F3-LM-1.2 EXPERIMENT NOT YET EXECUTED
F4 NOT STARTED
```
