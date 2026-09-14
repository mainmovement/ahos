"""Governed in-memory state with capability-token mutation access.

This module is inside the trusted boundary.  Public/untrusted modules are
forbidden by static import-boundary tests from importing it.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock

from agent_org.audit import AuditLedger
from agent_org.authority import CapabilityGrant, Delegation
from agent_org.contracts import GovernedTask, POLICY_VERSION
from agent_org.epistemic import Approval, Artifact
from agent_org.identity import Principal


class ConcurrentStateError(RuntimeError):
    pass


class MutationAccessError(RuntimeError):
    pass


class _MutationPermit:
    pass


@dataclass
class _GovernedState:
    principals: dict[str, Principal] = field(default_factory=dict)
    tasks: dict[str, GovernedTask] = field(default_factory=dict)
    grants: dict[str, CapabilityGrant] = field(default_factory=dict)
    delegations: dict[str, Delegation] = field(default_factory=dict)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    approvals: dict[str, Approval] = field(default_factory=dict)
    processed_commands: set[str] = field(default_factory=set)
    audit: AuditLedger = field(default_factory=AuditLedger)
    policy_version: str = POLICY_VERSION
    epoch: int = 0


class GovernedStore:
    """Single-writer store; mutation requires its unforgeable permit identity."""

    def __init__(self, initial: _GovernedState, permit: _MutationPermit) -> None:
        self.__state = initial
        self.__permit = permit
        self.__lock = RLock()

    @property
    def lock(self) -> RLock:
        return self.__lock

    def snapshot_for_projection(self) -> _GovernedState:
        with self.__lock:
            return deepcopy(self.__state)

    def begin(self, permit: object) -> tuple[_GovernedState, int]:
        self.__check(permit)
        return deepcopy(self.__state), self.__state.epoch

    def commit(
        self,
        working: _GovernedState,
        *,
        expected_epoch: int,
        permit: object,
    ) -> None:
        self.__check(permit)
        if self.__state.epoch != expected_epoch:
            raise ConcurrentStateError("state changed during transaction")
        working.audit.verify()
        working.epoch = expected_epoch + 1
        self.__state = working

    def __check(self, permit: object) -> None:
        if permit is not self.__permit:
            raise MutationAccessError("governed state mutation requires TCB permit")


def _create_governed_store(
    initial: _GovernedState | None = None,
) -> tuple[GovernedStore, _MutationPermit]:
    """Trusted construction function. Never re-exported from public modules."""
    permit = _MutationPermit()
    return GovernedStore(initial or _GovernedState(), permit), permit
