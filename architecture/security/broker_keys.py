"""M41 broker-key permission self-check. Mocked. No network. No secret read.

A key that can withdraw, is missing an IP lock, or lives outside broker/
fails closed. This module never opens the key file.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WITHDRAW_WORDS = frozenset({
    "withdraw", "withdrawal", "transfer", "send", "cashout",
})
ALLOWED = frozenset({"trade", "read"})


@dataclass(frozen=True, slots=True)
class KeyCheck:
    level: str
    allowed: bool
    reasons: tuple[str, ...]


def check_permissions(permissions: list[str] | tuple[str, ...], *, ip_locked: bool) -> KeyCheck:
    reasons: list[str] = []
    normalized = tuple(p.strip().lower() for p in permissions)
    if any(p in WITHDRAW_WORDS for p in normalized):
        reasons.append("withdraw permission is present")
    unknown = [p for p in normalized if p not in ALLOWED and p not in WITHDRAW_WORDS]
    if unknown:
        reasons.append("permission outside trade/read")
    if not ip_locked:
        reasons.append("ip lock missing")
    if not normalized:
        reasons.append("no permissions declared")
    if reasons:
        return KeyCheck("HALT", False, tuple(reasons))
    return KeyCheck("READ", True, ("trade and read only, ip locked",))


def location_allowed(path: Path, root: Path) -> bool:
    """True only for a file under <root>/broker/. Does not open the file."""
    root = Path(root).resolve()
    try:
        rel = Path(path).resolve().relative_to(root)
    except ValueError:
        return False
    if not rel.parts or rel.parts[0] != "broker":
        return False
    if path.name.lower().startswith(".env"):
        return False
    return True


def check_key(path: Path, root: Path, permissions: list[str] | tuple[str, ...], *, ip_locked: bool) -> KeyCheck:
    if not location_allowed(path, root):
        return KeyCheck("HALT", False, ("key is outside broker/",))
    return check_permissions(permissions, ip_locked=ip_locked)
