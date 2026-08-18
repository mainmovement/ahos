#!/usr/bin/env python3
"""Chain explorer provider adapter (Phase 7 — provider expansion).

Keyless Blockscout v2 API for chains with a public instance; honest
UNSUPPORTED envelopes for the rest. On-chain facts are only claimed when
the explorer actually returns them — everything else stays UNKNOWN.

Mapping discipline:
  addresses/{a}      -> is_contract (deployment existence)
  smart-contracts/{a}-> is_contract_verified, deployer_address
  tokens/{a}         -> symbol, name, exchange_rate -> price_usd

Chains WITHOUT a keyless explorer instance (bsc, avalanche, solana) return
UNSUPPORTED — their on-chain fields remain UNKNOWN downstream, never guessed.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from typing import Callable

from .adapters import BaseHttpProviderAdapter
from .contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    ProviderResponse,
    SecuritySignals,
)


class ChainExplorerAdapter(BaseHttpProviderAdapter):
    """On-chain contract verification & deployer identity via Blockscout."""

    # Public keyless Blockscout instances (chain -> base url).
    INSTANCES = {
        "ethereum": "https://eth.blockscout.com",
        "base": "https://base.blockscout.com",
        "arbitrum": "https://arbitrum.blockscout.com",
        "polygon": "https://polygon.blockscout.com",
    }
    UNSUPPORTED_CHAINS = ("bsc", "avalanche", "solana")  # no keyless explorer yet

    def __init__(self, transport: Callable = urllib.request.urlopen):
        super().__init__(
            provider_id="chain_explorer",
            base_url="https://eth.blockscout.com",   # default instance; per-chain override below
            capabilities=["onchain", "security", "contract-verification"],
            rate_limit_rps=1.0,
            timeout_sec=12.0,
            transport=transport,
        )

    def _get(self, base: str, path: str) -> tuple[dict | None, int]:
        """Single GET; 404 -> (None, 404) meaning 'not found', never an error envelope."""
        self._rate_limit()
        req = urllib.request.Request(f"{base}{path}", headers={"User-Agent": "ahos/1.0"})
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), status_code

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        return ProviderResponse(
            provider_id="chain_explorer",
            status="UNSUPPORTED",
            tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message="explorers index known addresses; discovery belongs to DEX screeners",
        )

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        ch = chain.lower()
        base = self.INSTANCES.get(ch)
        if not base:
            return ProviderResponse(
                provider_id="chain_explorer", status="UNSUPPORTED", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=(f"no keyless explorer instance for chain '{ch}'; "
                               f"on-chain fields stay UNKNOWN (never invented)"),
            )

        raw_concat = b""
        is_contract: bool | None = None
        verified: bool | None = None
        deployer: str | None = None
        symbol: str | None = None
        name: str | None = None
        price: float | None = None
        http_status: int | None = None
        try:
            try:
                addr_data, http_status = self._get(base, f"/api/v2/addresses/{address}")
                raw_concat += json.dumps(addr_data or {}).encode()
                is_contract = bool(addr_data.get("is_contract")) if addr_data else None
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise

            try:
                sc_data, _ = self._get(base, f"/api/v2/smart-contracts/{address}")
                raw_concat += json.dumps(sc_data or {}).encode()
                if sc_data:
                    verified = bool(sc_data.get("is_verified", sc_data.get("verified")))
                    deployer = sc_data.get("address") or None
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise   # unverified contract -> 404 on this endpoint is normal

            try:
                tok_data, _ = self._get(base, f"/api/v2/tokens/{address}")
                raw_concat += json.dumps(tok_data or {}).encode()
                if tok_data:
                    symbol = (tok_data.get("symbol") or "").upper() or None
                    name = tok_data.get("name") or None
                    price = tok_data.get("exchange_rate")
                    if price is not None:
                        price = float(price)
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise   # address is not an indexed token -> fine

        except Exception as e:  # network/5xx fail closed
            return ProviderResponse(
                provider_id="chain_explorer", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=str(e)[:150],
            )

        security = SecuritySignals(
            is_contract_verified=verified,
            deployer_address=deployer,
        )
        metrics = MarketMetrics(price_usd=price) if price is not None else MarketMetrics()

        candidate = NormalizedTokenCandidate(
            chain=ch,
            address=address,
            symbol=symbol or "",
            name=name or "",
            metrics=metrics,
            security=security,
            source_provider="chain_explorer",
            raw_payload_sha256=hashlib.sha256(raw_concat).hexdigest(),
        )
        candidate.identify_unknowns()
        return ProviderResponse(
            provider_id="chain_explorer", status="OK", tokens=[candidate],
            http_status=http_status, latency_ms=(time.time() - t0) * 1000.0,
        )
