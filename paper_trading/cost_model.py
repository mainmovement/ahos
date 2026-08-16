#!/usr/bin/env python3
"""Paper Trading Lab — COST MODEL v1 (locked constants; versioned, never tuned post-hoc).

Accounting contract (test-pinned):
  BUY:  exec = p_obs*(1+slip_bps/1e4); fee_entry = notional*FEE_BPS/1e4; qty = (notional-fee_entry)/exec
  SELL: exec_exit = p_exit_obs*(1-slip_bps_exit/1e4); fee_exit = qty*exec_exit*FEE_BPS/1e4
  GROSS     = qty*(p_exit_obs - p_entry_obs)          # pure price movement
  SLIPPAGE  = qty*(p_entry_exec - p_entry_obs) + qty*(p_exit_obs - p_exit_exec)
  COST      = fee_entry + fee_exit                     # fees
  NET       = GROSS - SLIPPAGE - COST
A gross-win / net-loss trade is reported as a LOSS (directive §7).
"""
from __future__ import annotations

COST_MODEL_VERSION = "PT-COST-v1"
FEE_BPS = 100.0            # 1.00% per side — taker-ish DEX reality incl. priority/gas amortization
MIN_SLIPPAGE_BPS = 25.0    # structural floor (routing + pool depth uncertainty)
IMPACT_FACTOR = 1.0        # linear impact: notional/liquidity * 1e4 bps * factor


def slippage_bps(notional_usd: float, liquidity_usd: float | None) -> float | None:
    """UNKNOWN liquidity ⇒ None (callers must record UNKNOWN, never guess execution quality)."""
    if liquidity_usd is None or liquidity_usd <= 0:
        return None
    return max(MIN_SLIPPAGE_BPS, (notional_usd / liquidity_usd) * 1e4 * IMPACT_FACTOR)


def buy(notional_usd: float, p_obs: float, liquidity_usd: float | None) -> dict | None:
    slip = slippage_bps(notional_usd, liquidity_usd)
    if slip is None or p_obs <= 0:
        return None
    exec_price = p_obs * (1 + slip / 1e4)
    fee_entry = notional_usd * FEE_BPS / 1e4
    qty = (notional_usd - fee_entry) / exec_price
    return {"exec_price": exec_price, "fee_entry_usd": fee_entry, "qty": qty, "slippage_bps": slip}


def sell(qty: float, p_exit_obs: float, liquidity_usd: float | None) -> dict | None:
    slip = slippage_bps(qty * p_exit_obs, liquidity_usd)
    if slip is None or p_exit_obs <= 0:
        return None
    exec_price = p_exit_obs * (1 - slip / 1e4)
    gross_proceeds = qty * exec_price
    fee_exit = gross_proceeds * FEE_BPS / 1e4
    return {"exec_price": exec_price, "fee_exit_usd": fee_exit, "slippage_bps": slip,
            "net_proceeds": gross_proceeds - fee_exit}


def pnl_decomposition(qty: float, p_entry_obs: float, entry_exec: float, fee_entry: float,
                      p_exit_obs: float, exit_exec: float, fee_exit: float) -> dict:
    gross = qty * (p_exit_obs - p_entry_obs)
    slippage = qty * (entry_exec - p_entry_obs) + qty * (p_exit_obs - exit_exec)
    cost = fee_entry + fee_exit
    net = gross - slippage - cost
    return {"gross_pnl_usd": gross, "slippage_usd": slippage,
            "cost_total_usd": cost, "net_pnl_usd": net}
