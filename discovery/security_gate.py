#!/usr/bin/env python3
"""AHOS STEP 7 — Security gate (veto registry, deterministic evaluator).
LAW: Security can veto opportunity. UNKNOWN ≠ PASS. Veto precedes ranking.
Verdict rows are append-only evidence; gate_summary is the current verdict at ts.
Evaluator is a pure function over check rows → testable against fixtures.
"""
from __future__ import annotations
import json, sqlite3

# Registry: check_key -> severity. TRUE means BAD. (E §2; registry, not hard-code in callers)
VETO_REGISTRY = {
    "honeypot": "CRITICAL",
    "sell_tax_extreme": "CRITICAL",
    "blacklist_function": "CRITICAL",
    "mint_authority_active": "CRITICAL",      # SOL: RugCheck
    "freeze_authority_active": "CRITICAL",    # SOL: RugCheck
    "lp_not_locked_fresh_pool": "CRITICAL",
    "deployer_prior_rug": "CRITICAL",
    "proxy_risk_upgradeable": "HIGH",
    "ownership_renounced_absent": "HIGH",
    "holder_concentration_high": "HIGH",      # Phase-3 RPC evidence
}
CRITICAL = [k for k, s in VETO_REGISTRY.items() if s == "CRITICAL"]
VALID_VALUES = ("TRUE", "FALSE", "UNKNOWN")


def record_check(conn: sqlite3.Connection, token_id: str, ts: float, provider: str,
                 check_key: str, value: str, raw_ref: str | None = None) -> None:
    if check_key not in VETO_REGISTRY:
        raise ValueError(f"unregistered check_key: {check_key}")
    if value not in VALID_VALUES:
        raise ValueError(f"invalid check value: {value}")
    conn.execute(
        "INSERT INTO security_verdicts(token_id,ts,provider,check_key,value,severity,raw_ref) VALUES (?,?,?,?,?,?,?)",
        (token_id, ts, provider, check_key, value, VETO_REGISTRY[check_key], raw_ref))


def evaluate(checks: list[dict]) -> dict:
    """Pure gate evaluation. checks: [{check_key, value, severity, provider, ts}].
    Returns {verdict, veto_reasons, unknown_critical, coverage, recommendation_cap}."""
    present = {c["check_key"]: c for c in checks}
    veto = [k for k in CRITICAL if present.get(k, {}).get("value") == "TRUE"]
    unknown_crit = [k for k in CRITICAL if present.get(k, {}).get("value") in (None, "UNKNOWN",)]
    # a critical check with NO row at all is UNKNOWN too
    unknown_crit += [k for k in CRITICAL if k not in present]
    unknown_crit = sorted(set(unknown_crit))
    total = len(CRITICAL)
    resolved = total - len(unknown_crit)
    coverage = resolved / total
    if veto:
        verdict, cap = "SECURITY_VETO", "AVOID"
    elif unknown_crit:
        verdict, cap = "PASS_WITH_UNKNOWN", "WATCH"
    else:
        verdict, cap = "PASS", "WATCH-if-early"  # early-token ceiling until research gate promotes
    return {"verdict": verdict, "veto_reasons": veto, "unknown_critical": unknown_crit,
            "coverage": round(coverage, 4), "recommendation_cap": cap}


def evaluate_token(conn: sqlite3.Connection, token_id: str, now: float) -> dict:
    rows = conn.execute(
        """SELECT check_key, value, severity, provider, ts FROM security_verdicts
           WHERE token_id=? AND ts<=? ORDER BY ts""", (token_id, now)).fetchall()
    # latest value per check_key wins (evidence supersedes by time)
    latest: dict[str, dict] = {}
    for r in rows:
        latest[r["check_key"]] = dict(r)
    result = evaluate(list(latest.values()))
    conn.execute(
        """INSERT INTO gate_summary(token_id,ts,verdict,veto_reasons,coverage,evidence_refs)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(token_id,ts) DO UPDATE SET verdict=excluded.verdict, coverage=excluded.coverage""",
        (token_id, now, result["verdict"], json.dumps(result["veto_reasons"]),
         result["coverage"], json.dumps([f"{c['check_key']}:{c['provider']}" for c in latest.values()])))
    return result


# ---------- RugCheck payload → check rows (SOL; probe-verified provider) ----------
def checks_from_rugcheck(payload: dict) -> list[dict]:
    """Normalize RugCheck report fields to gate checks. Missing field ⇒ UNKNOWN (never inferred)."""
    out = []

    def add(key, value):
        out.append({"check_key": key, "value": value, "severity": VETO_REGISTRY[key],
                    "provider": "rugcheck"})

    # freeze / mint authority: null in report = revoked; non-null = active
    for field, key in (("mintAuthority", "mint_authority_active"),
                       ("freezeAuthority", "freeze_authority_active")):
        if field in payload:
            add(key, "TRUE" if payload[field] else "FALSE")
        else:
            add(key, "UNKNOWN")
    # LP lock on fresh pools handled by caller (needs pool age) — here only raw lp signal:
    lp = payload.get("lpLockedPct")
    out.append({"check_key": "_lp_locked_pct", "value": "META", "severity": "INFO",
                "provider": "rugcheck", "num": lp})
    # named risks heuristics → registered checks
    risks = payload.get("risks") or []
    names = {str(r.get("name", "")).lower() for r in risks}
    add("honeypot", "TRUE" if any("honeypot" in n for n in names) else
        ("FALSE" if payload.get("risks") is not None else "UNKNOWN"))
    add("blacklist_function", "TRUE" if any("blacklist" in n for n in names) else "UNKNOWN")
    add("deployer_prior_rug",
        "TRUE" if any(("rug" in n and ("creator" in n or "deployer" in n)) for n in names) else "UNKNOWN")
    add("sell_tax_extreme", "TRUE" if any(("tax" in n and ("high" in n or "extreme" in n)) for n in names) else "UNKNOWN")
    return out


def lp_fresh_pool_check(lp_locked_pct, pair_created_ts, now: float, fresh_days: int = 7) -> str:
    """lp_not_locked_fresh_pool rule (needs age evidence; UNKNOWN when age unknown)."""
    if lp_locked_pct is None or pair_created_ts is None:
        return "UNKNOWN"
    young = (now - pair_created_ts) < fresh_days * 86400
    locked = lp_locked_pct > 0
    return "TRUE" if (young and not locked) else "FALSE"
