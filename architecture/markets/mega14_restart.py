"""Restart gate. Before the soak deadline this module does not stop a process."""
from __future__ import annotations

from datetime import datetime, timezone

DEADLINE = datetime(2026, 11, 1, 0, 45, 31, tzinfo=timezone.utc)
MIN_FREE_MB = 2048
# The listener stays up. Only the soak and the paper trader are restart targets.
SOAK_MARK = "m13_gold_soak.py"
TRADER_MARK = "paper_trader_cycle.py"
LISTENER_MARK = "run_bot.py"


def due(now: datetime) -> str:
    moment = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
    if moment.astimezone(timezone.utc) < DEADLINE:
        return "WAIT"
    return "DUE"


def is_restart_target(command: str) -> bool:
    text = command or ""
    if LISTENER_MARK in text:
        return False
    return SOAK_MARK in text or TRADER_MARK in text
