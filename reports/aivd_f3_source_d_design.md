# Source-D design

**F3 SOURCE-D DESIGN COMPLETE**

**SOURCE-D CORPUS NOT GENERATED**

**F3 IMPLEMENTATION NOT AUTHORIZED**

**F3 EXPERIMENT NOT AUTHORIZED**

The relations stay the ones frozen in `bbf5c12`: non-interference across a private channel, with all four sealed pairs required, and policy equality only when a policy arrives with the artifact. Nothing here was generated, run, or implemented. Source-D is not Source-A.

## What the claim is

Source-D can support this sentence, and only if the controls below hold:

The corpus was generated outside the discovery engine, under a target-neutral specification that was fixed first, and the engine did not receive labels.

It cannot support these sentences:

The vulnerability was already in the world. AIVD found a public CVE. The provider had no design choices. The person who wrote the request was blind.

## Roles

Four logical roles:

| Role | May do | Must not do |
|---|---|---|
| Provider | Generate artifacts from the frozen specification | See the discovery engine, its reports, or its historical targets. Name which artifact should fail |
| Sealer | Check schema, encrypt, shuffle, commit | Drop individual artifacts because they look interesting or dull |
| Discovery | Call the execution interface. Form a hypothesis from observations | Read source, labels, private inputs, provider notes, or the verifier's verdict |
| Verifier | Recompute the relation after the discovery lock | Send that verdict back |

These are not four people in this repository. If one operator writes the request and also reads the artifacts, the claim falls to engine-isolation. The design does not pretend otherwise.

## Provider request

The request states the relation, the schema, the runtime, the size, and the ordering rule. It does not contain an example of a violating program, a desired signature, a quota of failures, or a location where a leak should sit. It does not say which artifact discovery should notice.

A public model is not evidence that the provider has never seen this repository. That exclusion has to be shown, for example by a checkpoint that predates the repository, or by an air gap. If it is not shown, the report must say the prompt was clean and the model's history is `NOT_RECORDED`.

One shot. No second round that keeps the "interesting" artifacts. If any artifact fails the frozen schema, the sealer rejects the whole corpus before discovery starts. Partial deletion is selection.

## What is frozen before generation

Provider identity and version, the exact request text, grammar limits, corpus size, the two relations, `N = 4`, and the shuffle rule. The request text is part of the public commitment. A seed, if the provider has one, is committed as a sealed value, not published in the clear.

The discovery ledger does not publish how many artifacts violate the relation. A quota would tell the provider to manufacture failures. The schema allows both holds and violations. A corpus in which every relation holds is valid, and the honest result is that no hypothesis was formed. After the lock, the absence of a hold or a violation is a limitation of that corpus, not a reason to generate again.

## Sealing

A hash of a short program is not a seal. A small grammar can be searched until the hash matches.

The sealer encrypts each artifact, its four private pairs, and its own relation result under a key discovery does not have. The public ledger stores the handle, the ciphertext hash, the protocol version, and the time. It does not store the source, a filename containing a label, a directory named for the outcome, or the provider's result.

Discovery never receives the plaintext. It submits a handle and a pair index to an executor that holds the plaintext. The executor returns the public observation only. The private bytes stay on the executor's side, so discovery cannot choose them and cannot aim them at a historical target.

The key is released to the verifier only after the discovery ledger is locked. It is not released to discovery.

## Selection

Order is a shuffle under the sealed seed, not the provider's order and not a sort by outcome. The rule is fixed before any artifact exists. After the first call to the executor, nothing is added, removed, or replaced. An artifact that will not run is `EXECUTION_FAILURE`.

## Hypothesis

Discovery may record a new behavior. The security step may then ask only the two frozen relations, using the observations the executor returned. A difference in output is not enough. No third relation is added after the fact. A hypothesis does not read the sealed result.

Pipeline controls, if they are ever built, live in a separate ledger, are marked as pipeline controls, and are not historical AIVD programs. They are not an unknown finding. This design does not build one.

## Verifier

V2 comes first. The verifier gets the plaintext, the declarations, and the frozen relation, and recomputes it. The verifier does not get a bit that already says the artifact fails.

V1 comes after the verifier's own result is locked. The sealed provider result is opened and compared. A mismatch is `CORPUS_INTEGRITY_FAILURE`. It is not an AIVD failure, and it is not repaired by editing the relation.

The verifier's result does not go back to discovery.

## Attacks

| Attack | Disposition |
|---|---|
| The request says where the leak should be | Closed. The request has no example and no target location |
| The provider writes the answer into a field or a filename | Closed. The schema rejects those fields, and the sealer issues opaque handles |
| The experimenter reads the source | Open if the same person is provider and reader. The claim then drops to engine-isolation |
| A hash is searched | Closed. The ledger stores ciphertext hashes, and discovery does not receive plaintext |
| Metadata states how many artifacts fail | Closed. That count is not on the discovery ledger |
| The verifier trusts the provider's bit | Closed. V2 is computed before V1 opens the bit |
| Generation order clusters failures | Closed. The sealer shuffles with a sealed seed |
| A second round keeps the promising artifacts | Closed. Schema failure rejects the whole corpus |
| A public model already saw AIVD | Open. Prompt hygiene is not model hygiene. History stays `NOT_RECORDED` unless isolation is evidenced |
| The executor is told to vary inputs until a leak appears | Closed. The four pairs are fixed before discovery calls |
| Novelty is labeled a violation | Closed by the F3 rule, not by this corpus. No channel means not applicable |

No attack required a new security relation.

## Limits

Source-D is independent of the discovery engine. It is not independent of the decision to ask for a corpus. The provider chooses the programs. That choice can still shape what appears. Encryption does not remove that. A public model does not become a stranger by omitting the target from the prompt.

**SOURCE-D CORPUS NOT GENERATED. F3 IMPLEMENTATION NOT AUTHORIZED. F3 EXPERIMENT NOT AUTHORIZED.**
