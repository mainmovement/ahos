#!/usr/bin/env python3
"""W4 Slice 2 — identity resolution planning contract.

Pure planning layer. Not an identity authority and not a replacement for
the existing architecture.identity.resolution authority.

representation → observation → candidates → requirements → plan
Existing IdentityResolution + VERIFIED remains the only canonical authority.

Do not import this module from the operational daemon or the pipeline.
Do not persist, hash, query providers, or call the existing resolver.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from architecture.identity.fusion import (
    CanonicalTokenId,
    FallbackKind,
    IdentityObservation,
    IdentityRelationship,
    PoolAddress,
    ProviderResourceRef,
    RelationshipKind,
    RepresentationKind,
    TokenAddress,
    classify_fallback_key,
    classify_gecko_new_pool_item,
    copy_canonical_token_id,
    fallback_may_be_canonical,
    identity_observation,
    identity_relationship,
    is_canonical_verified,
    pool_address,
    provider_resource_ref,
    token_address,
)
from architecture.identity.types import IdentityResolution, IdentityState
from architecture.identity.validate import EVM_CHAINS

CONTRACT_VERSION = "identity-resolution-contract-v1"

CONSUMER_CONTRACT = (
    "This module plans resolution. It does not resolve identity. "
    "READY_FOR_RESOLUTION means the existing IdentityResolution authority "
    "could be asked later. It is not VERIFIED. "
    "Only is_canonical_verified(IdentityResolution) may classify canonical "
    "join. CanonicalTokenId wrappers, symbols, pools, provider IDs, "
    "fallbacks, and relationships never grant VERIFIED."
)

CANONICALIZATION_BOUNDARY = (
    "operational representation",
    "resolution planning",
    "existing IdentityResolution authority",
    "VERIFIED",
    "canonical join permitted",
)


class ResolutionSubjectKind(str, Enum):
    TOKEN = "TOKEN"
    POOL = "POOL"
    PROVIDER_RESOURCE = "PROVIDER_RESOURCE"
    ALIAS = "ALIAS"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"


class EvidenceKind(str, Enum):
    VALIDATED_ADDRESS = "VALIDATED_ADDRESS"
    PROVIDER_AGREEMENT = "PROVIDER_AGREEMENT"
    PROVIDER_DISAGREEMENT = "PROVIDER_DISAGREEMENT"
    TOKEN_RELATIONSHIP = "TOKEN_RELATIONSHIP"
    POOL_BASE_TOKEN = "POOL_BASE_TOKEN"
    POOL_QUOTE_TOKEN = "POOL_QUOTE_TOKEN"
    ALIAS = "ALIAS"
    HISTORICAL_MAPPING = "HISTORICAL_MAPPING"
    USER_MAPPING = "USER_MAPPING"


class ResolutionPlanStatus(str, Enum):
    """Planning status. Not IdentityState. Never VERIFIED."""

    READY_FOR_RESOLUTION = "READY_FOR_RESOLUTION"
    UNRESOLVED = "UNRESOLVED"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


_SUPPORTED_CHAIN_KEYS = frozenset(EVM_CHAINS) | {"solana"}
_HISTORICAL_KINDS = frozenset({
    RelationshipKind.MIGRATES_TO,
    RelationshipKind.SUCCEEDS,
    RelationshipKind.SUPERSEDED,
    RelationshipKind.WRAPS,
    RelationshipKind.BRIDGES_TO,
    RelationshipKind.PROXIES,
})


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


def _chain_key(chain: str | None) -> str | None:
    text = _text(chain)
    return text.lower() if text else None


def _supported_chain(chain: str | None) -> bool:
    key = _chain_key(chain)
    return key in _SUPPORTED_CHAIN_KEYS


def _freeze_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): value[k] for k in value})
    return MappingProxyType({})


def _deep_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_plain(value[k]) for k in value}
    if isinstance(value, (list, tuple)):
        return [_deep_plain(v) for v in value]
    return value


def address_validation_usable(addr: TokenAddress | PoolAddress | None) -> bool:
    """Delegate: existing validator UNRESOLVED means charset/length usable, not VERIFIED."""
    if addr is None:
        return False
    return addr.validation_state is IdentityState.UNRESOLVED


def solana_case_preserved(addr: TokenAddress | None) -> bool:
    if addr is None:
        return True
    if _chain_key(addr.chain) != "solana":
        return True
    raw = addr.address_input
    stored = addr.address
    if raw is None or not stored:
        return False
    return stored == raw and stored != raw.lower()


@dataclass(frozen=True)
class ResolutionInput:
    """Observed representation. Never a canonical identity."""

    chain: str | None
    representation_kind: RepresentationKind
    subject_kind: ResolutionSubjectKind
    original_value: str | None
    operational_value: str | None
    provider: str | None
    source: str | None
    symbol: str | None
    name: str | None
    token_address: TokenAddress | None
    pool_address: PoolAddress | None
    provider_ref: ProviderResourceRef | None
    observation: IdentityObservation | None
    relationships: tuple[IdentityRelationship, ...]
    fallback_kind: FallbackKind | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain,
            "representation_kind": self.representation_kind.value,
            "subject_kind": self.subject_kind.value,
            "original_value": self.original_value,
            "operational_value": self.operational_value,
            "provider": self.provider,
            "source": self.source,
            "symbol": self.symbol,
            "name": self.name,
            "token_address": self.token_address.as_dict() if self.token_address else None,
            "pool_address": self.pool_address.as_dict() if self.pool_address else None,
            "provider_ref": self.provider_ref.as_dict() if self.provider_ref else None,
            "observation": self.observation.as_dict() if self.observation else None,
            "relationships": [r.as_dict() for r in self.relationships],
            "fallback_kind": self.fallback_kind.value if self.fallback_kind else None,
            "is_canonical": False,
        }


@dataclass(frozen=True)
class ResolutionEvidence:
    kind: EvidenceKind
    detail: Mapping[str, Any]
    source: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "detail": _deep_plain(self.detail),
            "source": self.source,
            "produces_verified": False,
        }


def resolution_evidence(
    kind: EvidenceKind | str,
    detail: Mapping[str, Any] | None = None,
    source: Any = None,
) -> ResolutionEvidence:
    if isinstance(kind, EvidenceKind):
        ev = kind
    else:
        text = _text(kind)
        ev = (
            EvidenceKind(text)
            if text in EvidenceKind._value2member_map_
            else EvidenceKind.ALIAS
        )
    return ResolutionEvidence(kind=ev, detail=_freeze_mapping(detail or {}), source=_text(source))


@dataclass(frozen=True)
class ResolutionCandidate:
    subject_kind: ResolutionSubjectKind
    chain: str | None
    token_address: TokenAddress | None = None
    pool_address: PoolAddress | None = None
    provider_ref: ProviderResourceRef | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_kind": self.subject_kind.value,
            "chain": self.chain,
            "token_address": self.token_address.as_dict() if self.token_address else None,
            "pool_address": self.pool_address.as_dict() if self.pool_address else None,
            "provider_ref": self.provider_ref.as_dict() if self.provider_ref else None,
        }


def token_candidate(addr: TokenAddress) -> ResolutionCandidate:
    return ResolutionCandidate(
        subject_kind=ResolutionSubjectKind.TOKEN,
        chain=addr.chain,
        token_address=addr,
    )


def pool_candidate(addr: PoolAddress) -> ResolutionCandidate:
    return ResolutionCandidate(
        subject_kind=ResolutionSubjectKind.POOL,
        chain=addr.chain,
        pool_address=addr,
    )


def provider_candidate(ref: ProviderResourceRef, chain: str | None = None) -> ResolutionCandidate:
    return ResolutionCandidate(
        subject_kind=ResolutionSubjectKind.PROVIDER_RESOURCE,
        chain=chain,
        provider_ref=ref,
    )


@dataclass(frozen=True)
class ResolutionRequirement:
    chain_supported: bool
    subject_is_token: bool
    address_present: bool
    address_usable: bool
    solana_case_ok: bool
    symbol_alone_insufficient: bool
    provider_id_alone_insufficient: bool
    pool_alone_insufficient: bool
    fallback_alone_insufficient: bool
    relationship_alone_insufficient: bool
    unvalidated_token_id_insufficient: bool
    no_provider_disagreement: bool
    canonical_requires_existing_resolution: bool
    verified_required_for_canonical: bool

    @property
    def ready(self) -> bool:
        return (
            self.chain_supported
            and self.subject_is_token
            and self.address_present
            and self.address_usable
            and self.solana_case_ok
            and self.no_provider_disagreement
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "chain_supported": self.chain_supported,
            "subject_is_token": self.subject_is_token,
            "address_present": self.address_present,
            "address_usable": self.address_usable,
            "solana_case_ok": self.solana_case_ok,
            "symbol_alone_insufficient": self.symbol_alone_insufficient,
            "provider_id_alone_insufficient": self.provider_id_alone_insufficient,
            "pool_alone_insufficient": self.pool_alone_insufficient,
            "fallback_alone_insufficient": self.fallback_alone_insufficient,
            "relationship_alone_insufficient": self.relationship_alone_insufficient,
            "unvalidated_token_id_insufficient": self.unvalidated_token_id_insufficient,
            "no_provider_disagreement": self.no_provider_disagreement,
            "canonical_requires_existing_resolution": self.canonical_requires_existing_resolution,
            "verified_required_for_canonical": self.verified_required_for_canonical,
            "ready": self.ready,
        }


@dataclass(frozen=True)
class ResolutionPlan:
    status: ResolutionPlanStatus
    payload: ResolutionInput
    evidence: tuple[ResolutionEvidence, ...]
    candidates: tuple[ResolutionCandidate, ...]
    requirements: ResolutionRequirement
    reasons: tuple[str, ...]
    existing_canonical: bool
    consumer_contract: str = CONSUMER_CONTRACT
    composer_version: str = CONTRACT_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "input": self.payload.as_dict(),
            "evidence": [e.as_dict() for e in self.evidence],
            "candidates": [c.as_dict() for c in self.candidates],
            "requirements": self.requirements.as_dict(),
            "reasons": list(self.reasons),
            "existing_canonical": self.existing_canonical,
            "identity_state_emitted": None,
            "consumer_contract": self.consumer_contract,
            "composer_version": self.composer_version,
        }


def compose_resolution_input(
    *,
    chain: Any = None,
    representation_kind: Any = None,
    subject_kind: Any = None,
    original_value: Any = None,
    operational_value: Any = None,
    provider: Any = None,
    source: Any = None,
    symbol: Any = None,
    name: Any = None,
    token_addr: TokenAddress | None = None,
    pool_addr: PoolAddress | None = None,
    provider_ref: ProviderResourceRef | None = None,
    observation: IdentityObservation | None = None,
    relationships: Iterable[IdentityRelationship] | None = None,
    fallback_kind: FallbackKind | None = None,
) -> ResolutionInput:
    kind = representation_kind
    if not isinstance(kind, RepresentationKind):
        text = _text(kind)
        kind = (
            RepresentationKind(text)
            if text in RepresentationKind._value2member_map_
            else RepresentationKind.FALLBACK
        )
    subject = subject_kind
    if not isinstance(subject, ResolutionSubjectKind):
        text = _text(subject)
        subject = (
            ResolutionSubjectKind(text)
            if text in ResolutionSubjectKind._value2member_map_
            else ResolutionSubjectKind.UNKNOWN
        )
    if token_addr is not None:
        subject = ResolutionSubjectKind.TOKEN
        kind = RepresentationKind.TOKEN_ADDRESS
    elif pool_addr is not None and provider_ref is None:
        subject = ResolutionSubjectKind.POOL
        kind = RepresentationKind.POOL_ADDRESS
    elif provider_ref is not None and token_addr is None and pool_addr is None:
        subject = ResolutionSubjectKind.PROVIDER_RESOURCE
        kind = RepresentationKind.PROVIDER_RESOURCE
    return ResolutionInput(
        chain=_text(chain) or (token_addr.chain if token_addr else None) or (pool_addr.chain if pool_addr else None),
        representation_kind=kind,
        subject_kind=subject,
        original_value=_text(original_value),
        operational_value=_text(operational_value),
        provider=_text(provider),
        source=_text(source),
        symbol=_text(symbol),
        name=_text(name),
        token_address=token_addr,
        pool_address=pool_addr,
        provider_ref=provider_ref,
        observation=observation,
        relationships=tuple(relationships or ()),
        fallback_kind=fallback_kind,
    )


def _token_keys(candidates: Iterable[ResolutionCandidate]) -> set[tuple[str | None, str]]:
    keys: set[tuple[str | None, str]] = set()
    for cand in candidates:
        if cand.subject_kind is not ResolutionSubjectKind.TOKEN or cand.token_address is None:
            continue
        keys.add((_chain_key(cand.token_address.chain), cand.token_address.address))
    return keys


def _build_requirements(
    payload: ResolutionInput,
    candidates: tuple[ResolutionCandidate, ...],
    *,
    disagreement: bool,
) -> ResolutionRequirement:
    token_cands = tuple(c for c in candidates if c.subject_kind is ResolutionSubjectKind.TOKEN)
    token_addr = token_cands[0].token_address if token_cands else payload.token_address
    chain = payload.chain or (token_addr.chain if token_addr else None)
    symbol_only = (
        payload.symbol is not None
        and token_addr is None
        and payload.pool_address is None
    )
    provider_only = (
        payload.provider_ref is not None
        and token_addr is None
        and payload.subject_kind is ResolutionSubjectKind.PROVIDER_RESOURCE
    )
    pool_only = token_addr is None and payload.pool_address is not None
    fallback_only = payload.fallback_kind is not None and token_addr is None
    rel_only = bool(payload.relationships) and token_addr is None
    unvalidated = (
        payload.fallback_kind is FallbackKind.UNVALIDATED_TOKEN_ID
        and token_addr is None
    )
    return ResolutionRequirement(
        chain_supported=_supported_chain(chain),
        subject_is_token=token_addr is not None and any(
            c.subject_kind is ResolutionSubjectKind.TOKEN for c in candidates
        ),
        address_present=token_addr is not None and bool(token_addr.address),
        address_usable=address_validation_usable(token_addr),
        solana_case_ok=solana_case_preserved(token_addr) if token_addr is not None else True,
        symbol_alone_insufficient=True,
        provider_id_alone_insufficient=True,
        pool_alone_insufficient=True,
        fallback_alone_insufficient=True,
        relationship_alone_insufficient=True,
        unvalidated_token_id_insufficient=True,
        no_provider_disagreement=not disagreement,
        canonical_requires_existing_resolution=True,
        verified_required_for_canonical=True,
    )


def _status_for(
    payload: ResolutionInput,
    req: ResolutionRequirement,
    candidates: tuple[ResolutionCandidate, ...],
    *,
    disagreement: bool,
    stale: bool,
) -> tuple[ResolutionPlanStatus, tuple[str, ...]]:
    reasons: list[str] = []
    if stale:
        reasons.append("identity_evidence_stale")
        return ResolutionPlanStatus.STALE, tuple(reasons)
    if disagreement:
        reasons.append("provider_address_disagreement")
        return ResolutionPlanStatus.CONFLICT, tuple(reasons)
    if not candidates and payload.token_address is None and payload.pool_address is None:
        if payload.symbol or payload.name or payload.fallback_kind is not None:
            reasons.append("symbol_or_fallback_not_identity")
            return ResolutionPlanStatus.AMBIGUOUS, tuple(reasons)
        if payload.relationships:
            reasons.append("relationship_is_not_authority")
            return ResolutionPlanStatus.UNRESOLVED, tuple(reasons)
        reasons.append("missing_representation")
        return ResolutionPlanStatus.MISSING, tuple(reasons)
    chain = payload.chain or (
        payload.token_address.chain if payload.token_address is not None else None
    )
    if chain and not _supported_chain(chain):
        reasons.append("unsupported_chain")
        return ResolutionPlanStatus.UNSUPPORTED, tuple(reasons)
    if payload.token_address is not None and payload.token_address.validation_state is IdentityState.INVALID:
        reasons.append("token_address_invalid")
        return ResolutionPlanStatus.INVALID, tuple(reasons)
    if req.ready:
        reasons.append("ready_for_existing_resolver_not_verified")
        return ResolutionPlanStatus.READY_FOR_RESOLUTION, tuple(reasons)
    if payload.token_address is None and payload.pool_address is not None:
        reasons.append("pool_without_token")
        return ResolutionPlanStatus.UNRESOLVED, tuple(reasons)
    if payload.symbol and payload.token_address is None:
        reasons.append("symbol_cannot_select_entity")
        return ResolutionPlanStatus.AMBIGUOUS, tuple(reasons)
    reasons.append("insufficient_for_resolution")
    return ResolutionPlanStatus.UNRESOLVED, tuple(reasons)


def plan_resolution(
    payload: ResolutionInput,
    *,
    extra_evidence: Iterable[ResolutionEvidence] | None = None,
    extra_candidates: Iterable[ResolutionCandidate] | None = None,
    existing_resolution: Any = None,
    stale: bool = False,
) -> ResolutionPlan:
    """Classify what would be required. Never emits VERIFIED. Never hashes."""
    evidence = list(extra_evidence or ())
    candidates = list(extra_candidates or ())
    if payload.token_address is not None:
        candidates.append(token_candidate(payload.token_address))
        if address_validation_usable(payload.token_address):
            evidence.append(resolution_evidence(
                EvidenceKind.VALIDATED_ADDRESS,
                {"chain": payload.token_address.chain, "address": payload.token_address.address},
                payload.source,
            ))
    if payload.pool_address is not None:
        candidates.append(pool_candidate(payload.pool_address))
    if payload.provider_ref is not None:
        candidates.append(provider_candidate(payload.provider_ref, payload.chain))
    for rel in payload.relationships:
        if rel.kind in _HISTORICAL_KINDS:
            evidence.append(resolution_evidence(
                EvidenceKind.HISTORICAL_MAPPING,
                rel.as_dict(),
                payload.source,
            ))
        elif rel.kind is RelationshipKind.ALIASES:
            evidence.append(resolution_evidence(EvidenceKind.ALIAS, rel.as_dict(), payload.source))
        else:
            evidence.append(resolution_evidence(EvidenceKind.TOKEN_RELATIONSHIP, rel.as_dict(), payload.source))
    token_keys = _token_keys(candidates)
    disagreement = len(token_keys) > 1
    if disagreement:
        evidence.append(resolution_evidence(
            EvidenceKind.PROVIDER_DISAGREEMENT,
            {"addresses": sorted(f"{c}:{a}" for c, a in token_keys)},
            payload.source,
        ))
    elif len(token_keys) == 1 and sum(1 for c in candidates if c.subject_kind is ResolutionSubjectKind.TOKEN) > 1:
        evidence.append(resolution_evidence(EvidenceKind.PROVIDER_AGREEMENT, {}, payload.source))
    cand_tuple = tuple(candidates)
    ev_tuple = tuple(evidence)
    req = _build_requirements(payload, cand_tuple, disagreement=disagreement)
    status, reasons = _status_for(payload, req, cand_tuple, disagreement=disagreement, stale=stale)
    existing = is_canonical_verified(existing_resolution)
    if status is ResolutionPlanStatus.READY_FOR_RESOLUTION:
        reasons = reasons + ("plan_is_not_verified",)
    return ResolutionPlan(
        status=status,
        payload=payload,
        evidence=ev_tuple,
        candidates=cand_tuple,
        requirements=req,
        reasons=reasons,
        existing_canonical=existing,
    )


def plan_token_address(chain: Any, address: Any, *, source: Any = None) -> ResolutionPlan:
    addr = token_address(chain, address)
    obs = identity_observation(
        source=source,
        representation_kind=RepresentationKind.TOKEN_ADDRESS,
        original_value=addr.address_input,
        normalized_value=addr.address,
    )
    payload = compose_resolution_input(
        chain=chain,
        token_addr=addr,
        source=source,
        original_value=addr.address_input,
        operational_value=addr.address,
        observation=obs,
    )
    return plan_resolution(payload)


def plan_pool_address(chain: Any, address: Any, *, source: Any = None) -> ResolutionPlan:
    addr = pool_address(chain, address)
    payload = compose_resolution_input(
        chain=chain,
        pool_addr=addr,
        source=source,
        original_value=addr.address_input,
        operational_value=addr.address,
    )
    return plan_resolution(payload)


def plan_provider_resource(provider: Any, value: Any, *, chain: Any = None) -> ResolutionPlan:
    ref = provider_resource_ref(provider, value, "resource")
    payload = compose_resolution_input(chain=chain, provider_ref=ref, original_value=_text(value))
    return plan_resolution(payload)


def plan_symbol(symbol: Any, *, chain: Any = None, name: Any = None) -> ResolutionPlan:
    payload = compose_resolution_input(
        chain=chain,
        representation_kind=RepresentationKind.SYMBOL,
        subject_kind=ResolutionSubjectKind.ALIAS,
        symbol=symbol,
        name=name,
        original_value=symbol,
    )
    return plan_resolution(payload)


def plan_fallback(value: Any) -> ResolutionPlan:
    raw = _text(value)
    kind = classify_fallback_key(raw)
    payload = compose_resolution_input(
        representation_kind=RepresentationKind.FALLBACK,
        subject_kind=ResolutionSubjectKind.FALLBACK,
        original_value=raw,
        operational_value=raw,
        fallback_kind=kind,
    )
    return plan_resolution(payload)


def plan_gecko_new_pool(item: Mapping[str, Any] | None, *, network_chain: Any = None) -> ResolutionPlan:
    """Planning map of the known Gecko new_pools shape. Does not patch the adapter."""
    if not isinstance(item, Mapping):
        item = None
    classified = classify_gecko_new_pool_item(item)
    raw = item or {}
    attrs = raw.get("attributes") if isinstance(raw.get("attributes"), Mapping) else {}
    pool = classified.pool_address
    if pool is None:
        pool_raw = _text(attrs.get("address") if isinstance(attrs, Mapping) else None)
        chain = _text(network_chain) or (
            classified.base_token_address.chain if classified.base_token_address else None
        )
        if pool_raw and chain:
            pool = pool_address(chain, pool_raw)
    token = classified.base_token_address
    evidence: list[ResolutionEvidence] = []
    if classified.quote_token_address is not None:
        # Quote is relationship evidence only. It must not compete as a
        # resolution-satisfying token candidate (that would invent CONFLICT
        # or silently resolve the pool via the quote mint).
        evidence.append(resolution_evidence(
            EvidenceKind.POOL_QUOTE_TOKEN,
            classified.quote_token_address.as_dict(),
            "geckoterminal",
        ))
    if token is not None and pool is not None:
        evidence.append(resolution_evidence(
            EvidenceKind.POOL_BASE_TOKEN,
            {"pool": pool.address, "base": token.address},
            "geckoterminal",
        ))
    payload = compose_resolution_input(
        chain=(token.chain if token else None) or (pool.chain if pool else None) or _text(network_chain),
        token_addr=token,
        pool_addr=pool,
        provider_ref=classified.provider_pool_id,
        source="geckoterminal",
        original_value=pool.address_input if pool else None,
        symbol=_text(attrs.get("name") if isinstance(attrs, Mapping) else None),
    )
    return plan_resolution(payload, extra_evidence=evidence)


def plan_provider_disagreement(
    chain: Any,
    addresses: Mapping[str, Any],
) -> ResolutionPlan:
    """Preserve disagreement. Does not pick a winner."""
    extra: list[ResolutionCandidate] = []
    for provider, addr in addresses.items():
        extra.append(
            ResolutionCandidate(
                subject_kind=ResolutionSubjectKind.TOKEN,
                chain=_text(chain),
                token_address=token_address(chain, addr),
                provider_ref=provider_resource_ref(provider, addr, "address"),
            )
        )
    vals = [_text(v) for v in addresses.values()]
    first = next((v for v in vals if v), None)
    payload = compose_resolution_input(
        chain=chain,
        token_addr=token_address(chain, first) if first else None,
        source="providers",
        original_value=first,
    )
    return plan_resolution(payload, extra_candidates=extra)


def plan_historical_mapping(
    relationship: IdentityRelationship,
    *,
    original: ResolutionInput | None = None,
) -> ResolutionPlan:
    """Append-only mapping evidence. Does not rewrite the original identity."""
    payload = original or compose_resolution_input(
        representation_kind=RepresentationKind.OPERATIONAL_KEY,
        subject_kind=ResolutionSubjectKind.UNKNOWN,
        relationships=(relationship,),
        original_value="historical",
    )
    if original is not None and relationship not in original.relationships:
        payload = compose_resolution_input(
            chain=original.chain,
            representation_kind=original.representation_kind,
            subject_kind=original.subject_kind,
            original_value=original.original_value,
            operational_value=original.operational_value,
            provider=original.provider,
            source=original.source,
            symbol=original.symbol,
            name=original.name,
            token_addr=original.token_address,
            pool_addr=original.pool_address,
            provider_ref=original.provider_ref,
            observation=original.observation,
            relationships=original.relationships + (relationship,),
            fallback_kind=original.fallback_kind,
        )
    return plan_resolution(payload)


def authoritative_canonical(resolution: Any) -> bool:
    """Only the existing IdentityResolution classifier. Not CanonicalTokenId."""
    if isinstance(resolution, CanonicalTokenId):
        return False
    return is_canonical_verified(resolution)


def copy_canonical_if_authoritative(resolution: Any) -> CanonicalTokenId | None:
    if not authoritative_canonical(resolution):
        return None
    return copy_canonical_token_id(resolution)


def plan_promotes_to_verified(plan: ResolutionPlan) -> bool:
    """Invariant: planning never emits or upgrades to VERIFIED."""
    if plan.status.value == IdentityState.VERIFIED.value:
        return True
    if "VERIFIED" in plan.status.value:
        return True
    exported = plan.as_dict()
    if exported.get("identity_state_emitted") is not None:
        return True
    if exported.get("status") == IdentityState.VERIFIED.value:
        return True
    return False


def relationship_is_authority(_relationship: IdentityRelationship | None) -> bool:
    return False


def fallback_is_canonical(kind: FallbackKind | str | None) -> bool:
    return fallback_may_be_canonical(kind)
