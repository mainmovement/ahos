#!/usr/bin/env python3
"""AHOS Network Retry Policy with Exponential Backoff (Phase XX)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Any, Type


@dataclass
class RetryPolicy:
    max_retries: int = 3
    initial_delay_sec: float = 0.5
    backoff_multiplier: float = 2.0
    max_delay_sec: float = 5.0
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,)

    def execute(self, fn: Callable[[], Any], sleep_fn: Callable[[float], None] = time.sleep) -> Any:
        delay = self.initial_delay_sec
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                sleep_fn(delay)
                delay = min(self.max_delay_sec, delay * self.backoff_multiplier)

        if last_exception:
            raise last_exception
        raise RuntimeError("Retry policy failed without explicit exception")
