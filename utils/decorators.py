"""DEPRECATED PARALLEL SUBSYSTEM (PR #14). Not imported by canonical AHOS.

Previously contained an eval-based Redis cache (insecure deserialization)
and import-time Redis connections. Neutralized: no eval call, no network, no
secrets. Canonical retry/rate-limit live in architecture/collector and PAL.
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, Optional


def retry(max_retries: int = 3, exceptions: tuple = (Exception,)):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep((attempt + 1) * 2)
            raise last_exception
        return wrapper
    return decorator


def cache(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """In-process memo only. Never eval(), never Redis, never pickle."""
    store: dict[str, tuple[float, Any]] = {}
    ttl_sec = float(ttl or 3600)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = (key_func(*args, **kwargs) if key_func
                   else f"{func.__module__}.{func.__name__}:{args!r}:{sorted(kwargs.items())!r}")
            now = time.monotonic()
            hit = store.get(key)
            if hit is not None and now - hit[0] < ttl_sec:
                return hit[1]
            result = func(*args, **kwargs)
            store[key] = (now, result)
            return result
        return wrapper
    return decorator


def timing(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        return func(*args, **kwargs)
    return wrapper


def rate_limited(max_per_second: int = 10):
    min_interval = 1.0 / max(1, int(max_per_second))

    def decorator(func: Callable) -> Callable:
        last_time = [0.0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            elapsed = time.perf_counter() - last_time[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_time[0] = time.perf_counter()
            return func(*args, **kwargs)
        return wrapper
    return decorator
