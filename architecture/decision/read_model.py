#!/usr/bin/env python3
"""Canonical decision read model — Python writes, TypeScript only reads.

This is not a second brain. It serializes CanonicalDecision objects produced
by CanonicalDecisionAuthority so Command Center / Next.js can present them.

Missing, corrupt, or stale files are UNAVAILABLE / STALE. They must never be
interpreted as BUY / WATCH / ENTER.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Iterable

from architecture.decision.authority import AUTHORITY_VERSION, CanonicalDecision
from architecture.providers.contracts import NormalizedTokenCandidate
from config.paths import get_project_root

READ_MODEL_VERSION = "canonical-decision-read-model-v1"
DEFAULT_STALE_SEC = 24 * 3600
ENV_PATH = "AHOS_CANONICAL_READ_MODEL"


def canonical_read_model_path() -> Path:
    raw = (os.environ.get("AHOS_CANONICAL_READ_MODEL") or os.environ.get(ENV_PATH) or "").strip()
    if raw:
        return Path(raw)
    return get_project_root() / "reports" / "canonical_decision_read_model.json"


def decision_token_key(chain: str | None, address: str | None) -> str:
    c = (chain or "unknown").strip().lower() or "unknown"
    a = (address or "").strip()
    if not a:
        return f"{c}:unknown"
    return f"{c}:{a.lower()}"


def _row(
    decision: CanonicalDecision,
    *,
    chain: str | None = None,
    address: str | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    advice = decision.advice
    chain = chain or (advice.chain if advice is not None else None)
    address = address or (advice.address if advice is not None else None)
    symbol = symbol or (advice.symbol if advice is not None else None)
    body = decision.to_dict()
    body.update({
        "token_key": decision_token_key(chain, address),
        "chain": chain,
        "address": address,
        "symbol": symbol,
    })
    return body


def write_canonical_read_model(
    items: Iterable[tuple[NormalizedTokenCandidate | None, CanonicalDecision]],
    *,
    now: float | None = None,
    path: Path | None = None,
    status: str = "AVAILABLE",
) -> Path:
    """Atomically persist the latest canonical decisions for UI consumption."""
    ts = time.time() if now is None else now
    dest = path or canonical_read_model_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = [_row(decision, chain=getattr(cand, "chain", None),
                 address=getattr(cand, "address", None),
                 symbol=getattr(cand, "symbol", None))
            for cand, decision in items]
    payload = {
        "version": READ_MODEL_VERSION,
        "status": status,
        "generated_ts": ts,
        "authority_version": AUTHORITY_VERSION,
        "decision_count": len(rows),
        "decisions": rows,
        "no_invented_evidence": True,
    }
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dest)
    return dest


def write_unavailable_canonical_read_model(
    *,
    reason: str,
    now: float | None = None,
    path: Path | None = None,
) -> Path:
    ts = time.time() if now is None else now
    dest = path or canonical_read_model_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": READ_MODEL_VERSION,
        "status": "UNAVAILABLE",
        "reason": reason,
        "generated_ts": ts,
        "authority_version": AUTHORITY_VERSION,
        "decision_count": 0,
        "decisions": [],
        "no_invented_evidence": True,
    }
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dest)
    return dest


def load_canonical_read_model(
    *,
    now: float | None = None,
    stale_after_sec: float = DEFAULT_STALE_SEC,
    path: Path | None = None,
) -> dict[str, Any]:
    """Fail-closed loader. Missing/corrupt ⇒ UNAVAILABLE. Aged ⇒ STALE."""
    ts = time.time() if now is None else now
    dest = path or canonical_read_model_path()
    if not dest.is_file():
        return {
            "version": READ_MODEL_VERSION,
            "status": "UNAVAILABLE",
            "reason": "missing_read_model",
            "generated_ts": None,
            "authority_version": AUTHORITY_VERSION,
            "decision_count": 0,
            "decisions": [],
            "stale": False,
            "no_invented_evidence": True,
        }
    try:
        raw = json.loads(dest.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("not_an_object")
    except Exception as exc:  # noqa: BLE001 — fail closed
        return {
            "version": READ_MODEL_VERSION,
            "status": "UNAVAILABLE",
            "reason": f"corrupt_read_model:{type(exc).__name__}",
            "generated_ts": None,
            "authority_version": AUTHORITY_VERSION,
            "decision_count": 0,
            "decisions": [],
            "stale": False,
            "no_invented_evidence": True,
        }
    generated = raw.get("generated_ts")
    stale = False
    try:
        generated_f = float(generated)
        stale = (ts - generated_f) > stale_after_sec
    except (TypeError, ValueError):
        stale = True
    status = str(raw.get("status") or "UNAVAILABLE")
    if status != "AVAILABLE":
        status = "UNAVAILABLE"
    if stale and status == "AVAILABLE":
        status = "STALE"
    decisions = []
    for row in raw.get("decisions") or []:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        if status in ("STALE", "UNAVAILABLE"):
            item["is_positive"] = False
            item["alerts_allowed"] = False
            item["paper_allowed"] = False
        decisions.append(item)
    return {
        "version": str(raw.get("version") or READ_MODEL_VERSION),
        "status": status,
        "reason": raw.get("reason"),
        "generated_ts": generated,
        "authority_version": raw.get("authority_version"),
        "decision_count": len(decisions),
        "decisions": decisions,
        "stale": stale,
        "no_invented_evidence": True,
    }


def lookup_decision(model: dict[str, Any], *, chain: str | None, address: str | None) -> dict[str, Any] | None:
    key = decision_token_key(chain, address)
    for row in model.get("decisions") or []:
        if not isinstance(row, dict):
            continue
        if row.get("token_key") == key:
            return row
        row_addr = str(row.get("address") or "").strip()
        row_chain = str(row.get("chain") or "").strip().lower()
        if row_chain == (chain or "").strip().lower() and row_addr.lower() == (address or "").strip().lower():
            return row
    return None
