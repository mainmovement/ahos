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
import logging
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

logger = logging.getLogger("ahos.collector")


# PAL-aligned breaker contracts (discovery/providers.yaml, Lane-A frozen).
# Month 2 rate/breaker sync law (ROADMAP_v3 §2, tests/test_provider_yaml_sync.py):
# the architecture collector must never open later or recover sooner than the
# frozen PAL contract for the same provider_id.
PAL_BREAKER_CONFIGS: dict[str, CircuitBreakerConfig] = {
    "dexscreener": CircuitBreakerConfig(failure_threshold=3, recovery_timeout_sec=120.0),
    "geckoterminal": CircuitBreakerConfig(failure_threshold=3, recovery_timeout_sec=120.0),
    "goplus": CircuitBreakerConfig(failure_threshold=2, recovery_timeout_sec=300.0),
    "rugcheck": CircuitBreakerConfig(failure_threshold=3, recovery_timeout_sec=180.0),
}


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
            pid: CircuitBreaker(pid, PAL_BREAKER_CONFIGS[pid])
            for pid in PAL_BREAKER_CONFIGS
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
            # Month-1 GAP-002 fix: durable provider-failure events (previously a
            # provider outage was visible only as "candidates=0" — ambiguous with
            # an honestly empty market, and breaker state died with the process).
            conn.execute(
                """CREATE TABLE IF NOT EXISTS provider_failure_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_ts REAL NOT NULL,
                    event_utc TEXT NOT NULL,
                    kind TEXT NOT NULL,             -- FETCH_ERROR | BREAKER_OPEN_SKIP
                    provider_id TEXT NOT NULL,
                    chain TEXT NOT NULL,
                    error_class TEXT,
                    error_detail TEXT
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
            if not provider:
                self._record_provider_event("BREAKER_OPEN_SKIP", pid, chain, "provider_missing", None)
                continue
            if cb and not cb.allow_request(now=ts):
                self._record_provider_event("BREAKER_OPEN_SKIP", pid, chain, "circuit_open", None)
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
            except Exception as e:  # GAP-002: fail closed AND stay observable
                if cb:
                    cb.record_failure(now=ts)
                self._record_provider_event("FETCH_ERROR", pid, chain,
                                            type(e).__name__, str(e)[:200])

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

    def _record_provider_event(self, kind: str, provider_id: str, chain: str,
                               error_class: str, error_detail: str | None) -> None:
        """Durable, visible provider failure/skip event (GAP-002 fix).

        Logs a WARNING (or DEBUG for breaker skips) and appends to
        provider_failure_events so outages survive process restarts and are
        reconstructible from committed stores alone.
        """
        ts = time.time()
        detail = f"provider={provider_id} chain={chain} kind={kind} err={error_class}"
        if kind == "FETCH_ERROR":
            logger.warning("collector provider failure: %s detail=%s", detail, error_detail)
        else:
            logger.debug("collector breaker skip: %s", detail)
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO provider_failure_events"
                "(event_ts, event_utc, kind, provider_id, chain, error_class, error_detail) "
                "VALUES (?,?,?,?,?,?,?)",
                (ts, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)), kind,
                 provider_id, chain, error_class, error_detail),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error:
            logger.warning("provider_failure_events write failed for %s", detail)

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
