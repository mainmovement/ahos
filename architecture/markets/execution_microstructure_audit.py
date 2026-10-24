"""Paper-trade slippage, fees, and path excursions. PAPER_ONLY. No invented path."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_account import load_paper_trades

OUT_REL = Path("reports") / "grok" / "PAPER" / "microstructure_audit.json"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"


def _row_from_close(trade: dict[str, Any]) -> dict[str, Any]:
    path_n = trade.get("path_points")
    measured = isinstance(path_n, int) and path_n >= 2 and trade.get("mae") is not None and trade.get("mfe") is not None
    notional = trade.get("notional_usd")
    slip = trade.get("slippage_pct")
    slip_usd = None
    if isinstance(slip, (int, float)) and isinstance(notional, (int, float)):
        slip_usd = round(abs(float(slip)) * float(notional), 6)
    fees = trade.get("fees_usd")
    return {
        "symbol": trade.get("symbol"),
        "side": trade.get("side"),
        "reason": trade.get("reason"),
        "partial": bool(trade.get("partial")),
        "opened_at": trade.get("opened_at"),
        "closed_at": trade.get("closed_at"),
        "notional_usd": notional,
        "fees_usd": fees,
        "slippage_pct": slip,
        "slippage_usd_one_side": slip_usd,
        "realized_pnl_usd": trade.get("realized_pnl_usd"),
        "mae": trade.get("mae") if measured else None,
        "mfe": trade.get("mfe") if measured else None,
        "path_points": path_n if isinstance(path_n, int) else 0,
        "mae_mfe_status": "MEASURED" if measured else "UNAVAILABLE_NO_INTRATRADE_PATH",
    }


def _open_row(sym: str, pos: dict[str, Any]) -> dict[str, Any]:
    path_n = pos.get("path_points")
    measured = isinstance(path_n, int) and path_n >= 2 and pos.get("mae") is not None and pos.get("mfe") is not None
    return {
        "symbol": sym,
        "side": pos.get("side"),
        "status": "OPEN",
        "mae": pos.get("mae") if measured else None,
        "mfe": pos.get("mfe") if measured else None,
        "path_points": path_n if isinstance(path_n, int) else 0,
        "mae_mfe_status": "MEASURED" if measured else "UNAVAILABLE_NO_INTRATRADE_PATH",
        "chandelier_stop": pos.get("chandelier_stop"),
    }


def build_microstructure_audit(root: Path) -> dict[str, Any]:
    root = Path(root)
    closes = [t for t in load_paper_trades(root) if t.get("event") in (None, "CLOSE") or "realized_pnl_usd" in t]
    # load_paper_trades already keeps rows that carry realized_pnl_usd. OPEN rows are not in that list.
    rows = [_row_from_close(t) for t in closes]
    fee = round(sum(float(r["fees_usd"]) for r in rows if isinstance(r.get("fees_usd"), (int, float))), 6)
    slip = round(sum(float(r["slippage_usd_one_side"]) for r in rows if isinstance(r.get("slippage_usd_one_side"), (int, float))), 6)
    open_rows: list[dict[str, Any]] = []
    pos_path = root / POSITIONS_REL
    if pos_path.is_file():
        try:
            state = json.loads(pos_path.read_text(encoding="utf-8"))
        except ValueError:
            state = {}
        for sym, pos in (state.get("positions") or {}).items():
            if isinstance(pos, dict):
                open_rows.append(_open_row(sym, pos))
    measured = sum(1 for r in rows if r["mae_mfe_status"] == "MEASURED")
    return {
        "schema": "ahos.paper.microstructure_audit.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "closed_count": len(rows),
        "open_count": len(open_rows),
        "fee_drag_usd": fee,
        "slippage_usd_one_side_sum": slip,
        "mae_mfe_measured_closed": measured,
        "mae_mfe_unavailable_closed": len(rows) - measured,
        "note": "MAE and MFE are stored only after two or more marks on the position. A single entry-to-exit print is not an excursion.",
        "rows": rows,
        "open_positions": open_rows,
    }


def export_microstructure_audit(root: Path) -> dict[str, Any]:
    snap = build_microstructure_audit(root)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
