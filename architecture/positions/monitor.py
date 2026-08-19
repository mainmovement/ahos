#!/usr/bin/env python3
"""AHOS Position Monitor (AHOS-POSMON-v1).

The missing half of the loop.

The pipeline discovered tokens, vetted them and announced the good ones, and
then forgot about them. `PaperPositionManager.evaluate_position` and
`DecisionAdvisor.advise_position` both existed, both correct, and both were
called by nothing outside the test suite -- so a user who acted on an
announcement was never told when to leave. "When do I sell?" had no answer
that arrived on its own.

Two documented alert classes were dead for the same reason:
THESIS_STRENGTHENING and THESIS_INVALIDATED are registered as decisional in
the Telegram router and were emitted nowhere.

This module reviews every open position against fresh market data and turns
the advice into alerts. It decides nothing new: the exit rules stay in
`DecisionAdvisor` (EXIT_V1) and the accounting stays in the manager. It only
makes sure the answer reaches the person holding the bag.

Law:
  - Never invents a price. No data means NO_DATA, never a stale guess.
  - Every alert carries the reasoning that produced it.
  - Paper trading only: nothing here places or settles a real order.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from telegram_ai.alerts import Alert, build as build_alert

VERSION = "AHOS-POSMON-v1"

# A position whose liquidity has halved since entry is a different asset from
# the one that was bought, even when the price has not moved yet.
LIQUIDITY_HALVED = 0.5
MAX_MARKET_AGE_SEC = 4 * 3600.0


@dataclass
class PositionReview:
    """What the monitor concluded about one open position."""
    position_id: str
    symbol: str
    action: str                     # HOLD | REDUCE | EXIT | NO_DATA
    urgency: str                    # ROUTINE | SOON | IMMEDIATE
    pnl_pct: float | None
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id, "symbol": self.symbol,
            "action": self.action, "urgency": self.urgency,
            "pnl_pct": self.pnl_pct, "reasons": list(self.reasons),
            "risks": list(self.risks), "unknowns": list(self.unknowns),
            "alert_classes": [a.cls for a in self.alerts],
        }


def _alert_class_for(action: str, security: bool, invalidated: bool) -> str | None:
    """Map an exit decision onto the alert vocabulary the router already knows.

    THESIS_INVALIDATED is the strongest statement the system can make about a
    position: the reason for holding it is gone. It is reserved for that, not
    used for an ordinary stop-loss, or the word stops meaning anything.
    """
    if security:
        return "SECURITY_EVENT"
    if invalidated:
        return "THESIS_INVALIDATED"
    if action == "EXIT":
        return "RISK_INCREASING"
    if action == "REDUCE":
        return "THESIS_STRENGTHENING"   # target reached: take some off the table
    return None


class PositionMonitor:
    """Reviews open positions and raises the alerts nobody was raising.

    `price_lookup` is injected rather than imported so the monitor can be
    driven by the pipeline's already-fetched candidates instead of issuing a
    second round of provider calls for tokens it just looked at.
    """

    def __init__(self, manager, advisor, price_lookup: Callable[[str, str], dict | None]):
        self.manager = manager
        self.advisor = advisor
        self.price_lookup = price_lookup

    def review_all(self, now: float | None = None) -> list[PositionReview]:
        ts = time.time() if now is None else now
        return [self.review(p, now=ts) for p in self.manager.open_positions()]

    def review(self, position, now: float | None = None) -> PositionReview:
        ts = time.time() if now is None else now

        market = None
        try:
            market = self.price_lookup(position.chain, position.token_address)
        except Exception as exc:                      # noqa: BLE001
            # A provider failure must not be silent: an unmonitored position is
            # strictly worse than one reported as unmonitorable.
            return PositionReview(
                position_id=position.position_id, symbol=position.symbol,
                action="NO_DATA", urgency="ROUTINE", pnl_pct=None,
                reasons=["دریافت قیمت لحظه‌ای ناموفق بود — بدون داده تصمیم نمی‌گیریم"],
                unknowns=[f"قیمت فعلی ({type(exc).__name__})"],
            )

        if not market or market.get("price_usd") is None:
            return PositionReview(
                position_id=position.position_id, symbol=position.symbol,
                action="NO_DATA", urgency="ROUTINE", pnl_pct=None,
                reasons=["قیمت لحظه‌ای در دسترس نیست — موقعیت بدون داده رها نمی‌شود "
                         "اما توصیه‌ای هم صادر نمی‌شود"],
                unknowns=["قیمت فعلی"],
            )

        observed_ts = market.get("retrieved_ts")
        if observed_ts is not None and ts - float(observed_ts) > MAX_MARKET_AGE_SEC:
            return PositionReview(
                position_id=position.position_id, symbol=position.symbol,
                action="NO_DATA", urgency="ROUTINE", pnl_pct=None,
                reasons=["آخرین قیمت بیش از چهار ساعت قدمت دارد — داده کهنه مبنای خروج نیست"],
                unknowns=["قیمت تازه"],
            )

        price = float(market["price_usd"])
        liquidity = market.get("liquidity_usd")
        entry_liq = market.get("entry_liquidity_usd")
        security_alert = bool(market.get("is_honeypot")) or bool(market.get("security_alert"))

        advice = self.advisor.advise_position(
            symbol=position.symbol,
            entry_price=position.entry_price_usd,
            current_price=price,
            entry_ts=position.entry_ts,
            current_liquidity=liquidity,
            entry_liquidity=entry_liq,
            security_alert=security_alert,
            now=ts,
        )

        # A rug is an invalidation, not a stop-loss: the thesis is gone, not
        # merely wrong about timing.
        invalidated = bool(
            security_alert
            or (liquidity is not None
                and liquidity < self.advisor.exit_cfg["liq_collapse_floor_usd"])
        )

        review = PositionReview(
            position_id=position.position_id, symbol=position.symbol,
            action=advice.action, urgency=advice.urgency,
            pnl_pct=advice.pnl_pct,
            reasons=list(advice.reasons), risks=list(advice.risks),
            unknowns=list(advice.unknowns),
        )

        cls = _alert_class_for(advice.action, security_alert, invalidated)
        if cls:
            severity = {"IMMEDIATE": "HIGH", "SOON": "MED"}.get(advice.urgency, "LOW")
            evidence = [
                f"position_id={position.position_id}",
                f"entry_price={position.entry_price_usd:.8g}",
                f"current_price={price:.8g}",
            ]
            if advice.pnl_pct is not None:
                evidence.append(f"pnl_pct={advice.pnl_pct:.2f}")
            if liquidity is not None:
                evidence.append(f"liquidity_usd={liquidity:.0f}")
            review.alerts.append(build_alert(
                cls=cls, symbol=position.symbol,
                reasons=advice.reasons + advice.risks,
                evidence=evidence, severity=severity,
            ))

        return review



def sqlite_market_lookup(discovery_db: str):
    """Build a read-only lookup over the canonical Lane-A observation store."""
    import sqlite3
    from discovery.identity import token_id as canonical_token_id

    def lookup(chain: str, address: str) -> dict | None:
        try:
            subject = canonical_token_id(chain, address)
        except (TypeError, ValueError, AttributeError):
            return None
        try:
            conn = sqlite3.connect(f"file:{discovery_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute(
                    """SELECT price_usd, liquidity_usd, retrieved_ts
                       FROM discovery_observations
                       WHERE token_id=? AND price_usd IS NOT NULL
                         AND error_state IS NULL
                       ORDER BY retrieved_ts DESC LIMIT 1""",
                    (subject,),
                ).fetchone()
                gate = conn.execute(
                    """SELECT verdict FROM gate_summary WHERE token_id=?
                       ORDER BY ts DESC LIMIT 1""",
                    (subject,),
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        return {
            "price_usd": row["price_usd"],
            "liquidity_usd": row["liquidity_usd"],
            "retrieved_ts": row["retrieved_ts"],
            "security_alert": bool(gate and gate["verdict"] == "SECURITY_VETO"),
        }

    return lookup


def build_position_monitor(discovery_db: str, paper_db: str | None = None):
    """Construct the default paper-only monitor used by the runtime."""
    from architecture.decision.advisor import DecisionAdvisor
    from architecture.positions.manager import PaperPositionManager

    return PositionMonitor(
        PaperPositionManager(db_path=paper_db),
        DecisionAdvisor(),
        sqlite_market_lookup(discovery_db),
    )
