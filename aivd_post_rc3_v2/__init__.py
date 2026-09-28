"""POST-RC3-GROQ-V2. A fresh evaluation. Not a rerun of the aborted 8+8 corpus.

Does not modify RC3 or the historical POST-RC3 harness. Drives the same frozen
pipeline through a distinct experiment id, corpus, and report directory.
"""

EXPERIMENT_ID = "POST-RC3-GROQ-V2"
MARK = "POST-RC3-GROQ-V2 / FRESH CORPUS / NOT THE ABORTED 8+8 BENCHMARK"
HISTORICAL_ABORTED_COMMITMENT = "70881e66f727ba8e626031b5dc32bf6d7459d6aac1b7b5eb139a9aa9463a438b"
