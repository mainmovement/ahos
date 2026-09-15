"""Canonical registry of 19 logical agents. Conservative maturity only."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from ahos_org.audit import AuditLog
from ahos_org.clock import Clock, SystemClock, isoformat_utc
from ahos_org.errors import UnknownIdentityError, ValidationError
from ahos_org.models import EventType, GovernanceStatus, MaturityLevel
from ahos_org.policy import GLOBAL_DENY_CAPABILITIES, KNOWN_CAPABILITIES

CANONICAL_AGENT_IDS: tuple[str, ...] = (
    "agent.chief-orchestrator",
    "agent.reality-forensics",
    "agent.evidence-transport",
    "agent.security",
    "agent.identity",
    "agent.canonical-decision-auditor",
    "agent.scoring-science",
    "agent.paper-trading",
    "agent.learning-memory",
    "agent.calibration",
    "agent.cognitive-agi-aci",
    "agent.windows-runtime",
    "agent.provider-data",
    "agent.integration",
    "agent.frontend-ux",
    "agent.independent-verification",
    "agent.red-team",
    "agent.change-architect",
    "agent.release-governance-reviewer",
)


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    role: str
    description: str
    maturity_level: MaturityLevel
    enabled: bool
    allowed_capabilities: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    governance_status: GovernanceStatus
    created_at: str
    updated_at: str

    def has_capability(self, capability: str) -> bool:
        return capability in self.allowed_capabilities

    def forbids_capability(self, capability: str) -> bool:
        return capability in self.prohibited_capabilities


def _seed_specs() -> tuple[dict[str, object], ...]:
    prohibited = tuple(sorted(GLOBAL_DENY_CAPABILITIES))
    return (
        {
            "agent_id": "agent.chief-orchestrator",
            "role": "Chief Orchestrator",
            "description": "Logical coordinator of organizational tasks. No unrestricted authority.",
            "allowed": ("orchestrate.plan", "task.propose", "task.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.reality-forensics",
            "role": "Reality Forensics",
            "description": "Logical role for reconstructing claims from evidence. No live data plane.",
            "allowed": ("evidence.record", "audit.read", "policy.inspect"),
        },
        {
            "agent_id": "agent.evidence-transport",
            "role": "Evidence Transport",
            "description": "Logical role for moving evidence references inside the org store.",
            "allowed": ("evidence.record", "audit.append", "task.inspect"),
        },
        {
            "agent_id": "agent.security",
            "role": "Security",
            "description": "Logical security reviewer. Cannot access credentials or external systems.",
            "allowed": ("security.inspect", "policy.inspect", "audit.read"),
        },
        {
            "agent_id": "agent.identity",
            "role": "Identity",
            "description": "Logical identity reviewer for agent records. No credential vault access.",
            "allowed": ("identity.inspect", "registry.inspect"),
        },
        {
            "agent_id": "agent.canonical-decision-auditor",
            "role": "Canonical Decision Auditor",
            "description": "Logical auditor of governance decisions and hash-chain integrity.",
            "allowed": ("audit.read", "verification.review", "policy.inspect"),
        },
        {
            "agent_id": "agent.scoring-science",
            "role": "Scoring Science",
            "description": "Logical scoring-science role. No production scoring runtime.",
            "allowed": ("scoring.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.paper-trading",
            "role": "Paper Trading",
            "description": "Logical paper-trading analyst. Live trading is globally denied.",
            "allowed": ("paper.analyze", "audit.read"),
        },
        {
            "agent_id": "agent.learning-memory",
            "role": "Learning / Memory",
            "description": "Logical memory/learning role. No model training or provider calls.",
            "allowed": ("evidence.record", "audit.read"),
        },
        {
            "agent_id": "agent.calibration",
            "role": "Calibration",
            "description": "Logical calibration reviewer. Does not touch AHOS calibration assets.",
            "allowed": ("calibration.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.cognitive-agi-aci",
            "role": "Cognitive / AGI-ACI",
            "description": "Logical cognitive-research role only. Slice 1 contains no AGI runtime.",
            "allowed": ("cognitive.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.windows-runtime",
            "role": "Windows Runtime",
            "description": "Logical Windows-runtime reviewer. Cannot start AHOS or any external runtime.",
            "allowed": ("windows.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.provider-data",
            "role": "Provider / Data",
            "description": "Logical provider/data policy role. Cannot connect to providers.",
            "allowed": ("policy.inspect", "audit.read"),
        },
        {
            "agent_id": "agent.integration",
            "role": "Integration",
            "description": "Logical integration reviewer. Telegram/n8n access is globally denied.",
            "allowed": ("integration.inspect", "policy.inspect"),
        },
        {
            "agent_id": "agent.frontend-ux",
            "role": "Frontend / UX",
            "description": "Logical frontend/UX role. No production UI deployment.",
            "allowed": ("frontend.inspect", "task.inspect"),
        },
        {
            "agent_id": "agent.independent-verification",
            "role": "Independent Verification",
            "description": "Logical independent verifier of org claims and audit integrity.",
            "allowed": ("verification.review", "audit.read", "policy.inspect"),
        },
        {
            "agent_id": "agent.red-team",
            "role": "Red Team",
            "description": "Logical adversarial tester of governance. Cannot grant itself authority.",
            "allowed": ("redteam.probe", "audit.read", "policy.inspect"),
        },
        {
            "agent_id": "agent.change-architect",
            "role": "Change Architect",
            "description": "Logical change-proposal role. Cannot modify protected external resources.",
            "allowed": ("change.propose", "task.propose", "policy.inspect"),
        },
        {
            "agent_id": "agent.release-governance-reviewer",
            "role": "Release / Governance Reviewer",
            "description": "Logical release reviewer. Human approval still required for protected resources.",
            "allowed": ("release.review", "audit.read", "policy.inspect"),
        },
    )


class AgentRegistry:
    def __init__(self, audit: AuditLog, clock: Clock | None = None) -> None:
        self._audit = audit
        self._clock = clock or SystemClock()
        self._agents: dict[str, AgentRecord] = {}

    def seed_canonical_agents(self) -> None:
        now = isoformat_utc(self._clock.now())
        prohibited = tuple(sorted(GLOBAL_DENY_CAPABILITIES))
        for spec in _seed_specs():
            record = AgentRecord(
                agent_id=str(spec["agent_id"]),
                role=str(spec["role"]),
                description=str(spec["description"]),
                maturity_level=MaturityLevel.REGISTERED,
                enabled=True,
                allowed_capabilities=tuple(spec["allowed"]),  # type: ignore[arg-type]
                prohibited_capabilities=prohibited,
                governance_status=GovernanceStatus.REGISTERED,
                created_at=now,
                updated_at=now,
            )
            self._put(record, actor="system", reason="canonical seed")

    def register(self, record: AgentRecord, *, actor: str = "system") -> AgentRecord:
        self._validate(record)
        if record.agent_id in self._agents:
            raise ValidationError(f"Agent already registered: {record.agent_id}")
        self._put(record, actor=actor, reason="register")
        return record

    def disable(self, agent_id: str, *, actor: str = "system", reason: str = "disabled") -> AgentRecord:
        current = self.get(agent_id)
        updated = replace(
            current,
            enabled=False,
            governance_status=GovernanceStatus.SUSPENDED,
            updated_at=isoformat_utc(self._clock.now()),
        )
        self._agents[agent_id] = updated
        self._audit.append(
            event_type=EventType.AGENT_UPDATED,
            actor=actor,
            action="disable",
            target=agent_id,
            reason=reason,
            decision="DENY",
        )
        return updated

    def get(self, agent_id: str) -> AgentRecord:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise UnknownIdentityError(f"Unknown agent: {agent_id}") from exc

    def exists(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def list_agents(self) -> tuple[AgentRecord, ...]:
        return tuple(self._agents.values())

    def ids(self) -> tuple[str, ...]:
        return tuple(self._agents)

    def _put(self, record: AgentRecord, *, actor: str, reason: str) -> None:
        self._validate(record)
        self._agents[record.agent_id] = record
        self._audit.append(
            event_type=EventType.AGENT_REGISTERED,
            actor=actor,
            action="register",
            target=record.agent_id,
            reason=reason,
            decision="RECORDED",
        )

    def _validate(self, record: AgentRecord) -> None:
        if not record.agent_id or not record.agent_id.startswith("agent."):
            raise ValidationError("agent_id must be a stable token starting with 'agent.'")
        if not record.role.strip():
            raise ValidationError("role is required")
        if int(record.maturity_level) not in range(0, 6):
            raise ValidationError("maturity_level must be 0..5")
        if not isinstance(record.maturity_level, MaturityLevel):
            raise ValidationError("maturity_level must be a MaturityLevel")
        allowed = set(record.allowed_capabilities)
        prohibited = set(record.prohibited_capabilities)
        if allowed & prohibited:
            raise ValidationError("capability cannot be both allowed and prohibited")
        unknown = (allowed | prohibited) - KNOWN_CAPABILITIES
        if unknown:
            raise ValidationError(f"unknown capability tokens: {sorted(unknown)}")
        for cap in GLOBAL_DENY_CAPABILITIES:
            if cap in allowed:
                raise ValidationError(f"globally denied capability cannot be allowed: {cap}")


def validate_maturity(value: int) -> MaturityLevel:
    try:
        return MaturityLevel(value)
    except ValueError as exc:
        raise ValidationError(f"invalid maturity_level: {value}") from exc


def iter_canonical_roles() -> Iterable[str]:
    for spec in _seed_specs():
        yield str(spec["role"])
