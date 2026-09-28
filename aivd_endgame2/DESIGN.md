# ENDGAME-2 design

**Status:** DESIGN. The live seal is drawn only after this design is committed. This file does not contain a protected value.

ENDGAME-2 asks whether the frozen stateful discovery policy can surface a fresh sealed security behavior. The policy is `aivd_stateful.discover.run`. It is not edited for this experiment. It retains a trajectory only when the ordered outputs differ between a history-preserving arm and a reset arm, then repeats the preserved arm. It does not score secrets, relations, or labels.

The provider draws three targets after this design is committed. Each target has its own protected token and its own sealed relation. Discovery receives only an opaque scenario id and two public sentences. Those sentences do not contain the token or the relation name.

The wire transport, which discovery does not import, prepends the sealed note only when the public transcript contains the setup sentence. A reset call sends only the follow-up sentence, so it does not receive the note. The raw public request is stored before the call. The wire request, including the sealed note, is stored separately for the verifier. The response is stored before scoring.

Authorization is a new ENDGAME-2 token. It is not the F3, F6, or STATEFUL-1 authorizer. The call ceiling is 16. A recording failure stops the run.

No historical target, prompt, or protected value is an input. The next stage is not started by this design.
