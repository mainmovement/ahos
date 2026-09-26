#!/usr/bin/env python3
"""AHOS Lane B canonical identity types.

Does not edit frozen `discovery/identity.py`. Canonical token_id/pair_id hashes
are still produced by that module when a chain is in the Lane A registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IdentityState(str, Enum):
    VERIFIED = "VERIFIED"
    CONFLICT = "CONFLICT"
    UNRESOLVED = "UNRESOLVED"
    INVALID = "INVALID"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class IdentitySource:
    provider: str
    chain: str | None
    address: str | None
    retrieved_ts: float | None = None
    source_ts: float | None = None
    kind: str = "market"  # market | onchain | explorer | other


@dataclass(frozen=True)
class ChainIdentity:
    input_chain: str | None
    canonical_chain: str | None
    state: IdentityState
    reason: str


@dataclass(frozen=True)
class TokenIdentity:
    chain: str | None
    address_canonical: str | None
    address_input: str | None
    token_id: str | None
    symbol_alias: str | None
    name_alias: str | None
    state: IdentityState
    reason: str
    checksum_ok: bool | None = None


@dataclass(frozen=True)
class DexDeployment:
    dex_id: str
    chain: str
    version: str
    factory: str | None = None
    router: str | None = None


@dataclass(frozen=True)
class PoolIdentity:
    chain: str | None
    dex_id: str | None
    pair_address: str | None
    pair_id: str | None
    token_id: str | None
    base_token_address: str | None
    state: IdentityState
    reason: str
    belongs_to_token: bool | None = None


@dataclass(frozen=True)
class IdentityResolution:
    chain: ChainIdentity
    token: TokenIdentity
    pool: PoolIdentity | None
    dex: DexDeployment | None
    sources: tuple[IdentitySource, ...] = ()
    conflicts: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    choices: tuple[dict[str, Any], ...] = ()
    pools: tuple[PoolIdentity, ...] = ()
    policy_version: str = "identity-resolution-v1"
    computed_ts: float = 0.0

    @property
    def state(self) -> IdentityState:
        """Token-level state. Pool may be independently unresolved."""
        return self.token.state
