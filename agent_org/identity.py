"""Identity and bounded local-session contracts.

NON_PRODUCTION_LOCAL_OPERATOR_AUTH deliberately has no password, secret, or
external identity provider.  It is a deterministic trust-root stub for Slice
2B tests and local control-plane development only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from threading import RLock
from typing import Protocol

from agent_org.contracts import (
    IdentityStatus,
    IdentityType,
    Provenance,
    require_id,
    require_utc,
)


NON_PRODUCTION_LOCAL_OPERATOR_AUTH = "NON_PRODUCTION_LOCAL_OPERATOR_AUTH"


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdFactory(Protocol):
    def new(self, prefix: str) -> str: ...


@dataclass(frozen=True)
class Principal:
    principal_id: str
    identity_type: IdentityType
    display_name: str
    status: IdentityStatus
    provenance: Provenance
    created_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        require_id(self.principal_id, "principal.", "principal_id")
        require_utc(self.created_at, "created_at")
        if self.revoked_at is not None:
            require_utc(self.revoked_at, "revoked_at")
        if not self.display_name.strip():
            raise ValueError("display_name is required")


@dataclass(frozen=True)
class AgentIdentity(Principal):
    role: str = "logical-agent"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.identity_type is not IdentityType.AGENT:
            raise ValueError("AgentIdentity requires identity_type=AGENT")
        if not self.role.strip():
            raise ValueError("agent role is required")


@dataclass(frozen=True)
class HumanIdentity(Principal):
    operator_scope: str = "local-control-plane"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.identity_type is not IdentityType.HUMAN:
            raise ValueError("HumanIdentity requires identity_type=HUMAN")
        if not self.operator_scope:
            raise ValueError("operator_scope is required")


@dataclass(frozen=True)
class SystemIdentity(Principal):
    component: str = "tcb"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.identity_type is not IdentityType.SYSTEM:
            raise ValueError("SystemIdentity requires identity_type=SYSTEM")
        if not self.component:
            raise ValueError("component is required")


@dataclass(frozen=True)
class Session:
    session_id: str
    principal_id: str
    auth_method: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        require_id(self.session_id, "session.", "session_id")
        require_id(self.principal_id, "principal.", "principal_id")
        require_utc(self.issued_at, "issued_at")
        require_utc(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("session must have a bounded positive lifetime")
        if self.revoked_at is not None:
            require_utc(self.revoked_at, "revoked_at")

    def is_active(self, now: datetime) -> bool:
        require_utc(now, "now")
        return self.revoked_at is None and self.issued_at <= now < self.expires_at


class LocalOperatorSessionStub:
    """Trusted local issuer for exactly one configured operator.

    Holding this object is equivalent to controlling the non-production local
    trust root.  It must not be exposed as production authentication.
    """

    def __init__(
        self,
        operator: HumanIdentity,
        *,
        clock: Clock,
        ids: IdFactory,
        maximum_lifetime: timedelta = timedelta(minutes=30),
    ) -> None:
        if operator.status is not IdentityStatus.ACTIVE:
            raise ValueError("local operator must be active")
        if maximum_lifetime <= timedelta(0):
            raise ValueError("maximum_lifetime must be positive")
        self._operator = operator
        self._clock = clock
        self._ids = ids
        self._maximum_lifetime = maximum_lifetime
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()

    @property
    def operator(self) -> HumanIdentity:
        return self._operator

    def create_session(self, lifetime: timedelta) -> Session:
        if lifetime <= timedelta(0) or lifetime > self._maximum_lifetime:
            raise ValueError("requested session lifetime is outside local-stub bounds")
        with self._lock:
            now = self._clock.now()
            session = Session(
                session_id=self._ids.new("session"),
                principal_id=self._operator.principal_id,
                auth_method=NON_PRODUCTION_LOCAL_OPERATOR_AUTH,
                issued_at=now,
                expires_at=now + lifetime,
            )
            self._sessions[session.session_id] = session
            return session

    def revoke(self, session_id: str) -> Session:
        with self._lock:
            current = self._sessions[session_id]
            revoked = replace(current, revoked_at=self._clock.now())
            self._sessions[session_id] = revoked
            return revoked

    def resolve(self, supplied: Session) -> Session | None:
        """Resolve by ID and require exact equality to reject forged sessions."""
        with self._lock:
            registered = self._sessions.get(supplied.session_id)
            if registered is None or registered != supplied:
                return None
            return registered
