#!/usr/bin/env python3
"""AHOS Provider Contracts & Abstract Interfaces (Section VII).

Enforces:
  - Strict UNKNOWN representation: Missing or uncollected data is NEVER guessed.
  - Provable Source Provenance: Every datapoint carries source provider ID, timestamp, and SHA-256 raw digest.
  - Fail-Closed: Rate limit, connection, or schema errors return normalized error envelopes.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any

UNKNOWN_VALUE = None


@dataclass
class MarketMetrics:
    price_usd: float | None = UNKNOWN_VALUE
    liquidity_usd: float | None = UNKNOWN_VALUE
    volume_5m: float | None = UNKNOWN_VALUE
    volume_1h: float | None = UNKNOWN_VALUE
    volume_24h: float | None = UNKNOWN_VALUE
    volume_velocity: float | None = UNKNOWN_VALUE
    fdv_usd: float | None = UNKNOWN_VALUE
    market_cap_usd: float | None = UNKNOWN_VALUE
    price_change_5m: float | None = UNKNOWN_VALUE
    price_change_1h: float | None = UNKNOWN_VALUE
    price_change_6h: float | None = UNKNOWN_VALUE
    price_change_24h: float | None = UNKNOWN_VALUE
    txns_5m_buys: int | None = UNKNOWN_VALUE
    txns_5m_sells: int | None = UNKNOWN_VALUE
    txns_1h_buys: int | None = UNKNOWN_VALUE
    txns_1h_sells: int | None = UNKNOWN_VALUE


@dataclass
class SecuritySignals:
    is_honeypot: bool | None = UNKNOWN_VALUE
    buy_tax_pct: float | None = UNKNOWN_VALUE
    sell_tax_pct: float | None = UNKNOWN_VALUE
    is_contract_verified: bool | None = UNKNOWN_VALUE
    is_ownership_renounced: bool | None = UNKNOWN_VALUE
    has_mint_authority: bool | None = UNKNOWN_VALUE
    has_freeze_authority: bool | None = UNKNOWN_VALUE
    liquidity_locked_pct: float | None = UNKNOWN_VALUE
    liquidity_burned_pct: float | None = UNKNOWN_VALUE
    top10_holder_concentration_pct: float | None = UNKNOWN_VALUE
    deployer_address: str | None = UNKNOWN_VALUE
    deployer_past_rug_count: int | None = UNKNOWN_VALUE
    is_proxy: bool | None = UNKNOWN_VALUE
    is_upgradeable: bool | None = UNKNOWN_VALUE
    has_blacklist: bool | None = UNKNOWN_VALUE
    has_whitelist: bool | None = UNKNOWN_VALUE
    has_transfer_restriction: bool | None = UNKNOWN_VALUE


@dataclass
class NormalizedTokenCandidate:
    chain: str
    address: str
    symbol: str
    name: str
    pair_address: str | None = UNKNOWN_VALUE
    dex_id: str | None = UNKNOWN_VALUE
    pair_created_ts: float | None = UNKNOWN_VALUE
    boost_amount: float | None = UNKNOWN_VALUE   # paid DEX promotion spend, if observed
    metrics: MarketMetrics = field(default_factory=MarketMetrics)
    security: SecuritySignals = field(default_factory=SecuritySignals)
    social_presence: dict[str, str | None] = field(default_factory=dict)
    source_provider: str = "unknown"
    retrieved_ts: float = field(default_factory=time.time)
    raw_payload_sha256: str = ""
    confidence_level: str = "HIGH"               # HIGH | MED | LOW
    unknown_fields: list[str] = field(default_factory=list)

    def identify_unknowns(self) -> list[str]:
        unknowns = []
        for k, v in asdict(self.metrics).items():
            if v is None:
                unknowns.append(f"metrics.{k}")
        for k, v in asdict(self.security).items():
            if v is None:
                unknowns.append(f"security.{k}")
        if not self.social_presence:
            unknowns.append("social_presence")
        if self.pair_created_ts is None:
            unknowns.append("pair_created_ts")
        self.unknown_fields = sorted(unknowns)
        return self.unknown_fields


@dataclass
class ProviderResponse:
    provider_id: str
    status: str                                  # OK | DOWN | RATE_LIMITED | ERROR
    tokens: list[NormalizedTokenCandidate] = field(default_factory=list)
    latency_ms: float = 0.0
    http_status: int | None = None
    error_message: str | None = None
    raw_payload: Any = None
    raw_sha256: str = ""


class BaseMarketProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for the data provider."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capabilities supported (e.g. ['discovery', 'price', 'security', 'pairs'])."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Probes connectivity to provider."""
        pass

    @abstractmethod
    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        """Discovers early token candidates."""
        pass

    @abstractmethod
    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        """Fetches detailed market metrics for a token."""
        pass
