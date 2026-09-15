"""Composition root for the Slice 1 control plane."""

from __future__ import annotations

from pathlib import Path

from ahos_org.audit import AuditLog
from ahos_org.clock import Clock, SystemClock
from ahos_org.governance import AuthzRequest, AuthzResult, GovernanceEngine
from ahos_org.ids import IdFactory, UuidFactory
from ahos_org.registry import AgentRecord, AgentRegistry
from ahos_org.resources import ProtectedResourceRegistry
from ahos_org.tasks import TaskRecord, TaskStateMachine


class AgentOrganization:
    """One runtime, many logical agents, central governance."""

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        ids: IdFactory | None = None,
        audit_path: Path | None = None,
        seed: bool = True,
    ) -> None:
        self.clock = clock or SystemClock()
        self.ids = ids or UuidFactory()
        self.audit = AuditLog(clock=self.clock, ids=self.ids, path=audit_path)
        self.agents = AgentRegistry(self.audit, clock=self.clock)
        self.resources = ProtectedResourceRegistry(self.audit)
        self.tasks = TaskStateMachine(self.audit, clock=self.clock, ids=self.ids)
        self.governance = GovernanceEngine(
            agents=self.agents,
            tasks=self.tasks,
            resources=self.resources,
            audit=self.audit,
        )
        if seed:
            self.agents.seed_canonical_agents()
            self.resources.seed_canonical_resources()

    def authorize(
        self,
        *,
        agent_id: str,
        task_id: str,
        capability: str,
        resource_id: str,
        action: str,
        actor: str = "governance",
    ) -> AuthzResult:
        return self.governance.authorize(
            AuthzRequest(
                agent_id=agent_id,
                task_id=task_id,
                capability=capability,
                resource_id=resource_id,
                action=action,
            ),
            actor=actor,
        )

    def register_fixture_agent(self, record: AgentRecord) -> AgentRecord:
        """Register a non-canonical fixture agent. Does not alter canonical maturity."""
        return self.agents.register(record)

    def propose_task(self, **kwargs: object) -> TaskRecord:
        return self.tasks.create(**kwargs)  # type: ignore[arg-type]
