"""Decide whether a gold soak has stalled. A healthy window is not restarted.

A restart, when one is actually required, must use the same command and the
existing window start. This module does not kill a process by itself.
OP-3, a start after a real reboot, is not proven here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _age_seconds(stamp: str | None, now: datetime) -> float | None:
    if not isinstance(stamp, str):
        return None
    try:
        moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - moment).total_seconds()


def stall_decision(status: dict[str, Any], now: datetime, interval_sec: float) -> dict[str, Any]:
    last = status.get("last_cycle") if isinstance(status.get("last_cycle"), dict) else {}
    age = _age_seconds(last.get("ts") if isinstance(last, dict) else None, now)
    window = status.get("window_started_utc")
    if age is None:
        action = "NO_RESTART_NO_CYCLE"
    elif age > float(interval_sec) * 3:
        action = "RESTART_KEEP_WINDOW"
    else:
        action = "HOLD"
    return {
        "action": action,
        "window_started_utc": window,
        "age_s": None if age is None else round(age, 1),
        "reboot_proven": False,
        "paper_only": True,
    }
