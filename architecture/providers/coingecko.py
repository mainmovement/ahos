#!/usr/bin/env python3
"""CoinGecko provider adapter (Phase 7 — provider expansion).

Keyless public API (api.coingecko.com/api/v3); an optional demo key is read
from COINGECKO_API_KEY when present (raises rate ceiling, never required).

Honesty laws enforced here:
  - CoinGecko exposes NO free "new candidates" listing endpoint. Discovery
    requests return an explicit UNSUPPORTED envelope — never a fabricated list.
  - Liquidity is NOT provided by CoinGecko -> stays UNKNOWN (None), never guessed.
  - Every unsupported chain mapping returns an ERROR envelope, not empty data.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Callable

from .adapters import BaseHttpProviderAdapter
from .contracts import (
    BaseMarketProvider,
    MarketMetrics,
    NormalizedTokenCandidate,
    ProviderResponse,
    SecuritySignals,
)


class CoinGeckoAdapter(BaseHttpProviderAdapter):
    """Market-cap / metadata enrichment via CoinGecko contract lookup."""

    PLATFORM_IDS = {
        "ethereum": "ethereum",
        "eth": "ethereum",
        "bsc": "binance-smart-chain",
        "base": "base",
        "arbitrum": "arbitrum-one",
        "polygon": "polygon-pos",
        "avalanche": "avalanche",
        "solana": "solana",
    }

    def __init__(self, transport: Callable = urllib.request.urlopen,
                 demo_api_key: str | None = None):
        super().__init__(
            provider_id="coingecko",
            base_url="https://api.coingecko.com/api/v3",
            capabilities=["market", "metadata", "market_cap"],
            rate_limit_rps=0.5,          # conservative vs free-tier ~30 cpm
            timeout_sec=12.0,
            transport=transport,
        )
        self._api_key = demo_api_key if demo_api_key is not None else os.environ.get("COINGECKO_API_KEY", "")

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": "ahos/1.0", "Accept": "application/json"}
        if self._api_key:
            headers["x-cg-demo-api-key"] = self._api_key
        return headers

    def _get(self, path: str) -> tuple[dict, bytes, int]:
        self._rate_limit()
        req = urllib.request.Request(f"{self._base_url}{path}", headers=self._headers())
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), raw, status_code

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        return ProviderResponse(
            provider_id="coingecko",
            status="UNSUPPORTED",
            tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message=("CoinGecko free tier exposes no candidate-discovery listing; "
                           "use dexscreener/geckoterminal for discovery. Never fabricated."),
        )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        platform = self.PLATFORM_IDS.get(chain.lower())
        if not platform:
            return ProviderResponse(
                provider_id="coingecko", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"no CoinGecko platform mapping for chain '{chain}' (fields stay UNKNOWN)",
            )
        try:
            data, raw, status_code = self._get(f"/coins/{platform}/contract/{address}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ProviderResponse(
                    provider_id="coingecko", status="OK", tokens=[], http_status=404,
                    latency_ms=(time.time() - t0) * 1000.0,
                    error_message="address not indexed on CoinGecko for this platform",
                )
            return ProviderResponse(
                provider_id="coingecko", status="DOWN" if e.code >= 500 else "ERROR",
                tokens=[], http_status=e.code,
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"http {e.code}",
            )
        except Exception as e:  # network / parse failures fail closed
            return ProviderResponse(
                provider_id="coingecko", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=str(e)[:150],
            )

        md = data.get("market_data") or {}
        cp = md.get("current_price") or {}
        tv = md.get("total_volume") or {}
        links = data.get("links") or {}
        community = data.get("community_data") or {}

        metrics = MarketMetrics(
            price_usd=cp.get("usd"),
            volume_24h=tv.get("usd"),
            market_cap_usd=(md.get("market_cap") or {}).get("usd"),
            fdv_usd=(md.get("fully_diluted_valuation") or {}).get("usd"),
            price_change_1h=md.get("price_change_percentage_1h_in_currency"),
            price_change_24h=md.get("price_change_percentage_24h_in_currency"),
        )

        social: dict[str, str | None] = {}
        homepage = (links.get("homepage") or [None])[0]
        if homepage:
            social["homepage"] = homepage
        if links.get("twitter_screen_name"):
            social["twitter"] = f"https://x.com/{links['twitter_screen_name']}"
        if links.get("telegram_channel_identifier"):
            social["telegram"] = f"https://t.me/{links['telegram_channel_identifier']}"

        symbol = str(data.get("symbol") or "").upper()
        name = data.get("name") or ""

        candidate = NormalizedTokenCandidate(
            chain=chain.lower(),
            address=address,
            symbol=symbol,
            name=name,
            metrics=metrics,
            security=SecuritySignals(),      # CoinGecko provides none -> UNKNOWN
            social_presence=social or {},    # empty stays UNKNOWN-flagged
            source_provider="coingecko",
            raw_payload_sha256=hashlib.sha256(raw).hexdigest(),
        )
        candidate.identify_unknowns()
        return ProviderResponse(
            provider_id="coingecko", status="OK", tokens=[candidate],
            http_status=status_code, latency_ms=(time.time() - t0) * 1000.0,
            raw_payload=data,
        )
