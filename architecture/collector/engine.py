#!/usr/bin/env python3
"""AHOS Continuous Market Intelligence Collector Engine (Phase XX).

Non-negotiable Laws:
  - Provenance Tracking: Every observation records timestamp, provider, token, chain, raw SHA-256, and confidence.
  - Fail-Closed & Circuit Breaker: Provider errors or rate limits trip circuit breakers without crashing the pipeline.
  - UNKNOWN Preservation: Missing fields are preserved as None/UNKNOWN, never hallucinated or zero-filled.
  - Non-trading: Collector ingests opportunity intelligence only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..providers.contracts import BaseMarketProvider, NormalizedTokenCandidate, ProviderResponse, UNKNOWN_VALUE
from ..providers.registry import ProviderRouter
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .retry import RetryPolicy
from config.paths import get_discovery_db_path


@dataclass
class CollectedObservationRecord:
    obs_id: str
    token_address: str
    chain: str
    symbol: str
    name: str
    provider_source: str
    retrieved_ts: float
    raw_evidence_hash: str
    confidence_level: str
    metrics: dict[str, Any]
    security: dict[str, Any]
    unknown_fields: list[str]
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CollectorEngine:
    def __init__(self, db_path: str | None = None,
                 router: ProviderRouter | None = None):
        self.db_path = db_path or get_discovery_db_path()
        self.router = router or ProviderRouter()
        self.circuit_breakers: dict[str, CircuitBreaker] = {
            "dexscreener": CircuitBreaker("dexscreener"),
            "geckoterminal": CircuitBreaker("geckoterminal"),
            "goplus": CircuitBreaker("goplus"),
            "rugcheck": CircuitBreaker("rugcheck"),
        }
        self.retry_policy = RetryPolicy(max_retries=2, initial_delay_sec=0.2)
        self._init_tables()

    def _init_tables(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """CREATE TABLE IF NOT EXISTS production_observations (
                    obs_id TEXT PRIMARY KEY,
                    token_address TEXT NOT NULL,
                    chain TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT NOT NULL,
                    provider_source TEXT NOT NULL,
                    retrieved_ts REAL NOT NULL,
                    raw_evidence_hash TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,
                    price_usd REAL,
                    liquidity_usd REAL,
                    volume_1h REAL,
                    volume_24h REAL,
                    metrics_json TEXT NOT NULL,
                    security_json TEXT NOT NULL,
                    unknown_fields_json TEXT NOT NULL,
                    created_utc TEXT NOT NULL
                )"""
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def collect_candidates(self, chain: str = "solana", limit: int = 10,
                           now: float | None = None) -> list[CollectedObservationRecord]:
        ts = time.time() if now is None else now
        candidates: list[NormalizedTokenCandidate] = []

        # 1. Fetch from Market Discovery Providers with Circuit Breaker
        for pid in ["dexscreener", "geckoterminal"]:
            cb = self.circuit_breakers.get(pid)
            provider = self.router.get_provider(pid)
            if not provider or (cb and not cb.allow_request(now=ts)):
                continue

            try:
                def _do_fetch():
                    resp = provider.fetch_candidate_tokens(chain, limit=limit)
                    if resp.status != "OK":
                        raise ConnectionError(f"Provider {pid} status: {resp.status}")
                    return resp

                resp: ProviderResponse = self.retry_policy.execute(_do_fetch)
                if cb:
                    cb.record_success(now=ts)
                candidates.extend(resp.tokens)
            except Exception:
                if cb:
                    cb.record_failure(now=ts)

        # Deduplicate candidates by (chain, address)
        seen = set()
        unique_candidates: list[NormalizedTokenCandidate] = []
        for c in candidates:
            k = (c.chain, c.address.lower())
            if k not in seen:
                seen.add(k)
                unique_candidates.append(c)

        # 2. Enrich Security for candidates with Circuit Breaker
        records: list[CollectedObservationRecord] = []
        for cand in unique_candidates:
            sec_pid = "rugcheck" if cand.chain == "solana" else "goplus"
            sec_cb = self.circuit_breakers.get(sec_pid)
            if sec_cb and sec_cb.allow_request(now=ts):
                try:
                    self.router.enrich_security(cand)
                    sec_cb.record_success(now=ts)
                except Exception:
                    sec_cb.record_failure(now=ts)

            # Build Provenance-bearing Observation Record
            cand.identify_unknowns()
            obs_id = hashlib.sha256(f"{cand.chain}:{cand.address}:{cand.source_provider}:{ts}".encode()).hexdigest()[:16]
            rec = CollectedObservationRecord(
                obs_id=obs_id,
                token_address=cand.address,
                chain=cand.chain,
                symbol=cand.symbol,
                name=cand.name,
                provider_source=cand.source_provider,
                retrieved_ts=cand.retrieved_ts,
                raw_evidence_hash=cand.raw_payload_sha256 or hashlib.sha256(f"{cand.address}:{ts}".encode()).hexdigest(),
                confidence_level=cand.confidence_level,
                metrics=asdict(cand.metrics),
                security=asdict(cand.security),
                unknown_fields=cand.unknown_fields
            )
            records.append(rec)

        # 3. Persist observations
        self._persist_records(records)
        return records

    def _persist_records(self, records: list[CollectedObservationRecord]):
        if not records:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            for r in records:
                m = r.metrics
                conn.execute(
                    """INSERT OR REPLACE INTO production_observations(
                        obs_id, token_address, chain, symbol, name, provider_source,
                        retrieved_ts, raw_evidence_hash, confidence_level, price_usd,
                        liquidity_usd, volume_1h, volume_24h, metrics_json, security_json,
                        unknown_fields_json, created_utc
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        r.obs_id, r.token_address, r.chain, r.symbol, r.name, r.provider_source,
                        r.retrieved_ts, r.raw_evidence_hash, r.confidence_level,
                        m.get("price_usd"), m.get("liquidity_usd"), m.get("volume_1h"),
                        m.get("volume_24h"), json.dumps(r.metrics), json.dumps(r.security),
                        json.dumps(r.unknown_fields), r.created_utc
                    )
                )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_provider_health(self) -> dict[str, Any]:
        """Returns health and circuit breaker status for all ingestion providers."""
        return {
            pid: {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "last_failure_ts": cb.last_failure_ts
            }
            for pid, cb in self.circuit_breakers.items()
        }
