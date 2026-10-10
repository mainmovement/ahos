#!/usr/bin/env python3
"""Paper-track risk: volatility-targeted sizing and the fail-closed breaker.

DEDUP_MERGE_MAP v1.20 sets M13's acceptance to "two-source price witness, exit
rules, risk, M42 judge, M39 breaker", and AHOS_TRADING_SKILLS_v2 names the
techniques in build order 13 -> 5 -> 12. This module is §5 (sizing) and §12
(risk of ruin and kill-switches) for the paper tracks; §13 (performance evals)
lives in ``tier_gate.py``.

Everything here is PAPER_ONLY. The breaker never closes a real position --
there are none -- it stops the *paper* track from taking new risk. It is
fail-closed in the direction that matters: a risk that cannot be evaluated
trips the breaker, because an unmeasured drawdown is not a small drawdown.

§5 sizing: ``Units = (Equity * r_trade) / (k * ATR * point_value)``. For the
paper tracks the "unit" is the notional committed per trade, and ATR is
estimated from the track's own observed price series rather than assumed. A
track with no observations has no ATR, and §5 then declines to size rather than
sizing from a guess -- which is why the gold track starts at its declared
default notional and hands over once it has a volatility history.

§12: ``P(DD > L)`` over a horizon is bootstrapped from the closed-paper-trade
PnL distribution; new risk is blocked at P > 5%. The hard limits are daily
loss, weekly loss, max open risk and max per-market exposure. The bootstrap is
honest about sample size: fewer than 30 closed trades (the number the skills
file requires before any promotion claim) cannot support a ruin probability, so
the bootstrap reports UNMEASURED and the *limits* still bind -- the numeric
gate is not waived, it is reported as not-yet-evaluable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

#: The owner-approved ruin probability above which new risk is blocked
#: (TRADING_SKILLS v2 §12: "Block new risk if P > 5%").
RUIN_PROBABILITY_LIMIT = 0.05

#: Horizon for the bootstrap, in trades rather than days, so it is independent
#: of how often a track happens to cycle.
RUIN_HORIZON_TRADES = 30

#: Drawdown limit of the paper bankroll, in percent. The vision's T1 gate uses
#: 15%; the paper breaker is stricter so a paper track cannot silently approach
#: the promotion limit and present the near-miss as progress.
BREAKER_DRAWDOWN_LIMIT_PCT = 10.0

#: Hard loss limits, percent of the bankroll (§12's daily/weekly limits).
DAILY_LOSS_LIMIT_PCT = 3.0
WEEKLY_LOSS_LIMIT_PCT = 6.0

#: Maximum notional exposed in one open position, percent of equity.
MAX_OPEN_RISK_PCT = 15.0

#: Maximum aggregate exposure across one market's open positions.
MAX_PER_MARKET_PCT = 25.0

#: The skills file's promotion threshold; below this a ruin bootstrap cannot
#: support a probability claim.
MIN_TRADES_FOR_BOOTSTRAP = 30

DAY_S = 24 * 3600.0
WEEK_S = 7 * DAY_S

TRIPPED = "TRIPPED"
ARMED = "ARMED"
UNMEASURED = "UNMEASURED"


@dataclass(frozen=True)
class BreakerState:
    """The paper breaker's verdict. ``allowed`` is False on any trip."""

    state: str                        # ARMED | TRIPPED | UNMEASURED
    allowed: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    p_ruin: float | None = None
    drawdown_pct: float | None = None
    daily_loss_pct: float | None = None
    weekly_loss_pct: float | None = None
    open_exposure_pct: float | None = None


def realized_pnl_series(trades: list[dict]) -> list[float]:
    """Realised PnL per closed trade, in order, skipping unpriced entries."""
    out = []
    for t in trades or []:
        v = t.get("realized_pnl_usd")
        if v is None:
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def drawdown_pct(equity_curve: list[float]) -> float:
    """Max peak-to-trough drawdown of an equity curve, in percent.

    An empty or non-positive curve has no drawdown to measure, which the caller
    must treat as UNMEASURED rather than as a clean record.
    """
    peak = None
    worst = 0.0
    for v in equity_curve or []:
        if v <= 0:
            continue
        if peak is None or v > peak:
            peak = v
        if peak and peak > 0:
            worst = max(worst, (peak - v) / peak * 100.0)
    return worst


def loss_in_window(trades: list[dict], *, now: float, window_s: float) -> float:
    """Sum of realised losses closing inside the trailing window, as a percent
    of a reference notional. Losses only -- a profit spike does not earn credit
    against a loss limit, which is how the §12 limits are written.
    """
    total_loss = 0.0
    for t in trades or []:
        ts = t.get("exit_ts")
        v = t.get("realized_pnl_usd")
        if ts is None or v is None:
            continue
        try:
            ts = float(ts)
            v = float(v)
        except (TypeError, ValueError):
            continue
        if v < 0 and (now - ts) <= window_s:
            total_loss += -v
    return total_loss


def bootstrap_ruin_probability(
    pnls: list[float],
    *,
    horizon: int = RUIN_HORIZON_TRADES,
    drawdown_limit_pct: float = BREAKER_DRAWDOWN_LIMIT_PCT,
    bankroll: float,
    n_trials: int = 4000,
    seed: int = 0,
) -> float | None:
    """P(drawdown > limit) over `horizon` resampled closed trades.

    Resamples the *per-trade* PnL distribution with replacement, which assumes
    the future looks like the past. That assumption is exactly what makes this
    a paper-only tool: it is a bound on the historical distribution, not a
    forecast, and §12 requires it be reported alongside the bootstrap CI rather
    than quoted alone.

    Returns None when the sample cannot support the estimate.
    """
    pnls = [p for p in pnls if math.isfinite(p)]
    if len(pnls) < MIN_TRADES_FOR_BOOTSTRAP or bankroll <= 0:
        return None
    rng = random.Random(seed)
    limit = bankroll * drawdown_limit_pct / 100.0
    hits = 0
    for _ in range(n_trials):
        equity = bankroll
        peak = bankroll
        for _ in range(horizon):
            equity += rng.choice(pnls)
            peak = max(peak, equity)
            if peak > 0 and (peak - equity) >= limit:
                hits += 1
                break
    return hits / n_trials


@dataclass
class PaperBreaker:
    """Fail-closed risk gate for a paper track.

    ``check`` decides whether a new position may open. Every limit that cannot
    be evaluated trips the breaker rather than passing silently, because an
    unmeasured limit is not a satisfied limit.
    """

    bankroll: float
    drawdown_limit_pct: float = BREAKER_DRAWDOWN_LIMIT_PCT
    daily_loss_limit_pct: float = DAILY_LOSS_LIMIT_PCT
    weekly_loss_limit_pct: float = WEEKLY_LOSS_LIMIT_PCT
    max_open_risk_pct: float = MAX_OPEN_RISK_PCT
    max_per_market_pct: float = MAX_PER_MARKET_PCT
    ruin_limit: float = RUIN_PROBABILITY_LIMIT
    horizon: int = RUIN_HORIZON_TRADES

    def check(
        self,
        *,
        now: float,
        trades: list[dict] | None = None,
        equity_curve: list[float] | None = None,
        open_exposure_usd: float = 0.0,
        market_exposure_usd: float = 0.0,
        equity_usd: float | None = None,
        seed: int = 0,
    ) -> BreakerState:
        trades = list(trades or [])
        equity = self.bankroll if equity_usd is None else float(equity_usd)
        reasons: list[str] = []
        measured_any = False

        # --- drawdown over the observed equity curve ----------------------
        dd = drawdown_pct(equity_curve or [])
        if equity_curve:
            measured_any = True
            if dd > self.drawdown_limit_pct:
                reasons.append(
                    f"drawdown {dd:.2f}% > limit {self.drawdown_limit_pct:.2f}%")

        # --- trailing loss limits (losses only, §12) ----------------------
        daily_loss = loss_in_window(trades, now=now, window_s=DAY_S)
        weekly_loss = loss_in_window(trades, now=now, window_s=WEEK_S)
        if trades:
            measured_any = True
            if equity > 0:
                d_pct = daily_loss / equity * 100.0
                w_pct = weekly_loss / equity * 100.0
                if d_pct > self.daily_loss_limit_pct:
                    reasons.append(
                        f"daily loss {d_pct:.2f}% > limit "
                        f"{self.daily_loss_limit_pct:.2f}%")
                if w_pct > self.weekly_loss_limit_pct:
                    reasons.append(
                        f"weekly loss {w_pct:.2f}% > limit "
                        f"{self.weekly_loss_limit_pct:.2f}%")
            else:
                reasons.append("equity is not positive; loss limits unevaluable")

        # --- exposure caps -------------------------------------------------
        # A non-positive equity is not a measurement: it means the exposure
        # caps have no denominator. It is recorded as an unevaluable limit
        # (which trips) rather than as a zero exposure (which would pass).
        if equity > 0:
            measured_any = True
            open_pct = open_exposure_usd / equity * 100.0
            mkt_pct = market_exposure_usd / equity * 100.0
            if open_pct > self.max_open_risk_pct:
                reasons.append(
                    f"open risk {open_pct:.2f}% > limit "
                    f"{self.max_open_risk_pct:.2f}%")
            if mkt_pct > self.max_per_market_pct:
                reasons.append(
                    f"market exposure {mkt_pct:.2f}% > limit "
                    f"{self.max_per_market_pct:.2f}%")
        else:
            reasons.append("equity is not positive; exposure caps unevaluable")

        # --- risk of ruin (§12 bootstrap) ----------------------------------
        pnls = realized_pnl_series(trades)
        p_ruin = bootstrap_ruin_probability(
            pnls, horizon=self.horizon,
            drawdown_limit_pct=self.drawdown_limit_pct,
            bankroll=self.bankroll, seed=seed)
        if p_ruin is not None:
            measured_any = True
            if p_ruin > self.ruin_limit:
                reasons.append(
                    f"P(DD>{self.drawdown_limit_pct:.0f}%) = {p_ruin:.3f} > "
                    f"limit {self.ruin_limit:.2f}")

        if not measured_any:
            # No limit was evaluable at all: no closed trades, no equity curve,
            # and no positive equity to measure exposure against. This is a
            # distinct state from TRIPPED -- nothing was *violated*, nothing
            # was *satisfied* -- and it holds new risk rather than assuming the
            # unmeasured limits are fine.
            return BreakerState(UNMEASURED, False,
                                ("no risk measurement was possible yet; the "
                                 "breaker holds new risk until it can be "
                                 "evaluated",), None, None, None, None,
                                (open_exposure_usd / equity * 100.0)
                                if equity > 0 else None)
        if reasons:
            return BreakerState(TRIPPED, False, tuple(reasons), p_ruin,
                                dd if equity_curve else None,
                                (daily_loss / equity * 100.0) if equity > 0 and trades else None,
                                (weekly_loss / equity * 100.0) if equity > 0 and trades else None,
                                (open_exposure_usd / equity * 100.0) if equity > 0 else None)
        return BreakerState(ARMED, True, (), p_ruin,
                            dd if equity_curve else None,
                            (daily_loss / equity * 100.0) if equity > 0 and trades else None,
                            (weekly_loss / equity * 100.0) if equity > 0 and trades else None,
                            (open_exposure_usd / equity * 100.0) if equity > 0 else None)


# ------------------------------------------------------------- sizing §5 ----


@dataclass(frozen=True)
class SizingResult:
    notional_usd: float | None
    detail: str


def volatility_targeted_notional(
    *,
    equity_usd: float,
    observed_prices: list[float],
    risk_per_trade_pct: float = 1.0,
    atr_multiple: float = 2.0,
    max_notional_usd: float | None = None,
) -> SizingResult:
    """§5: Units = (Equity * r_trade) / (k * ATR * point_value).

    For a spot/CFD-style instrument ``point_value`` is 1, so the formula
    reduces to notional = (Equity * r) / (k * ATR). ATR is the true range over
    the observed series; with one observation there is no range and sizing
    declines rather than guessing.

    The result is a notional, not a position it can open on its own: the caller
    caps it at the breaker's exposure limits, which is why sizing and the
    breaker are in one module.
    """
    if equity_usd <= 0:
        return SizingResult(None, "equity is not positive; cannot size")
    prices = [p for p in observed_prices or [] if p and math.isfinite(p)]
    if len(prices) < 2:
        return SizingResult(
            None,
            f"only {len(prices)} observation(s); ATR is undefined, so §5 "
            f"declines to size rather than assume a volatility")
    risk = equity_usd * risk_per_trade_pct / 100.0
    atr = _atr(prices)
    if atr is None or atr <= 0:
        return SizingResult(None, "ATR computed as zero; cannot size")
    notional = risk / (atr_multiple * atr)
    if max_notional_usd is not None:
        notional = min(notional, max_notional_usd)
    if notional <= 0:
        return SizingResult(None, "sized to zero")
    return SizingResult(notional,
                        f"equity {equity_usd:.2f} * r {risk_per_trade_pct}% / "
                        f"({atr_multiple} * ATR {atr:.4f})")


def _atr(prices: list[float]) -> float | None:
    """Average true range of a close-only series, as a fraction of the mean.

    A close-only series has no high/low, so the "true range" is the absolute
    close-to-close move -- the standard close-only proxy. Returned as a
    *fraction* so it is commensurable across instruments priced in different
    units (dollars per ounce vs dollars per share).
    """
    if len(prices) < 2:
        return None
    moves = [abs(b - a) / a for a, b in zip(prices, prices[1:]) if a > 0]
    if not moves:
        return None
    return sum(moves) / len(moves)
