"""Shared deterministic fixtures. Not production agents and not maturity claims."""

from __future__ import annotations

from ahos_org.clock import FrozenClock, isoformat_utc
from ahos_org.ids import SequentialIdFactory
from ahos_org.models import GovernanceStatus, MaturityLevel, RiskLevel, TaskState
from ahos_org.organization import AgentOrganization
from ahos_org.policy import GLOBAL_DENY_CAPABILITIES
from ahos_org.registry import AgentRecord
from ahos_org.tasks import TaskRecord

DEFAULT_ALLOWED = (
    "sandbox.execute",
    "audit.read",
    "policy.inspect",
    "registry.inspect",
    "release.review",
)


def new_org() -> AgentOrganization:
    return AgentOrganization(clock=FrozenClock(), ids=SequentialIdFactory())


def fixture_agent(
    clock: FrozenClock,
    *,
    agent_id: str = "agent.test-executor",
    maturity: MaturityLevel = MaturityLevel.IMPLEMENTED,
    enabled: bool = True,
    allowed: tuple[str, ...] = DEFAULT_ALLOWED,
) -> AgentRecord:
    now = isoformat_utc(clock.now())
    return AgentRecord(
        agent_id=agent_id,
        role="Test Fixture",
        description="Non-canonical fixture agent used only by Slice 1 tests.",
        maturity_level=maturity,
        enabled=enabled,
        allowed_capabilities=allowed,
        prohibited_capabilities=tuple(sorted(GLOBAL_DENY_CAPABILITIES)),
        governance_status=GovernanceStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def authorized_task(
    org: AgentOrganization,
    *,
    agent_id: str,
    capabilities: tuple[str, ...],
    resources: tuple[str, ...],
    risk: RiskLevel = RiskLevel.LOW,
) -> TaskRecord:
    task = org.tasks.create(
        task_type="slice1-test",
        requester="tester",
        assigned_agent=agent_id,
        requested_capabilities=capabilities,
        target_resources=resources,
        risk_level=risk,
        actor="tester",
    )
    return org.tasks.transition(
        task.task_id,
        TaskState.AUTHORIZED,
        actor="tester",
        reason="fixture authorization",
    )
