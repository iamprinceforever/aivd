"""Avatar store: returns a user's stored avatar file (text placeholder) from the avatars directory."""
import os


def handle(params: dict, ctx: dict) -> str:
    name = str(params.get("name", ""))
    name = name.lstrip("/")
    path = os.path.join(ctx["base_dir"], name)
    if not os.path.isfile(path):
        return "error: not found"
    with open(path) as fh:
        return fh.read()
