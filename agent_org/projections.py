"""Read-only projections over governed state.

Returned values are immutable records/tuples copied from the store.  This API
contains no mutation method and exposes no session secrets (none are stored).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from agent_org.audit import AuditEvent
from agent_org.authority import CapabilityGrant, Delegation
from agent_org.contracts import GovernedTask
from agent_org.epistemic import Artifact, ResearchMission
from agent_org.identity import AgentIdentity, Principal
from agent_org.stores import _GovernedState


@dataclass(frozen=True)
class CapabilityStatus:
    principal_id: str
    grants: tuple[CapabilityGrant, ...]
    delegations: tuple[Delegation, ...]


class ReadOnlyProjections:
    def __init__(self, snapshot: Callable[[], _GovernedState]) -> None:
        self.__snapshot = snapshot

    def agents(self) -> tuple[AgentIdentity, ...]:
        state = self.__snapshot()
        return tuple(
            item for item in state.principals.values() if isinstance(item, AgentIdentity)
        )

    def principals(self) -> tuple[Principal, ...]:
        return tuple(self.__snapshot().principals.values())

    def tasks(self) -> tuple[GovernedTask, ...]:
        return tuple(self.__snapshot().tasks.values())

    def epistemic_objects(self) -> tuple[Artifact, ...]:
        return tuple(self.__snapshot().artifacts.values())

    def research_missions(self) -> tuple[ResearchMission, ...]:
        return tuple(
            item
            for item in self.__snapshot().artifacts.values()
            if isinstance(item, ResearchMission)
        )

    def audit_events(self) -> tuple[AuditEvent, ...]:
        return self.__snapshot().audit.events()

    def capability_status(self, principal_id: str) -> CapabilityStatus:
        state = self.__snapshot()
        return CapabilityStatus(
            principal_id=principal_id,
            grants=tuple(
                grant
                for grant in state.grants.values()
                if grant.principal_id == principal_id
            ),
            delegations=tuple(
                delegation
                for delegation in state.delegations.values()
                if delegation.delegatee_principal_id == principal_id
            ),
        )

    def artifact(self, artifact_id: str) -> Artifact | None:
        return self.__snapshot().artifacts.get(artifact_id)

    def task(self, task_id: str) -> GovernedTask | None:
        return self.__snapshot().tasks.get(task_id)

    def verify_audit(self) -> bool:
        state = self.__snapshot()
        return state.audit.verify()
