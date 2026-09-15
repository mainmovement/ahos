"""Deterministic fixture helpers for Slice 2B tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from agent_org.authority import CapabilityGrant
from agent_org.commands import (
    CommandEnvelope,
    CommandPayload,
    CreateTaskPayload,
    DelegateAuthorityPayload,
    RegisterAgentPayload,
    TransitionTaskPayload,
)
from agent_org.contracts import (
    Capability,
    CommandType,
    DERIVE_AUTHORITY_AT_TCB,
    GovernedTask,
    IdentityStatus,
    IdentityType,
    POLICY_VERSION,
    Resource,
    TaskState,
)
from agent_org.governance import COMMAND_POLICIES
from agent_org.identity import AgentIdentity
from agent_org.tcb import InjectedFailure, LocalControlPlane, build_local_control_plane
from ahos_org.clock import FrozenClock
from ahos_org.ids import SequentialIdFactory


class PlannedFailure:
    def __init__(self) -> None:
        self.stage: str | None = None
        self.remaining = 0
        self.succeed_before_fail = 0

    def arm(self, stage: str, count: int = 1, *, after: int = 0) -> None:
        self.stage = stage
        self.remaining = count
        self.succeed_before_fail = after

    def trip(self, stage: str) -> None:
        if self.stage != stage:
            return
        if self.succeed_before_fail > 0:
            self.succeed_before_fail -= 1
            return
        if self.remaining > 0:
            self.remaining -= 1
            raise InjectedFailure(stage)


@dataclass
class Env:
    clock: FrozenClock
    ids: SequentialIdFactory
    failures: PlannedFailure
    plane: LocalControlPlane
    session: object


def new_env() -> Env:
    clock = FrozenClock()
    ids = SequentialIdFactory()
    failures = PlannedFailure()
    plane = build_local_control_plane(clock=clock, ids=ids, failures=failures)
    session = plane.local_operator_auth.create_session(timedelta(minutes=20))
    return Env(clock, ids, failures, plane, session)


def make_command(
    env: Env,
    command_type: CommandType,
    payload_factory: Callable[[str], CommandPayload],
    *,
    task_scope: str | None = None,
    expected_state_version: int = 0,
    evidence_lineage: tuple[str, ...] = (),
    actor_principal_id: str | None = None,
    session_id: str | None = None,
    policy_version: str = POLICY_VERSION,
    parent_command_id: str | None = None,
) -> CommandEnvelope:
    command_id = env.ids.new("command")
    policy = COMMAND_POLICIES[command_type]
    return CommandEnvelope(
        command_id=command_id,
        command_type=command_type,
        actor_principal_id=actor_principal_id or env.plane.operator.principal_id,
        session_id=session_id or env.session.session_id,  # type: ignore[attr-defined]
        authority_context_ref=DERIVE_AUTHORITY_AT_TCB,
        task_scope=task_scope,
        resource_scope=policy.resource,
        capability_scope=policy.capability,
        requested_operation=policy.operation,
        policy_version=policy_version,
        causation_id=None,
        correlation_id=env.ids.new("correlation"),
        parent_command_id=parent_command_id,
        evidence_lineage=evidence_lineage,
        expected_state_version=expected_state_version,
        payload=payload_factory(command_id),
        issued_at=env.clock.now(),
    )


def submit(env: Env, command: CommandEnvelope):
    return env.plane.tcb.submit(command, env.session)  # type: ignore[arg-type]


def provenance(env: Env, command_id: str, *, method: str = "deterministic-test"):
    from agent_org.contracts import Provenance

    return Provenance(
        creator_principal_id=env.plane.operator.principal_id,
        session_id=env.session.session_id,  # type: ignore[attr-defined]
        command_id=command_id,
        method=method,
    )


def register_agent(env: Env, principal_id: str = "principal.agent-producer") -> AgentIdentity:
    holder: dict[str, AgentIdentity] = {}

    def payload(command_id: str) -> RegisterAgentPayload:
        identity = AgentIdentity(
            principal_id=principal_id,
            identity_type=IdentityType.AGENT,
            display_name=principal_id,
            status=IdentityStatus.ACTIVE,
            provenance=provenance(env, command_id),
            created_at=env.clock.now(),
            role="test-logical-agent",
        )
        holder["identity"] = identity
        return RegisterAgentPayload(identity)

    result = submit(env, make_command(env, CommandType.REGISTER_AGENT, payload))
    assert result.accepted, result
    return holder["identity"]


def create_task(
    env: Env,
    *,
    owner_principal_id: str | None = None,
    capabilities: tuple[Capability, ...] = (
        Capability.TASK_MANAGE,
        Capability.EPISTEMIC_WRITE,
        Capability.EPISTEMIC_CHALLENGE,
        Capability.VERIFICATION_RECORD,
        Capability.APPROVAL_ISSUE,
        Capability.KNOWLEDGE_PROMOTE,
    ),
    resources: tuple[Resource, ...] = (
        Resource.TASK_STORE,
        Resource.EPISTEMIC_STORE,
        Resource.APPROVAL_STORE,
    ),
    parent_task_id: str | None = None,
) -> GovernedTask:
    task = GovernedTask(
        task_id=env.ids.new("task"),
        owner_principal_id=owner_principal_id or env.plane.operator.principal_id,
        state=TaskState.PROPOSED,
        capability_scope=capabilities,
        resource_scope=resources,
        created_at=env.clock.now(),
        updated_at=env.clock.now(),
        parent_task_id=parent_task_id,
    )
    command = make_command(
        env,
        CommandType.CREATE_TASK,
        lambda _command_id: CreateTaskPayload(task),
    )
    result = submit(env, command)
    assert result.accepted, result
    return task


def _root_grant(
    env: Env, capability: Capability, operation, resource: Resource
) -> CapabilityGrant:
    matches = [
        grant
        for grant in env.plane.projections.capability_status(
            env.plane.operator.principal_id
        ).grants
        if grant.task_id is None
        and grant.capability_id == capability
        and grant.operation == operation
        and grant.resource_id == resource
    ]
    assert len(matches) == 1, (capability, operation, resource, matches)
    return matches[0]


def delegate_for_command(
    env: Env,
    task_id: str,
    command_type: CommandType,
    *,
    principal_id: str | None = None,
    expires_in: timedelta = timedelta(hours=1),
) -> CapabilityGrant:
    policy = COMMAND_POLICIES[command_type]
    parent = _root_grant(env, policy.capability, policy.operation, policy.resource)
    child = CapabilityGrant(
        grant_id=env.ids.new("grant"),
        principal_id=principal_id or env.plane.operator.principal_id,
        capability_id=policy.capability,
        operation=policy.operation,
        resource_id=policy.resource,
        task_id=task_id,
        issued_by_principal_id=env.plane.operator.principal_id,
        issued_at=env.clock.now(),
        expires_at=min(env.clock.now() + expires_in, parent.expires_at),
        policy_version=POLICY_VERSION,
        parent_grant_id=parent.grant_id,
        delegation_depth=1,
    )
    command = make_command(
        env,
        CommandType.DELEGATE_AUTHORITY,
        lambda _command_id: DelegateAuthorityPayload(child),
    )
    result = submit(env, command)
    assert result.accepted, result
    return child


def authorize_task(env: Env, task: GovernedTask) -> GovernedTask:
    delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
    command = make_command(
        env,
        CommandType.TRANSITION_TASK,
        lambda _command_id: TransitionTaskPayload(
            task_id=task.task_id, target_state=TaskState.AUTHORIZED.value
        ),
        task_scope=task.task_id,
        expected_state_version=task.version,
    )
    result = submit(env, command)
    assert result.accepted, result
    updated = env.plane.projections.task(task.task_id)
    assert updated is not None
    return updated


def ready_task(env: Env) -> GovernedTask:
    task = create_task(env)
    return authorize_task(env, task)


def grant_task_commands(
    env: Env, task_id: str, command_types: tuple[CommandType, ...]
) -> None:
    existing = env.plane.projections.capability_status(
        env.plane.operator.principal_id
    ).grants
    for command_type in command_types:
        policy = COMMAND_POLICIES[command_type]
        if not any(
            grant.task_id == task_id
            and grant.capability_id == policy.capability
            and grant.operation == policy.operation
            and grant.resource_id == policy.resource
            and grant.revoked_at is None
            for grant in existing
        ):
            delegate_for_command(env, task_id, command_type)
