#!/usr/bin/env python3
"""Paper Trading Lab — ENTRY RULES. Versioned deterministic policies; no edge is claimed.

PT-BASELINE-v1 (truth baseline): young + liquid-enough + not-security-vetoed.
Rationale published WITH the card; thresholds were chosen a priori (before any paper
result) and are LOCKED — changing any constant = a new strategy version (directive §4/§9).
"""
from __future__ import annotations

BASELINE_V1 = {
    "version": "PT-BASELINE-v1",
    "created": "2026-08-12",
    "hypothesis": ("Transparent naive baseline: newly discovered tokens that are liquid enough for "
                   "honest execution modeling and free of CRITICAL security vetoes. This is a TRUTH "
                   "BASELINE for cost/liquidity reality — NO profitability claim is made or implied."),
    "max_token_age_hours": 24.0,
    "min_liquidity_usd": 10_000.0,
    "require_price_known": True,
    "require_security_not_veto": True,   # PASS / PASS_WITH_UNKNOWN allowed; veto ⇒ reject
    "notional_usd": 1_000.0,
    "exit_rules": "PT-X1-v1",
    "cost_model": "PT-COST-v1",
    "data_window": "live E-01 stream from 2026-08-12",
    "sample_size_target": "descriptive; ≥30 closed trades before any expectancy statement",
    "failure_criteria": ("net expectancy ≤ 0 across ≥30 closed trades ⇒ baseline stands as "
                         "negative evidence, preserved, never rescued"),
    "success_criteria": ("descriptive statistics only; ANY promotion requires independent validation "
                         "protocol (none exists yet by design)"),
}

# EPS-dust guard (R-23): provider floating-point dust (≈-1e-14) is treated as UNKNOWN-quality data,
# never as a tradeable signal.
_EPS = 1e-9


def evaluate_entry(*, now: float, first_seen_ts: float, price_usd: float | None,
                   liquidity_usd: float | None, security: dict,
                   cfg: dict = BASELINE_V1) -> tuple[str, str]:
    """Pure function over decision-time data only. Returns (QUALIFIED_ENTRY|NOT_QUALIFIED, reason)."""
    if price_usd is None:
        return "NOT_QUALIFIED", "price UNKNOWN at decision time"
    if not (price_usd > 0):
        return "NOT_QUALIFIED", f"price non-positive ({price_usd}) — invalid data"
    if liquidity_usd is None:
        return "NOT_QUALIFIED", "liquidity UNKNOWN at decision time"
    if liquidity_usd < cfg["min_liquidity_usd"] and liquidity_usd > -_EPS:
        return "NOT_QUALIFIED", f"liquidity {liquidity_usd:.0f} < min {cfg['min_liquidity_usd']:.0f}"
    if liquidity_usd <= -_EPS:
        return "NOT_QUALIFIED", "liquidity negative beyond EPS dust — invalid data, evidence preserved"
    if liquidity_usd < cfg["min_liquidity_usd"]:   # dust-adjusted tiny negatives cannot qualify
        return "NOT_QUALIFIED", f"liquidity {liquidity_usd:.0f} < min {cfg['min_liquidity_usd']:.0f}"
    if first_seen_ts > now:
        return "NOT_QUALIFIED", "first_seen_ts in the future — clock/integrity violation"
    age_h = (now - first_seen_ts) / 3600.0
    if age_h > cfg["max_token_age_hours"]:
        return "NOT_QUALIFIED", f"age {age_h:.1f}h > {cfg['max_token_age_hours']:.0f}h"
    if cfg["require_security_not_veto"]:
        verdict = (security or {}).get("verdict", "UNKNOWN")
        if verdict == "SECURITY_VETO":
            return "NOT_QUALIFIED", "security veto: " + ",".join(security.get("veto_reasons", []))
    return "QUALIFIED_ENTRY", "baseline conditions met (age/liquidity/price/security-not-vetoed)"


# ---------------------------------------------------------------- Wave-8 experiment
BANKROLL_V2 = {
    "version": "PT-BANKROLL-v2",
    "created": "2026-08-12",
    "hypothesis": ("24h realistic experiment: with a $20.00 virtual bankroll, transparent "
                   "threshold gates, and scam/rug defense — what would ACTUALLY happen to the $20? "
                   "No edge claim; the answer may be 'the bankroll shrinks' — that is valid evidence."),
    "bankroll_start_usd": 20.00,
    "alloc_rule": "min(2.00, 0.25 * cash_now)",   # locked before any result was seen
    "min_ticket_usd": 0.50,
    "min_liquidity_usd": 5_000.0,
    "max_age_hours": 72.0,                        # segment by cohort, not by admission
    "max_exit_impact_bps": 1_500.0,               # expected exit must be absorbable (est. at entry)
    "min_resolved_critical_checks": 2,            # §C/§D: insufficient coverage ⇒ NO ENTRY
    "evm_requires": ["honeypot resolved FALSE", "sell_tax resolved below extreme threshold"],
    "require_price_known": True,
    "require_security_not_veto": True,
    "exit_rules": "PT-X2-v2",
    "cost_model": "PT-COST-v1 (+ token taxes where provider-known; UNKNOWN kept UNKNOWN)",
    "cohorts": {"NEW_LAUNCH": "<1h", "EARLY_LAUNCH": "1h–24h", "ESTABLISHED": ">=24h"},
    "data_window": "24h live experiment starting 2026-08-12",
    "sample_size_target": "whatever the 24h window honestly yields (no forced trades)",
    "failure_criteria": ("bankroll decline, trapped capital, or zero qualifying candidates are ALL "
                         "publishable outcomes — the experiment may not be 'rescued'"),
    "success_criteria": ("descriptive answers to the directive §O questions only; no profitability "
                         "claim before the ≥30-closed-trades descriptive gate"),
}


def cohort_of(age_hours: float) -> str:
    if age_hours < 1.0:
        return "NEW_LAUNCH"
    if age_hours < 24.0:
        return "EARLY_LAUNCH"
    return "ESTABLISHED"


def opportunity_class(obs: dict) -> str:
    """Qualitative banding (categorical — numeric scores remain banned pre-research-gate).
    Rule published with the card: counts available evidence bullets, nothing more."""
    bullets = 0
    liq = obs.get("liquidity_usd") or 0
    vol = obs.get("volume_24h") or 0
    if liq >= 25_000:
        bullets += 1
    if vol >= 0.5 * liq and liq > 0:
        bullets += 1
    b, s = obs.get("txns_5m_buys"), obs.get("txns_5m_sells")
    if b is not None and s is not None and b + s > 0 and b > s:
        bullets += 1
    return {0: "LOW", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}[bullets]
