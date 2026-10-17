"""M35.5 command inbox. Trade and withdraw wait for a human. They do not run."""
from __future__ import annotations

from dataclasses import dataclass

HUMAN = frozenset({"trade", "withdraw", "promote", "live", "clear_hold"})


@dataclass(frozen=True, slots=True)
class InboxItem:
    command: str
    state: str
    executed: bool


def route_command(command: str) -> InboxItem:
    name = command.strip().lower()
    if name in HUMAN:
        return InboxItem(name, "WAITING_FOR_OWNER", False)
    if name == "status":
        return InboxItem(name, "ANSWERED_PAPER", False)
    return InboxItem(name, "REFUSED", False)
