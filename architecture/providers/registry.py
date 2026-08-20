#!/usr/bin/env python3
"""AHOS Provider Registry & Multi-Provider Router (Section VII)."""
from __future__ import annotations

from typing import Callable, Any
from .contracts import BaseMarketProvider, ProviderResponse, NormalizedTokenCandidate
from .adapters import (
    DexScreenerAdapter,
    GeckoTerminalAdapter,
    GoPlusSecurityAdapter,
    RugCheckSecurityAdapter
)
from .coingecko import CoinGeckoAdapter
from .chain_explorer import ChainExplorerAdapter
from .coinmarketcap import CoinMarketCapAdapter
from .pumpfun import PumpFunLaunchpadAdapter


class ProviderRouter:
    def __init__(self, transport: Callable | None = None):
        kwargs = {"transport": transport} if transport else {}
        self.providers: dict[str, BaseMarketProvider] = {
            "dexscreener": DexScreenerAdapter(**kwargs),
            "geckoterminal": GeckoTerminalAdapter(**kwargs),
            "goplus": GoPlusSecurityAdapter(**kwargs),
            "rugcheck": RugCheckSecurityAdapter(**kwargs),
            # Phase 7 additions (enrichment-only; discovery candidates still come
            # from dexscreener/geckoterminal lists below):
            "coingecko": CoinGeckoAdapter(**kwargs),
            "chain_explorer": ChainExplorerAdapter(**kwargs),
            # Month 2 (M-GAP-011): keyed free tier — inert (NO_KEY) until
            # COINMARKETCAP_API_KEY is configured; never emits traffic without it.
            "coinmarketcap": CoinMarketCapAdapter(**kwargs),
            # Month 2 (M-GAP-011): keyless Solana launchpad discovery feed.
            "pumpfun": PumpFunLaunchpadAdapter(**kwargs),
        }

    def get_provider(self, provider_id: str) -> BaseMarketProvider | None:
        return self.providers.get(provider_id)

    def discover_candidates(self, chain: str, limit: int = 20) -> list[NormalizedTokenCandidate]:
        candidates: list[NormalizedTokenCandidate] = []
        for pid in ["dexscreener", "geckoterminal"]:
            provider = self.providers.get(pid)
            if provider:
                resp = provider.fetch_candidate_tokens(chain, limit=limit)
                if resp.status == "OK":
                    candidates.extend(resp.tokens)
        # Deduplicate by (chain, address)
        seen = set()
        unique = []
        for c in candidates:
            key = (c.chain, c.address.lower())
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def enrich_security(self, candidate: NormalizedTokenCandidate) -> NormalizedTokenCandidate:
        if candidate.chain == "solana":
            provider = self.providers.get("rugcheck")
        else:
            provider = self.providers.get("goplus")
        if provider:
            sec_resp = provider.fetch_token_metrics(candidate.chain, candidate.address)
            if sec_resp.status == "OK" and sec_resp.tokens:
                candidate.security = sec_resp.tokens[0].security
                candidate.identify_unknowns()
        return candidate
