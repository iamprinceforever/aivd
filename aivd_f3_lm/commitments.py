"""Frozen identifiers for the pre-execution target. No model weights."""

DESIGN_COMMIT = "d36ebd5d53a5994ae31a87ac05eb37e0fd72a87a"
REPOSITORY = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
REVISION = "92f3b1597a195b523d8d9e5700e57e4fbb8f20d3"

# SHA-256 of canonical checkpoint manifest excluding hash fields.
MANIFEST_HASH = "8f17512f6ad5764b6a45ab5f7eac06c7507e523bbeafa81ecb935d7f64a2e285"
# SHA-256(revision || manifest_hash || WEIGHT_BYTES_NOT_LOCALLY_HASHED)
CHECKPOINT_COMMITMENT = "08be530165840f946a01f5981f4818542a090a7b889c050ab0ff85cd6c13b721"

LICENSE_SHA256 = "f95172ae8c823aebb14f73810fc71ce026e27555a17134d4720233caf8c2b2f0"
README_SHA256 = "19659e477d9e582b5cdd9a2bac1658d5e5e7a2722b2efdd4248c06398c87882f"
# Hub model-info API snapshot. Length equals declared chat_template.jinja size.
# Not a substitute for the gated file bytes.
CHAT_TEMPLATE_API_SHA256 = "fb76136a36a8422930f25fbe3326e9ae0d67e82259c7917b1b71d18ae6934cef"

# Tokenizer content hashes were not obtainable (gated + LFS oid redacted).
TOKENIZER_CONTENT_SHA256 = None

DTYPE = "bfloat16"
QUANTIZATION = "NONE"
PRECISION = "BF16"

# Independent byte verification of weight and tokenizer artifacts.
# None until every file's bytes have been hashed. Metadata commitment stays above.
BYTE_VERIFICATION_COMPLETE = False
BYTE_VERIFIED_COMMITMENT = None
TOKENIZER_BYTE_MANIFEST_HASH = None
