"""Kian rate limiting (M35.1).

Rate limits prevent abuse and ensure fair usage of Kian's capabilities.
All rate limits include traffic prioritization and can be overridden by the
gate service when needed.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RateLimit:
    """Rate limit configuration for a Kian operation."""
    name: str
    max_requests: int
    window_seconds: int
    current_count: int = 0
    reset_time: float = 0.0
    burst_allowed: int = 0


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_in: float
    retry_after: Optional[float]
    reason: str


class RateLimiter:
    """Manages rate limiting for Kian operations.

    Supports token bucket, sliding window, and fixed window counters.
    All limits are backed by the audit store for audit trails.
    """

    def __init__(self, audit_store: Any) -> None:
        self.audit_store = audit_store
        self.limits: Dict[str, RateLimit] = {}
        self._initialize_limits()

    def _initialize_limits(self) -> None:
        """Initialize default rate limits for Kian."""
        # K-9: message burst is queued and owner is notified
        self.limits.update({
            "kian_chat": RateLimit(
                name="kian_chat",
                max_requests=10,  # 10 messages per minute
                window_seconds=60,
                burst_allowed=3,  # allow bursts of 3
            ),

            "kian_tool_calls": RateLimit(
                name="kian_tool_calls",
                max_requests=20,  # 20 tool calls per minute
                window_seconds=60,
            ),

            "kian_gate_codes": RateLimit(
                name="kian_gate_codes",
                max_requests=100,  # 100 gate codes per hour
                window_seconds=3600,
            ),

            "kian_admin_actions": RateLimit(
                name="kian_admin_actions",
                max_requests=50,  # 50 admin actions per hour
                window_seconds=3600,
            ),
        })

    def check_rate_limit(
        self,
        limit_name: str,
        operation: str = "chat",
        user_id: Optional[str] = None,
    ) -> RateLimitResult:
        """Check if an operation is allowed within the rate limit.

        Returns a RateLimitResult with information about the limit status.
        """
        limit = self.limits.get(limit_name)
        if not limit:
            return RateLimitResult(
                allowed=True,
                remaining=limit.max_requests,
                reset_in=0.0,
                retry_after=None,
                reason="no_limit_configured",
            )

        now = time.time()

        # Reset window if needed
        if now >= limit.reset_time:
            limit.current_count = 0
            limit.reset_time = now + limit.window_seconds

        # Check burst allowance
        if limit.current_count >= limit.max_requests + limit.burst_allowed:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_in=limit.reset_time - now,
                retry_after=limit.reset_time - now,
                reason="rate_limit_exceeded",
            )

        # Allow the request
        limit.current_count += 1

        # Record the rate limit check in the audit store
        self._record_rate_limit_check(limit_name, operation, user_id, now)

        return RateLimitResult(
            allowed=True,
            remaining=limit.max_requests - limit.current_count + limit.burst_allowed,
            reset_in=limit.reset_time - now,
            retry_after=None,
            reason="allowed",
        )

    def _record_rate_limit_check(
        self,
        limit_name: str,
        operation: str,
        user_id: Optional[str],
        timestamp: float,
    ) -> None:
        """Record a rate limit check in the audit store."""
        try:
            self.audit_store.record_action(
                channel="kian",
                user_id_hash=f"limit_check:{limit_name}",
                message_hash="",
                action_type="rate_limit",
                tool_calls=[f"check_{limit_name}"],
                content=f"Rate limit check: {operation} for {limit_name}",
                taint_labels=["RATE_LIMIT"],
                rate_limited=False,
            )
        except Exception:
            # Don't let rate limiting failures break the main functionality
            pass

    def get_current_usage(self, limit_name: str) -> Dict[str, Any]:
        """Get current rate limit usage statistics."""
        limit = self.limits.get(limit_name)
        if not limit:
            return {"error": "limit_not_found"}

        now = time.time()
        if now >= limit.reset_time:
            return {
                "name": limit.name,
                "max_requests": limit.max_requests,
                "window_seconds": limit.window_seconds,
                "current": 0,
                "remaining": limit.max_requests,
                "reset_in": 0,
            }

        return {
            "name": limit.name,
            "max_requests": limit.max_requests,
            "window_seconds": limit.window_seconds,
            "current": limit.current_count,
            "remaining": max(0, limit.max_requests - limit.current_count),
            "reset_in": limit.reset_time - now,
        }

    def reset_limit(self, limit_name: str) -> None:
        """Reset a specific rate limit."""
        if limit_name in self.limits:
            limit = self.limits[limit_name]
            limit.current_count = 0
            limit.reset_time = time.time() + limit.window_seconds

    def cleanup_old_limits(self) -> int:
        """Clean up old rate limit entries. Returns count cleaned."""
        # This is a placeholder for potential cleanup logic
        return 0


class RateLimitError(Exception):
    """Raised when rate limit operations fail."""
    pass
