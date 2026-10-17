"""M63 ops guard. Push, secret print, and clearing HOLD are refused."""
from __future__ import annotations

REFUSED = frozenset({"push", "print_env", "clear_hold", "delete"})


def ops_command(command: str) -> str:
    if command.strip().lower() in REFUSED:
        return "REFUSED"
    if command.strip().lower() == "local_status":
        return "ALLOWED"
    return "REFUSED"
