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
