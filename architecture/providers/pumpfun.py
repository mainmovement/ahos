#!/usr/bin/env python3
"""Pump.fun launchpad provider adapter (Month 2 — M-GAP-011, "Launchpads").

pump.fun is the dominant Solana launchpad and exposes a keyless public
frontend feed of newly created coins — the honest, free way to cover the
launchpad segment of the market.

Honesty laws enforced here:
  - Discovery only. The feed has no enrichment endpoint we rely on:
    ``fetch_token_metrics`` returns an explicit UNSUPPORTED envelope (fields
    stay UNKNOWN; enrichment comes from dexscreener/geckoterminal/coingecko).
  - pump.fun is Solana-only -> every other chain is UNSUPPORTED, never a
    fabricated list.
  - Missing fields stay UNKNOWN. ``price``/``market_cap`` are only claimed
    when the payload actually carries them.
  - Creation time is mapped to ``pair_created_ts`` ONLY when parseable
    (the token's launch moment is when its bonding-curve pair starts
    trading); unparseable timestamps stay None.
  - Failure envelopes distinguish DOWN (network/5xx), RATE_LIMIT (429) and
    ERROR (payload) — a launchpad outage is never confused with an honestly
    empty market (M-GAP-002 discipline).

Segment risk: pump.fun candidates are predominantly high-risk memecoins.
This adapter only DISCOVERS them; downstream security checks
(rugcheck/goplus) and the risk/scoring layer are what decide whether a
candidate is worth an observation. The adapter itself never scores.

Runtime status: fixture-verified offline (tests/test_pumpfun_adapter.py).
Live reachability is probe-verified only (M-GAP-007 — pending host egress).
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Any

from .adapters import BaseHttpProviderAdapter
from .contracts import MarketMetrics, NormalizedTokenCandidate, ProviderResponse

# Undocumented endpoint budget -> conservative. The feed is polled once per
# discovery cycle, so 20 rpm is far more than the collector needs and leaves
# headroom for the free frontend's own throttling.
_RATE_LIMIT_RPS = 0.33
_TIMEOUT_SEC = 12.0
_SUPPORTED_CHAIN = "solana"


def _parse_iso_ts(value: Any) -> float | None:
    """'2026-08-20T01:02:03.456Z' -> epoch seconds. None on any failure."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00").replace("z", "+00:00")
        ).timestamp()
    except ValueError:
        return None


class PumpFunLaunchpadAdapter(BaseHttpProviderAdapter):
    """Keyless discovery feed for newly created pump.fun (Solana) coins."""

    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="pumpfun",
            base_url="https://frontend-api.pump.fun",
            capabilities=["discovery", "launchpad", "metadata", "market"],
            rate_limit_rps=_RATE_LIMIT_RPS,
            timeout_sec=_TIMEOUT_SEC,
            transport=transport,
        )

    def _fetch(self, path: str) -> tuple[Any, bytes, int]:
        self._rate_limit()
        req = urllib.request.Request(
            f"{self._base_url}{path}", headers={"User-Agent": "ahos/1.0"})
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), raw, status_code

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        if chain.lower() != _SUPPORTED_CHAIN:
            return ProviderResponse(
                provider_id="pumpfun", status="UNSUPPORTED", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=("pump.fun is a Solana-only launchpad; other chains "
                               "are not served (never fabricated)"),
            )
        try:
            data, raw, status_code = self._fetch(
                f"/coins?limit={max(1, min(int(limit), 50))}&offset=0&sort=created")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return ProviderResponse(
                    provider_id="pumpfun", status="RATE_LIMIT", tokens=[],
                    latency_ms=(time.time() - t0) * 1000.0, http_status=429,
                    error_message="launchpad feed rate ceiling reached (http 429)")
            if e.code >= 500:
                return ProviderResponse(
                    provider_id="pumpfun", status="DOWN", tokens=[],
                    latency_ms=(time.time() - t0) * 1000.0, http_status=e.code,
                    error_message=f"http {e.code} — provider-side failure")
            return ProviderResponse(
                provider_id="pumpfun", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=e.code,
                error_message=f"http {e.code}")
        except Exception as e:  # network / parse failures fail closed
            return ProviderResponse(
                provider_id="pumpfun", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=str(e)[:150],
            )

        rows = data if isinstance(data, list) else (data.get("coins") or data.get("data") or [])
        tokens = []
        for row in rows[:limit]:
            item = row if isinstance(row, dict) else {}
            addr = item.get("mint") or item.get("address")
            if not addr:
                continue
            metrics = MarketMetrics(
                price_usd=_num(item.get("price")),
                market_cap_usd=_num(item.get("usd_market_cap")
                                    if item.get("usd_market_cap") is not None
                                    else item.get("market_cap")),
            )
            social: dict[str, str | None] = {}
            for key, field in (("twitter", "twitter"), ("telegram", "telegram"),
                               ("website", "website")):
                val = item.get(field)
                if isinstance(val, str) and val.strip():
                    social[key] = val.strip()
            tok = NormalizedTokenCandidate(
                chain="solana",
                address=addr,
                symbol=str(item.get("symbol") or "UNKNOWN"),
                name=str(item.get("name") or "Unknown Token"),
                pair_created_ts=_parse_iso_ts(
                    item.get("created_timestamp", item.get("creation_time"))),
                metrics=metrics,
                social_presence=social,
                source_provider="pumpfun",
                retrieved_ts=time.time(),
                raw_payload_sha256=_sha(raw),
            )
            tok.identify_unknowns()
            tokens.append(tok)

        # A reachable-but-empty launchpad feed is an honest observation (no new
        # coins in the window) — still distinguishable from DOWN by status.
        return ProviderResponse(
            provider_id="pumpfun", status="OK", tokens=tokens,
            latency_ms=(time.time() - t0) * 1000.0,
            http_status=status_code, raw_sha256=_sha(raw),
        )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        return ProviderResponse(
            provider_id="pumpfun", status="UNSUPPORTED", tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message=("launchpad feed is discovery-only; enrich via "
                           "dexscreener/geckoterminal/coingecko (fields stay UNKNOWN)"),
        )


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha(raw: bytes | str) -> str:
    b = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
    return hashlib.sha256(b).hexdigest()
