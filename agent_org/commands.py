"""Immutable typed command envelopes accepted by the TCB."""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from datetime import datetime
from enum import StrEnum

from agent_org.authority import CapabilityGrant
from agent_org.contracts import (
    Capability,
    CommandType,
    DERIVE_AUTHORITY_AT_TCB,
    GovernedTask,
    Operation,
    Resource,
    require_id,
    require_utc,
)
from agent_org.epistemic import (
    Approval,
    Artifact,
    ContradictionCase,
    VerificationRecord,
)
from agent_org.identity import AgentIdentity


@dataclass(frozen=True, slots=True)
class RegisterAgentPayload:
    identity: AgentIdentity


@dataclass(frozen=True, slots=True)
class RevokeAgentPayload:
    principal_id: str


@dataclass(frozen=True, slots=True)
class CreateTaskPayload:
    task: GovernedTask


@dataclass(frozen=True, slots=True)
class TransitionTaskPayload:
    task_id: str
    target_state: str


@dataclass(frozen=True, slots=True)
class DelegateAuthorityPayload:
    grant: CapabilityGrant


@dataclass(frozen=True, slots=True)
class RevokeGrantPayload:
    grant_id: str


@dataclass(frozen=True, slots=True)
class RegisterArtifactPayload:
    artifact: Artifact


@dataclass(frozen=True, slots=True)
class TransitionArtifactPayload:
    artifact_id: str
    target_state: StrEnum
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateContradictionPayload:
    contradiction: ContradictionCase


@dataclass(frozen=True, slots=True)
class CreateVerificationPayload:
    verification: VerificationRecord


@dataclass(frozen=True, slots=True)
class CreateApprovalPayload:
    approval: Approval


@dataclass(frozen=True, slots=True)
class RevokeApprovalPayload:
    approval_id: str


@dataclass(frozen=True, slots=True)
class PromoteKnowledgePayload:
    candidate_id: str
    approval_id: str


@dataclass(frozen=True, slots=True)
class UpdatePolicyPayload:
    proposed_policy_version: str


CommandPayload = (
    RegisterAgentPayload
    | RevokeAgentPayload
    | CreateTaskPayload
    | TransitionTaskPayload
    | DelegateAuthorityPayload
    | RevokeGrantPayload
    | RegisterArtifactPayload
    | TransitionArtifactPayload
    | CreateContradictionPayload
    | CreateVerificationPayload
    | CreateApprovalPayload
    | RevokeApprovalPayload
    | PromoteKnowledgePayload
    | UpdatePolicyPayload
)


PAYLOAD_TYPES: dict[CommandType, type[object]] = {
    CommandType.REGISTER_AGENT: RegisterAgentPayload,
    CommandType.REVOKE_AGENT: RevokeAgentPayload,
    CommandType.CREATE_TASK: CreateTaskPayload,
    CommandType.TRANSITION_TASK: TransitionTaskPayload,
    CommandType.DELEGATE_AUTHORITY: DelegateAuthorityPayload,
    CommandType.REVOKE_GRANT: RevokeGrantPayload,
    CommandType.REGISTER_ARTIFACT: RegisterArtifactPayload,
    CommandType.TRANSITION_ARTIFACT: TransitionArtifactPayload,
    CommandType.CREATE_CONTRADICTION: CreateContradictionPayload,
    CommandType.CREATE_VERIFICATION: CreateVerificationPayload,
    CommandType.CREATE_APPROVAL: CreateApprovalPayload,
    CommandType.REVOKE_APPROVAL: RevokeApprovalPayload,
    CommandType.PROMOTE_KNOWLEDGE: PromoteKnowledgePayload,
    CommandType.UPDATE_POLICY: UpdatePolicyPayload,
}


@dataclass(frozen=True, slots=True)
class CommandEnvelope:
    command_id: str
    command_type: CommandType
    actor_principal_id: str
    session_id: str
    authority_context_ref: str
    task_scope: str | None
    resource_scope: Resource
    capability_scope: Capability
    requested_operation: Operation
    policy_version: str
    causation_id: str | None
    correlation_id: str
    parent_command_id: str | None
    evidence_lineage: tuple[str, ...]
    expected_state_version: int
    payload: CommandPayload
    issued_at: datetime

    def __post_init__(self) -> None:
        require_id(self.command_id, "command.", "command_id")
        require_id(self.actor_principal_id, "principal.", "actor_principal_id")
        require_id(self.session_id, "session.", "session_id")
        require_id(self.correlation_id, "correlation.", "correlation_id")
        if self.task_scope is not None:
            require_id(self.task_scope, "task.", "task_scope")
        if self.parent_command_id is not None:
            require_id(self.parent_command_id, "command.", "parent_command_id")
        if self.causation_id is not None and not self.causation_id:
            raise ValueError("causation_id cannot be empty")
        if self.authority_context_ref != DERIVE_AUTHORITY_AT_TCB:
            raise ValueError("caller-supplied authority context is forbidden")
        if not self.policy_version:
            raise ValueError("policy_version is required")
        if self.expected_state_version < 0:
            raise ValueError("expected_state_version cannot be negative")
        require_utc(self.issued_at, "issued_at")
        expected = PAYLOAD_TYPES.get(self.command_type)
        if expected is None or not isinstance(self.payload, expected):
            raise ValueError(
                f"{self.command_type} requires payload {getattr(expected, '__name__', None)}"
            )
        if not is_dataclass(self.payload):
            raise ValueError("command payload must be an immutable typed dataclass")
        params = getattr(type(self.payload), "__dataclass_params__", None)
        if params is None or not params.frozen:
            raise ValueError("command payload must be frozen")
        if len(set(self.evidence_lineage)) != len(self.evidence_lineage):
            raise ValueError("duplicate evidence lineage")
