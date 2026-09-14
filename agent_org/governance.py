"""Pure fail-closed policy checks used by the Trusted Command Boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from agent_org.commands import CommandEnvelope
from agent_org.contracts import (
    Capability,
    CommandType,
    Decision,
    IdentityStatus,
    Operation,
    POLICY_VERSION,
    PROTECTED_RESOURCES,
    Resource,
    TaskState,
)
from agent_org.identity import Session
from agent_org.stores import _GovernedState


COMMAND_MAX_AGE = timedelta(minutes=5)


@dataclass(frozen=True)
class CommandPolicy:
    capability: Capability
    operation: Operation
    resource: Resource
    task_required: bool


COMMAND_POLICIES: dict[CommandType, CommandPolicy] = {
    CommandType.REGISTER_AGENT: CommandPolicy(
        Capability.IDENTITY_MANAGE, Operation.REGISTER, Resource.IDENTITY_STORE, False
    ),
    CommandType.CREATE_TASK: CommandPolicy(
        Capability.TASK_MANAGE, Operation.CREATE, Resource.TASK_STORE, False
    ),
    CommandType.TRANSITION_TASK: CommandPolicy(
        Capability.TASK_MANAGE, Operation.TRANSITION, Resource.TASK_STORE, True
    ),
    CommandType.DELEGATE_AUTHORITY: CommandPolicy(
        Capability.AUTHORITY_DELEGATE,
        Operation.DELEGATE,
        Resource.AUTHORITY_STORE,
        False,
    ),
    CommandType.REVOKE_GRANT: CommandPolicy(
        Capability.AUTHORITY_DELEGATE,
        Operation.REVOKE,
        Resource.AUTHORITY_STORE,
        False,
    ),
    CommandType.REGISTER_ARTIFACT: CommandPolicy(
        Capability.EPISTEMIC_WRITE, Operation.CREATE, Resource.EPISTEMIC_STORE, True
    ),
    CommandType.TRANSITION_ARTIFACT: CommandPolicy(
        Capability.EPISTEMIC_WRITE,
        Operation.TRANSITION,
        Resource.EPISTEMIC_STORE,
        True,
    ),
    CommandType.CREATE_CONTRADICTION: CommandPolicy(
        Capability.EPISTEMIC_CHALLENGE,
        Operation.CREATE,
        Resource.EPISTEMIC_STORE,
        True,
    ),
    CommandType.CREATE_VERIFICATION: CommandPolicy(
        Capability.VERIFICATION_RECORD,
        Operation.VERIFY,
        Resource.EPISTEMIC_STORE,
        True,
    ),
    CommandType.CREATE_APPROVAL: CommandPolicy(
        Capability.APPROVAL_ISSUE,
        Operation.APPROVE,
        Resource.APPROVAL_STORE,
        True,
    ),
    CommandType.REVOKE_APPROVAL: CommandPolicy(
        Capability.APPROVAL_ISSUE,
        Operation.REVOKE,
        Resource.APPROVAL_STORE,
        True,
    ),
    CommandType.PROMOTE_KNOWLEDGE: CommandPolicy(
        Capability.KNOWLEDGE_PROMOTE,
        Operation.PROMOTE,
        Resource.EPISTEMIC_STORE,
        True,
    ),
    CommandType.UPDATE_POLICY: CommandPolicy(
        Capability.POLICY_MODIFY,
        Operation.UPDATE_POLICY,
        Resource.POLICY_STORE,
        False,
    ),
}


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str


def evaluate_command_policy(
    command: CommandEnvelope,
    *,
    session: Session,
    state: _GovernedState,
    now: datetime,
) -> PolicyDecision:
    """Validate fixed command semantics before authority derivation."""
    if command.policy_version != state.policy_version or state.policy_version != POLICY_VERSION:
        return PolicyDecision(Decision.DENY, "policy_version_mismatch")
    if command.actor_principal_id != session.principal_id:
        return PolicyDecision(Decision.DENY, "wrong_principal")
    if command.session_id != session.session_id:
        return PolicyDecision(Decision.DENY, "wrong_session")
    if command.issued_at > now or now - command.issued_at > COMMAND_MAX_AGE:
        return PolicyDecision(Decision.DENY, "command_expired_or_from_future")
    principal = state.principals.get(session.principal_id)
    if principal is None:
        return PolicyDecision(Decision.DENY, "unknown_principal")
    if principal.status is not IdentityStatus.ACTIVE or principal.revoked_at is not None:
        return PolicyDecision(Decision.DENY, "principal_inactive")
    policy = COMMAND_POLICIES.get(command.command_type)
    if policy is None:
        return PolicyDecision(Decision.DENY, "unknown_command_policy")
    if (
        command.capability_scope != policy.capability
        or command.requested_operation != policy.operation
        or command.resource_scope != policy.resource
    ):
        return PolicyDecision(Decision.DENY, "command_scope_policy_mismatch")
    if command.resource_scope in PROTECTED_RESOURCES:
        return PolicyDecision(Decision.DENY, "protected_resource_global_deny")
    if command.requested_operation in {Operation.EXECUTE, Operation.UPDATE_POLICY}:
        return PolicyDecision(Decision.DENY, "operation_global_deny")
    if command.capability_scope in {Capability.EXECUTION, Capability.POLICY_MODIFY}:
        return PolicyDecision(Decision.DENY, "capability_global_deny")
    if policy.task_required and command.task_scope is None:
        return PolicyDecision(Decision.DENY, "task_scope_required")
    if not policy.task_required and command.task_scope is not None:
        return PolicyDecision(Decision.DENY, "task_scope_not_applicable")
    if command.parent_command_id is not None:
        if command.parent_command_id not in state.processed_commands:
            return PolicyDecision(Decision.DENY, "unknown_parent_command")
    if command.task_scope is not None:
        task = state.tasks.get(command.task_scope)
        if task is None:
            return PolicyDecision(Decision.DENY, "unknown_task")
        if command.capability_scope not in task.capability_scope:
            return PolicyDecision(Decision.DENY, "capability_outside_task_scope")
        if command.resource_scope not in task.resource_scope:
            return PolicyDecision(Decision.DENY, "resource_outside_task_scope")
        if (
            command.command_type is not CommandType.TRANSITION_TASK
            and task.state not in {TaskState.AUTHORIZED, TaskState.RUNNING}
        ):
            return PolicyDecision(Decision.DENY, "task_not_executable")
    for evidence_id in command.evidence_lineage:
        artifact = state.artifacts.get(evidence_id)
        if artifact is None or not evidence_id.startswith(("evidence.", "evidence-")):
            return PolicyDecision(Decision.DENY, "invalid_evidence_lineage")
    return PolicyDecision(Decision.ALLOW, "policy_allows_evaluation")
