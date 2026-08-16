#!/usr/bin/env python3
"""Paper Trading Lab — scam classification + post-entry rug defense + trapped-capital model.
§N classification is evidence-derived only; 'safe' is NEVER a possible value.
Trapped model (§B): executable value is computed, not assumed from displayed price.
"""
from __future__ import annotations

CLASSIFICATIONS = ("LOW_RISK", "MEDIUM_RISK", "HIGH_RISK", "CRITICAL_RISK",
                   "CONFIRMED_HONEYPOT", "CONFIRMED_RUG", "CONFIRMED_UNEXITSABLE", "UNKNOWN")
STATES = ("WATCHING", "QUALIFIED", "ENTRY", "OPEN", "PROFITABLE", "LOSING", "EXIT_SIGNAL",
          "EXITED_PROFIT", "EXITED_LOSS", "RISK_ESCALATION", "TRAPPED", "TOTAL_LOSS",
          "INVALID", "NO_DATA")

MEANINGFUL_RECOVERY_FRAC = 0.10     # of allocated (locked, PT-X2-v2)
LIQ_DROP_ESCALATION_FRAC = 0.50     # liq halves vs entry ⇒ risk escalation
DIVERGENCE_PRICE_UP = 2.0           # price ×2 while liq halves ⇒ divergence escalation


def classify(checks: list[dict], verdict: str, sources: dict | None = None) -> tuple[str, list[str]]:
    """§N: blunt, reason-carrying classification. Multiple reasons may stack."""
    reasons: list[str] = []
    present = {c["check_key"]: c["value"] for c in checks}
    if present.get("honeypot") == "TRUE":
        reasons.append("honeypot=TRUE (provider evidence)")
        return "CONFIRMED_HONEYPOT", reasons
    crit_true = sorted(k for k, v in present.items()
                       if v == "TRUE" and k in
                       ("sell_tax_extreme", "blacklist_function", "mint_authority_active",
                        "freeze_authority_active", "lp_not_locked_fresh_pool", "deployer_prior_rug"))
    if crit_true:
        reasons.append("CRITICAL veto evidence: " + ",".join(crit_true))
        return "CRITICAL_RISK", reasons
    high_true = sorted(k for k, v in present.items()
                       if v == "TRUE" and k in
                       ("proxy_risk_upgradeable", "ownership_renounced_absent", "holder_concentration_high"))
    n_unknown_sources = sum(1 for v in (sources or {}).values() if v != "OK")
    if (sources and all(v != "OK" for v in sources.values())):
        return "UNKNOWN", ["no security source answered OK — UNKNOWN is not PASS"]
    if verdict == "SECURITY_VETO":
        return "CRITICAL_RISK", reasons or ["verdict SECURITY_VETO"]
    if high_true:
        reasons.append("HIGH signals: " + ",".join(high_true))
        return "HIGH_RISK", reasons
    resolved = sum(1 for v in present.values() if v not in (None, "UNKNOWN"))
    if verdict == "PASS" and resolved >= 4:
        return "LOW_RISK", [f"no vetoes; {resolved} checks resolved non-UNKNOWN"]
    return "MEDIUM_RISK", [f"no vetoes; partial coverage ({resolved} resolved); residual UNKNOWN remains"]


def risk_escalation(*, entry_liq: float | None, obs_liq: float | None,
                    entry_price: float, obs_price: float | None,
                    recheck_classification: str | None, prior_escalated: bool) -> list[str]:
    """§E: post-entry danger detection. Returns escalation reasons (empty = none)."""
    out = []
    if recheck_classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK", "CONFIRMED_RUG"):
        out.append(f"security recheck ⇒ {recheck_classification}")
    if entry_liq and obs_liq is not None and obs_liq <= entry_liq * (1 - LIQ_DROP_ESCALATION_FRAC):
        out.append(f"liquidity fell {100*(1-obs_liq/entry_liq):.0f}% vs entry "
                   f"({entry_liq:.0f}→{obs_liq:.0f})")
    if (entry_liq and obs_liq is not None and obs_price is not None
            and obs_price >= entry_price * DIVERGENCE_PRICE_UP
            and obs_liq <= entry_liq * (1 - LIQ_DROP_ESCALATION_FRAC)):
        out.append("price/liquidity divergence (price ×2 while liq halved) — rug anatomy")
    return out


def recoverable_value(*, classification: str, qty: float, price_obs: float | None,
                      liq_now: float | None, sell_tax_bps: float | None,
                      slippage_bps: float | None, fee_bps: float) -> dict:
    """§B: what an exit would REALISTICALLY recover right now. Never equal to mark price
    when sellability is broken or liquidity cannot absorb the size."""
    if classification == "CONFIRMED_HONEYPOT":
        return {"recoverable": 0.0, "sellable": False, "why": "confirmed honeypot — sells blocked"}
    if price_obs is None or price_obs <= 0:
        return {"recoverable": 0.0, "sellable": False, "why": "no fresh price — treat as unexitable now"}
    if liq_now is None or liq_now <= 0:
        return {"recoverable": 0.0, "sellable": False, "why": "exit liquidity UNKNOWN/absent"}
    if slippage_bps is None:
        return {"recoverable": None, "sellable": False, "why": "impact UNKNOWN (liq≈0) — cannot model exit"}
    gross = qty * price_obs * (1 - slippage_bps / 1e4)
    tax = (gross * sell_tax_bps / 1e4) if sell_tax_bps else 0.0
    net = gross - tax - gross * fee_bps / 1e4
    return {"recoverable": max(0.0, net), "sellable": True,
            "why": f"modeled executable exit (impact {slippage_bps:.0f}bps"
                   + (f", sell tax {sell_tax_bps:.0f}bps" if sell_tax_bps else ", tax UNKNOWN") + ")"}


def trapped_status(*, allocated: float, recoverable: float | None) -> dict:
    """TRAPPED / TOTAL_LOSS determination with capital_loss math (§B)."""
    if recoverable is None:
        return {"state": "TRAPPED", "recoverable": 0.0, "capital_loss": allocated,
                "why": "exit cannot be modeled — conservatively treated as fully trapped"}
    if recoverable < allocated * MEANINGFUL_RECOVERY_FRAC:
        state = "TOTAL_LOSS" if recoverable <= 1e-12 else "TRAPPED"
        return {"state": state, "recoverable": recoverable,
                "capital_loss": allocated - recoverable,
                "why": f"recoverable {recoverable:.4f} < {MEANINGFUL_RECOVERY_FRAC:.0%} of allocated"}
    return {"state": None, "recoverable": recoverable, "capital_loss": 0.0, "why": "exit meaningful"}
