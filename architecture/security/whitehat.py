"""M80 defensive task allowlist. Exploit-shaped tasks are refused."""
from __future__ import annotations

ALLOWED = frozenset({"public_header_check", "license_check"})


def task(kind: str) -> str:
    if kind in ALLOWED:
        return "ALLOWED"
    return "REFUSED"
