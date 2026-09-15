"""Research-host contracts. These are not human identity and not authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from agent_org.contracts import Capability, Resource, require_id, require_utc


SAME_PROCESS_RUNTIME = "NON_PRODUCTION"
API_BOUNDARY = "ENFORCED"
PROCESS_ISOLATION_PROVIDED = False
SAME_PROCESS_RESIDUAL = True

RESEARCH_CONTEXT_KIND = "RESEARCH_AGENT_CONTEXT"
RESEARCH_PRINCIPAL_ID = "principal.research-agent-context"
RESEARCH_PRINCIPAL_ROLE = "bounded-research-cognitive-context"


class OperationClass(StrEnum):
    READ = "READ"
    RESEARCH_WRITE = "RESEARCH_WRITE"
    GOVERNANCE = "GOVERNANCE"
    EXECUTION = "EXECUTION"


class HostDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


SANDBOX_OPERATION_CLASSES: frozenset[OperationClass] = frozenset(
    {OperationClass.READ, OperationClass.RESEARCH_WRITE}
)

FORBIDDEN_RESEARCH_CAPABILITIES: frozenset[Capability] = frozenset(
    {
        Capability.IDENTITY_MANAGE,
        Capability.APPROVAL_ISSUE,
        Capability.KNOWLEDGE_PROMOTE,
        Capability.AUTHORITY_DELEGATE,
        Capability.EXECUTION,
        Capability.POLICY_MODIFY,
        Capability.VERIFICATION_RECORD,
        Capability.TASK_MANAGE,
    }
)

ALLOWED_RESEARCH_CAPABILITIES: frozenset[Capability] = frozenset(
    {
        Capability.EPISTEMIC_WRITE,
        Capability.EPISTEMIC_CHALLENGE,
        Capability.PROJECTION_READ,
    }
)

ALLOWED_MISSION_INTENT_RESOURCES: frozenset[Resource] = frozenset(
    {Resource.EPISTEMIC_STORE}
)

NETWORK_LOCATOR_PREFIXES: tuple[str, ...] = (
    "http://",
    "https://",
    "ftp://",
    "ws://",
    "wss://",
)


@dataclass(frozen=True)
class ResearchAgentContext:
    """Host-supplied cognitive attribution. Not a session and not a human."""

    context_id: str
    principal_id: str
    kind: str = RESEARCH_CONTEXT_KIND
    display_name: str = (
        "RESEARCH_AGENT_CONTEXT (not human identity, not production authority)"
    )
    issues_sessions: bool = False
    production_authority: bool = False

    def __post_init__(self) -> None:
        require_id(self.context_id, "research-context.", "context_id")
        require_id(self.principal_id, "principal.", "principal_id")
        if self.kind != RESEARCH_CONTEXT_KIND:
            raise ValueError("research context kind is fixed")
        if self.issues_sessions or self.production_authority:
            raise ValueError("research context cannot issue sessions or authority")


@dataclass(frozen=True)
class HostResult:
    decision: HostDecision
    classification: OperationClass
    operation: str
    reason: str
    resource: str
    command_id: str | None = None
    correlation_id: str | None = None
    artifact_id: str | None = None
    payload: Any = None

    @property
    def accepted(self) -> bool:
        return self.decision is HostDecision.ALLOW


@dataclass(frozen=True)
class HostAuditRecord:
    research_agent_context: str
    operation: str
    resource: str
    command: str
    result: str
    timestamp: datetime
    correlation_id: str
    reason: str
    classification: str

    def __post_init__(self) -> None:
        require_utc(self.timestamp, "timestamp")
        if not self.research_agent_context or not self.operation:
            raise ValueError("host audit requires research context and operation")


@dataclass(frozen=True)
class RuntimeClassification:
    api_boundary: str
    process_isolation: bool
    same_process_runtime: str
    same_process_residual: bool
    agent_one_implemented: bool
    network_provided: bool
    ahos_connected: bool


def deny(
    operation: str,
    classification: OperationClass,
    reason: str,
    *,
    resource: str = "N/A",
    correlation_id: str | None = None,
) -> HostResult:
    return HostResult(
        decision=HostDecision.DENY,
        classification=classification,
        operation=operation,
        reason=reason,
        resource=resource,
        correlation_id=correlation_id,
    )


def allow(
    operation: str,
    classification: OperationClass,
    reason: str,
    *,
    resource: str,
    command_id: str | None = None,
    correlation_id: str | None = None,
    artifact_id: str | None = None,
    payload: Any = None,
) -> HostResult:
    return HostResult(
        decision=HostDecision.ALLOW,
        classification=classification,
        operation=operation,
        reason=reason,
        resource=resource,
        command_id=command_id,
        correlation_id=correlation_id,
        artifact_id=artifact_id,
        payload=payload,
    )
