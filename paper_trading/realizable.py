#!/usr/bin/env python3
"""Paper Trading Lab — REALIZABLE VALUE MODEL (PT-REALIZABLE-v1, Wave-8 continuation §2/§3/§7).

Primary truth law: DISPLAYED_VALUE (qty*price) is NEVER equated with recoverable money.
Realizable value = what an exit NOW would realistically recover after:
  executable-amount cap (linear impact ≤ EXIT_IMPACT_CAP_BPS, same liquidity model as PT-COST-v1)
  − exit slippage (PT-COST-v1, floor 25bps)
  − exit fee (PT-COST-v1 FEE_BPS on post-slip proceeds)
  − token sell tax (provider-resolved ONLY; UNKNOWN ⇒ NULL, cost_completeness PARTIAL)
  − network/gas (MODEL constant per chain — 2026-08-12 estimate, NOT a live feed; recorded as such)

All constants were locked BEFORE any results, versioned with the card. Change ⇒ new version.
"""
from __future__ import annotations

from . import cost_model as cm

MODEL_VERSION = "PT-REALIZABLE-v1"
EXIT_IMPACT_CAP_BPS = 1500.0        # inherits PT-BANKROLL-v2 max_exit_impact_bps (exitability law)
MIN_PARTIAL_NOTIONAL_USD = 0.25     # chunks smaller than this are merged into a FULL exit
MIN_EXIT_NOTIONAL_USD = 0.05        # below this an exit is economically void => treated unexitable-now
# Gas: MODEL constants (documented assumption, no live gas oracle in the lab). Deliberately
# conservative-cheap for 2026 L2 reality, still material vs $2 tickets — that IS the lesson.
GAS_MODEL_USD = {"solana": 0.02, "ethereum": 0.80, "bsc": 0.10, "base": 0.05,
                 "polygon": 0.05, "arbitrum": 0.10, "avalanche": 0.10}
GAS_DEFAULT_USD = 0.30

ROUTE_STATUSES = ("EXECUTABLE_FULL", "EXECUTABLE_PARTIAL", "UNEXITABLE_HONEYPOT",
                  "UNEXITABLE_NO_PRICE", "UNEXITABLE_NO_LIQUIDITY", "UNEXITABLE_DUST",
                  "SECURITY_RECHECK_CRITICAL")


def gas_usd(chain: str | None) -> float:
    return GAS_MODEL_USD.get((chain or "").lower(), GAS_DEFAULT_USD)


def max_executable_notional(liq_usd: float) -> float:
    """Invert the locked linear impact model: n/liq*1e4 ≤ cap ⇒ n ≤ liq*cap/1e4."""
    return liq_usd * EXIT_IMPACT_CAP_BPS / 1e4


def assess(*, qty: float, price_obs: float | None, liq_now: float | None,
           sell_tax_bps: float | None, chain: str | None,
           classification: str, fee_bps: float = cm.FEE_BPS) -> dict:
    """The §2/§3 exitability verdict for selling `qty` at observation (price, liq).

    Deduction order (locked): slip → fee on post-slip → tax on post-slip (if known) → gas.
    Returns everything the ledger needs; NEVER fabricates (UNKNOWN stays None-with-reason).
    """
    gas = gas_usd(chain)
    base = {"qty": qty, "price_observed": price_obs, "liquidity_usd": liq_now,
            "gas_cost_usd": gas, "sell_tax_bps": sell_tax_bps, "model_version": MODEL_VERSION,
            "displayed_value_usd": None, "max_executable_notional_usd": None,
            "requested_exit_notional_usd": None, "executable_exit_notional_usd": 0.0,
            "exit_slippage_bps": None, "exit_fee_usd": None, "exit_slippage_usd": None,
            "sell_tax_usd": None, "realizable_value_usd": 0.0, "unexited_displayed_usd": None,
            "sellable_full": False, "sellable_partial": False}
    if classification == "CONFIRMED_HONEYPOT":
        return base | {"route_status": "UNEXITABLE_HONEYPOT",
                       "why": "confirmed honeypot — sells blocked (provider evidence)"}
    if price_obs is None or price_obs <= 0:
        return base | {"route_status": "UNEXITABLE_NO_PRICE",
                       "why": "no fresh positive price — exit not modelable now"}
    displayed = qty * price_obs
    base["displayed_value_usd"] = displayed
    base["requested_exit_notional_usd"] = displayed
    base["unexited_displayed_usd"] = displayed
    if liq_now is None or liq_now <= 0:
        return base | {"route_status": "UNEXITABLE_NO_LIQUIDITY",
                       "why": "exit liquidity UNKNOWN/absent — displayed value not spendable"}
    max_exec = max_executable_notional(liq_now)
    base["max_executable_notional_usd"] = max_exec
    exec_notional = min(displayed, max_exec)
    if exec_notional < MIN_EXIT_NOTIONAL_USD:
        return base | {"route_status": "UNEXITABLE_DUST",
                       "why": f"executable chunk {exec_notional:.4f} < dust floor — exit void"}
    slip = cm.slippage_bps(exec_notional, liq_now)
    if slip is None:                                    # defensive; liq>0 ⇒ not None
        return base | {"route_status": "UNEXITABLE_NO_LIQUIDITY", "why": "impact unmodelable"}
    gross = exec_notional * (1 - slip / 1e4)
    fee = gross * fee_bps / 1e4
    tax = gross * sell_tax_bps / 1e4 if sell_tax_bps else None
    realizable = max(0.0, gross - fee - (tax or 0.0) - gas)
    full = displayed <= max_exec + 1e-12
    status = "EXECUTABLE_FULL" if full else "EXECUTABLE_PARTIAL"
    if classification in ("CRITICAL_RISK", "CONFIRMED_RUG", "CONFIRMED_UNEXITSABLE"):
        status = "SECURITY_RECHECK_CRITICAL"            # still priced, but flagged CRITICAL
    return base | {
        "route_status": status, "executable_exit_notional_usd": exec_notional,
        "exit_slippage_bps": slip, "exit_slippage_usd": exec_notional * slip / 1e4,
        "exit_fee_usd": fee, "sell_tax_usd": tax, "realizable_value_usd": realizable,
        "unexited_displayed_usd": max(0.0, displayed - exec_notional),
        "sellable_full": full, "sellable_partial": not full,
        "why": (f"impact-capped executable {exec_notional:.4f} of displayed {displayed:.4f}; "
                f"slip {slip:.0f}bps, fee {fee:.4f}, "
                + (f"tax {tax:.4f}" if tax is not None else "tax UNKNOWN") + f", gas {gas:.2f}")}


def executable_chunk(a: dict) -> dict:
    """§7: given an assess() verdict, the chunk to sell NOW.
    FULL = whole position executable (or the leftover is below the partial floor — merge it).
    PARTIAL = sell the impact-capped chunk, remainder keeps its own (displayed-only) truth."""
    if not a["route_status"].startswith(("EXECUTABLE", "SECURITY")):
        return {"kind": "NONE", "notional": 0.0}
    displayed = a["displayed_value_usd"] or 0.0
    remainder = displayed - a["executable_exit_notional_usd"]
    if a["sellable_full"] or remainder < MIN_PARTIAL_NOTIONAL_USD:
        return {"kind": "FULL", "notional": displayed}
    return {"kind": "PARTIAL", "notional": a["executable_exit_notional_usd"]}
