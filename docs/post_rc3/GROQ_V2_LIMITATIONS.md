# POST-RC3-GROQ-V2 limitations

- The original 8+8 benchmark remains `ABORTED_BEFORE_EXECUTION`.
- V2 execution stopped on model 1. A transport retry would have exceeded the current stage budget, which the frozen session records as `RecordingFailure: retry exceeded stage budget` and an integrity failure.
- Because that failure is raised inside discovery, the driver exception path attributes those calls to investigation. The stage table for the failed run is therefore not a completed stage breakdown.
- Models 2 and 3 were not run. No comparison and no reproducibility measurement exist.
- The discovery ceiling remains 48. It was not increased after this failure.
- No claim is made about model security, model insecurity, or generalization.
