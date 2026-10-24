"""Report viewer: returns the text of a report stored under the service's reports directory."""
from pathlib import Path


def handle(params: dict, ctx: dict) -> str:
    name = str(params.get("name", ""))
    base = Path(ctx["base_dir"]).resolve()
    target = (base / name).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return "error: invalid report name"
    if not target.is_file():
        return "error: not found"
    return target.read_text()
