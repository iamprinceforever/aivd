"""Exact model IDs for the POST-RC3 Groq evaluation. No substitution.

The third ID is the availability amendment recorded in
docs/post_rc3/GROQ_MODEL_GENERALIZATION_AMENDMENT.md.
llama-3.3-70b-versatile and moonshotai/kimi-k2-instruct-0905 are not used.
"""

MODELS = (
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
)

# Short filesystem-safe labels (one dir per model).
MODEL_DIRS = {
    "openai/gpt-oss-20b": "gpt_oss_20b",
    "openai/gpt-oss-120b": "gpt_oss_120b",
    "qwen/qwen3.8-27b": "qwen3_8_27b",
}

# GPT-OSS models accept provider-mandated reasoning parameters; Qwen does not.
GPT_OSS_MODELS = frozenset({"openai/gpt-oss-20b", "openai/gpt-oss-120b"})
