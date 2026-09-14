"""ID factories. Production uses UUID4; tests inject a sequential factory."""

from __future__ import annotations

import uuid
from typing import Protocol


class IdFactory(Protocol):
    def new(self, prefix: str) -> str:
        ...


class UuidFactory:
    def new(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"


class SequentialIdFactory:
    def __init__(self) -> None:
        self._n = 0

    def new(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}-{self._n:04d}"
