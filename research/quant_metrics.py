"""AHOS Institutional Quantitative Risk & Performance Metrics Engine (QuantStats Pattern).

Pure-Python and NumPy implementation of institutional financial performance,
tail-risk, and portfolio evaluation metrics.

Metrics implemented:
- Sharpe Ratio (Annualized)
- Sortino Ratio (Downside deviation penalized)
- Calmar Ratio (CAGR over Max Drawdown)
- Omega Ratio (Gain/Loss probability mass)
- Tail Ratio (95th / 5th percentile asymmetry)
- Value at Risk (VaR 95% and 99%)
- Conditional Value at Risk (CVaR / Expected Shortfall 95% and 99%)
- Maximum Drawdown (Peak-to-Trough) and Drawdown Duration
- Win Rate, Payoff Ratio, Profit Factor
- Half-Kelly & Full-Kelly optimal allocation fraction
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union

import numpy as np


class QuantMetricsEngine:
    """Calculates institutional statistical and risk metrics from returns or equity series."""

    @staticmethod
    def returns_from_equity(
        equity_curve: Union[List[float], np.ndarray]
    ) -> np.ndarray:
        """Converts an equity curve array into periodic fractional returns."""
        eq = np.asarray(equity_curve, dtype=np.float64)
        if len(eq) < 2:
            return np.array([], dtype=np.float64)
        returns = np.diff(eq) / eq[:-1]
        # Replace non-finite values (div by zero or nan) with 0.0
        returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
        return returns

    @staticmethod
    def sharpe_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """Annualized Sharpe Ratio."""
        if len(returns) < 2:
            return 0.0
        excess = returns - (risk_free_rate / periods_per_year)
        std = np.std(excess, ddof=1)
        if std <= 1e-12:
            return 0.0
        return float((np.mean(excess) / std) * math.sqrt(periods_per_year))

    @staticmethod
    def sortino_ratio(
        returns: np.ndarray,
        target_return: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """Annualized Sortino Ratio (penalizes only downside variance)."""
        if len(returns) < 2:
            return 0.0
        excess = returns - (target_return / periods_per_year)
        downside = excess[excess < 0.0]
        if len(downside) == 0:
            return 10.0  # Zero downside observed
        downside_std = math.sqrt(np.mean(downside**2))
        if downside_std <= 1e-12:
            return 0.0
        return float((np.mean(excess) / downside_std) * math.sqrt(periods_per_year))

    @staticmethod
    def max_drawdown_and_duration(
        equity_curve: Union[List[float], np.ndarray]
    ) -> tuple[float, int]:
        """Calculates peak-to-trough Maximum Drawdown and maximum duration in periods."""
        eq = np.asarray(equity_curve, dtype=np.float64)
        if len(eq) < 2:
            return 0.0, 0
        running_max = np.maximum.accumulate(eq)
        drawdowns = (eq - running_max) / np.where(running_max > 0, running_max, 1.0)
        max_dd = float(np.min(drawdowns))  # Negative number

        # Calculate max drawdown duration
        max_duration = 0
        current_duration = 0
        for dd in drawdowns:
            if dd < 0.0:
                current_duration += 1
                if current_duration > max_duration:
                    max_duration = current_duration
            else:
                current_duration = 0

        return max_dd, max_duration

    @staticmethod
    def calmar_ratio(
        equity_curve: Union[List[float], np.ndarray],
        periods_per_year: int = 252,
    ) -> float:
        """Calmar Ratio = CAGR / |Max Drawdown|."""
        eq = np.asarray(equity_curve, dtype=np.float64)
        if len(eq) < 2:
            return 0.0
        max_dd, _ = QuantMetricsEngine.max_drawdown_and_duration(eq)
        if abs(max_dd) <= 1e-6:
            return 10.0  # Zero drawdown
        n_periods = len(eq) - 1
        total_return = (eq[-1] / eq[0]) - 1.0 if eq[0] > 0 else 0.0
        years = n_periods / periods_per_year
        if years <= 0:
            return 0.0
        cagr = (
            (1.0 + total_return) ** (1.0 / years) - 1.0 if total_return > -1.0 else -1.0
        )
        return float(cagr / abs(max_dd))

    @staticmethod
    def var_cvar(
        returns: np.ndarray, alpha: float = 0.95
    ) -> tuple[float, float]:
        """Value at Risk (VaR) and Conditional Value at Risk (CVaR / Expected Shortfall)."""
        if len(returns) < 5:
            return 0.0, 0.0
        quantile = 1.0 - alpha
        var_val = float(-np.percentile(returns, quantile * 100))
        tail_losses = returns[returns <= -var_val]
        cvar_val = (
            float(-np.mean(tail_losses)) if len(tail_losses) > 0 else var_val
        )
        return var_val, cvar_val

    @staticmethod
    def omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
        """Omega Ratio: Probability weighted ratio of gains vs losses."""
        if len(returns) < 2:
            return 0.0
        excess = returns - threshold
        gains = excess[excess > 0].sum()
        losses = -excess[excess < 0].sum()
        if losses <= 1e-12:
            return 10.0 if gains > 0 else 1.0
        return float(gains / losses)

    @staticmethod
    def tail_ratio(returns: np.ndarray) -> float:
        """Tail Ratio = |95th percentile| / |5th percentile|."""
        if len(returns) < 5:
            return 1.0
        p95 = np.percentile(returns, 95)
        p5 = np.percentile(returns, 5)
        if abs(p5) <= 1e-12:
            return 1.0
        return float(abs(p95) / abs(p5))

    @staticmethod
    def win_rate_payoff_profit_factor(
        trade_returns: Union[List[float], np.ndarray]
    ) -> tuple[float, float, float]:
        """Computes Win Rate, Payoff Ratio (Avg Win / Avg Loss), and Profit Factor."""
        tr = np.asarray(trade_returns, dtype=np.float64)
        if len(tr) == 0:
            return 0.0, 0.0, 0.0
        wins = tr[tr > 0]
        losses = tr[tr < 0]
        win_rate = float(len(wins) / len(tr))
        avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
        avg_loss = float(abs(np.mean(losses))) if len(losses) > 0 else 0.0
        payoff_ratio = float(avg_win / avg_loss) if avg_loss > 1e-12 else 10.0
        gross_profit = float(np.sum(wins)) if len(wins) > 0 else 0.0
        gross_loss = float(abs(np.sum(losses))) if len(losses) > 0 else 0.0
        profit_factor = (
            float(gross_profit / gross_loss) if gross_loss > 1e-12 else 10.0
        )
        return win_rate, payoff_ratio, profit_factor

    @staticmethod
    def kelly_fraction(win_rate: float, payoff_ratio: float) -> float:
        """Calculates Full-Kelly fraction: K = W - (1-W)/R. Clamped to [0.0, 0.5]."""
        if payoff_ratio <= 1e-6 or win_rate <= 0.0:
            return 0.0
        k = win_rate - ((1.0 - win_rate) / payoff_ratio)
        return float(max(0.0, min(0.5, k)))

    @classmethod
    def generate_tearsheet(
        cls,
        equity_curve: Union[List[float], np.ndarray],
        trade_returns: Optional[Union[List[float], np.ndarray]] = None,
        periods_per_year: int = 252,
    ) -> Dict[str, Any]:
        """Generates a complete institutional quantitative tear-sheet summary."""
        eq = np.asarray(equity_curve, dtype=np.float64)
        returns = cls.returns_from_equity(eq)
        max_dd, max_dd_dur = cls.max_drawdown_and_duration(eq)
        sharpe = cls.sharpe_ratio(returns, periods_per_year=periods_per_year)
        sortino = cls.sortino_ratio(returns, periods_per_year=periods_per_year)
        calmar = cls.calmar_ratio(eq, periods_per_year=periods_per_year)
        var95, cvar95 = cls.var_cvar(returns, alpha=0.95)
        var99, cvar99 = cls.var_cvar(returns, alpha=0.99)
        omega = cls.omega_ratio(returns)
        tail = cls.tail_ratio(returns)

        if trade_returns is not None and len(trade_returns) > 0:
            win_rate, payoff, pf = cls.win_rate_payoff_profit_factor(trade_returns)
            kelly = cls.kelly_fraction(win_rate, payoff)
            total_trades = len(trade_returns)
        else:
            win_rate, payoff, pf, kelly, total_trades = (
                0.0,
                0.0,
                0.0,
                0.0,
                0,
            )

        total_return = float((eq[-1] / eq[0]) - 1.0) if len(eq) > 1 and eq[0] > 0 else 0.0

        return {
            "initial_equity": float(eq[0]) if len(eq) > 0 else 0.0,
            "final_equity": float(eq[-1]) if len(eq) > 0 else 0.0,
            "total_return_pct": round(total_return * 100.0, 2),
            "annualized_sharpe": round(sharpe, 3),
            "annualized_sortino": round(sortino, 3),
            "calmar_ratio": round(calmar, 3),
            "max_drawdown_pct": round(abs(max_dd) * 100.0, 2),
            "max_drawdown_duration_ticks": max_dd_dur,
            "var_95_pct": round(var95 * 100.0, 3),
            "cvar_95_pct": round(cvar95 * 100.0, 3),
            "var_99_pct": round(var99 * 100.0, 3),
            "cvar_99_pct": round(cvar99 * 100.0, 3),
            "omega_ratio": round(omega, 3),
            "tail_ratio": round(tail, 3),
            "win_rate_pct": round(win_rate * 100.0, 2),
            "payoff_ratio": round(payoff, 3),
            "profit_factor": round(pf, 3),
            "kelly_fraction": round(kelly, 4),
            "total_trades": total_trades,
            "sample_periods": len(eq),
        }
