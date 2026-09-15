"""Protected-resource policy registry. Symbolic only — no resource is accessed."""

from __future__ import annotations

from dataclasses import dataclass

from ahos_org.audit import AuditLog
from ahos_org.errors import UnknownIdentityError, ValidationError
from ahos_org.models import EventType
from ahos_org.policy import GLOBAL_DENY_OPERATIONS, KNOWN_OPERATIONS

PROTECTED_AHOS_RESOURCE_IDS: tuple[str, ...] = (
    "AHOS_REPOSITORY",
    "AHOS_DATABASES",
    "AHOS_LANE_A",
    "AHOS_LANE_B",
    "AHOS_CALIBRATION",
    "AHOS_RUNTIME",
    "AHOS_SOAK",
    "AHOS_TELEGRAM",
    "AHOS_N8N",
    "AHOS_CREDENTIALS",
    "AHOS_PRODUCTION",
    "AHOS_LIVE_TRADING",
)

INTERNAL_RESOURCE_IDS: tuple[str, ...] = (
    "ORG_REGISTRY",
    "ORG_TASK_STORE",
    "ORG_AUDIT_LOG",
    "ORG_TEST_SANDBOX",
    "ORG_CHANGE_CONTROL",
)


@dataclass(frozen=True)
class ProtectedResource:
    resource_id: str
    classification: str
    protection_level: int
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    requires_human_approval: bool
    requires_verified_agent: bool
    notes: str

    def allows(self, operation: str) -> bool:
        return operation in self.allowed_operations

    def forbids(self, operation: str) -> bool:
        return operation in self.forbidden_operations or operation in GLOBAL_DENY_OPERATIONS


class ProtectedResourceRegistry:
    def __init__(self, audit: AuditLog) -> None:
        self._audit = audit
        self._resources: dict[str, ProtectedResource] = {}

    def seed_canonical_resources(self) -> None:
        forbidden = tuple(sorted(GLOBAL_DENY_OPERATIONS | {"read", "write", "delete", "query", "migrate", "invoke", "start", "stop", "execute"}))
        ahos_notes = (
            "Symbolic policy entry only. Slice 1 does not open, query, or connect "
            "to the named external system."
        )
        for resource_id in PROTECTED_AHOS_RESOURCE_IDS:
            self.register(
                ProtectedResource(
                    resource_id=resource_id,
                    classification="PROTECTED_EXTERNAL",
                    protection_level=5,
                    allowed_operations=(),
                    forbidden_operations=forbidden,
                    requires_human_approval=True,
                    requires_verified_agent=True,
                    notes=ahos_notes,
                ),
                actor="system",
            )
        internal = (
            ProtectedResource(
                resource_id="ORG_REGISTRY",
                classification="INTERNAL",
                protection_level=1,
                allowed_operations=("inspect",),
                forbidden_operations=tuple(sorted(GLOBAL_DENY_OPERATIONS)),
                requires_human_approval=False,
                requires_verified_agent=False,
                notes="In-process agent registry. No external I/O.",
            ),
            ProtectedResource(
                resource_id="ORG_TASK_STORE",
                classification="INTERNAL",
                protection_level=1,
                allowed_operations=("inspect", "propose", "transition"),
                forbidden_operations=tuple(sorted(GLOBAL_DENY_OPERATIONS)),
                requires_human_approval=False,
                requires_verified_agent=False,
                notes="In-process task state machine.",
            ),
            ProtectedResource(
                resource_id="ORG_AUDIT_LOG",
                classification="INTERNAL",
                protection_level=2,
                allowed_operations=("inspect", "append", "read"),
                forbidden_operations=tuple(sorted(GLOBAL_DENY_OPERATIONS)),
                requires_human_approval=False,
                requires_verified_agent=False,
                notes="In-process append-only audit log.",
            ),
            ProtectedResource(
                resource_id="ORG_TEST_SANDBOX",
                classification="INTERNAL_TEST",
                protection_level=1,
                allowed_operations=("inspect", "execute"),
                forbidden_operations=tuple(sorted(GLOBAL_DENY_OPERATIONS)),
                requires_human_approval=False,
                requires_verified_agent=False,
                notes="Fixture-only sandbox for positive authorization tests.",
            ),
            ProtectedResource(
                resource_id="ORG_CHANGE_CONTROL",
                classification="INTERNAL",
                protection_level=3,
                allowed_operations=("inspect", "review"),
                forbidden_operations=tuple(sorted(GLOBAL_DENY_OPERATIONS)),
                requires_human_approval=True,
                requires_verified_agent=False,
                notes="Internal change-control gate used to test human-approval enforcement.",
            ),
        )
        for resource in internal:
            self.register(resource, actor="system")

    def register(self, resource: ProtectedResource, *, actor: str = "system") -> ProtectedResource:
        self._validate(resource)
        if resource.resource_id in self._resources:
            raise ValidationError(f"Resource already registered: {resource.resource_id}")
        self._resources[resource.resource_id] = resource
        self._audit.append(
            event_type=EventType.RESOURCE_REGISTERED,
            actor=actor,
            action="register",
            target=resource.resource_id,
            reason="protected resource policy recorded",
            decision="RECORDED",
        )
        return resource

    def get(self, resource_id: str) -> ProtectedResource:
        try:
            return self._resources[resource_id]
        except KeyError as exc:
            raise UnknownIdentityError(f"Unknown resource: {resource_id}") from exc

    def exists(self, resource_id: str) -> bool:
        return resource_id in self._resources

    def ids(self) -> tuple[str, ...]:
        return tuple(self._resources)

    def list_resources(self) -> tuple[ProtectedResource, ...]:
        return tuple(self._resources.values())

    def _validate(self, resource: ProtectedResource) -> None:
        if not resource.resource_id:
            raise ValidationError("resource_id is required")
        if resource.protection_level < 0 or resource.protection_level > 5:
            raise ValidationError("protection_level must be 0..5")
        allowed = set(resource.allowed_operations)
        forbidden = set(resource.forbidden_operations)
        unknown = (allowed | forbidden) - KNOWN_OPERATIONS
        if unknown:
            raise ValidationError(f"unknown operations: {sorted(unknown)}")
        if allowed & forbidden:
            raise ValidationError("operation cannot be both allowed and forbidden")
        if allowed & GLOBAL_DENY_OPERATIONS:
            raise ValidationError("globally denied operations cannot be allowed")
