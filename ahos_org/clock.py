"""Injectable clocks so audit timestamps can be deterministic in tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


class Clock(Protocol):
    def now(self) -> datetime:
        ...


class SystemClock:
    def now(self) -> datetime:
        return utc_now()


class FrozenClock:
    def __init__(self, instant: datetime | None = None) -> None:
        if instant is None:
            instant = datetime(2026, 9, 14, 1, 0, 0, tzinfo=timezone.utc)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        self._instant = instant.astimezone(timezone.utc).replace(microsecond=0)

    def now(self) -> datetime:
        return self._instant

    def advance(self, seconds: int) -> None:
        self._instant = self._instant + timedelta(seconds=seconds)
