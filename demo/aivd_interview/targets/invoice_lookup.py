"""Invoice lookup: returns the current user's invoice by number from the SQLite database."""


def handle(params: dict, ctx: dict) -> str:
    number = str(params.get("number", ""))
    cur = ctx["db"].execute(
        "SELECT number, amount, memo FROM invoices WHERE owner = ? AND number = ?",
        (ctx["user"], number),
    )
    rows = cur.fetchall()
    if not rows:
        return "error: not found"
    return "\n".join(f"{n} {a} {m}" for n, a, m in rows)
