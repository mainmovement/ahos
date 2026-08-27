#!/usr/bin/env python3
"""AHOS Prediction → Observation lifecycle bridge (Lane B).

WHY
---
ScoreLedger predictions and Lane-A outcome labels share `token_id`, but the
opportunity pipeline historically wrote only to `production_observations` and
never called the frozen Lane-A registration APIs. Result: hundreds of `local`
predictions with zero `outcome_label` rows → calibration `no_matching_label`.

This module is the missing deterministic link. It does NOT:

  * invent prices or outcomes
  * rewrite historical scores
  * modify Lane-A source files
  * accelerate T+72h resolution
  * fabricate calibration pairs

It ONLY calls frozen Lane-A APIs:

  upsert_token → register_discovery → record_observation → on_observation

so that subsequent `--observation-cycle` runs can poll, close horizons at
T+72h via `lifecycle.sweep`, and materialize genuine outcome labels.

Provenance: every observation carries provider + retrieved_ts + raw_ref.
Missing metrics stay NULL.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from config.paths import get_discovery_db_path

# Metric keys Lane-A discovery_observations accepts (discovery/observations.py).
_LANE_A_METRIC_KEYS = (
    "price_usd", "liquidity_usd", "fdv", "market_cap",
    "volume_5m", "volume_1h", "volume_6h", "volume_24h",
    "txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells",
    "txns_24h_buys", "txns_24h_sells",
    "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
    "pair_age_minutes", "boost_amount",
)

# Map collector / MarketMetrics names → Lane-A column names.
_METRIC_ALIASES = {
    "fdv_usd": "fdv",
    "market_cap_usd": "market_cap",
}

LIFECYCLE_BRIDGE_VERSION = "prediction_lifecycle:v1"


@dataclass
class RegistrationResult:
    attempted: int = 0
    registered: int = 0          # new observation_state rows (first seen)
    observations_written: int = 0
    skipped: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)
    token_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "ahos.prediction_lifecycle_registration.v1",
            "version": LIFECYCLE_BRIDGE_VERSION,
            "attempted": self.attempted,
            "registered": self.registered,
            "observations_written": self.observations_written,
            "skipped": self.skipped,
            "errors": list(self.errors),
            "token_ids": list(self.token_ids),
        }


def _normalize_metrics(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map provider/collector metric names onto Lane-A columns; drop unknowns."""
    out: dict[str, Any] = {}
    if not raw:
        return out
    for k, v in raw.items():
        key = _METRIC_ALIASES.get(k, k)
        if key in _LANE_A_METRIC_KEYS:
            out[key] = v  # may be None — honesty preserved
    return out


def _record_to_ingest_dict(rec: Any) -> dict[str, Any] | None:
    """Accept CollectedObservationRecord or a Mapping with the same fields."""
    if rec is None:
        return None
    if hasattr(rec, "token_address"):
        chain = getattr(rec, "chain", None)
        address = getattr(rec, "token_address", None)
        if not chain or not address:
            return None
        metrics = getattr(rec, "metrics", None) or {}
        if hasattr(metrics, "__dataclass_fields__"):
            metrics = asdict(metrics)
        return {
            "chain": chain,
            "address": address,
            "symbol": getattr(rec, "symbol", None),
            "name": getattr(rec, "name", None),
            "provider": getattr(rec, "provider_source", None) or "unknown",
            "retrieved_ts": float(getattr(rec, "retrieved_ts", time.time())),
            "raw_sha": getattr(rec, "raw_evidence_hash", None) or "missing_raw",
            "metrics": _normalize_metrics(metrics),
            "pair_address": None,
            "dex": None,
        }
    if isinstance(rec, Mapping):
        chain = rec.get("chain")
        address = rec.get("token_address") or rec.get("address")
        if not chain or not address:
            return None
        return {
            "chain": chain,
            "address": address,
            "symbol": rec.get("symbol"),
            "name": rec.get("name"),
            "provider": rec.get("provider_source") or rec.get("provider") or "unknown",
            "retrieved_ts": float(rec.get("retrieved_ts") or time.time()),
            "raw_sha": rec.get("raw_evidence_hash") or rec.get("raw_ref") or "missing_raw",
            "metrics": _normalize_metrics(rec.get("metrics") or {}),
            "pair_address": rec.get("pair_address"),
            "dex": rec.get("dex_id") or rec.get("dex"),
        }
    return None


def register_for_observation(
    records: Iterable[Any],
    *,
    discovery_db: str | None = None,
    now: float | None = None,
    conn: sqlite3.Connection | None = None,
) -> RegistrationResult:
    """Seed Lane-A observation lifecycle for scored/collected candidates.

    Idempotent: existing tokens get additional observations; observation_state
    uses ON CONFLICT DO NOTHING for first registration.
    """
    from discovery import lifecycle
    from discovery import observations as obs

    ts = time.time() if now is None else now
    result = RegistrationResult()
    own_conn = conn is None
    if own_conn:
        conn = obs.open_store(discovery_db or get_discovery_db_path())

    try:
        for raw in records:
            result.attempted += 1
            payload = _record_to_ingest_dict(raw)
            if payload is None:
                result.skipped += 1
                result.errors.append({"error": "invalid_record", "detail": type(raw).__name__})
                continue
            try:
                # Ensure raw payload row exists for FK integrity when possible.
                raw_sha = payload["raw_sha"]
                if raw_sha and raw_sha != "missing_raw":
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO raw_payloads"
                            "(payload_sha256,provider,endpoint,retrieved_ts,http_status,payload_json)"
                            " VALUES (?,?,?,?,?,?)",
                            (raw_sha, payload["provider"], "pipeline_bridge",
                             payload["retrieved_ts"], None,
                             json.dumps({"bridge": LIFECYCLE_BRIDGE_VERSION}, sort_keys=True)),
                        )
                    except sqlite3.Error:
                        pass

                tok = obs.upsert_token(
                    conn,
                    payload["chain"],
                    payload["address"],
                    first_seen_ts=payload["retrieved_ts"],
                    provider=payload["provider"],
                    symbol=payload.get("symbol"),
                    name=payload.get("name"),
                )
                existed = conn.execute(
                    "SELECT 1 FROM observation_state WHERE token_id=?", (tok,)
                ).fetchone()
                lifecycle.register_discovery(conn, tok, payload["retrieved_ts"])
                if existed is None:
                    # first registration into the active set
                    if conn.execute(
                        "SELECT 1 FROM observation_state WHERE token_id=?", (tok,)
                    ).fetchone():
                        result.registered += 1

                pid = None
                if payload.get("pair_address"):
                    pid = obs.upsert_pair(
                        conn,
                        payload["chain"],
                        payload.get("dex") or "unknown",
                        payload["pair_address"],
                        tok,
                        payload["retrieved_ts"],
                        payload["provider"],
                        raw_sha,
                    )

                oid = obs.record_observation(
                    conn,
                    tok,
                    payload["provider"],
                    payload["retrieved_ts"],
                    raw_sha,
                    pair=pid,
                    metrics=payload["metrics"],
                )
                del oid  # observation id retained in Lane-A store
                lifecycle.on_observation(conn, tok, payload["retrieved_ts"])
                result.observations_written += 1
                result.token_ids.append(tok)
            except Exception as e:  # noqa: BLE001 — never abort a scoring cycle
                result.errors.append({
                    "error": type(e).__name__,
                    "detail": str(e)[:160],
                    "address": str(payload.get("address", ""))[:20],
                })
                result.skipped += 1
        if own_conn:
            conn.commit()
        else:
            conn.commit()
    finally:
        if own_conn and conn is not None:
            conn.close()
    return result


def backfill_from_production_observations(
    *,
    discovery_db: str | None = None,
    limit: int | None = None,
    now: float | None = None,
) -> RegistrationResult:
    """Register existing production_observations into Lane-A (real rows only).

    Does not invent metrics. Reads whatever was already persisted by the
    collector. Safe to re-run (idempotent registration + INSERT OR IGNORE obs).
    """
    path = discovery_db or get_discovery_db_path()
    from discovery import observations as obs

    conn = obs.open_store(path)
    try:
        sql = (
            "SELECT token_address, chain, symbol, name, provider_source, "
            "retrieved_ts, raw_evidence_hash, "
            "price_usd, liquidity_usd, volume_1h, volume_24h, metrics_json "
            "FROM production_observations ORDER BY retrieved_ts ASC"
        )
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as e:
        conn.close()
        r = RegistrationResult()
        r.errors.append({"error": type(e).__name__, "detail": str(e)[:160]})
        return r

    records = []
    for row in rows:
        metrics: dict[str, Any] = {}
        raw_json = row["metrics_json"] if "metrics_json" in row.keys() else None
        if isinstance(raw_json, str) and raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict):
                    metrics.update(parsed)
            except json.JSONDecodeError:
                pass
        # Flat columns win when present (collector dual-writes them).
        for k in ("price_usd", "liquidity_usd", "volume_1h", "volume_24h"):
            try:
                v = row[k]
            except (IndexError, KeyError):
                v = None
            if v is not None:
                metrics[k] = v
        records.append({
            "token_address": row["token_address"],
            "chain": row["chain"],
            "symbol": row["symbol"],
            "name": row["name"],
            "provider_source": row["provider_source"],
            "retrieved_ts": row["retrieved_ts"],
            "raw_evidence_hash": row["raw_evidence_hash"],
            "metrics": metrics,
        })
    result = register_for_observation(records, now=now, conn=conn)
    conn.close()
    return result


def lifecycle_status(*, discovery_db: str | None = None,
                     ledger_db: str | None = None) -> dict[str, Any]:
    """Read-only census of the prediction→outcome pipeline."""
    from config.paths import get_local_db_path

    disc = discovery_db or get_discovery_db_path()
    led = ledger_db or get_local_db_path()
    out: dict[str, Any] = {
        "schema": "ahos.prediction_lifecycle_status.v1",
        "version": LIFECYCLE_BRIDGE_VERSION,
        "discovery_db": disc,
        "ledger_db": led,
        "observation_state": {},
        "outcome_labels": 0,
        "discovery_observations": 0,
        "production_observations": 0,
        "local_predictions": 0,
        "eligible_join_pairs_estimate": 0,
        "notes": [],
    }

    try:
        dconn = sqlite3.connect(disc)
        dconn.row_factory = sqlite3.Row
        rows = dconn.execute(
            "SELECT state, COUNT(*) AS c FROM observation_state GROUP BY state"
        ).fetchall()
        out["observation_state"] = {r["state"]: r["c"] for r in rows}
        out["outcome_labels"] = dconn.execute(
            "SELECT COUNT(*) FROM outcome_label").fetchone()[0]
        out["discovery_observations"] = dconn.execute(
            "SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
        try:
            out["production_observations"] = dconn.execute(
                "SELECT COUNT(*) FROM production_observations").fetchone()[0]
        except sqlite3.Error:
            out["production_observations"] = 0
        dconn.close()
    except sqlite3.Error as e:
        out["notes"].append(f"discovery_read_error: {e}")

    try:
        lconn = sqlite3.connect(led)
        out["local_predictions"] = lconn.execute(
            "SELECT COUNT(*) FROM opportunity_score_ledger WHERE source='local'"
        ).fetchone()[0]
        lconn.close()
    except sqlite3.Error as e:
        out["notes"].append(f"ledger_read_error: {e}")

    if not out["observation_state"]:
        out["notes"].append(
            "Lane-A observation_state empty — predictions cannot join outcomes "
            "until register_for_observation / backfill runs"
        )
    if out["local_predictions"] and not out["outcome_labels"]:
        out["notes"].append(
            "CALIBRATION_READY_BUT_DATA_REQUIRED — await T+72h RESOLVED + materialize"
        )
    return out
