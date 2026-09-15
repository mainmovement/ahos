"""Shared immutable contracts for the Slice 2B control plane.

These are data contracts, not authentication, execution, or external-service
implementations.  All timestamps are timezone-aware UTC datetimes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


POLICY_VERSION = "slice-2b-v1"
DERIVE_AUTHORITY_AT_TCB = "DERIVE_AT_TCB"
NOT_APPLICABLE = "N/A"


def require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def require_id(value: str, prefix: str, field: str) -> None:
    namespace = prefix.rstrip(".-")
    if not value or not value.startswith((namespace + ".", namespace + "-")):
        raise ValueError(f"{field} must use namespace {namespace!r}")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class IdentityType(StrEnum):
    AGENT = "AGENT"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


class IdentityStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    BLOCKED = "BLOCKED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CommandStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    DENIED = "DENIED"
    FAILED = "FAILED"
    REPLAYED = "REPLAYED"


class CommandType(StrEnum):
    REGISTER_AGENT = "REGISTER_AGENT"
    REVOKE_AGENT = "REVOKE_AGENT"
    CREATE_TASK = "CREATE_TASK"
    TRANSITION_TASK = "TRANSITION_TASK"
    DELEGATE_AUTHORITY = "DELEGATE_AUTHORITY"
    REVOKE_GRANT = "REVOKE_GRANT"
    REGISTER_ARTIFACT = "REGISTER_ARTIFACT"
    TRANSITION_ARTIFACT = "TRANSITION_ARTIFACT"
    CREATE_CONTRADICTION = "CREATE_CONTRADICTION"
    CREATE_VERIFICATION = "CREATE_VERIFICATION"
    CREATE_APPROVAL = "CREATE_APPROVAL"
    REVOKE_APPROVAL = "REVOKE_APPROVAL"
    PROMOTE_KNOWLEDGE = "PROMOTE_KNOWLEDGE"
    UPDATE_POLICY = "UPDATE_POLICY"


class Operation(StrEnum):
    REGISTER = "REGISTER"
    CREATE = "CREATE"
    TRANSITION = "TRANSITION"
    DELEGATE = "DELEGATE"
    REVOKE = "REVOKE"
    VERIFY = "VERIFY"
    APPROVE = "APPROVE"
    PROMOTE = "PROMOTE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    UPDATE_POLICY = "UPDATE_POLICY"


class Capability(StrEnum):
    IDENTITY_MANAGE = "identity.manage"
    TASK_MANAGE = "task.manage"
    AUTHORITY_DELEGATE = "authority.delegate"
    EPISTEMIC_WRITE = "epistemic.write"
    EPISTEMIC_CHALLENGE = "epistemic.challenge"
    VERIFICATION_RECORD = "verification.record"
    APPROVAL_ISSUE = "approval.issue"
    KNOWLEDGE_PROMOTE = "knowledge.promote"
    PROJECTION_READ = "projection.read"
    EXECUTION = "execution"
    POLICY_MODIFY = "policy.modify"


class Resource(StrEnum):
    IDENTITY_STORE = "IDENTITY_STORE"
    TASK_STORE = "TASK_STORE"
    AUTHORITY_STORE = "AUTHORITY_STORE"
    EPISTEMIC_STORE = "EPISTEMIC_STORE"
    APPROVAL_STORE = "APPROVAL_STORE"
    AUDIT_LOG = "AUDIT_LOG"
    POLICY_STORE = "POLICY_STORE"
    EXTERNAL_EXECUTION = "EXTERNAL_EXECUTION"
    AHOS_REPOSITORY = "AHOS_REPOSITORY"
    AHOS_DATABASES = "AHOS_DATABASES"
    AHOS_LANE_A = "AHOS_LANE_A"
    AHOS_LANE_B = "AHOS_LANE_B"
    AHOS_RUNTIME = "AHOS_RUNTIME"
    AHOS_SOAK = "AHOS_SOAK"
    AHOS_CREDENTIALS = "AHOS_CREDENTIALS"
    AHOS_PRODUCTION = "AHOS_PRODUCTION"
    AHOS_LIVE_TRADING = "AHOS_LIVE_TRADING"


PROTECTED_RESOURCES = frozenset(
    {
        Resource.AHOS_REPOSITORY,
        Resource.AHOS_DATABASES,
        Resource.AHOS_LANE_A,
        Resource.AHOS_LANE_B,
        Resource.AHOS_RUNTIME,
        Resource.AHOS_SOAK,
        Resource.AHOS_CREDENTIALS,
        Resource.AHOS_PRODUCTION,
        Resource.AHOS_LIVE_TRADING,
        Resource.EXTERNAL_EXECUTION,
    }
)


class TaskState(StrEnum):
    PROPOSED = "PROPOSED"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


TASK_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.PROPOSED: frozenset(
        {TaskState.AUTHORIZED, TaskState.REJECTED, TaskState.CANCELLED}
    ),
    TaskState.AUTHORIZED: frozenset(
        {TaskState.RUNNING, TaskState.BLOCKED, TaskState.REJECTED, TaskState.CANCELLED}
    ),
    TaskState.RUNNING: frozenset(
        {TaskState.BLOCKED, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}
    ),
    TaskState.BLOCKED: frozenset(
        {TaskState.AUTHORIZED, TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELLED}
    ),
    TaskState.FAILED: frozenset(),
    TaskState.COMPLETED: frozenset(),
    TaskState.CANCELLED: frozenset(),
    TaskState.REJECTED: frozenset(),
}


@dataclass(frozen=True)
class Provenance:
    creator_principal_id: str
    session_id: str
    command_id: str
    method: str
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_id(self.creator_principal_id, "principal.", "creator_principal_id")
        if not self.session_id or not self.command_id or not self.method:
            raise ValueError("provenance session, command, and method are required")


@dataclass(frozen=True)
class GovernedTask:
    task_id: str
    owner_principal_id: str
    state: TaskState
    capability_scope: tuple[Capability, ...]
    resource_scope: tuple[Resource, ...]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    parent_task_id: str | None = None

    def __post_init__(self) -> None:
        require_id(self.task_id, "task.", "task_id")
        require_id(self.owner_principal_id, "principal.", "owner_principal_id")
        require_utc(self.created_at, "created_at")
        require_utc(self.updated_at, "updated_at")
        if self.version < 1:
            raise ValueError("task version must be positive")
        if not self.capability_scope or not self.resource_scope:
            raise ValueError("empty task scope is deny and cannot create a governed task")
        if len(set(self.capability_scope)) != len(self.capability_scope):
            raise ValueError("duplicate task capability")
        if len(set(self.resource_scope)) != len(self.resource_scope):
            raise ValueError("duplicate task resource")


@dataclass(frozen=True)
class CommandResult:
    command_id: str
    status: CommandStatus
    decision: Decision
    reason: str
    event_id: str | None
    resulting_version: int | None

    @property
    def accepted(self) -> bool:
        return self.status is CommandStatus.ACCEPTED and self.decision is Decision.ALLOW


JsonPrimitive = str | int | float | bool | None
ImmutablePayloadValue = JsonPrimitive | tuple[Any, ...]
