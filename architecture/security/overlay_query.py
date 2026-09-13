#!/usr/bin/env python3
"""Lane B JSON adapter: consume frozen overlay evaluate_security().

TypeScript must not re-evaluate security. This module maps a JSON signal
dict onto SecuritySignals (missing → None) and returns overlay.state.
It does not copy discovery.security_gate.evaluate().
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any

from architecture.providers.contracts import SecuritySignals
from architecture.security.gate import evaluate_security
from architecture.security.identity_join import (
    SecurityAttachment,
    overlay_attachment_for_item,
)


def _tri(value: Any) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    return None


def _float_or_none(value: Any) -> float | None:
    if value is None or value is True or value is False:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None or value is True or value is False:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def signals_from_dict(raw: dict[str, Any] | None) -> SecuritySignals:
    d = raw or {}
    return SecuritySignals(
        is_honeypot=_tri(d.get("is_honeypot")),
        buy_tax_pct=_float_or_none(d.get("buy_tax_pct")),
        sell_tax_pct=_float_or_none(d.get("sell_tax_pct")),
        is_contract_verified=_tri(d.get("is_contract_verified")),
        is_ownership_renounced=_tri(d.get("is_ownership_renounced")),
        has_mint_authority=_tri(d.get("has_mint_authority")),
        has_freeze_authority=_tri(d.get("has_freeze_authority")),
        liquidity_locked_pct=_float_or_none(d.get("liquidity_locked_pct")),
        liquidity_burned_pct=_float_or_none(d.get("liquidity_burned_pct")),
        top10_holder_concentration_pct=_float_or_none(d.get("top10_holder_concentration_pct")),
        deployer_past_rug_count=_int_or_none(d.get("deployer_past_rug_count")),
        is_blacklisted=_tri(d.get("is_blacklisted")),
        cannot_sell_all=_tri(d.get("cannot_sell_all")),
        is_proxy=_tri(d.get("is_proxy")),
    )


def overlay_state_for_item(item: dict[str, Any], *, now: float) -> str:
    sec = signals_from_dict(item.get("signals") if isinstance(item.get("signals"), dict) else None)
    pair_ts = _float_or_none(item.get("pair_created_ts"))
    retrieved = _float_or_none(item.get("retrieved_ts"))
    overlay = evaluate_security(
        sec, now=now, pair_created_ts=pair_ts, retrieved_ts=retrieved,
    )
    return overlay.state.value


def run(payload: dict[str, Any], *, now: float | None = None) -> dict[str, str]:
    """Operational tokenKey → overlay.state. tokenKey is never canonical identity."""
    ts = float(now) if now is not None else time.time()
    out: dict[str, str] = {}
    tokens = payload.get("tokens") if isinstance(payload, dict) else None
    if not isinstance(tokens, list):
        return out
    for item in tokens:
        if not isinstance(item, dict):
            continue
        key = item.get("tokenKey") or item.get("token_key")
        if not key:
            continue
        # Operational lookup key only. Never treat as canonical attachment.
        out[str(key)] = overlay_state_for_item(item, now=ts)
    return out


def attachment_for_overlay_item(
    item: dict[str, Any],
    *,
    identity: Any = None,
    subject_kind: str | None = None,
) -> SecurityAttachment:
    """Classify canonical attachment for an overlay item. tokenKey is not authority."""
    return overlay_attachment_for_item(
        item, identity=identity, subject_kind=subject_kind,
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        json.dump({"states": {}, "error": "MALFORMED_INPUT"}, sys.stdout)
        return 1
    if not isinstance(payload, dict):
        json.dump({"states": {}, "error": "MALFORMED_INPUT"}, sys.stdout)
        return 1
    now = payload.get("now")
    try:
        now_f = float(now) if now is not None else None
    except (TypeError, ValueError):
        json.dump({"states": {}, "error": "MALFORMED_INPUT"}, sys.stdout)
        return 1
    states = run(payload, now=now_f)
    json.dump({"states": states}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
