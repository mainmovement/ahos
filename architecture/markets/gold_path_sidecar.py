"""Read-only path log for open paper positions. It never writes the position file."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_REL = Path("reports") / "grok" / "PAPER" / "gold_path_ledger.jsonl"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"


def atr_pct_from_bars(highs: list[float], lows: list[float], closes: list[float]) -> float | None:
    n = min(len(highs), len(lows), len(closes))
    if n < 5 or closes[n - 1] <= 0:
        return None
    spans = []
    for i in range(1, n):
        spans.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    if not spans:
        return None
    return round((sum(spans) / len(spans)) / closes[n - 1], 6)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_open_positions(
    root: Path,
    positions: dict[str, Any],
    *,
    bars: dict[str, dict[str, Any]] | None = None,
    pid: int | None = None,
) -> list[dict[str, Any]]:
    """Append one ledger row per open position. The positions mapping is not saved."""
    root = Path(root)
    moment = _utc()
    rows: list[dict[str, Any]] = []
    bars = bars or {}
    for symbol, pos in positions.items():
        if not isinstance(pos, dict):
            continue
        last = pos.get("mark_price")
        if not isinstance(last, (int, float)) or isinstance(last, bool):
            last = pos.get("entry_price")
        quote = bars.get(symbol) or {}
        bid, ask = quote.get("bid"), quote.get("ask")
        mid = None
        mid_reason = "NO_BID_ASK"
        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)) and not isinstance(bid, bool) and ask >= bid > 0:
            mid = round((float(bid) + float(ask)) / 2.0, 6)
            mid_reason = None
        highs = [float(v) for v in (quote.get("highs") or []) if isinstance(v, (int, float))]
        lows = [float(v) for v in (quote.get("lows") or []) if isinstance(v, (int, float))]
        closes = [float(v) for v in (quote.get("closes") or []) if isinstance(v, (int, float))]
        atr = atr_pct_from_bars(highs, lows, closes)
        features = pos.get("entry_features") if isinstance(pos.get("entry_features"), dict) else {}
        entry_atr = features.get("atr_pct")
        rows.append({
            "schema": "ahos.gold_path_sidecar.v1",
            "ts": moment,
            "pid": pid,
            "symbol": symbol,
            "desk": pos.get("desk"),
            "side": pos.get("side"),
            "last": None if not isinstance(last, (int, float)) or isinstance(last, bool) else float(last),
            "mid": mid,
            "mid_reason": mid_reason,
            "atr_pct": atr,
            "atr_reason": None if atr is not None else "NO_BAR_OHLC",
            "atr_pct_at_entry": entry_atr if isinstance(entry_atr, (int, float)) and not isinstance(entry_atr, bool) else None,
            "writes_positions": False,
            "applied_to_live": False,
        })
    path = root / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return rows


_YAHOO = {
    "GC": "GC=F",
    "ES": "ES=F",
    "BZ": "BZ=F",
    "BRENT": "BZ=F",
    "NDX": "^NDX",
    "QQQ": "QQQ",
    "SPX": "^GSPC",
}


def bars_for(symbol: str) -> dict[str, Any]:
    """One keyless chart. An empty result leaves ATR unset."""
    yahoo = _YAHOO.get(symbol)
    if not yahoo:
        return {}
    from urllib.parse import quote
    from urllib.request import Request, urlopen

    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(yahoo) + "?range=1d&interval=5m"
    try:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (AHOS paper research)"}), timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        quote_row = (((payload.get("chart") or {}).get("result") or [{}])[0].get("indicators") or {}).get("quote") or [{}]
        quote_row = quote_row[0]
    except (OSError, TimeoutError, json.JSONDecodeError, ValueError, IndexError, KeyError, TypeError):
        return {}
    def nums(key: str) -> list[float]:
        return [float(value) for value in (quote_row.get(key) or []) if isinstance(value, (int, float))]
    return {"highs": nums("high"), "lows": nums("low"), "closes": nums("close")}


def read_positions(root: Path) -> dict[str, Any]:
    path = Path(root) / POSITIONS_REL
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    positions = doc.get("positions") if isinstance(doc, dict) else None
    return positions if isinstance(positions, dict) else {}
