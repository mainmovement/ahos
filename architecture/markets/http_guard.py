"""Keyless HTTP fetch: 8s timeout, one retry, then a circuit breaker. PAPER_ONLY."""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Any, Callable

TIMEOUT_S = 8.0
ATTEMPTS = 2
OPEN_AFTER = 3
OPEN_S = 15 * 60
UA = {"User-Agent": "Mozilla/5.0 (AHOS paper research)", "Accept": "application/json"}


class Breaker:
    def __init__(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def allow(self, now: float) -> bool:
        return now >= self.open_until

    def success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def failure(self, now: float) -> None:
        self.failures += 1
        if self.failures >= OPEN_AFTER:
            self.open_until = now + OPEN_S
            self.failures = 0


BREAKERS: dict[str, Breaker] = {}


def breaker(source: str) -> Breaker:
    return BREAKERS.setdefault(source, Breaker())


def reset_breakers() -> None:
    BREAKERS.clear()


def _default_open(req: urllib.request.Request, timeout: float) -> bytes:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str, *, source: str, method: str = "GET", payload: dict[str, Any] | None = None,
               opener: Callable[..., bytes] | None = None, timeout: float = TIMEOUT_S,
               now: float | None = None) -> dict[str, Any]:
    """One retry. Three failed calls open the breaker for 15 minutes."""
    moment = time.time() if now is None else now
    gate = breaker(source)
    if not gate.allow(moment):
        return {"ok": False, "reason": "circuit_open", "latency_ms": 0, "data": None}
    data_bytes = None if payload is None else json.dumps(payload).encode()
    headers = dict(UA)
    if data_bytes is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    open_fn = opener or _default_open
    started = time.perf_counter()
    last = "fetch_failed"
    for _ in range(ATTEMPTS):
        try:
            raw = open_fn(req, timeout)
            parsed = json.loads(raw.decode("utf-8", "replace"))
            gate.success()
            return {"ok": True, "reason": None, "latency_ms": int((time.perf_counter() - started) * 1000), "data": parsed}
        except Exception as exc:
            last = type(exc).__name__
    gate.failure(moment)
    return {"ok": False, "reason": last, "latency_ms": int((time.perf_counter() - started) * 1000), "data": None}
