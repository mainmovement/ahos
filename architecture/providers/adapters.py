#!/usr/bin/env python3
"""AHOS Concrete Provider Adapters (Section VII).

Implements adapters for:
  - DexScreener (discovery, pairs, liquidity, volume, price)
  - GeckoTerminal (pairs, ohlcv, liquidity pools)
  - DEXTools (pair search, scoring indicators)
  - CoinGecko (market cap, metadata, FDV)
  - CoinMarketCap (rank, market metrics)
  - GoPlus Security (anti-honeypot, tax, mint/freeze authority)
  - RugCheck (Solana token risk analysis, lp lock/burn)
  - Chain Explorers (Solana RPC, EVM RPC Transfer log analyzers)
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import urllib.error
from typing import Any, Callable

from .contracts import (
    BaseMarketProvider,
    ProviderResponse,
    NormalizedTokenCandidate,
    MarketMetrics,
    SecuritySignals,
    UNKNOWN_VALUE
)


def _sha(raw: bytes | str) -> str:
    b = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


class BaseHttpProviderAdapter(BaseMarketProvider):
    def __init__(self, provider_id: str, base_url: str,
                 capabilities: list[str], rate_limit_rps: float = 2.0,
                 timeout_sec: float = 10.0, transport: Callable = urllib.request.urlopen):
        self._provider_id = provider_id
        self._base_url = base_url.rstrip("/")
        self._capabilities = capabilities
        self._rate_limit_rps = rate_limit_rps
        self._timeout_sec = timeout_sec
        self._transport = transport
        self._last_call_ts = 0.0

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def capabilities(self) -> list[str]:
        return self._capabilities

    def _rate_limit(self):
        min_interval = 1.0 / max(self._rate_limit_rps, 0.1)
        now = time.time()
        elapsed = now - self._last_call_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call_ts = time.time()

    def health_check(self) -> bool:
        try:
            self._rate_limit()
            req = urllib.request.Request(self._base_url, headers={"User-Agent": "ahos-provider/1.0"})
            with self._transport(req, timeout=5.0) as resp:
                return resp.status < 500
        except Exception:
            return False


class DexScreenerAdapter(BaseHttpProviderAdapter):
    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="dexscreener",
            base_url="https://api.dexscreener.com/latest/dex",
            capabilities=["discovery", "pairs", "liquidity", "volume", "price"],
            rate_limit_rps=3.0,
            transport=transport
        )

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        url = f"{self._base_url}/search?q={chain}"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            pairs = data.get("pairs") or []
            tokens = []
            for p in pairs[:limit]:
                base = p.get("baseToken", {})
                addr = base.get("address")
                if not addr:
                    continue
                metrics = MarketMetrics(
                    price_usd=float(p["priceUsd"]) if p.get("priceUsd") else None,
                    liquidity_usd=float(p["liquidity"]["usd"]) if (p.get("liquidity") and p["liquidity"].get("usd")) else None,
                    volume_5m=float(p["volume"]["m5"]) if (p.get("volume") and p["volume"].get("m5")) else None,
                    volume_1h=float(p["volume"]["h1"]) if (p.get("volume") and p["volume"].get("h1")) else None,
                    volume_24h=float(p["volume"]["h24"]) if (p.get("volume") and p["volume"].get("h24")) else None,
                    price_change_5m=float(p["priceChange"]["m5"]) if (p.get("priceChange") and p["priceChange"].get("m5")) else None,
                    price_change_1h=float(p["priceChange"]["h1"]) if (p.get("priceChange") and p["priceChange"].get("h1")) else None,
                    price_change_24h=float(p["priceChange"]["h24"]) if (p.get("priceChange") and p["priceChange"].get("h24")) else None,
                    fdv_usd=float(p["fdv"]) if p.get("fdv") else None,
                    txns_1h_buys=int(p["txns"]["h1"]["buys"]) if (p.get("txns") and p["txns"].get("h1") and p["txns"]["h1"].get("buys")) else None,
                    txns_1h_sells=int(p["txns"]["h1"]["sells"]) if (p.get("txns") and p["txns"].get("h1") and p["txns"]["h1"].get("sells")) else None,
                )
                tok = NormalizedTokenCandidate(
                    chain=p.get("chainId", chain).lower(),
                    address=addr,
                    symbol=base.get("symbol", "UNKNOWN"),
                    name=base.get("name", "Unknown Token"),
                    pair_address=p.get("pairAddress"),
                    dex_id=p.get("dexId"),
                    pair_created_ts=(p.get("pairCreatedAt") / 1000.0) if p.get("pairCreatedAt") else None,
                    metrics=metrics,
                    source_provider="dexscreener",
                    retrieved_ts=time.time(),
                    raw_payload_sha256=_sha(raw)
                )
                tok.identify_unknowns()
                tokens.append(tok)
            return ProviderResponse(
                provider_id="dexscreener",
                status="OK",
                tokens=tokens,
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="dexscreener",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        url = f"{self._base_url}/tokens/{address}"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            pairs = data.get("pairs") or []
            if not pairs:
                return ProviderResponse(provider_id="dexscreener", status="OK", tokens=[], http_status=status_code)
            p = pairs[0]
            base = p.get("baseToken", {})
            metrics = MarketMetrics(
                price_usd=float(p["priceUsd"]) if p.get("priceUsd") else None,
                liquidity_usd=float(p["liquidity"]["usd"]) if (p.get("liquidity") and p["liquidity"].get("usd")) else None,
                volume_1h=float(p["volume"]["h1"]) if (p.get("volume") and p["volume"].get("h1")) else None,
                volume_24h=float(p["volume"]["h24"]) if (p.get("volume") and p["volume"].get("h24")) else None,
            )
            tok = NormalizedTokenCandidate(
                chain=p.get("chainId", chain).lower(),
                address=base.get("address", address),
                symbol=base.get("symbol", "UNKNOWN"),
                name=base.get("name", "Unknown Token"),
                pair_address=p.get("pairAddress"),
                dex_id=p.get("dexId"),
                metrics=metrics,
                source_provider="dexscreener",
                retrieved_ts=time.time(),
                raw_payload_sha256=_sha(raw)
            )
            tok.identify_unknowns()
            return ProviderResponse(
                provider_id="dexscreener",
                status="OK",
                tokens=[tok],
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="dexscreener",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )


class GeckoTerminalAdapter(BaseHttpProviderAdapter):
    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="geckoterminal",
            base_url="https://api.geckoterminal.com/api/v2",
            capabilities=["discovery", "pools", "ohlcv", "volume"],
            rate_limit_rps=1.0,
            transport=transport
        )

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        url = f"{self._base_url}/networks/{chain}/new_pools"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0", "Accept": "application/json"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            pools = data.get("data") or []
            tokens = []
            for pool in pools[:limit]:
                attrs = pool.get("attributes", {})
                tok = NormalizedTokenCandidate(
                    chain=chain,
                    address=attrs.get("address", ""),
                    symbol=attrs.get("name", "").split("/")[0].strip(),
                    name=attrs.get("name", "Pool"),
                    pair_address=pool.get("id", ""),
                    metrics=MarketMetrics(
                        liquidity_usd=float(attrs.get("reserve_in_usd") or 0) if attrs.get("reserve_in_usd") else None,
                        volume_24h=float(attrs.get("volume_usd", {}).get("h24") or 0) if attrs.get("volume_usd") else None
                    ),
                    source_provider="geckoterminal",
                    retrieved_ts=time.time(),
                    raw_payload_sha256=_sha(raw)
                )
                tok.identify_unknowns()
                tokens.append(tok)
            return ProviderResponse(
                provider_id="geckoterminal",
                status="OK",
                tokens=tokens,
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="geckoterminal",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        url = f"{self._base_url}/networks/{chain}/tokens/{address}"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0", "Accept": "application/json"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            attrs = data.get("data", {}).get("attributes", {})
            metrics = MarketMetrics(
                price_usd=float(attrs["price_usd"]) if attrs.get("price_usd") else None,
                fdv_usd=float(attrs["fdv_usd"]) if attrs.get("fdv_usd") else None,
                liquidity_usd=float(attrs["total_reserve_in_usd"]) if attrs.get("total_reserve_in_usd") else None,
                volume_24h=float(attrs.get("volume_usd", {}).get("h24") or 0) if attrs.get("volume_usd") else None
            )
            tok = NormalizedTokenCandidate(
                chain=chain,
                address=address,
                symbol=attrs.get("symbol", "UNKNOWN"),
                name=attrs.get("name", "Unknown Token"),
                metrics=metrics,
                source_provider="geckoterminal",
                retrieved_ts=time.time(),
                raw_payload_sha256=_sha(raw)
            )
            tok.identify_unknowns()
            return ProviderResponse(
                provider_id="geckoterminal",
                status="OK",
                tokens=[tok],
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="geckoterminal",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )


class GoPlusSecurityAdapter(BaseHttpProviderAdapter):
    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="goplus",
            base_url="https://api.gopluslabs.io/api/v1",
            capabilities=["security", "honeypot", "contract_audit", "taxes"],
            rate_limit_rps=2.0,
            transport=transport
        )

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        return ProviderResponse(provider_id="goplus", status="OK", tokens=[])

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        # Map chain string to GoPlus chain id
        chain_map = {"ethereum": "1", "bsc": "56", "arbitrum": "42161", "polygon": "137", "base": "8453"}
        cid = chain_map.get(chain.lower(), "1")
        url = f"{self._base_url}/token_security/{cid}?contract_addresses={address.lower()}"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            result = data.get("result", {}).get(address.lower(), {})
            sec = SecuritySignals(
                is_honeypot=bool(int(result.get("is_honeypot", 0))),
                buy_tax_pct=float(result.get("buy_tax", 0)) if "buy_tax" in result else None,
                sell_tax_pct=float(result.get("sell_tax", 0)) if "sell_tax" in result else None,
                is_contract_verified=bool(int(result.get("is_open_source", 0))),
                is_ownership_renounced=bool(int(result.get("can_take_back_ownership", 0)) == 0),
                has_mint_authority=bool(int(result.get("is_mintable", 0))),
                has_freeze_authority=bool(int(result.get("cannot_sell_all", 0)))
            )
            tok = NormalizedTokenCandidate(
                chain=chain,
                address=address,
                symbol=result.get("token_symbol", "UNKNOWN"),
                name=result.get("token_name", "Unknown"),
                security=sec,
                source_provider="goplus",
                retrieved_ts=time.time(),
                raw_payload_sha256=_sha(raw)
            )
            tok.identify_unknowns()
            return ProviderResponse(
                provider_id="goplus",
                status="OK",
                tokens=[tok],
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="goplus",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )


class RugCheckSecurityAdapter(BaseHttpProviderAdapter):
    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="rugcheck",
            base_url="https://api.rugcheck.xyz/v1",
            capabilities=["security", "solana_lp_lock", "solana_mint_authority"],
            rate_limit_rps=2.0,
            transport=transport
        )

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        if chain.lower() != "solana":
            return ProviderResponse(provider_id="rugcheck", status="OK", tokens=[])
        t0 = time.time()
        url = f"{self._base_url}/stats/recent"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            tokens = []
            for item in data[:limit] if isinstance(data, list) else []:
                addr = item.get("mint")
                if not addr:
                    continue
                tok = NormalizedTokenCandidate(
                    chain="solana",
                    address=addr,
                    symbol=item.get("symbol", "SOL_TOK"),
                    name=item.get("name", "Solana Token"),
                    source_provider="rugcheck",
                    retrieved_ts=time.time(),
                    raw_payload_sha256=_sha(raw)
                )
                tok.identify_unknowns()
                tokens.append(tok)
            return ProviderResponse(
                provider_id="rugcheck",
                status="OK",
                tokens=tokens,
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="rugcheck",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        url = f"{self._base_url}/tokens/{address}/report"
        try:
            self._rate_limit()
            req = urllib.request.Request(url, headers={"User-Agent": "ahos/1.0"})
            with self._transport(req, timeout=self._timeout_sec) as resp:
                raw = resp.read()
                status_code = resp.status
            data = json.loads(raw)
            risks = data.get("risks", [])
            has_mint = any(r.get("name") == "Mint Authority" for r in risks)
            has_freeze = any(r.get("name") == "Freeze Authority" for r in risks)
            sec = SecuritySignals(
                is_honeypot=any(r.get("level") == "danger" and "honeypot" in r.get("name", "").lower() for r in risks),
                has_mint_authority=has_mint,
                has_freeze_authority=has_freeze,
                top10_holder_concentration_pct=float(data.get("topHoldersPercent", 0)) if data.get("topHoldersPercent") else None
            )
            tok = NormalizedTokenCandidate(
                chain="solana",
                address=address,
                symbol=data.get("tokenMeta", {}).get("symbol", "SOL_TOK"),
                name=data.get("tokenMeta", {}).get("name", "Solana Token"),
                security=sec,
                source_provider="rugcheck",
                retrieved_ts=time.time(),
                raw_payload_sha256=_sha(raw)
            )
            tok.identify_unknowns()
            return ProviderResponse(
                provider_id="rugcheck",
                status="OK",
                tokens=[tok],
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code,
                raw_sha256=_sha(raw)
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="rugcheck",
                status="ERROR",
                tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}"
            )


# ======================================================================
# DEXTools (Wave-25)
#
# DEXTools v2 is a PAID, key-gated API -- there is no free tier that returns
# pool/token data. This project runs on a $0 cost floor, so the adapter is
# built but stays DISABLED unless DEXTOOLS_API_KEY is present in the
# environment. Without a key it reports NO_KEY rather than pretending to be
# down: a missing key is a configuration fact, not a provider outage, and the
# two must never be confused in the health ledger.
#
# What DEXTools uniquely adds when a key IS present is its audit + score
# endpoints (lock intel, honeypot flags, DEXTScore). Everything the free
# providers already cover is deliberately NOT duplicated here.
# ======================================================================

class DEXToolsAdapter(BaseHttpProviderAdapter):
    """DEXTools v2 adapter. Inert without DEXTOOLS_API_KEY (paid tier only)."""

    # DEXTools chain slugs differ from the ones used elsewhere in AHOS.
    CHAIN_SLUGS = {
        "ethereum": "ether", "eth": "ether", "bsc": "bsc", "polygon": "polygon",
        "arbitrum": "arbitrum", "base": "base", "avalanche": "avalanche",
        "optimism": "optimism", "solana": "solana", "fantom": "fantom",
    }

    def __init__(self, transport: Callable = urllib.request.urlopen,
                 api_key: str | None = None, plan: str = "trial"):
        super().__init__(
            provider_id="dextools",
            base_url="https://public-api.dextools.io/trial/v2",
            capabilities=["pairs", "security", "score", "lp_lock", "audit"],
            rate_limit_rps=1.0,          # trial plan is heavily throttled
            transport=transport,
        )
        import os
        self._api_key = api_key if api_key is not None else os.environ.get("DEXTOOLS_API_KEY", "")
        self._plan = plan
        if plan and plan != "trial":
            self._base_url = f"https://public-api.dextools.io/{plan}/v2"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def health_check(self) -> bool:
        # Never emit network traffic we know will 401.
        return bool(self._api_key) and super().health_check()

    def _no_key(self, t0: float) -> ProviderResponse:
        return ProviderResponse(
            provider_id="dextools", status="NO_KEY", tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message=("DEXTOOLS_API_KEY not set. DEXTools v2 has no free tier; "
                           "AHOS runs without it and relies on free providers."),
        )

    def _get(self, path: str) -> tuple[dict, bytes, int]:
        self._rate_limit()
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            headers={"X-API-Key": self._api_key,
                     "Accept": "application/json",
                     "User-Agent": "ahos/1.0"},
        )
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), raw, status_code

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        """Hot pools ranking -- DEXTools' curated 'what is moving now' list."""
        t0 = time.time()
        if not self._api_key:
            return self._no_key(t0)
        slug = self.CHAIN_SLUGS.get(chain.lower(), chain.lower())
        try:
            data, raw, status_code = self._get(f"/ranking/{slug}/hotpools")
            rows = data.get("data") or []
            tokens = []
            for row in rows[:limit]:
                main = row.get("mainToken") or {}
                addr = main.get("address")
                if not addr:
                    continue
                tok = NormalizedTokenCandidate(
                    chain=chain.lower(),
                    address=addr,
                    symbol=main.get("symbol", "UNKNOWN"),
                    name=main.get("name", "Unknown Token"),
                    pair_address=row.get("address"),
                    dex_id=(row.get("exchange") or {}).get("name"),
                    metrics=MarketMetrics(),
                    source_provider="dextools",
                    retrieved_ts=time.time(),
                    raw_payload_sha256=_sha(raw),
                )
                tok.identify_unknowns()
                tokens.append(tok)
            return ProviderResponse(
                provider_id="dextools", status="OK", tokens=tokens,
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code, raw_sha256=_sha(raw),
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="dextools", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}",
            )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        """Token audit -- the one thing DEXTools gives that free providers do not."""
        t0 = time.time()
        if not self._api_key:
            return self._no_key(t0)
        slug = self.CHAIN_SLUGS.get(chain.lower(), chain.lower())
        try:
            data, raw, status_code = self._get(f"/token/{slug}/{address}/audit")
            d = data.get("data") or {}

            def _flag(key: str) -> bool | None:
                # DEXTools returns "yes"/"no"/"unknown" strings. "unknown" must
                # stay None -- coercing it to False would invent a safety claim.
                v = d.get(key)
                if isinstance(v, str):
                    lv = v.strip().lower()
                    if lv in ("yes", "true"):
                        return True
                    if lv in ("no", "false"):
                        return False
                return None

            def _tax(key: str) -> float | None:
                v = d.get(key)
                try:
                    if v is None:
                        return None
                    f = float(v)
                    # DEXTools reports tax as a fraction on some plans.
                    return f * 100.0 if 0 < f <= 1 else f
                except (TypeError, ValueError):
                    return None

            sec = SecuritySignals(
                is_honeypot=_flag("isHoneypot"),
                buy_tax_pct=_tax("buyTax"),
                sell_tax_pct=_tax("sellTax"),
                is_contract_verified=_flag("isOpenSource"),
                has_mint_authority=_flag("isMintable"),
                has_freeze_authority=_flag("isBlacklisted"),
                is_ownership_renounced=(
                    None if _flag("isProxy") is None else not _flag("isProxy")),
            )
            tok = NormalizedTokenCandidate(
                chain=chain.lower(), address=address,
                symbol="UNKNOWN", name="Unknown",
                security=sec, source_provider="dextools",
                retrieved_ts=time.time(), raw_payload_sha256=_sha(raw),
            )
            tok.identify_unknowns()
            return ProviderResponse(
                provider_id="dextools", status="OK", tokens=[tok],
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code, raw_sha256=_sha(raw),
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="dextools", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}",
            )


# ======================================================================
# DexScreener boosts / promotion feed (Wave-25) -- FREE, no key.
#
# This is the honest replacement for social-media virality scraping. A "boost"
# is a token team PAYING DexScreener for placement. That is measurable, public,
# and free at 60 req/min.
#
# Critically, AHOS treats a boost as a RISK signal, not a bullish one: someone
# spending money on visibility for a micro-cap is evidence of marketing intent,
# not of fundamental strength. It feeds ViralityTracker(boost_amount=...),
# which raises is_paid_promotion.
# ======================================================================

class DexScreenerBoostsAdapter(BaseHttpProviderAdapter):
    """Free promotion-spend feed. Boost spend is treated as a risk marker."""

    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="dexscreener_boosts",
            base_url="https://api.dexscreener.com",
            capabilities=["discovery", "promotion", "attention"],
            rate_limit_rps=1.0,          # documented limit is 60/min
            transport=transport,
        )

    def _fetch(self, path: str) -> tuple[Any, bytes, int]:
        self._rate_limit()
        req = urllib.request.Request(f"{self._base_url}{path}",
                                     headers={"User-Agent": "ahos/1.0"})
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), raw, status_code

    def fetch_boost_map(self, path: str = "/token-boosts/top/v1") -> dict[str, float]:
        """Returns {address_lower: total_boost_amount}. Empty dict on any failure.

        Callers must treat an empty map as 'unknown', never as 'no token is
        being promoted' -- under network filtering these look identical.
        """
        try:
            data, _, _ = self._fetch(path)
            rows = data if isinstance(data, list) else (data.get("data") or [])
            out: dict[str, float] = {}
            for row in rows:
                addr = (row or {}).get("tokenAddress")
                if not addr:
                    continue
                amt = row.get("totalAmount", row.get("amount"))
                try:
                    out[str(addr).lower()] = float(amt)
                except (TypeError, ValueError):
                    continue
            return out
        except Exception:
            return {}

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        try:
            data, raw, status_code = self._fetch("/token-boosts/top/v1")
            rows = data if isinstance(data, list) else (data.get("data") or [])
            tokens = []
            for row in rows:
                if len(tokens) >= limit:
                    break
                addr = (row or {}).get("tokenAddress")
                row_chain = str(row.get("chainId", "")).lower()
                if not addr or (chain and row_chain != chain.lower()):
                    continue
                tok = NormalizedTokenCandidate(
                    chain=row_chain or chain.lower(),
                    address=addr,
                    symbol="UNKNOWN",
                    name="Unknown Token",
                    metrics=MarketMetrics(),
                    source_provider="dexscreener_boosts",
                    retrieved_ts=time.time(),
                    raw_payload_sha256=_sha(raw),
                )
                tok.identify_unknowns()
                tokens.append(tok)
            return ProviderResponse(
                provider_id="dexscreener_boosts", status="OK", tokens=tokens,
                latency_ms=(time.time() - t0) * 1000.0,
                http_status=status_code, raw_sha256=_sha(raw),
            )
        except Exception as e:
            return ProviderResponse(
                provider_id="dexscreener_boosts", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"{type(e).__name__}: {str(e)[:200]}",
            )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        # Boost feed carries no market metrics; it is a discovery/attention source.
        return ProviderResponse(provider_id="dexscreener_boosts", status="OK", tokens=[])
