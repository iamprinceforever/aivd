# POST-RC3-GROQ-V2 limitations

- The original 8+8 benchmark remains `ABORTED_BEFORE_EXECUTION`. Its seal was not recovered and was not rebuilt.
- V2 itself has not been executed. The Groq credential was not present in the environment, and previously pasted credentials were not reused.
- The frozen discovery ceiling is 48 calls. About 24 scenarios need roughly 70 discovery calls, so a future run is expected to leave some scenarios `NOT_EXPLORED`. That budget was not increased.
- Groq does not guarantee that seed 20260926 makes outputs bitwise deterministic.
- This evaluation cannot support a claim of universal generalization, model security, or model insecurity.
