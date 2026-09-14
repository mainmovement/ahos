"""Shared enumerations and value objects for Slice 1."""

from __future__ import annotations

from enum import IntEnum, StrEnum


class MaturityLevel(IntEnum):
    REGISTERED = 0
    DESIGNED = 1
    IMPLEMENTED = 2
    TESTED = 3
    VERIFIED = 4
    OPERATIONALLY_TRUSTED = 5


class GovernanceStatus(StrEnum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class TaskState(StrEnum):
    PROPOSED = "PROPOSED"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class AuthzDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    BLOCKED = "BLOCKED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventType(StrEnum):
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_UPDATED = "AGENT_UPDATED"
    TASK_CREATED = "TASK_CREATED"
    TASK_TRANSITION = "TASK_TRANSITION"
    AUTHZ_DECISION = "AUTHZ_DECISION"
    RESOURCE_REGISTERED = "RESOURCE_REGISTERED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"


TERMINAL_TASK_STATES = frozenset(
    {
        TaskState.FAILED,
        TaskState.COMPLETED,
        TaskState.CANCELLED,
        TaskState.REJECTED,
    }
)

LEGAL_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.PROPOSED: frozenset(
        {TaskState.AUTHORIZED, TaskState.REJECTED, TaskState.CANCELLED}
    ),
    TaskState.AUTHORIZED: frozenset(
        {
            TaskState.RUNNING,
            TaskState.CANCELLED,
            TaskState.REJECTED,
            TaskState.BLOCKED,
        }
    ),
    TaskState.RUNNING: frozenset(
        {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.BLOCKED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.BLOCKED: frozenset(
        {
            TaskState.AUTHORIZED,
            TaskState.RUNNING,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.FAILED: frozenset(),
    TaskState.COMPLETED: frozenset(),
    TaskState.CANCELLED: frozenset(),
    TaskState.REJECTED: frozenset(),
}

EXECUTABLE_TASK_STATES = frozenset({TaskState.AUTHORIZED, TaskState.RUNNING})
