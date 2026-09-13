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
from datetime import datetime
from typing import Any, Callable, Mapping

from architecture.identity.fusion import (
    classify_gecko_new_pool_item,
    pool_address,
    token_address,
)
from architecture.identity.types import IdentityState
from architecture.identity.validate import EVM_CHAINS

from .contracts import (
    BaseMarketProvider,
    ProviderResponse,
    NormalizedTokenCandidate,
    MarketMetrics,
    SecuritySignals,
    UNKNOWN_VALUE
)

# Gecko network id → existing validator chain. Display/request chain is unchanged.
_GECKO_NETWORK_ALIASES = {"eth": "ethereum"}
_GECKO_VALIDATOR_CHAINS = frozenset(EVM_CHAINS) | {"solana"}


def _gecko_validator_chain(network: Any) -> str | None:
    if not isinstance(network, str):
        return None
    key = network.strip().lower()
    if not key:
        return None
    key = _GECKO_NETWORK_ALIASES.get(key, key)
    if key not in _GECKO_VALIDATOR_CHAINS:
        return None
    return key


def _gecko_included_token_attrs(payload: Any, resource_id: Any) -> Mapping[str, Any]:
    """Display metadata only. Never used as an identity source."""
    if not isinstance(payload, Mapping) or not isinstance(resource_id, str) or not resource_id:
        return {}
    included = payload.get("included")
    if not isinstance(included, list):
        return {}
    for item in included:
        if not isinstance(item, Mapping):
            continue
        if item.get("id") == resource_id and item.get("type") == "token":
            attrs = item.get("attributes")
            return attrs if isinstance(attrs, Mapping) else {}
    return {}


def _gecko_relationship_id(item: Mapping[str, Any], rel_name: str) -> str | None:
    rels = item.get("relationships")
    if not isinstance(rels, Mapping):
        return None
    rel = rels.get(rel_name)
    data = rel.get("data") if isinstance(rel, Mapping) else None
    value = data.get("id") if isinstance(data, Mapping) else None
    return value if isinstance(value, str) and value.strip() else None


def _gecko_new_pool_candidate(
    item: Any,
    *,
    request_chain: str,
    payload: Any,
    raw_sha: str,
) -> NormalizedTokenCandidate | None:
    """Emit a BASE TOKEN candidate. Never treat the pool as the token.

    Fail closed when the base-token relationship cannot be extracted and
    validated. Pool address, provider resource id, symbol, and pool name
    never become the token address.
    """
    if not isinstance(item, Mapping):
        return None
    req_chain = _gecko_validator_chain(request_chain)
    if req_chain is None:
        return None
    classified = classify_gecko_new_pool_item(item)
    base = classified.base_token_address
    if base is None or not base.address:
        return None
    base_chain = _gecko_validator_chain(base.chain)
    if base_chain is None or base_chain != req_chain:
        return None
    validated = token_address(base_chain, base.address)
    if validated.validation_state is not IdentityState.UNRESOLVED or not validated.address:
        return None
    attrs = item.get("attributes") if isinstance(item.get("attributes"), Mapping) else {}
    pool_raw = attrs.get("address")
    if not isinstance(pool_raw, str) or not pool_raw.strip():
        pool_raw = classified.pool_address.address if classified.pool_address else None
    pair_address = None
    if isinstance(pool_raw, str) and pool_raw.strip():
        pool = pool_address(req_chain, pool_raw.strip())
        if pool.validation_state is IdentityState.UNRESOLVED and pool.address:
            pair_address = pool.address
    token_attrs = _gecko_included_token_attrs(payload, _gecko_relationship_id(item, "base_token"))
    symbol_raw = token_attrs.get("symbol")
    symbol = symbol_raw.strip() if isinstance(symbol_raw, str) and symbol_raw.strip() else "UNKNOWN"
    name_raw = token_attrs.get("name")
    if isinstance(name_raw, str) and name_raw.strip():
        name = name_raw.strip()
    else:
        pool_name = attrs.get("name")
        name = pool_name.strip() if isinstance(pool_name, str) and pool_name.strip() else "Unknown Token"
    volume = attrs.get("volume_usd") if isinstance(attrs.get("volume_usd"), Mapping) else {}
    tok = NormalizedTokenCandidate(
        chain=request_chain,
        address=validated.address,
        symbol=symbol,
        name=name,
        pair_address=pair_address,
        pair_created_ts=_parse_iso_epoch(attrs.get("pool_created_at")),
        metrics=MarketMetrics(
            liquidity_usd=float(attrs["reserve_in_usd"]) if attrs.get("reserve_in_usd") else None,
            volume_24h=float(volume["h24"]) if volume.get("h24") else None,
        ),
        source_provider="geckoterminal",
        retrieved_ts=time.time(),
        raw_payload_sha256=raw_sha,
    )
    tok.identify_unknowns()
    return tok


def _sha(raw: bytes | str) -> str:
    b = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _parse_iso_epoch(value: Any) -> float | None:
    """Parse provider ISO/epoch pool-created time. None on missing or unparseable.

    Never invents a timestamp. Numeric values are treated as epoch seconds only
    when finite; ISO-8601 strings (including trailing Z) map to UTC epoch.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            ts = float(value)
        except (TypeError, ValueError):
            return None
        if ts != ts or ts in (float("inf"), float("-inf")):  # NaN / Inf
            return None
        return ts
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00").replace("z", "+00:00")
        ).timestamp()
    except ValueError:
        return None


def _tri_bool(value) -> bool | None:
    """Missing/unparseable flags stay None. Never default a security flag to False."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes"}:
        return True
    if s in {"0", "false", "no"}:
        return False
    try:
        return bool(int(float(s)))
    except (TypeError, ValueError):
        return None


def _maybe_tax_pct(result: dict, key: str) -> float | None:
    """GoPlus taxes are ratios in [0, 1]. Store percent to match SecuritySignals."""
    if key not in result or result.get(key) in (None, ""):
        return None
    try:
        f = float(result[key])
    except (TypeError, ValueError):
        return None
    return f * 100.0 if 0 <= f <= 1.0 else f


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
            # 120 rpm — equals the frozen PAL budget (discovery/providers.yaml);
            # never exceed it (tests/test_provider_yaml_sync.py).
            rate_limit_rps=2.0,
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
            # 24 rpm — under PAL's frozen 25 rpm budget
            # (discovery/providers.yaml; tests/test_provider_yaml_sync.py).
            rate_limit_rps=0.4,
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
            raw_items = data.get("data") if isinstance(data, Mapping) else None
            pools = raw_items if isinstance(raw_items, list) else []
            tokens = []
            raw_sha = _sha(raw)
            for pool in pools[:limit]:
                tok = _gecko_new_pool_candidate(
                    pool, request_chain=chain, payload=data, raw_sha=raw_sha
                )
                if tok is None:
                    continue
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
            # ~20 rpm — PAL's frozen goplus_evm budget is 20 rpm
            # (discovery/providers.yaml; tests/test_provider_yaml_sync.py).
            rate_limit_rps=0.33,
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
            take_back = _tri_bool(result.get("can_take_back_ownership"))
            sec = SecuritySignals(
                is_honeypot=_tri_bool(result.get("is_honeypot")),
                buy_tax_pct=_maybe_tax_pct(result, "buy_tax"),
                sell_tax_pct=_maybe_tax_pct(result, "sell_tax"),
                is_contract_verified=_tri_bool(result.get("is_open_source")),
                is_ownership_renounced=(None if take_back is None else (not take_back)),
                has_mint_authority=_tri_bool(result.get("is_mintable")),
                has_freeze_authority=_tri_bool(
                    result.get("transfer_pausable") if "transfer_pausable" in result
                    else result.get("is_freezable")
                ),
                is_blacklisted=_tri_bool(
                    result.get("is_blacklisted") if "is_blacklisted" in result
                    else result.get("is_in_blacklist")
                ),
                cannot_sell_all=_tri_bool(
                    result.get("cannot_sell_all") if "cannot_sell_all" in result
                    else result.get("can_not_sell_all")
                ),
                is_proxy=_tri_bool(result.get("is_proxy")),
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
            # 30 rpm — equals PAL's frozen rugcheck budget
            # (discovery/providers.yaml; tests/test_provider_yaml_sync.py).
            rate_limit_rps=0.5,
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
            # Missing risks must stay UNKNOWN (never []). Empty risks ⇒ no named honeypot.
            risks = data["risks"] if "risks" in data else None
            if "mintAuthority" in data:
                has_mint = bool(data.get("mintAuthority"))
            else:
                has_mint = None
            if "freezeAuthority" in data:
                has_freeze = bool(data.get("freezeAuthority"))
            else:
                has_freeze = None
            if risks is None:
                is_honeypot = None
            else:
                is_honeypot = any(
                    r.get("level") == "danger" and "honeypot" in str(r.get("name", "")).lower()
                    for r in risks
                )
            top = data.get("topHoldersPercent")
            try:
                top_pct = float(top) if top not in (None, "") else None
            except (TypeError, ValueError):
                top_pct = None
            sec = SecuritySignals(
                is_honeypot=is_honeypot,
                has_mint_authority=has_mint,
                has_freeze_authority=has_freeze,
                top10_holder_concentration_pct=top_pct,
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
                has_freeze_authority=_flag("isFreezable"),
                is_blacklisted=_flag("isBlacklisted"),
                is_ownership_renounced=_flag("isOwnershipRenounced"),
                is_proxy=_flag("isProxy"),
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
