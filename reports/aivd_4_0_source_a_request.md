# AIVD 4.0 Source-A request

Status: issued, unfilled. This repository is not the provider. No corpus is attached. No candidate was generated, selected, or inspected.

The text below is the request a separated provider would receive. It is frozen at experimenter commit `473f6f092e5af4ed3be65e1ff984d29e50d3aee0`.

---

AIVD 4.0
SOURCE-A INDEPENDENT SEALED CORPUS REQUEST

Purpose

We are conducting a pre-registered experiment on autonomous behavioral discovery.

The experiment requires a corpus of programs that existed independently of the experiment and were NOT selected, filtered, constructed, or modified for this study.

The experimenter must not be able to inspect the programs before the behavioral-discovery experiment is complete.

IMPORTANT:

You are NOT being asked to:

- find a vulnerability
- find novel behavior
- avoid a vulnerability
- reproduce a known target
- generate a particular behavioral pattern
- search for a particular operator
- optimize for the experiment

The corpus must be target-neutral.

SOURCE-A REQUIREMENT

The preferred corpus consists of programs that already existed before this experiment and were not created specifically for it.

Examples may include:

- independently developed programs
- previously existing research artifacts
- previously existing program corpora
- previously existing transformations
- previously existing compositions

The corpus must not be selected because the provider expects certain behaviors to appear.

Do not filter candidates based on:

- novelty
- security relevance
- vulnerability
- expected behavioral signature
- similarity to historical AIVD examples

WHAT MUST NOT BE PROVIDED BEFORE THE EXPERIMENT

Do NOT provide the experimenter with:

- plaintext programs
- program keys
- plaintext filenames revealing behavior
- plaintext signatures
- expected behavioral relations
- target labels
- candidate descriptions
- operator summaries
- behavioral classifications

The experimenter may receive only:

- corpus commitment
- opaque candidate handles
- protocol metadata
- receipt information

CORPUS SIZE

The requested corpus size is provider-selected, but fixed before commitment.

The provider must NOT add or remove candidates after commitment.

The final order must be frozen before the experiment begins.

CORPUS ORDER

Candidates must have a deterministic committed order.

The provider must commit:

- candidate count
- candidate ordering
- encrypted candidate contents

before the experimenter can inspect them.

PROVENANCE

For every candidate, the provider should retain privately:

- original source
- acquisition date
- original creation date if available
- original artifact identifier
- original program bytes
- provenance information

This metadata remains sealed.

The evaluator may inspect it after the experiment.

The experimenter must not receive it before discovery.

TARGET NEUTRALITY

The provider must not be asked to:

- find doubled-odd
- avoid doubled-odd
- find an AIVD target
- avoid AIVD targets
- search for security vulnerabilities
- search for behavioral novelty

The provider should simply supply eligible existing programs.

The provider's statement that the corpus was target-neutral is accepted as a procedural declaration, not as mathematical proof of intent.

CRYPTOGRAPHIC SEAL

A simple body hash is insufficient.

A signature hash is insufficient.

The micro-language is sufficiently small that hashes may be searchable or enumerable.

The commitment must therefore bind encrypted corpus contents.

The provider should produce:

- encrypted corpus
- corpus commitment
- immutable manifest
- opaque candidate handles

The content identifier remains inside the encrypted package.

OPAQUE HANDLES

Each candidate receives an opaque handle.

Example:

- SRC-A-000001
- SRC-A-000002
- SRC-A-000003

The handle must NOT encode:

- operator
- family
- body key
- behavior
- provenance
- expected result

The experimenter may see the handle.

The experimenter must not be able to derive the plaintext candidate from the handle.

SEALED MANIFEST

The sealed manifest should contain privately:

- opaque_handle
- encrypted_candidate
- content_id
- original provenance
- ordering index

The experimenter receives only:

- opaque_handle
- ordering index
- commitment

COMMITMENT RECEIPT

Before the experimenter can access any candidate, the provider must provide a receipt containing:

- corpus commitment
- candidate count
- ordering commitment
- protocol version
- bank hash
- timestamp
- provider identifier

The receipt does NOT contain:

- plaintext body
- body key
- signature
- content id

IMPORTANT EXECUTION REQUIREMENT

The experimenter must not operate an environment where they can simply decrypt the corpus and inspect stdout/logs.

The measurement environment must be isolated so that:

- the discovery engine can access plaintext
- the experimenter cannot observe plaintext

The discovery process should emit only permitted opaque results.

REVEAL

The evaluator retains the sealed reference.

The evaluator opens the corpus only after:

- the discovery receipt is finalized
- the discovery state is immutable
- the behavioral experiment is complete

The evaluator may then compare:

- original candidate
- provenance
- behavioral signature
- discovery result
- dimension assignment

The evaluator must not modify discovery results.

PROVIDER DECLARATION

The provider should sign a statement equivalent to:

"The submitted corpus consists of artifacts that existed independently of the AIVD 4.0 study and were not selected, constructed, modified, or filtered for the purpose of producing a desired result in this experiment."

The provider should NOT make claims about what behaviors the corpus contains.

FAILURE CONDITIONS

The corpus becomes ineligible if:

- candidates are added after commitment
- candidates are removed after commitment
- order changes after commitment
- candidates are selected for the AIVD target
- the experimenter receives plaintext before discovery
- candidate keys are exposed
- behavioral labels are exposed
- expected outputs are exposed
- the provider modifies candidates after commitment
- the evaluator sends labels back into discovery

FINAL PRINCIPLE

We are not asking you to manufacture an unknown behavior.

We are asking you to provide independently existing artifacts that the experimenter has not previously inspected.

The scientific value comes from the fact that the behavioral relationship is unknown to the experimenter when discovery begins.
