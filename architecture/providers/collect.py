#!/usr/bin/env python3
"""Unified provider collection facade (Phase 7 Step 4).

`ProviderCollector.collect(chain, address)` fans out across every registered
market/security provider, merges their answers into ONE NormalizedTokenCandidate
and reports exactly where each field came from — and which fields stayed UNKNOWN.

Merge laws (UNKNOWN discipline, test-pinned):
  1. UNKNOWN never overwrites a known value.
  2. Conflicting known values: FIRST provider in provider order wins; the
     conflict is recorded in the outcome report (never silently resolved).
  3. Field-level provenance is recorded for every known field.
  4. A total provider failure yields an all-UNKNOWN candidate with
     confidence LOW — never an exception, never invented data.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .adapters import (
    DexScreenerAdapter,
    GeckoTerminalAdapter,
    GoPlusSecurityAdapter,
    RugCheckSecurityAdapter,
)
from .coingecko import CoinGeckoAdapter
from .chain_explorer import ChainExplorerAdapter
from .contracts import NormalizedTokenCandidate

MARKET_PROVIDER_ORDER = ["dexscreener", "geckoterminal", "coingecko"]
SECURITY_PROVIDER_ORDER = {
    # chain_explorer is attempted on every family; chains without a keyless
    # explorer instance honestly return UNSUPPORTED (recorded, never faked).
    "solana": ["rugcheck", "chain_explorer"],
    "evm": ["goplus", "chain_explorer"],
}


@dataclass
class CollectionOutcome:
    chain: str
    address: str
    candidate: NormalizedTokenCandidate
    provider_statuses: dict[str, str] = field(default_factory=dict)
    field_sources: dict[str, str] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    collected_at_ts: float = field(default_factory=time.time)

    def summary(self) -> str:
        known = len(self.field_sources)
        return (f"{self.candidate.symbol or self.address[:8]}: "
                f"{known} fields known / {len(self.unknown_fields)} UNKNOWN; "
                f"providers={self.provider_statuses}")


def _merge_metrics(base: NormalizedTokenCandidate,
                   incoming: NormalizedTokenCandidate,
                   provider: str,
                   outcome_field_sources: dict[str, str],
                   conflicts: list[str]) -> None:
    """Fill UNKNOWN metric/security fields; record provenance; log conflicts."""
    for section in ("metrics", "security"):
        base_map = asdict(getattr(base, section))
        inc_map = asdict(getattr(incoming, section))
        for key, inc_val in inc_map.items():
            if inc_val is None:
                continue
            base_val = base_map[key]
            fpath = f"{section}.{key}"
            if base_val is None:
                setattr(getattr(base, section), key, inc_val)
                outcome_field_sources[fpath] = provider
            elif base_val != inc_val:
                conflicts.append(f"{fpath}: {provider}={inc_val!r} != kept {base_val!r}")


class ProviderCollector:
    """Unified `collect(token)` interface over the AHOS provider registry."""

    def __init__(self, transport: Callable | None = None):
        kwargs = {"transport": transport} if transport else {}
        self._providers: dict[str, Any] = {
            "dexscreener": DexScreenerAdapter(**kwargs),
            "geckoterminal": GeckoTerminalAdapter(**kwargs),
            "coingecko": CoinGeckoAdapter(**kwargs),
            "goplus": GoPlusSecurityAdapter(**kwargs),
            "rugcheck": RugCheckSecurityAdapter(**kwargs),
            "chain_explorer": ChainExplorerAdapter(**kwargs),
        }

    def available_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    # -- field bookkeeping helpers -------------------------------------------------

    @staticmethod
    def _record_initial_sources(candidate: NormalizedTokenCandidate,
                                provider: str,
                                sources: dict[str, str]) -> None:
        for section in ("metrics", "security"):
            for key, val in asdict(getattr(candidate, section)).items():
                if val is not None:
                    sources[f"{section}.{key}"] = provider
        for key, val in candidate.social_presence.items():
            if val is not None:
                sources[f"social_presence.{key}"] = provider
        if candidate.pair_created_ts is not None:
            sources["pair_created_ts"] = provider

    def _fill_toplevel(self, base: NormalizedTokenCandidate,
                       incoming: NormalizedTokenCandidate,
                       provider: str,
                       sources: dict[str, str],
                       conflicts: list[str]) -> None:
        if not base.symbol and incoming.symbol:
            base.symbol = incoming.symbol
            sources["symbol"] = provider
        if not base.name and incoming.name:
            base.name = incoming.name
            sources["name"] = provider
        for attr in ("pair_address", "dex_id"):
            if getattr(base, attr) is None and getattr(incoming, attr) is not None:
                setattr(base, attr, getattr(incoming, attr))
                sources[attr] = provider
        if base.pair_created_ts is None and incoming.pair_created_ts is not None:
            base.pair_created_ts = incoming.pair_created_ts
            sources["pair_created_ts"] = provider
        for key, val in incoming.social_presence.items():
            if val is not None and key not in base.social_presence:
                base.social_presence[key] = val
                sources[f"social_presence.{key}"] = provider
        _merge_metrics(base, incoming, provider, sources, conflicts)

    # -- public interface -----------------------------------------------------------

    def collect(self, chain: str, address: str,
                include_security: bool = True) -> CollectionOutcome:
        chain = chain.lower()
        statuses: dict[str, str] = {}
        sources: dict[str, str] = {}
        conflicts: list[str] = []
        base: NormalizedTokenCandidate | None = None

        # 1. Market & metadata providers, in deterministic order
        for pid in MARKET_PROVIDER_ORDER:
            provider = self._providers[pid]
            resp = provider.fetch_token_metrics(chain, address)
            statuses[pid] = resp.status
            if resp.status == "OK" and resp.tokens:
                token = resp.tokens[0]
                if base is None:
                    base = token
                    self._record_initial_sources(base, pid, sources)
                else:
                    self._fill_toplevel(base, token, pid, sources, conflicts)

        if base is None:
            base = NormalizedTokenCandidate(
                chain=chain, address=address, symbol="", name="",
                source_provider="none", confidence_level="LOW",
            )

        # 2. Security / on-chain providers, routed by chain family
        family = "solana" if chain == "solana" else "evm"
        if include_security:
            for pid in SECURITY_PROVIDER_ORDER[family]:
                provider = self._providers[pid]
                resp = provider.fetch_token_metrics(chain, address)
                statuses[pid] = resp.status
                if resp.status == "OK" and resp.tokens:
                    self._fill_toplevel(base, resp.tokens[0], pid, sources, conflicts)

        # 3. UNKNOWN accounting + deterministic confidence level
        base.identify_unknowns()
        total_fields = len(sources) + len(base.unknown_fields)
        known = len(sources)
        if total_fields == 0:
            base.confidence_level = "LOW"
        else:
            known_ratio = known / total_fields
            base.confidence_level = "HIGH" if known_ratio >= 0.55 else (
                "MED" if known_ratio >= 0.30 else "LOW")
        base.source_provider = "+".join(
            p for p in (MARKET_PROVIDER_ORDER + SECURITY_PROVIDER_ORDER[family])
            if statuses.get(p) == "OK")

        return CollectionOutcome(
            chain=chain,
            address=address,
            candidate=base,
            provider_statuses=statuses,
            field_sources=sources,
            conflicts=conflicts,
            unknown_fields=list(base.unknown_fields),
            collected_at_ts=time.time(),
        )
