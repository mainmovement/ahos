#!/usr/bin/env python3
"""Deterministic Lane B identity resolution.

Wraps frozen `discovery.identity.token_id` / `pair_id` when the chain is in
the Lane A registry. Does not mutate Lane A files or silently overwrite IDs.
"""
from __future__ import annotations

import time
from typing import Any, Iterable, Mapping

from architecture.identity.dex_registry import lookup_dex
from architecture.identity.types import (
    ChainIdentity,
    IdentityResolution,
    IdentitySource,
    IdentityState,
    PoolIdentity,
    TokenIdentity,
)
from architecture.identity.validate import (
    EVM_CHAINS,
    validate_address_for_chain,
)
from discovery.identity import normalize_chain, pair_id, token_id

POLICY_VERSION = "identity-resolution-v1"
DEFAULT_STALE_SEC = 7 * 24 * 3600
INDEPENDENT_KIND_GROUPS = {
    "onchain": "onchain",
    "explorer": "onchain",
    "market": "market",
    "other": "other",
}


def _chain_identity(raw: str | None) -> ChainIdentity:
    if not raw or not str(raw).strip():
        return ChainIdentity(raw, None, IdentityState.INVALID, "missing_chain")
    canonical = normalize_chain(raw)
    if canonical is None:
        return ChainIdentity(raw, None, IdentityState.UNSUPPORTED, "unknown_chain")
    return ChainIdentity(raw, canonical, IdentityState.VERIFIED, "chain_registered")


def _independent_enough(sources: tuple[IdentitySource, ...]) -> bool:
    addressed = [s for s in sources if s.address and str(s.address).strip()]
    providers = {s.provider for s in addressed}
    kinds = {INDEPENDENT_KIND_GROUPS.get(s.kind, s.kind) for s in addressed}
    if len(providers) < 2:
        return False
    if "onchain" in kinds and "market" in kinds:
        return True
    # Two independent non-shared upstream sources (provider names differ).
    return True


def _sources_conflict(
    sources: tuple[IdentitySource, ...], chain: str, address: str
) -> list[str]:
    conflicts: list[str] = []
    for src in sources:
        if src.chain and normalize_chain(src.chain) not in (None, chain):
            conflicts.append(f"provider_chain_mismatch:{src.provider}")
        if src.address and src.address.strip() and chain in EVM_CHAINS:
            if src.address.strip().lower() != address.lower():
                conflicts.append(f"provider_address_mismatch:{src.provider}")
        elif src.address and src.address.strip() and src.address.strip() != address:
            conflicts.append(f"provider_address_mismatch:{src.provider}")
    return conflicts


def _belongs(chain: str, pool_base: str | None, token_canonical: str | None) -> bool | None:
    if not pool_base or not token_canonical:
        return None
    if chain in EVM_CHAINS:
        return pool_base.strip().lower() == token_canonical.lower()
    return pool_base.strip() == token_canonical


def _build_pool(
    *,
    chain: str,
    dex_id: str | None,
    pool_address: str,
    pool_base_token: str | None,
    token_id_value: str | None,
    token_canonical: str | None,
    token_state: IdentityState,
) -> PoolIdentity:
    pst, preason, pcanon, _checksum = validate_address_for_chain(chain, pool_address)
    if pst == IdentityState.INVALID:
        return PoolIdentity(
            chain, dex_id, pool_address, None, token_id_value, pool_base_token,
            IdentityState.INVALID, preason, False,
        )
    belongs = _belongs(chain, pool_base_token, token_canonical)
    pid = None
    try:
        pid = pair_id(chain, dex_id or "unknown", pcanon or pool_address)
    except ValueError:
        pid = None
    pstate = IdentityState.VERIFIED
    pr = "pool_bound"
    if belongs is False:
        pstate, pr = IdentityState.CONFLICT, "pool_base_mismatch"
    elif belongs is None:
        pstate, pr = IdentityState.UNRESOLVED, "pool_base_unknown"
    elif token_state != IdentityState.VERIFIED:
        pstate, pr = IdentityState.UNRESOLVED, "token_not_verified"
    return PoolIdentity(
        chain, dex_id, pcanon or pool_address, pid, token_id_value, pool_base_token,
        pstate, pr, belongs,
    )


def resolve_identity(
    *,
    chain: str | None,
    address: str | None = None,
    symbol: str | None = None,
    name: str | None = None,
    sources: Iterable[IdentitySource] = (),
    pool_dex: str | None = None,
    pool_address: str | None = None,
    pool_base_token: str | None = None,
    pool_dex_version: str | None = None,
    pools: Iterable[Mapping[str, Any]] = (),
    alias_matches: Iterable[Mapping[str, Any]] = (),
    now: float | None = None,
    stale_after_sec: float = DEFAULT_STALE_SEC,
) -> IdentityResolution:
    ts = time.time() if now is None else now
    srcs = tuple(sources)
    chain_id = _chain_identity(chain)

    def _empty(token: TokenIdentity, choices: tuple[dict, ...] = ()) -> IdentityResolution:
        return IdentityResolution(
            chain_id, token, None, None, srcs, (), (), choices, (), POLICY_VERSION, ts,
        )

    if chain_id.state in {IdentityState.INVALID, IdentityState.UNSUPPORTED}:
        return _empty(TokenIdentity(
            None, None, address, None, symbol, name, chain_id.state, chain_id.reason,
        ))

    assert chain_id.canonical_chain is not None
    cchain = chain_id.canonical_chain
    matches = tuple(dict(m) for m in alias_matches)

    if not address or not str(address).strip():
        if matches:
            choices = matches
        elif symbol:
            choices = ({"symbol": symbol, "reason": "symbol_is_alias_not_identity"},)
        else:
            choices = ()
        token = TokenIdentity(
            cchain, None, None, None, symbol, name,
            IdentityState.UNRESOLVED, "symbol_only_or_missing_address",
        )
        return IdentityResolution(
            chain_id, token, None, lookup_dex(cchain, pool_dex, pool_dex_version),
            srcs, (), (), choices, (), POLICY_VERSION, ts,
        )

    st, reason, canonical_addr, checksum_ok = validate_address_for_chain(cchain, address)
    if st == IdentityState.INVALID:
        token = TokenIdentity(
            cchain, canonical_addr, address, None, symbol, name, st, reason, checksum_ok,
        )
        return IdentityResolution(
            chain_id, token, None, lookup_dex(cchain, pool_dex, pool_dex_version),
            srcs, (), (), (), (), POLICY_VERSION, ts,
        )

    tid = token_id(cchain, canonical_addr or address)
    conflicts = tuple(_sources_conflict(srcs, cchain, canonical_addr or address))
    stale = False
    if srcs:
        ages = [ts - (s.source_ts or s.retrieved_ts or ts) for s in srcs]
        if ages and max(ages) > stale_after_sec:
            stale = True

    if conflicts:
        token_state, token_reason = IdentityState.CONFLICT, "source_disagreement"
    elif not _independent_enough(srcs):
        token_state, token_reason = IdentityState.UNRESOLVED, "insufficient_independent_sources"
    elif stale:
        token_state, token_reason = IdentityState.STALE, "identity_evidence_stale"
    else:
        token_state, token_reason = IdentityState.VERIFIED, "min_sources_met"

    token = TokenIdentity(
        cchain, canonical_addr, address, tid, symbol, name, token_state, token_reason, checksum_ok,
    )

    pool_specs: list[Mapping[str, Any]] = []
    if pool_address:
        pool_specs.append({
            "dex_id": pool_dex,
            "address": pool_address,
            "base_token": pool_base_token,
            "version": pool_dex_version,
        })
    for spec in pools:
        pool_specs.append(spec)

    built_pools: list[PoolIdentity] = []
    seen_pools: set[tuple[str | None, str]] = set()
    for spec in pool_specs:
        paddr = str(spec.get("address") or spec.get("pair_address") or "").strip()
        if not paddr:
            continue
        dex_label = spec.get("dex_id") or spec.get("dex") or pool_dex
        key = (str(dex_label).lower() if dex_label else None, paddr.lower() if cchain in EVM_CHAINS else paddr)
        if key in seen_pools:
            continue
        seen_pools.add(key)
        built_pools.append(
            _build_pool(
                chain=cchain,
                dex_id=dex_label,
                pool_address=paddr,
                pool_base_token=spec.get("base_token") or spec.get("base_token_address"),
                token_id_value=tid,
                token_canonical=canonical_addr,
                token_state=token_state,
            )
        )
    primary_pool = built_pools[0] if built_pools else None
    dex = lookup_dex(
        cchain,
        (pool_dex or (built_pools[0].dex_id if built_pools else None)),
        pool_dex_version,
    )

    provenance = tuple(
        {
            "provider": s.provider,
            "kind": s.kind,
            "chain": s.chain,
            "address": s.address,
            "retrieved_ts": s.retrieved_ts,
            "source_ts": s.source_ts,
        }
        for s in srcs
    )
    return IdentityResolution(
        chain_id, token, primary_pool, dex, srcs, conflicts, provenance, (),
        tuple(built_pools), POLICY_VERSION, ts,
    )
