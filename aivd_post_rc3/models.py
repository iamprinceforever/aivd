"""Exact model IDs for the POST-RC3 Groq evaluation. No substitution."""

MODELS = (
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
)

# Short filesystem-safe labels (one dir per model).
MODEL_DIRS = {
    "openai/gpt-oss-20b": "gpt_oss_20b",
    "openai/gpt-oss-120b": "gpt_oss_120b",
    "llama-3.3-70b-versatile": "llama_3_3_70b",
}

# GPT-OSS models accept provider-mandated reasoning parameters; llama-3.3 does not.
GPT_OSS_MODELS = frozenset({"openai/gpt-oss-20b", "openai/gpt-oss-120b"})
