#!/usr/bin/env python3
"""Track 1: live two-source witness probe by asset class (PAPER_ONLY, no trades)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.live_price_feed import fetch_live_market_prices
from architecture.markets.paper_trader import INSTRUMENTS, fetch_second_sources
from architecture.markets.second_source import witness
from architecture.markets.weekday_session_gate import session_report


def main() -> int:
    sess = session_report()
    quotes = (fetch_live_market_prices() or {}).get("quotes") or {}
    second = fetch_second_sources()
    by_desk: dict[str, list[dict[str, object]]] = {}
    for sym, (desk, _f, _s) in INSTRUMENTS.items():
        w = witness(sym, quotes.get(sym), second.get(sym))
        by_desk.setdefault(desk, []).append(
            {"symbol": sym, "verdict": w["verdict"], "gap": w.get("gap"), "source_a": w.get("source_a"), "source_b": w.get("source_b")}
        )
    verified_desks = sorted({d for d, rows in by_desk.items() if any(r["verdict"] == "VERIFIED" for r in rows)})
    payload = {
        "schema": "ahos.weekday_witness_probe.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "session_gate": sess,
        "verified_asset_classes": verified_desks,
        "by_desk": by_desk,
        "summary_fa": (
            f"کلاس‌های با شاهد VERIFIED الان: {', '.join(verified_desks) or 'هیچ'} — "
            f"{sess.get('summary_fa', '')}"
        ),
    }
    out = ROOT / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"verified": verified_desks, "weekend": sess.get("weekend_tehran")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
