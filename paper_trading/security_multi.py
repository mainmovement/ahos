#!/usr/bin/env python3
"""Paper Trading Lab — multi-signal security evaluation (Wave-8 §C/§D).

Reuses the FROZEN Track-A registry (VETO_REGISTRY / evaluate) as READ-ONLY authority.
NEW here (Track-B internal): the GoPlus→registry normalizer, which did not exist before.
Mapping law: a field absent in the payload ⇒ check value UNKNOWN — never FALSE, never TRUE.
Numeric tax thresholds are locked constants below (chosen pre-result, versioned with the card).
True sell-simulation via API is NOT freely available anywhere we probed (recorded UNKNOWN);
for EVM, GoPlus honeypot verdict (their simulation-based check) is the documented proxy.
"""
from __future__ import annotations

from discovery.pal import PAL
from discovery.security_gate import (CRITICAL, VETO_REGISTRY, checks_from_rugcheck,
                                     evaluate, lp_fresh_pool_check)

EXTREME_SELL_TAX = 0.20     # catastrophic sell tax (locked, pre-registered with PT-BANKROLL-v2)
MIN_RESOLVED_CRITICAL = 2   # fewer resolved CRITICAL checks ⇒ insufficient coverage ⇒ NO ENTRY


def checks_from_goplus(payload: dict) -> list[dict]:
    """GoPlus token_security payload → registry checks. Missing field ⇒ UNKNOWN (law)."""
    tok = None
    if isinstance(payload, dict):
        res = payload.get("result")
        if isinstance(res, dict) and res:
            tok = next(iter(res.values()))
    out = []

    def add(key, value):
        if key in VETO_REGISTRY:
            out.append({"check_key": key, "value": value,
                        "severity": VETO_REGISTRY[key], "provider": "goplus"})

    def flag(field, key):
        if tok is None:
            add(key, "UNKNOWN")
            return
        v = tok.get(field)
        add(key, "UNKNOWN" if v is None else ("TRUE" if str(v) in ("1", "true", "True") else "FALSE"))

    flag("is_honeypot", "honeypot")
    flag("is_blacklisted", "blacklist_function")
    flag("is_mintable", "mint_authority_active")
    flag("is_proxy", "proxy_risk_upgradeable")            # HIGH severity row
    if tok is not None and "hidden_owner" in tok:
        flag("hidden_owner", "ownership_renounced_absent")
    else:
        add("ownership_renounced_absent", "UNKNOWN")
    # sell tax: extreme threshold (locked). Present-as-number required; else UNKNOWN.
    st = tok.get("sell_tax") if tok else None
    try:
        v = float(st)
        add("sell_tax_extreme", "TRUE" if v >= EXTREME_SELL_TAX else "FALSE")
    except (TypeError, ValueError):
        add("sell_tax_extreme", "UNKNOWN")
    # deployer/holder evidence unavailable from this endpoint → UNKNOWN, recorded
    add("deployer_prior_rug", "UNKNOWN")
    add("holder_concentration_high", "UNKNOWN")
    return out


def resolved_critical_count(checks: list[dict]) -> int:
    return sum(1 for c in checks
               if c["check_key"] in CRITICAL and c["value"] not in (None, "UNKNOWN"))


def evaluate_candidate(pal: PAL, chain: str, address: str, now: float,
                       pair_created_ts: float | None, lp_locked_pct: float | None) -> dict:
    """Strongest available free analysis per chain. Returns checks + verdict + coverage math
    + per-field taxes (UNKNOWN stays UNKNOWN) + availability of each source, probe-honest."""
    sources, checks, taxes = {}, [], {"buy_tax_bps": None, "sell_tax_bps": None,
                                      "transfer_tax_bps": None}
    if chain == "solana":
        env = pal.call("security_sol", "summary", address=address, now=now)
        sources["rugcheck"] = env["availability"]
        if env["availability"] == "OK":
            checks = checks_from_rugcheck(env["payload"] or {})
            meta_lp = next((c.get("num") for c in checks if c["check_key"] == "_lp_locked_pct"), lp_locked_pct)
            checks.append({"check_key": "lp_not_locked_fresh_pool",
                           "value": lp_fresh_pool_check(meta_lp, pair_created_ts, now),
                           "severity": "CRITICAL", "provider": "rugcheck+pairs"})
    else:
        env = pal.call("security_evm", "token_security", chain=chain, address=address, now=now)
        sources["goplus"] = env["availability"]
        if env["availability"] == "OK":
            checks = checks_from_goplus(env["payload"] or {})
            tok = next(iter((env["payload"] or {}).get("result", {}).values()), {}) \
                if isinstance(env["payload"], dict) else {}
            def _taxbps(f):
                try:
                    return round(float(tok[f]) * 10_000, 2)
                except (TypeError, ValueError, KeyError):
                    return None
            taxes = {"buy_tax_bps": _taxbps("buy_tax"), "sell_tax_bps": _taxbps("sell_tax"),
                     "transfer_tax_bps": _taxbps("transfer_tax")}
    verdict = evaluate(checks)
    verdict.update(sources=sources, resolved_critical=resolved_critical_count(checks),
                   taxes=taxes, checks=checks,
                   sell_simulation="NOT_AVAILABLE_FREE_API — UNKNOWN" if chain == "solana"
                   else ("PROXY:goplus_is_honeypot" if sources.get("goplus") == "OK" else "UNKNOWN"))
    return verdict


def coverage_sufficient(chain: str, sec: dict) -> tuple[bool, str]:
    """§C/§D: insufficient security coverage ⇒ NO ENTRY. Unknown is never treated as PASS."""
    if all(v != "OK" for v in (sec.get("sources") or {"none": "DOWN"}).values()):
        return False, "all security sources unavailable → coverage UNKNOWN → no-entry"
    if sec["resolved_critical"] < MIN_RESOLVED_CRITICAL:
        return False, (f"resolved CRITICAL checks {sec['resolved_critical']} < "
                       f"{MIN_RESOLVED_CRITICAL} → insufficient coverage")
    return True, "coverage sufficient (source OK, resolved minimum met)"
