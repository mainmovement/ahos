#!/usr/bin/env python3
"""Build SPEC_TRACE PARTIAL receipt from live paper + soak artifacts (PAPER_ONLY, read-only)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DESK_TO_TRACE = {
    "M13.3": "US_EQUITIES",
    "M13.4": "EU_EQUITIES",
    "M13.5": "ASIA_EQUITIES",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_partial_receipt(root: Path) -> dict:
    edge_path = root / "reports" / "grok" / "PAPER" / "edge_report.json"
    edge = _load_json(edge_path) or {}
    soak = _load_json(root / "reports" / "grok" / "M13_SOAK" / "soak_status.json") or {}
    status = _load_json(root / "reports" / "grok" / "PAPER" / "paper_trader_status.json") or {}

    desks = {d.get("desk"): d for d in (edge.get("desks") or []) if isinstance(d, dict)}
    n_closed = int((edge.get("promotion_gate") or {}).get("n_closed") or status.get("closed_trades") or 0)
    asset_classes_with_closes = sorted(
        {
            name
            for name, cell in desks.items()
            if name and int(cell.get("closes") or 0) > 0
        }
    )
    desk_closes = {
        trace_id: int((desks.get(desk) or {}).get("closes") or 0)
        for trace_id, desk in DESK_TO_TRACE.items()
    }

    still_partial = {
        "M13": {
            "reason": ">=1 calendar month continuous real soak rows + full journal",
            "soak_cycles_ok": soak.get("cycles_ok"),
            "multi_market_closes": n_closed,
        },
        "M31": {"reason": "30 consecutive nightly digest sends without number drift"},
        "M36": {"reason": "72h uninterrupted multi-market soak with zero gate bypass"},
    }
    upgraded: dict[str, dict] = {}
    if len(asset_classes_with_closes) >= 4:
        upgraded["M19"] = {
            "from": "PARTIAL",
            "to": "REAL",
            "reason": f">=4 desk families with live CLOSE rows ({len(asset_classes_with_closes)} desks with closes)",
            "desks_with_closes": asset_classes_with_closes,
        }
    if n_closed >= 30:
        upgraded["M58"] = {
            "from": "PARTIAL",
            "to": "REAL",
            "reason": f"M58.1-M58.6 tested; live book {n_closed} closes (eval sample met; edge UNPROVEN_EDGE per edge_report)",
            "edge_status": edge.get("edge_status"),
            "dsr": edge.get("deflated_sharpe"),
        }
    for trace_id, desk in DESK_TO_TRACE.items():
        n = desk_closes.get(trace_id, 0)
        if n > 0:
            upgraded[trace_id] = {
                "from": "PARTIAL",
                "to": "REAL",
                "reason": f"{desk} desk: {n} CLOSE rows in live paper_trades.jsonl",
                "closes": n,
            }

    upgrade_count = len(upgraded)
    partial_n = 3
    real_n = 114 + upgrade_count

    return {
        "schema": "ahos.spec_trace_partial_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "sources": {
            "edge_report": str(edge_path.relative_to(root)) if edge_path.is_file() else None,
            "soak_status": "reports/grok/M13_SOAK/soak_status.json",
            "paper_trader_status": "reports/grok/PAPER/paper_trader_status.json",
        },
        "live_book": {
            "closed_trades": n_closed,
            "edge_status": edge.get("edge_status"),
            "eligible": (edge.get("promotion_gate") or {}).get("eligible"),
            "mark_to_market_equity_usd": status.get("mark_to_market_equity_usd"),
        },
        "desk_closes": desk_closes,
        "still_partial": still_partial,
        "recommended_upgrades": upgraded,
        "coverage_after_apply": {
            "total": 122,
            "real": real_n,
            "partial": partial_n,
            "weighted_pct": round(100 * (real_n + 0.5 * partial_n) / 122, 1),
        },
    }


def main() -> int:
    report = build_partial_receipt(ROOT)
    out = ROOT / "reports" / "grok" / "SPEC_TRACE_PARTIAL_RECEIPT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(
        f"closes={report['live_book']['closed_trades']} "
        f"upgrades={len(report['recommended_upgrades'])} "
        f"still_partial={len(report['still_partial'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
