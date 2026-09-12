#!/usr/bin/env python3
"""W4 Slice 1 — typed identity foundation (refined Option D).

Isolated research/analytical contracts. Not an identity authority.

Do not import this module from the operational daemon or the pipeline.
Do not persist, resolve providers, hash Lane A token_id, or trade from here.

Reuses existing IdentityState / IdentityResolution / TokenIdentity and the
Lane B address validators. Does not replace the existing resolution function.
Does not import discovery, runtime, scoring, security, calibration, or W1/W2/W3.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from architecture.identity.validate import EVM_CHAINS, validate_address_for_chain

FUSION_VERSION = "identity-fusion-foundation-v1"

CONSUMER_CONTRACT = (
    "These types classify representations. They do not resolve identity. "
    "Only a structurally valid IdentityResolution with token.state=VERIFIED "
    "and a non-empty token.token_id may be treated as CANONICAL_TOKEN+VERIFIED. "
    "token_id is a deterministic namespace. canonical_token_id is a copy of "
    "that token_id under VERIFIED. Relationships, symbols, pools, provider "
    "IDs, fallbacks, and search folds never grant canonical identity."
)


class RepresentationKind(str, Enum):
    TOKEN_ADDRESS = "TOKEN_ADDRESS"
    POOL_ADDRESS = "POOL_ADDRESS"
    PROVIDER_RESOURCE = "PROVIDER_RESOURCE"
    SYMBOL = "SYMBOL"
    NAME = "NAME"
    ALIAS = "ALIAS"
    OPERATIONAL_KEY = "OPERATIONAL_KEY"
    FALLBACK = "FALLBACK"


class RelationshipKind(str, Enum):
    IDENTITY = "IDENTITY"
    OBSERVED_AS = "OBSERVED_AS"
    PAIRS_WITH = "PAIRS_WITH"
    CONTAINS = "CONTAINS"
    QUOTES = "QUOTES"
    WRAPS = "WRAPS"
    BRIDGES_TO = "BRIDGES_TO"
    MIGRATES_TO = "MIGRATES_TO"
    SUCCEEDS = "SUCCEEDS"
    PROXIES = "PROXIES"
    ALIASES = "ALIASES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    SUPERSEDED = "SUPERSEDED"


class FallbackKind(str, Enum):
    CHAIN_UNKNOWN = "CHAIN_UNKNOWN"
    CHAIN_SYM_SYMBOL = "CHAIN_SYM_SYMBOL"
    CHAIN_SYMBOL = "CHAIN_SYMBOL"
    MANUAL_SYMBOL = "MANUAL_SYMBOL"
    UNVALIDATED_TOKEN_ID = "UNVALIDATED_TOKEN_ID"
    OTHER = "OTHER"


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(value[k]) for k in value})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(v) for v in value)
    try:
        return deepcopy(value)
    except Exception:
        return MappingProxyType({
            "untrusted": True,
            "value_type": type(value).__name__,
            "note": "non-deepcopyable object discarded; not authoritative",
        })


def _freeze_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze_value(value[k]) for k in value})
    return MappingProxyType({})


def _deep_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_plain(value[k]) for k in value}
    if isinstance(value, (list, tuple)):
        return [_deep_plain(v) for v in value]
    return value


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


def _validate_onchain(chain: str | None, address: str | None) -> tuple[IdentityState, str, str | None]:
    key = _chain_key(chain)
    raw = _text(address)
    if key is None:
        return IdentityState.INVALID, "missing_chain", raw
    if raw is None:
        return IdentityState.INVALID, "missing_address", None
    if key in EVM_CHAINS or key == "solana":
        state, reason, canonical, _checksum = validate_address_for_chain(key, raw)
        return state, reason, canonical
    return IdentityState.UNRESOLVED, "chain_no_extra_validator", raw


@dataclass(frozen=True)
class TokenAddress:
    """On-chain token contract/mint. Never a pool or provider resource."""

    chain: str
    address: str
    address_input: str | None
    validation_state: IdentityState
    validation_reason: str
    entity_kind: str = "TOKEN"

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity_kind": self.entity_kind,
            "chain": self.chain,
            "address": self.address,
            "address_input": self.address_input,
            "validation_state": self.validation_state.value,
            "validation_reason": self.validation_reason,
        }


@dataclass(frozen=True)
class PoolAddress:
    """On-chain pool/pair address. Never a token mint."""

    chain: str
    address: str
    address_input: str | None
    validation_state: IdentityState
    validation_reason: str
    entity_kind: str = "POOL"

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity_kind": self.entity_kind,
            "chain": self.chain,
            "address": self.address,
            "address_input": self.address_input,
            "validation_state": self.validation_state.value,
            "validation_reason": self.validation_reason,
        }


def token_address(chain: Any, address: Any) -> TokenAddress:
    """Compose a TokenAddress. Validates; does not hash; does not lowercase Solana."""
    chain_text = _text(chain) or ""
    raw = _text(address)
    state, reason, canonical = _validate_onchain(chain_text or None, raw)
    stored = canonical if canonical is not None else (raw or "")
    return TokenAddress(
        chain=chain_text,
        address=stored,
        address_input=raw,
        validation_state=state,
        validation_reason=reason,
    )


def pool_address(chain: Any, address: Any) -> PoolAddress:
    """Compose a PoolAddress. Same charset rules; different entity type."""
    chain_text = _text(chain) or ""
    raw = _text(address)
    state, reason, canonical = _validate_onchain(chain_text or None, raw)
    stored = canonical if canonical is not None else (raw or "")
    return PoolAddress(
        chain=chain_text,
        address=stored,
        address_input=raw,
        validation_state=state,
        validation_reason=reason,
    )


@dataclass(frozen=True)
class ProviderResourceRef:
    """Provider-specific resource. Must never mint token_id."""

    provider: str
    value: str
    resource_kind: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "value": self.value,
            "resource_kind": self.resource_kind,
            "entity_kind": "PROVIDER_RESOURCE",
        }


def provider_resource_ref(provider: Any, value: Any, resource_kind: Any = None) -> ProviderResourceRef:
    return ProviderResourceRef(
        provider=_text(provider) or "",
        value=_text(value) or "",
        resource_kind=_text(resource_kind),
    )


@dataclass(frozen=True)
class TokenRepresentation:
    token_address: TokenAddress | None
    symbol: str | None
    name: str | None
    provider_ref: ProviderResourceRef | None
    source: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "token_address": self.token_address.as_dict() if self.token_address else None,
            "symbol": self.symbol,
            "name": self.name,
            "provider_ref": self.provider_ref.as_dict() if self.provider_ref else None,
            "source": self.source,
        }


def token_representation(
    *,
    token_addr: TokenAddress | None = None,
    symbol: Any = None,
    name: Any = None,
    provider_ref: ProviderResourceRef | None = None,
    source: Any = None,
) -> TokenRepresentation:
    return TokenRepresentation(
        token_address=token_addr,
        symbol=_text(symbol),
        name=_text(name),
        provider_ref=provider_ref,
        source=_text(source),
    )


@dataclass(frozen=True)
class PoolRepresentation:
    pool_address: PoolAddress | None
    provider_pool_id: ProviderResourceRef | None
    base_token_address: TokenAddress | None
    quote_token_address: TokenAddress | None
    source: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "pool_address": self.pool_address.as_dict() if self.pool_address else None,
            "provider_pool_id": self.provider_pool_id.as_dict() if self.provider_pool_id else None,
            "base_token_address": self.base_token_address.as_dict() if self.base_token_address else None,
            "quote_token_address": self.quote_token_address.as_dict() if self.quote_token_address else None,
            "source": self.source,
        }


def pool_representation(
    *,
    pool_addr: PoolAddress | None = None,
    provider_pool_id: ProviderResourceRef | None = None,
    base_token_address: TokenAddress | None = None,
    quote_token_address: TokenAddress | None = None,
    source: Any = None,
) -> PoolRepresentation:
    return PoolRepresentation(
        pool_address=pool_addr,
        provider_pool_id=provider_pool_id,
        base_token_address=base_token_address,
        quote_token_address=quote_token_address,
        source=_text(source),
    )


def distinct_entity_types(token: TokenAddress | None, pool: PoolAddress | None) -> bool:
    """Even identical address strings remain different entity types."""
    if token is None or pool is None:
        return True
    return type(token) is not type(pool)


@dataclass(frozen=True)
class IdentityObservation:
    source: str | None
    representation_kind: RepresentationKind
    original_value: str | None
    normalized_value: str | None
    observed_at: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "representation_kind": self.representation_kind.value,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "observed_at": self.observed_at,
        }


def identity_observation(
    *,
    source: Any = None,
    representation_kind: Any = None,
    original_value: Any = None,
    normalized_value: Any = None,
    observed_at: Any = None,
) -> IdentityObservation:
    """Compose an observation. Does not invent time, source, or confidence."""
    kind = representation_kind
    if not isinstance(kind, RepresentationKind):
        text = _text(kind)
        kind = RepresentationKind(text) if text in RepresentationKind._value2member_map_ else RepresentationKind.FALLBACK
    ts: float | None
    if observed_at is None:
        ts = None
    elif isinstance(observed_at, bool):
        ts = None
    elif isinstance(observed_at, (int, float)):
        ts = float(observed_at)
    else:
        ts = None
    return IdentityObservation(
        source=_text(source),
        representation_kind=kind,
        original_value=_text(original_value),
        normalized_value=_text(normalized_value),
        observed_at=ts,
    )


@dataclass(frozen=True)
class IdentityRelationship:
    kind: RelationshipKind
    left: Mapping[str, Any]
    right: Mapping[str, Any]
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "left": _deep_plain(self.left),
            "right": _deep_plain(self.right),
            "note": self.note,
            "grants_canonical_identity": False,
        }


def identity_relationship(
    kind: Any,
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
    note: Any = None,
) -> IdentityRelationship:
    if isinstance(kind, RelationshipKind):
        rel = kind
    else:
        text = _text(kind)
        try:
            rel = RelationshipKind(text)
        except ValueError:
            rel = RelationshipKind.OBSERVED_AS
    return IdentityRelationship(
        kind=rel,
        left=_freeze_mapping(left or {}),
        right=_freeze_mapping(right or {}),
        note=_text(note),
    )


def relationship_grants_canonical(relationship: IdentityRelationship | None) -> bool:
    return False


@dataclass(frozen=True)
class IdentityConflict:
    source: str | None
    left: Mapping[str, Any]
    right: Mapping[str, Any]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "left": _deep_plain(self.left),
            "right": _deep_plain(self.right),
            "reason": self.reason,
            "winner": None,
        }


def identity_conflict(
    *,
    source: Any = None,
    left: Mapping[str, Any] | None = None,
    right: Mapping[str, Any] | None = None,
    reason: Any = None,
) -> IdentityConflict:
    return IdentityConflict(
        source=_text(source),
        left=_freeze_mapping(left or {}),
        right=_freeze_mapping(right or {}),
        reason=_text(reason) or "unspecified_conflict",
    )


@dataclass(frozen=True)
class TokenIdNamespace:
    """Deterministic Lane A hash namespace value. Not authority."""

    value: str

    def as_dict(self) -> dict[str, Any]:
        return {"value": self.value, "authoritative": False, "kind": "token_id_namespace"}


@dataclass(frozen=True)
class CanonicalTokenId:
    """token_id copied from a VERIFIED IdentityResolution. Not minted here."""

    value: str
    resolution_version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "authoritative": True,
            "kind": "canonical_token_id",
            "resolution_version": self.resolution_version,
        }


@dataclass(frozen=True)
class ResolutionVersionRef:
    """Versioned assertion pointer. Does not mutate the underlying resolution."""

    resolution: IdentityResolution
    resolution_version: str
    superseded_by: str | None = None

    def as_dict(self) -> dict[str, Any]:
        token = self.resolution.token
        return {
            "resolution_version": self.resolution_version,
            "superseded_by": self.superseded_by,
            "identity_state": token.state.value,
            "token_id": token.token_id,
            "policy_version": self.resolution.policy_version,
            "computed_ts": self.resolution.computed_ts,
            "conflicts": list(self.resolution.conflicts),
        }


def resolution_version_ref(
    resolution: IdentityResolution,
    resolution_version: Any,
    superseded_by: Any = None,
) -> ResolutionVersionRef:
    version = _text(resolution_version)
    if version is None:
        raise ValueError("resolution_version must be supplied; fusion does not invent versions")
    return ResolutionVersionRef(
        resolution=resolution,
        resolution_version=version,
        superseded_by=_text(superseded_by),
    )


def is_canonical_verified(resolution: Any) -> bool:
    """Classification only. Does not mint, resolve, or query providers."""
    if not isinstance(resolution, IdentityResolution):
        return False
    token = resolution.token
    if not isinstance(token, TokenIdentity):
        return False
    if token.state is not IdentityState.VERIFIED:
        return False
    tid = _text(token.token_id)
    if tid is None:
        return False
    if _text(token.address_canonical) is None:
        return False
    return True


def copy_canonical_token_id(
    resolution: Any,
    resolution_version: Any = None,
) -> CanonicalTokenId | None:
    """Copy token_id only from a VERIFIED structurally valid resolution."""
    if not is_canonical_verified(resolution):
        return None
    return CanonicalTokenId(
        value=str(resolution.token.token_id).strip(),
        resolution_version=_text(resolution_version),
    )


def display_search_fold(value: Any) -> str | None:
    """Lossy fold for search/display. Never a canonical join key."""
    text = _text(value)
    return text.lower() if text else None


def is_canonical_join_key(kind: Any, value: Any = None) -> bool:
    """Fail-closed: only CanonicalTokenId is a canonical join key."""
    if isinstance(kind, CanonicalTokenId):
        return bool(kind.value)
    text = _text(kind)
    if text in {
        FallbackKind.CHAIN_UNKNOWN.value,
        FallbackKind.CHAIN_SYM_SYMBOL.value,
        FallbackKind.CHAIN_SYMBOL.value,
        FallbackKind.MANUAL_SYMBOL.value,
        FallbackKind.UNVALIDATED_TOKEN_ID.value,
        RepresentationKind.SYMBOL.value,
        RepresentationKind.NAME.value,
        RepresentationKind.ALIAS.value,
        RepresentationKind.FALLBACK.value,
        RepresentationKind.PROVIDER_RESOURCE.value,
        RepresentationKind.POOL_ADDRESS.value,
        "search_fold",
        "display_search_fold",
    }:
        return False
    return False


def classify_fallback_key(value: Any) -> FallbackKind:
    text = _text(value)
    if text is None:
        return FallbackKind.OTHER
    if text.startswith("manual:"):
        return FallbackKind.MANUAL_SYMBOL
    if ":sym:" in text:
        return FallbackKind.CHAIN_SYM_SYMBOL
    if text.endswith(":unknown"):
        return FallbackKind.CHAIN_UNKNOWN
    parts = text.split(":")
    if len(parts) == 2 and parts[1] and parts[1] == parts[1].upper() and not parts[1].startswith("0x"):
        return FallbackKind.CHAIN_SYMBOL
    if text.lower().startswith("unvalidated_token_id:") or text == "unvalidated_token_id":
        return FallbackKind.UNVALIDATED_TOKEN_ID
    return FallbackKind.OTHER


def fallback_may_be_canonical(kind: FallbackKind | str | None) -> bool:
    return False


@dataclass(frozen=True)
class GeckoNewPoolClassification:
    item_type: str | None
    pool_address: PoolAddress | None
    provider_pool_id: ProviderResourceRef | None
    base_token_address: TokenAddress | None
    quote_token_address: TokenAddress | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_type": self.item_type,
            "pool_address": self.pool_address.as_dict() if self.pool_address else None,
            "provider_pool_id": self.provider_pool_id.as_dict() if self.provider_pool_id else None,
            "base_token_address": self.base_token_address.as_dict() if self.base_token_address else None,
            "quote_token_address": self.quote_token_address.as_dict() if self.quote_token_address else None,
        }


def _gecko_token_id(resource_id: Any) -> tuple[str | None, str | None]:
    text = _text(resource_id)
    if text is None or "_" not in text:
        return None, None
    chain, _, addr = text.partition("_")
    chain = chain or None
    addr = addr or None
    return chain, addr


def classify_gecko_new_pool_item(item: Mapping[str, Any] | None) -> GeckoNewPoolClassification:
    """Map the known Gecko new_pools shape without touching the adapter.

    attributes.address → PoolAddress
    data.id → ProviderResourceRef
    relationships.base_token/quote_token → TokenAddress
    """
    raw = item or {}
    item_type = _text(raw.get("type"))
    attrs = raw.get("attributes") if isinstance(raw.get("attributes"), Mapping) else {}
    rels = raw.get("relationships") if isinstance(raw.get("relationships"), Mapping) else {}
    pool_raw = _text(attrs.get("address") if isinstance(attrs, Mapping) else None)
    provider_id = _text(raw.get("id"))
    base_rel = rels.get("base_token") if isinstance(rels, Mapping) else None
    quote_rel = rels.get("quote_token") if isinstance(rels, Mapping) else None
    base_data = base_rel.get("data") if isinstance(base_rel, Mapping) else None
    quote_data = quote_rel.get("data") if isinstance(quote_rel, Mapping) else None
    base_id = base_data.get("id") if isinstance(base_data, Mapping) else None
    quote_id = quote_data.get("id") if isinstance(quote_data, Mapping) else None
    base_chain, base_addr = _gecko_token_id(base_id)
    quote_chain, quote_addr = _gecko_token_id(quote_id)
    chain = base_chain or quote_chain
    return GeckoNewPoolClassification(
        item_type=item_type,
        pool_address=pool_address(chain, pool_raw) if chain and pool_raw else None,
        provider_pool_id=provider_resource_ref("geckoterminal", provider_id, "pool") if provider_id else None,
        base_token_address=token_address(base_chain, base_addr) if base_chain and base_addr else None,
        quote_token_address=token_address(quote_chain, quote_addr) if quote_chain and quote_addr else None,
    )


def gecko_silently_treats_pool_as_token(classified: GeckoNewPoolClassification) -> bool:
    """True only if the classifier put the pool into a TokenAddress."""
    if classified.pool_address is None:
        return False
    if type(classified.pool_address) is TokenAddress:
        return True
    if classified.base_token_address is None:
        return False
    return type(classified.pool_address) is type(classified.base_token_address)
