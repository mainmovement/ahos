"""Centralized fail-closed authorization. UNKNOWN never becomes ALLOW."""

from __future__ import annotations

from dataclasses import dataclass

from ahos_org.audit import AuditLog
from ahos_org.models import AuthzDecision, EventType, EXECUTABLE_TASK_STATES, RiskLevel, TaskState
from ahos_org.policy import (
    GLOBAL_DENY_CAPABILITIES,
    GLOBAL_DENY_OPERATIONS,
    KNOWN_CAPABILITIES,
    KNOWN_OPERATIONS,
    MINIMUM_MATURITY_FOR_ALLOW,
    MINIMUM_MATURITY_WHEN_VERIFIED_REQUIRED,
)
from ahos_org.registry import AgentRegistry
from ahos_org.resources import ProtectedResourceRegistry
from ahos_org.tasks import TaskStateMachine


@dataclass(frozen=True)
class AuthzRequest:
    agent_id: str
    task_id: str
    capability: str
    resource_id: str
    action: str


@dataclass(frozen=True)
class AuthzResult:
    request: AuthzRequest
    decision: AuthzDecision
    reason: str

    def is_granted(self) -> bool:
        return self.decision is AuthzDecision.ALLOW


class GovernanceEngine:
    def __init__(
        self,
        *,
        agents: AgentRegistry,
        tasks: TaskStateMachine,
        resources: ProtectedResourceRegistry,
        audit: AuditLog,
    ) -> None:
        self._agents = agents
        self._tasks = tasks
        self._resources = resources
        self._audit = audit

    def authorize(self, request: AuthzRequest, *, actor: str = "governance") -> AuthzResult:
        result = self._decide(request)
        self._audit.append(
            event_type=EventType.AUTHZ_DECISION,
            actor=actor,
            action=request.action,
            target=request.resource_id,
            reason=result.reason,
            task_id=request.task_id,
            decision=str(result.decision),
            evidence_refs=(request.agent_id, request.capability),
        )
        return result

    def _decide(self, request: AuthzRequest) -> AuthzResult:
        deny = lambda reason: AuthzResult(request, AuthzDecision.DENY, reason)

        if not request.agent_id or not self._agents.exists(request.agent_id):
            return deny("unknown_agent")
        agent = self._agents.get(request.agent_id)
        if not agent.enabled:
            return deny("agent_disabled")

        if not request.capability or request.capability not in KNOWN_CAPABILITIES:
            return deny("unknown_capability")
        if request.capability in GLOBAL_DENY_CAPABILITIES:
            return deny("globally_denied_capability")
        if agent.forbids_capability(request.capability):
            return deny("prohibited_capability")
        if not agent.has_capability(request.capability):
            return deny("missing_capability")

        if not request.action or request.action not in KNOWN_OPERATIONS:
            return deny("unknown_operation")
        if request.action in GLOBAL_DENY_OPERATIONS:
            return deny("globally_denied_operation")

        if not request.resource_id or not self._resources.exists(request.resource_id):
            return deny("unknown_resource")
        resource = self._resources.get(request.resource_id)
        if resource.forbids(request.action):
            return deny("forbidden_operation")
        if not resource.allows(request.action):
            return deny("operation_not_allowed")

        if not request.task_id or not self._tasks.exists(request.task_id):
            return deny("unknown_task")
        task = self._tasks.get(request.task_id)
        if task.assigned_agent != request.agent_id:
            return deny("agent_not_assigned")
        if request.capability not in task.requested_capabilities:
            return deny("capability_not_on_task")
        if request.resource_id not in task.target_resources:
            return deny("resource_not_on_task")

        if task.current_state is TaskState.BLOCKED:
            return AuthzResult(request, AuthzDecision.BLOCKED, "task_blocked")
        if task.current_state not in EXECUTABLE_TASK_STATES:
            return deny("invalid_task_state")

        required_maturity = MINIMUM_MATURITY_FOR_ALLOW
        if resource.requires_verified_agent:
            required_maturity = MINIMUM_MATURITY_WHEN_VERIFIED_REQUIRED
        if int(agent.maturity_level) < required_maturity:
            return deny("insufficient_maturity")

        needs_review = resource.requires_human_approval or task.risk_level in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }
        if needs_review and not task.human_approved:
            return AuthzResult(request, AuthzDecision.REQUIRES_REVIEW, "human_approval_required")

        return AuthzResult(request, AuthzDecision.ALLOW, "all_conditions_passed")
