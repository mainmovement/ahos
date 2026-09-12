#!/usr/bin/env python3
"""W4 Slice 4 — canonical identity join boundary.

Read-only classifier. Not an identity authority and not a resolver.

representation / operational key
        ↓
W4 resolution contract
        ↓
existing IdentityResolution authority
        ↓
canonical join decision

Do not import this module from the operational daemon or the pipeline.
Do not persist, hash, query providers, mint token_id, or call resolve_identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from architecture.identity.fusion import (
    CanonicalTokenId,
    FallbackKind,
    IdentityConflict,
    IdentityObservation,
    IdentityRelationship,
    PoolAddress,
    ProviderResourceRef,
    RelationshipKind,
    RepresentationKind,
    ResolutionVersionRef,
    TokenAddress,
    TokenIdNamespace,
    classify_fallback_key,
    is_canonical_verified,
)
from architecture.identity.resolution_contract import (
    ResolutionInput,
    ResolutionPlan,
    ResolutionPlanStatus,
    ResolutionSubjectKind,
)
from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from architecture.identity.validate import EVM_CHAINS

JOIN_VERSION = "identity-join-boundary-v1"

CONSUMER_CONTRACT = (
    "This module classifies whether a representation may participate in a "
    "canonical entity join. It does not resolve identity. "
    "CANONICAL_JOIN requires a structurally valid IdentityResolution with "
    "TokenIdentity.state=VERIFIED, a non-empty token_id, and a canonical "
    "address. CanonicalTokenId wrappers, TokenAddress.validation_state, "
    "symbols, pools, provider IDs, fallbacks, relationships, and historical "
    "mappings never grant CANONICAL_JOIN by themselves."
)

_SUPPORTED_CHAINS = frozenset(EVM_CHAINS) | {"solana"}
_HISTORICAL_KINDS = frozenset({
    RelationshipKind.MIGRATES_TO,
    RelationshipKind.SUCCEEDS,
    RelationshipKind.SUPERSEDED,
})
_SYMBOL_KINDS = frozenset({
    RepresentationKind.SYMBOL,
    RepresentationKind.NAME,
    RepresentationKind.ALIAS,
})


class JoinClass(str, Enum):
    """Join permission class. Not IdentityState. Never VERIFIED."""

    CANONICAL_JOIN = "CANONICAL_JOIN"
    OPERATIONAL_JOIN = "OPERATIONAL_JOIN"
    DISPLAY_ONLY = "DISPLAY_ONLY"
    PROVIDER_REFERENCE = "PROVIDER_REFERENCE"
    POOL_REFERENCE = "POOL_REFERENCE"
    HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class JoinDecision:
    classification: JoinClass
    reason: str
    consumer_contract: str = CONSUMER_CONTRACT
    composer_version: str = JOIN_VERSION

    @property
    def permits_canonical_join(self) -> bool:
        return self.classification is JoinClass.CANONICAL_JOIN

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "reason": self.reason,
            "permits_canonical_join": self.permits_canonical_join,
            "identity_state_emitted": None,
            "consumer_contract": self.consumer_contract,
            "composer_version": self.composer_version,
        }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        raw = value.value
        text = str(raw).strip() if raw is not None else ""
        return text or None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _chain_key(chain: Any) -> str | None:
    text = _text(chain)
    return text.lower() if text else None


def _supported_chain(chain: Any) -> bool:
    key = _chain_key(chain)
    return key in _SUPPORTED_CHAINS


def _decision(classification: JoinClass, reason: str) -> JoinDecision:
    return JoinDecision(classification=classification, reason=reason)


def _canonical(resolution: IdentityResolution) -> JoinDecision:
    return _decision(JoinClass.CANONICAL_JOIN, "existing_identity_resolution_verified")


def _from_identity_state(state: IdentityState | None, *, reason: str) -> JoinDecision:
    if state is IdentityState.INVALID:
        return _decision(JoinClass.REJECTED, reason)
    if state is IdentityState.UNSUPPORTED:
        return _decision(JoinClass.REJECTED, reason)
    if state is IdentityState.VERIFIED:
        # VERIFIED without the structural IdentityResolution gate is not a join.
        return _decision(JoinClass.REJECTED, reason)
    return _decision(JoinClass.UNRESOLVED, reason)


def _classify_resolution(resolution: IdentityResolution) -> JoinDecision:
    if is_canonical_verified(resolution):
        return _canonical(resolution)
    token = resolution.token
    if not isinstance(token, TokenIdentity):
        return _decision(JoinClass.REJECTED, "malformed_resolution_missing_token")
    if token.state is IdentityState.VERIFIED:
        if not _text(token.token_id):
            return _decision(JoinClass.REJECTED, "verified_resolution_empty_token_id")
        if not _text(token.address_canonical):
            return _decision(JoinClass.REJECTED, "verified_resolution_missing_canonical_address")
        return _decision(JoinClass.REJECTED, "verified_resolution_failed_structural_gate")
    return _from_identity_state(token.state, reason=f"identity_state_{token.state.value.lower()}")


def _classify_token_address(addr: TokenAddress) -> JoinDecision:
    if addr.validation_state is IdentityState.VERIFIED:
        return _decision(JoinClass.REJECTED, "token_address_validation_state_is_not_authority")
    if not _supported_chain(addr.chain):
        return _decision(JoinClass.REJECTED, "unsupported_chain")
    if addr.validation_state is IdentityState.INVALID or not addr.address:
        return _decision(JoinClass.REJECTED, "token_address_invalid")
    if addr.validation_state is IdentityState.UNRESOLVED:
        return _decision(JoinClass.OPERATIONAL_JOIN, "validated_token_address_operational_only")
    return _decision(JoinClass.UNRESOLVED, "token_address_not_canonical")


def _classify_relationship(rel: IdentityRelationship) -> JoinDecision:
    if rel.kind in _HISTORICAL_KINDS:
        return _decision(JoinClass.HISTORICAL_REFERENCE, "historical_mapping_is_not_current_join")
    return _decision(JoinClass.UNRESOLVED, "relationship_is_not_authority")


def _classify_fallback(value: Any) -> JoinDecision:
    kind = value if isinstance(value, FallbackKind) else classify_fallback_key(value)
    if kind is FallbackKind.OTHER and _text(value) is None:
        return _decision(JoinClass.REJECTED, "missing_representation")
    return _decision(JoinClass.OPERATIONAL_JOIN, f"fallback_{kind.value.lower()}")


def _classify_subject(subject: Any) -> JoinDecision:
    if subject is None:
        return _decision(JoinClass.REJECTED, "missing_representation")
    if isinstance(subject, IdentityResolution):
        return _classify_resolution(subject)
    if isinstance(subject, CanonicalTokenId):
        return _decision(JoinClass.REJECTED, "canonical_token_id_wrapper_is_not_authority")
    if isinstance(subject, TokenIdNamespace):
        return _decision(JoinClass.OPERATIONAL_JOIN, "token_id_namespace_is_not_authority")
    if isinstance(subject, ResolutionVersionRef):
        return _decision(JoinClass.HISTORICAL_REFERENCE, "resolution_version_is_historical")
    if isinstance(subject, IdentityConflict):
        return _decision(JoinClass.UNRESOLVED, "provider_conflict_has_no_winner")
    if isinstance(subject, IdentityRelationship):
        return _classify_relationship(subject)
    if isinstance(subject, PoolAddress):
        return _decision(JoinClass.POOL_REFERENCE, "pool_is_not_token")
    if isinstance(subject, ProviderResourceRef):
        return _decision(JoinClass.PROVIDER_REFERENCE, "provider_resource_is_not_identity")
    if isinstance(subject, TokenAddress):
        return _classify_token_address(subject)
    if isinstance(subject, IdentityObservation):
        if subject.representation_kind in _SYMBOL_KINDS:
            return _decision(JoinClass.DISPLAY_ONLY, "symbol_name_alias_display_only")
        return _classify_subject(subject.original_value)
    if isinstance(subject, ResolutionPlan):
        if subject.status is ResolutionPlanStatus.INVALID:
            return _decision(JoinClass.REJECTED, "resolution_plan_invalid")
        if subject.status is ResolutionPlanStatus.UNSUPPORTED:
            return _decision(JoinClass.REJECTED, "resolution_plan_unsupported")
        if subject.status is ResolutionPlanStatus.MISSING:
            return _decision(JoinClass.REJECTED, "resolution_plan_missing")
        if subject.status is ResolutionPlanStatus.CONFLICT:
            return _decision(JoinClass.UNRESOLVED, "resolution_plan_conflict")
        return _classify_subject(subject.payload)
    if isinstance(subject, ResolutionInput):
        if subject.subject_kind is ResolutionSubjectKind.POOL or subject.pool_address is not None:
            if subject.token_address is None:
                return _decision(JoinClass.POOL_REFERENCE, "pool_representation")
            return _decision(JoinClass.UNRESOLVED, "pool_token_representation_mismatch")
        if subject.subject_kind is ResolutionSubjectKind.PROVIDER_RESOURCE or (
            subject.provider_ref is not None and subject.token_address is None
        ):
            return _decision(JoinClass.PROVIDER_REFERENCE, "provider_representation")
        if subject.fallback_kind is not None and subject.token_address is None:
            return _classify_fallback(subject.fallback_kind)
        if subject.symbol and subject.token_address is None:
            return _decision(JoinClass.DISPLAY_ONLY, "symbol_display_only")
        if subject.relationships and subject.token_address is None:
            return _classify_relationship(subject.relationships[0])
        if subject.token_address is not None:
            return _classify_token_address(subject.token_address)
        return _decision(JoinClass.UNRESOLVED, "resolution_input_not_canonical")
    if isinstance(subject, RepresentationKind):
        if subject in _SYMBOL_KINDS:
            return _decision(JoinClass.DISPLAY_ONLY, "symbol_name_alias_display_only")
        if subject is RepresentationKind.POOL_ADDRESS:
            return _decision(JoinClass.POOL_REFERENCE, "pool_kind")
        if subject is RepresentationKind.PROVIDER_RESOURCE:
            return _decision(JoinClass.PROVIDER_REFERENCE, "provider_kind")
        if subject is RepresentationKind.FALLBACK:
            return _decision(JoinClass.OPERATIONAL_JOIN, "fallback_kind")
        return _decision(JoinClass.UNRESOLVED, "representation_kind_not_canonical")
    if isinstance(subject, FallbackKind):
        return _classify_fallback(subject)
    if isinstance(subject, JoinClass):
        if subject is JoinClass.CANONICAL_JOIN:
            return _decision(JoinClass.REJECTED, "join_class_is_not_authority")
        return _decision(subject, "already_classified_non_canonical")
    if isinstance(subject, IdentityState):
        return _from_identity_state(subject, reason="identity_state_alone_is_not_authority")
    text = _text(subject)
    if text is None:
        return _decision(JoinClass.REJECTED, "malformed_representation")
    if text.lower() in _SYMBOL_KINDS or text in {k.value for k in _SYMBOL_KINDS}:
        return _decision(JoinClass.DISPLAY_ONLY, "symbol_name_alias_display_only")
    folded = classify_fallback_key(text)
    if folded is not FallbackKind.OTHER:
        return _classify_fallback(folded)
    if text.isupper() and ":" not in text and not text.startswith("0x"):
        return _decision(JoinClass.DISPLAY_ONLY, "symbol_display_only")
    return _decision(JoinClass.OPERATIONAL_JOIN, "opaque_operational_key")


def classify_canonical_join(
    subject: Any = None,
    *evidence: Any,
    resolution: Any = None,
) -> JoinDecision:
    """Classify whether a representation may participate in a canonical join.

    Only a legitimate existing IdentityResolution may return CANONICAL_JOIN.
    Extra evidence never upgrades a non-authoritative subject.
    """
    if is_canonical_verified(resolution):
        return _canonical(resolution)
    if isinstance(resolution, IdentityResolution):
        return _classify_resolution(resolution)

    parts = (subject,) + evidence
    for part in parts:
        if isinstance(part, IdentityResolution) and is_canonical_verified(part):
            return _canonical(part)

    if subject is None and not evidence:
        if resolution is None:
            return _decision(JoinClass.REJECTED, "missing_representation")
        return _classify_subject(resolution)

    primary = _classify_subject(subject if subject is not None else evidence[0])
    if primary.classification is JoinClass.CANONICAL_JOIN:
        candidate = subject if isinstance(subject, IdentityResolution) else None
        if candidate is not None and is_canonical_verified(candidate):
            return primary
        return _decision(JoinClass.REJECTED, "canonical_join_requires_identity_resolution")

    extras = [p for p in parts if p is not None]
    kinds = {type(p) for p in extras}
    if PoolAddress in kinds and TokenAddress in kinds:
        return _decision(JoinClass.UNRESOLVED, "pool_token_representation_mismatch")
    return primary


def permits_canonical_join(subject: Any = None, *evidence: Any, resolution: Any = None) -> bool:
    return classify_canonical_join(subject, *evidence, resolution=resolution).permits_canonical_join
