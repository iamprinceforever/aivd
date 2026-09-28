"""POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.

Groq three-model generalization evaluation harness. Imports and drives the frozen
RC3 pipeline (discovery, stateful trajectory, investigation, hypothesis,
provenance-aware verification) unchanged. Adds only a Groq OpenAI-compatible
model-client adapter and evaluation orchestration.
"""

EXPERIMENT_ID = "POST-RC3-GROQ"
MARK = "POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE"
