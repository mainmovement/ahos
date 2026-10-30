"""Our formulas for the cited rules. A bar's signal uses only bars up to that bar."""
from __future__ import annotations

import math


def _ret(closes: list[float], t: int, lookback: int) -> float | None:
    if t < lookback or closes[t - lookback] == 0:
        return None
    return closes[t] / closes[t - lookback] - 1.0


def ts_momentum(closes: list[float], lookback: int = 12) -> list[int]:
    out = []
    for t in range(len(closes)):
        r = _ret(closes, t, lookback)
        out.append(0 if r is None or r == 0 else (1 if r > 0 else -1))
    return out


def donchian(highs: list[float], lows: list[float], entry: int = 20, exit_n: int = 10) -> list[int]:
    signal = 0
    out = []
    for t in range(len(highs)):
        if t >= entry:
            window_h = highs[t - entry:t]
            window_l = lows[t - entry:t]
            if highs[t] > max(window_h):
                signal = 1
            elif lows[t] < min(window_l):
                signal = -1
        if t >= exit_n and signal != 0:
            if signal > 0 and lows[t] < min(lows[t - exit_n:t]):
                signal = 0
            elif signal < 0 and highs[t] > max(highs[t - exit_n:t]):
                signal = 0
        out.append(signal)
    return out


def dual_ma(closes: list[float], fast: int = 10, slow: int = 30) -> list[int]:
    out = []
    for t in range(len(closes)):
        if t + 1 < slow:
            out.append(0)
            continue
        fast_m = sum(closes[t + 1 - fast:t + 1]) / fast
        slow_m = sum(closes[t + 1 - slow:t + 1]) / slow
        out.append(0 if fast_m == slow_m else (1 if fast_m > slow_m else -1))
    return out


def cs_momentum(panels: dict[str, list[float]], lookback: int = 12, skip: int = 1) -> dict[str, int]:
    """Sign of the past return, skipping the last bars. One cross-section, not a path."""
    scores = {}
    for name, closes in panels.items():
        if len(closes) <= lookback + skip:
            continue
        end = len(closes) - 1 - skip
        start = end - lookback
        if start < 0 or closes[start] == 0:
            continue
        scores[name] = closes[end] / closes[start] - 1.0
    if not scores:
        return {}
    ordered = sorted(scores, key=lambda name: scores[name])
    mid = len(ordered) // 2
    return {name: (1 if index >= mid else -1) for index, name in enumerate(ordered)}


def short_term_reversal(closes: list[float], lookback: int = 1) -> list[int]:
    out = []
    for t in range(len(closes)):
        r = _ret(closes, t, lookback)
        out.append(0 if r is None or r == 0 else (-1 if r > 0 else 1))
    return out


def _rsi(closes: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= length:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, length + 1):
        delta = closes[i] - closes[i - 1]
        gains += max(delta, 0.0)
        losses += max(-delta, 0.0)
    avg_g = gains / length
    avg_l = losses / length
    for t in range(length, len(closes)):
        if t > length:
            delta = closes[t] - closes[t - 1]
            avg_g = (avg_g * (length - 1) + max(delta, 0.0)) / length
            avg_l = (avg_l * (length - 1) + max(-delta, 0.0)) / length
        if avg_l == 0:
            out[t] = 100.0
        else:
            rs = avg_g / avg_l
            out[t] = 100.0 - 100.0 / (1.0 + rs)
    return out


def rsi2(closes: list[float], length: int = 2, buy: float = 10.0, sell: float = 90.0) -> list[int]:
    out = []
    for value in _rsi(closes, length):
        if value is None:
            out.append(0)
        elif value < buy:
            out.append(1)
        elif value > sell:
            out.append(-1)
        else:
            out.append(0)
    return out


def bollinger_fade(closes: list[float], length: int = 20, width: float = 2.0) -> list[int]:
    out = []
    for t in range(len(closes)):
        if t + 1 < length:
            out.append(0)
            continue
        window = closes[t + 1 - length:t + 1]
        mean = sum(window) / length
        var = sum((x - mean) ** 2 for x in window) / length
        sd = math.sqrt(var)
        upper = mean + width * sd
        lower = mean - width * sd
        if closes[t] > upper:
            out.append(-1)
        elif closes[t] < lower:
            out.append(1)
        else:
            out.append(0)
    return out


def pairs_zscore(left: list[float], right: list[float], length: int = 20, entry_z: float = 2.0) -> list[int]:
    n = min(len(left), len(right))
    out = []
    for t in range(n):
        if t + 1 < length or right[t] == 0:
            out.append(0)
            continue
        ratios = [left[i] / right[i] for i in range(t + 1 - length, t + 1) if right[i]]
        if len(ratios) < length:
            out.append(0)
            continue
        mean = sum(ratios) / len(ratios)
        var = sum((x - mean) ** 2 for x in ratios) / len(ratios)
        sd = math.sqrt(var)
        if sd == 0:
            out.append(0)
            continue
        z = (ratios[-1] - mean) / sd
        if z >= entry_z:
            out.append(-1)
        elif z <= -entry_z:
            out.append(1)
        else:
            out.append(0)
    return out


def futures_carry(front: float, back: float) -> int:
    if front == 0:
        return 0
    roll = back / front - 1.0
    if roll > 0:
        return 1
    if roll < 0:
        return -1
    return 0


def funding_carry(rate: float) -> int:
    """Positive funding pays the short. That is the carry side."""
    if rate > 0:
        return -1
    if rate < 0:
        return 1
    return 0


def turn_of_month(day: int, first_days: int = 3, last_days: int = 3) -> int:
    if day <= first_days or day >= 32 - last_days:
        return 1
    return 0


def overnight_vs_intraday(prev_close: float, open_: float, close: float) -> dict[str, float | None]:
    if prev_close == 0 or open_ == 0:
        return {"overnight": None, "intraday": None}
    return {"overnight": open_ / prev_close - 1.0, "intraday": close / open_ - 1.0}


def pre_fomc(days_until_event: int, days_before: int = 1) -> int:
    return 1 if 0 < days_until_event <= days_before else 0


def pead(surprise: float, days_since: int, hold_days: int = 60) -> int:
    if days_since < 0 or days_since > hold_days or surprise == 0:
        return 0
    return 1 if surprise > 0 else -1


def news_shock(score: float | None, min_abs: float = 0.2) -> int:
    if score is None or abs(score) < min_abs:
        return 0
    return 1 if score > 0 else -1


def macro_surprise(actual: float | None, consensus: float | None) -> int:
    if actual is None or consensus is None or actual == consensus:
        return 0
    return 1 if actual > consensus else -1


def vol_breakout(ranges: list[float], closes: list[float], length: int = 14, multiple: float = 1.5) -> list[int]:
    """A bar breaks when its range exceeds a multiple of the prior average range."""
    out = []
    for t in range(len(ranges)):
        if t < length:
            out.append(0)
            continue
        atr = sum(ranges[t - length:t]) / length
        if atr <= 0 or t == 0:
            out.append(0)
            continue
        direction = 1 if closes[t] > closes[t - 1] else (-1 if closes[t] < closes[t - 1] else 0)
        out.append(direction if ranges[t] > multiple * atr else 0)
    return out


def liquidation_fade(long_liquidations: float, short_liquidations: float, ratio: float = 2.0) -> int:
    """Fade the side that was forced out. Missing prints stay flat."""
    if long_liquidations < 0 or short_liquidations < 0:
        return 0
    if long_liquidations > ratio * max(short_liquidations, 1e-12):
        return 1
    if short_liquidations > ratio * max(long_liquidations, 1e-12):
        return -1
    return 0


def vol_target(realized_vol: float, target: float = 0.01, cap: float = 1.0) -> float | None:
    if realized_vol <= 0:
        return None
    return round(min(cap, target / realized_vol), 4)


def low_vol_ranks(vols: dict[str, float]) -> dict[str, int]:
    ordered = sorted(vols, key=lambda name: vols[name])
    mid = len(ordered) // 2
    return {name: (1 if index < mid else -1) for index, name in enumerate(ordered)}


def cot_extreme(z: float, threshold: float = 2.0) -> int:
    if z >= threshold:
        return -1
    if z <= -threshold:
        return 1
    return 0


def wick_sweep(open_: float, high: float, low: float, close: float, wick_share: float = 0.6) -> int:
    span = high - low
    if span <= 0:
        return 0
    lower = min(open_, close) - low
    upper = high - max(open_, close)
    if lower / span >= wick_share and close >= low + 0.5 * span:
        return 1
    if upper / span >= wick_share and close <= low + 0.5 * span:
        return -1
    return 0


def pump_token_allowed(*, safety_pass: bool, agreeing_families: int, time_stop_set: bool) -> bool:
    """A token idea cannot open from its own signal."""
    return bool(safety_pass and agreeing_families >= 2 and time_stop_set)


def apply_cost(gross: float, fee_per_side: float, slippage_per_side: float) -> float:
    return gross - 2.0 * (fee_per_side + slippage_per_side)


def sign_on_closes(strategy_id: str, closes: list[float]) -> list[int] | None:
    """The cited rule on a close series. None means this rule needs inputs we do not have."""
    if strategy_id == "ts_momentum":
        return ts_momentum(closes, 12)
    if strategy_id == "dual_ma":
        return dual_ma(closes, 10, 30)
    if strategy_id == "short_term_reversal":
        return short_term_reversal(closes, 1)
    if strategy_id == "rsi2_connors":
        return rsi2(closes, 2, 10.0, 90.0)
    if strategy_id == "bollinger_fade":
        return bollinger_fade(closes, 20, 2.0)
    if strategy_id == "vol_breakout":
        ranges = [abs(closes[i] - closes[i - 1]) if i else 0.0 for i in range(len(closes))]
        return vol_breakout(ranges, closes, 14, 1.5)
    if strategy_id == "donchian_turtle":
        return donchian(closes, closes, 20, 10)
    return None


def shadow_round_trips(signs: list[int], prices: list[float], fee: float, slip: float) -> list[float]:
    """A completed sign change is one shadow close. Fees are deducted."""
    trips: list[float] = []
    entry: int | None = None
    side = 0
    for t, sign in enumerate(signs):
        if entry is None:
            if sign != 0:
                entry = t
                side = sign
            continue
        if sign != side:
            if prices[entry] > 0 and t != entry:
                gross = side * (prices[t] / prices[entry] - 1.0)
                trips.append(apply_cost(gross, fee, slip))
            entry = t if sign != 0 else None
            side = sign
    return trips
