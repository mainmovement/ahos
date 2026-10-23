"""$100 paper pilot account — derived ONLY from real paper trade records (PAPER_ONLY).

Ledger: reports/grok/PAPER/paper_trades.jsonl, one JSON object per CLOSED paper trade with at least
``realized_pnl_usd`` (plus symbol/desk/opened_at/closed_at). With no records the account is exactly
$100.00 with 0 profit. Nothing here is typed by hand.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PAPER_ONLY: bool = True
INITIAL_CAPITAL_USD = 100.0
LEDGER_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
DESKS = ("GOLD", "OIL", "CRYPTO", "US_EQUITIES", "EU_EQUITIES", "ASIA_EQUITIES", "FOREX")


def load_paper_trades(root: Path) -> list[dict[str, Any]]:
    p = root / LEDGER_REL
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and isinstance(row.get("realized_pnl_usd"), (int, float)):
            out.append(row)
    return out


def paper_account_summary(root: Path) -> dict[str, Any]:
    trades = load_paper_trades(root)
    pnl = round(sum(float(t["realized_pnl_usd"]) for t in trades), 2)
    equity = round(INITIAL_CAPITAL_USD + pnl, 2)
    per_desk = {d: round(sum(float(t["realized_pnl_usd"]) for t in trades if t.get("desk") == d), 2) for d in DESKS}
    return {
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "current_equity_usd": equity,
        "realized_pnl_usd": pnl,
        "roi_pct": round(pnl / INITIAL_CAPITAL_USD * 100.0, 2),
        "trade_count": len(trades),
        "per_desk_realized_pnl_usd": per_desk,
        "source": str(LEDGER_REL).replace("\\", "/"),
        "basis": "real_paper_trades" if trades else "no_paper_trades_yet",
        "paper_only": True,
    }
