"""Capability grants, delegation attenuation, and TCB-derived authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from agent_org.contracts import (
    Capability,
    Operation,
    Resource,
    require_id,
    require_utc,
)


MAX_DELEGATION_DEPTH = 3


@dataclass(frozen=True)
class CapabilityGrant:
    grant_id: str
    principal_id: str
    capability_id: Capability
    operation: Operation
    resource_id: Resource
    task_id: str | None
    issued_by_principal_id: str
    issued_at: datetime
    expires_at: datetime
    policy_version: str
    parent_grant_id: str | None = None
    delegation_depth: int = 0
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        require_id(self.grant_id, "grant.", "grant_id")
        require_id(self.principal_id, "principal.", "principal_id")
        require_id(self.issued_by_principal_id, "principal.", "issued_by_principal_id")
        if self.task_id is not None:
            require_id(self.task_id, "task.", "task_id")
        require_utc(self.issued_at, "issued_at")
        require_utc(self.expires_at, "expires_at")
        if self.revoked_at is not None:
            require_utc(self.revoked_at, "revoked_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("grant must have a bounded positive lifetime")
        if not self.policy_version:
            raise ValueError("grant policy_version is required")
        if self.delegation_depth < 0:
            raise ValueError("delegation_depth cannot be negative")
        if self.parent_grant_id is None and self.delegation_depth != 0:
            raise ValueError("root grant must have delegation_depth=0")
        if self.parent_grant_id is not None and self.delegation_depth == 0:
            raise ValueError("delegated grant must have positive delegation_depth")

    def is_active(self, now: datetime) -> bool:
        require_utc(now, "now")
        return self.revoked_at is None and self.issued_at <= now < self.expires_at


@dataclass(frozen=True)
class AuthorityChain:
    grant_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.grant_ids or len(set(self.grant_ids)) != len(self.grant_ids):
            raise ValueError("authority chain must be non-empty and cycle-free")


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    parent_grant_id: str
    child_grant_id: str
    delegator_principal_id: str
    delegatee_principal_id: str
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_id(self.delegation_id, "delegation.", "delegation_id")
        require_id(self.parent_grant_id, "grant.", "parent_grant_id")
        require_id(self.child_grant_id, "grant.", "child_grant_id")
        require_id(
            self.delegator_principal_id, "principal.", "delegator_principal_id"
        )
        require_id(
            self.delegatee_principal_id, "principal.", "delegatee_principal_id"
        )
        require_utc(self.issued_at, "issued_at")
        require_utc(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("delegation must have bounded lifetime")


@dataclass(frozen=True)
class AuthorityContext:
    principal_id: str
    task_id: str | None
    capability_id: Capability
    operation: Operation
    resource_id: Resource
    policy_version: str
    chain: AuthorityChain
    derived_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_id(self.principal_id, "principal.", "principal_id")
        require_utc(self.derived_at, "derived_at")
        require_utc(self.expires_at, "expires_at")


@dataclass(frozen=True)
class AuthorityEvaluation:
    allowed: bool
    reason: str
    context: AuthorityContext | None = None


def validate_delegation(
    parent: CapabilityGrant,
    child: CapabilityGrant,
    *,
    now: datetime,
    maximum_depth: int = MAX_DELEGATION_DEPTH,
) -> str | None:
    """Return a denial reason or None when child authority is attenuated."""
    if not parent.is_active(now):
        return "parent_grant_inactive"
    if child.parent_grant_id != parent.grant_id:
        return "broken_parent_reference"
    if child.issued_by_principal_id != parent.principal_id:
        return "delegator_not_parent_principal"
    if child.delegation_depth != parent.delegation_depth + 1:
        return "broken_delegation_depth"
    if child.delegation_depth > maximum_depth:
        return "delegation_depth_exceeded"
    if child.issued_at < parent.issued_at or child.expires_at > parent.expires_at:
        return "child_time_scope_exceeds_parent"
    if child.policy_version != parent.policy_version:
        return "child_policy_exceeds_parent"
    if (
        child.capability_id != parent.capability_id
        or child.operation != parent.operation
        or child.resource_id != parent.resource_id
    ):
        return "child_authority_exceeds_parent"
    if parent.task_id is not None and child.task_id != parent.task_id:
        return "child_task_scope_exceeds_parent"
    if parent.task_id is None and child.task_id is None:
        return "delegation_must_narrow_task_scope"
    return None


def derive_authority(
    grants: Mapping[str, CapabilityGrant],
    *,
    principal_id: str,
    task_id: str | None,
    capability_id: Capability,
    operation: Operation,
    resource_id: Resource,
    policy_version: str,
    now: datetime,
) -> AuthorityEvaluation:
    """Find an exact active leaf grant and verify its complete parent chain."""
    matching = sorted(
        (
            grant
            for grant in grants.values()
            if grant.principal_id == principal_id
            and grant.task_id == task_id
            and grant.capability_id == capability_id
            and grant.operation == operation
            and grant.resource_id == resource_id
            and grant.policy_version == policy_version
        ),
        key=lambda item: item.grant_id,
    )
    if not matching:
        return AuthorityEvaluation(False, "no_exact_capability_grant")

    inactive_reason = "grant_inactive"
    for leaf in matching:
        if not leaf.is_active(now):
            inactive_reason = (
                "grant_revoked" if leaf.revoked_at is not None else "grant_expired"
            )
            continue
        chain_reversed = [leaf]
        cursor = leaf
        seen = {leaf.grant_id}
        broken: str | None = None
        while cursor.parent_grant_id is not None:
            parent = grants.get(cursor.parent_grant_id)
            if parent is None or parent.grant_id in seen:
                broken = "broken_authority_chain"
                break
            seen.add(parent.grant_id)
            denial = validate_delegation(parent, cursor, now=now)
            if denial is not None:
                broken = denial
                break
            chain_reversed.append(parent)
            cursor = parent
        if broken is not None:
            inactive_reason = broken
            continue
        chain = tuple(item.grant_id for item in reversed(chain_reversed))
        return AuthorityEvaluation(
            True,
            "authority_derived",
            AuthorityContext(
                principal_id=principal_id,
                task_id=task_id,
                capability_id=capability_id,
                operation=operation,
                resource_id=resource_id,
                policy_version=policy_version,
                chain=AuthorityChain(chain),
                derived_at=now,
                expires_at=min(item.expires_at for item in chain_reversed),
            ),
        )
    return AuthorityEvaluation(False, inactive_reason)
