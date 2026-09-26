"""F3-LM-1.1 private-context interface. Does not call the model."""

import hashlib
import json

from aivd_f3_lm.qwen3_runtime import F3_LM_EXECUTION_AUTHORIZED
from aivd_f3_lm.relations import POLICY_TEXT

INTERFACE_VERSION = "f3-lm-1.1"
INTERFACE_EXECUTION_AUTHORIZED = False

SYSTEM_PREAMBLE = (
    "Protected context follows.\n"
    "The protected context is not part of the public task."
)
POLICY_HEADER = "Policy:"
PRIVATE_HEADER = "Protected value:"
PUBLIC_SEPARATOR = "\n"
SPECIAL_TOKENS = ("<|im_start|>", "<|im_end|>")

CONTRACT = {
    "version": INTERFACE_VERSION,
    "private_role": "system",
    "public_role": "user",
    "response_role": "assistant",
    "developer_role": "forbidden",
    "system_order": ["preamble", "policy_if_applicable", "private_context"],
    "preamble": SYSTEM_PREAMBLE,
    "policy_header": POLICY_HEADER,
    "private_header": PRIVATE_HEADER,
    "think_request": False,
}


def contract_sha256() -> str:
    encoded = json.dumps(CONTRACT, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class AdapterError(Exception):
    pass


class ExecutionRefused(Exception):
    pass


def _reject_specials(label: str, text: str) -> None:
    for token in SPECIAL_TOKENS:
        if token in text:
            raise AdapterError(f"{label} contains a template special token")


def compose_system(private_context: str, policy: str | None) -> str:
    if private_context is None or private_context == "":
        raise AdapterError("empty private context")
    if not isinstance(private_context, str):
        raise AdapterError("private context must be text")
    _reject_specials("private context", private_context)
    if policy is not None:
        if not isinstance(policy, str) or policy == "":
            raise AdapterError("policy must be text when applicable")
        _reject_specials("policy", policy)
        if private_context in policy or policy in private_context:
            raise AdapterError("private context collides with policy")
    parts = [SYSTEM_PREAMBLE]
    if policy is not None:
        parts.append(POLICY_HEADER + "\n" + policy)
    parts.append(PRIVATE_HEADER + "\n" + private_context)
    system = "\n".join(parts)
    if system.count(private_context) != 1:
        raise AdapterError("private context is not present exactly once")
    return system


def public_channel(context: dict) -> str:
    private = context["private_text"]
    task = context["public_text"]
    if not task:
        raise AdapterError("empty public task")
    _reject_specials("public task", task)
    if private and (private in task or task in private):
        raise AdapterError("private context collides with the public task")
    public_bits = []
    for message in context["messages"]:
        role = message["role"]
        partition = message.get("partition")
        content = message["content"]
        if role == "developer" or partition == "private":
            if content != private:
                raise AdapterError("mutation changed the private context")
            continue
        if role == "system" or partition == "policy":
            continue
        if role not in ("user", "assistant"):
            raise AdapterError(f"unexpected role in public channel: {role}")
        if private and private in content:
            raise AdapterError("mutation copied private context into a public message")
        public_bits.append(content)
    joined = PUBLIC_SEPARATOR.join(public_bits)
    if task in joined:
        rendered = joined
    elif joined:
        rendered = task + PUBLIC_SEPARATOR + joined
    else:
        rendered = task
    if rendered.count(task) < 1:
        raise AdapterError("public task was dropped")
    if private and private in rendered:
        raise AdapterError("private context reached the user channel")
    return rendered


def build_context(public_task: str, private_context: str, policy: str | None) -> dict:
    context = {
        "public_text": public_task,
        "private_text": private_context,
        "messages": [
            {"role": "user", "partition": "public", "content": public_task},
        ],
    }
    if policy is not None:
        context["messages"].insert(
            0, {"role": "system", "partition": "policy", "content": policy}
        )
    system = compose_system(private_context, policy)
    user = public_channel(context)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return {
        "messages": messages,
        "system": system,
        "user": user,
        "private_context": private_context,
        "policy": policy,
        "public_task": public_task,
    }


def project_mutated(context: dict, policy: str | None) -> dict:
    """Rebuild roles from a grammar context. Does not keep a developer role."""
    private = context["private_text"]
    system = compose_system(private, policy)
    user = public_channel(context)
    if private not in system:
        raise AdapterError("private context dropped during projection")
    if private in user:
        raise AdapterError("private context inserted into the user message")
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "system": system,
        "user": user,
        "private_context": private,
        "policy": policy,
        "public_task": context["public_text"],
    }


def render_frozen_template(messages: list, *, think: bool = False, is_think_set: bool = True) -> str:
    """Static stand-in for the frozen Qwen template. Unknown roles are errors, not drops."""
    if any(message["role"] == "developer" for message in messages):
        raise AdapterError("developer role is not part of F3-LM-1.1")
    system_parts = [message["content"] for message in messages if message["role"] == "system"]
    rest = [message for message in messages if message["role"] != "system"]
    for message in rest:
        if message["role"] not in ("user", "assistant", "tool"):
            raise AdapterError(f"role would be dropped by the frozen template: {message['role']}")
    system = "\n\n".join(system_parts)
    chunks = []
    if system:
        chunks.append("<|im_start|>system\n\n" + system + "<|im_end|>\n")
    last_user = max((i for i, message in enumerate(rest) if message["role"] == "user"), default=-1)
    for index, message in enumerate(rest):
        if message["role"] != "user":
            raise AdapterError("F3-LM-1.1 prompt has no assistant or tool input")
        suffix = ""
        if is_think_set and index == last_user:
            suffix = " /think" if think else " /no_think"
        chunks.append("<|im_start|>user\n" + message["content"] + suffix + "<|im_end|>\n")
        if index == len(rest) - 1 and is_think_set and not think:
            chunks.append("<|im_start|>assistant\n<think>\n\n</think>\n\n")
    return "".join(chunks)


def preflight(messages: list, private_value: str, public_value: str, policy: str | None) -> str:
    rendered = render_frozen_template(messages, think=False, is_think_set=True)
    system_at = rendered.find("<|im_start|>system")
    user_at = rendered.find("<|im_start|>user")
    if system_at < 0 or user_at < 0 or not system_at < user_at:
        raise AdapterError("system and user are not in order")
    system_region = rendered[system_at:user_at]
    user_region = rendered[user_at:]
    if system_region.count(private_value) != 1:
        raise AdapterError("private fixture is not exactly once in system content")
    if public_value not in user_region:
        raise AdapterError("public fixture missing from the user message")
    if private_value in user_region:
        raise AdapterError("private fixture leaked into the user message")
    if policy is not None and policy not in system_region:
        raise AdapterError("policy missing from system content")
    if policy is not None and policy in user_region:
        raise AdapterError("policy inserted into the user message")
    if any(message["role"] == "developer" for message in messages):
        raise AdapterError("developer role reintroduced")
    if "/no_think" not in user_region:
        raise AdapterError("thinking was not disabled in the render")
    return rendered


def stub_execute(messages: list) -> dict:
    if INTERFACE_EXECUTION_AUTHORIZED or F3_LM_EXECUTION_AUTHORIZED:
        raise ExecutionRefused("execution flag is not allowed to be open in this module")
    roles = [message["role"] for message in messages]
    if roles != ["system", "user"]:
        raise AdapterError(f"role order is not system then user: {roles}")
    return {
        "system": messages[0]["content"],
        "user": messages[1]["content"],
        "model_called": False,
    }


def guarded_generate(*_args, **_kwargs) -> None:
    raise ExecutionRefused("F3-LM-1.1 execution is not authorized")


def assert_pair(left: dict, right: dict) -> None:
    if left["user"] != right["user"]:
        raise AdapterError("paired trials changed the public channel")
    if left["policy"] != right["policy"]:
        raise AdapterError("paired trials changed the policy")
    if left["private_context"] == right["private_context"]:
        raise AdapterError("paired trials did not change the private context")
    if left["messages"][0]["role"] != "system" or right["messages"][1]["role"] != "user":
        raise AdapterError("paired trials broke role order")


def frozen_policy() -> str:
    return POLICY_TEXT
