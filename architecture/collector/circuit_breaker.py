#!/usr/bin/env python3
"""AHOS Provider Circuit Breaker (Phase XX).

States:
  - CLOSED: Normal operation. Requests flow through.
  - OPEN: Provider experiencing repeated failures. Requests fail fast without hitting API.
  - HALF_OPEN: Trial period. A single request is attempted to test recovery.
"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass


class CircuitState(enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    recovery_timeout_sec: float = 30.0
    half_open_max_trials: int = 1


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_ts = 0.0
        self.last_state_change_ts = time.time()
        self.trial_count = 0

    def allow_request(self, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if ts - self.last_failure_ts >= self.config.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                self.trial_count = 0
                self.last_state_change_ts = ts
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return self.trial_count < self.config.half_open_max_trials
        return False

    def record_success(self, now: float | None = None):
        ts = time.time() if now is None else now
        if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.trial_count = 0
            self.last_state_change_ts = ts
        else:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self, now: float | None = None):
        ts = time.time() if now is None else now
        self.failure_count += 1
        self.last_failure_ts = ts
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change_ts = ts
            self.trial_count = 0
