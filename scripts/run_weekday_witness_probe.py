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
from architecture.markets.weekday_witness_probe import build_witness_probe_payload


def main() -> int:
    quotes = (fetch_live_market_prices() or {}).get("quotes") or {}
    second = fetch_second_sources()
    payload = build_witness_probe_payload(INSTRUMENTS, quotes, second)
    payload["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = ROOT / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "tradable": payload["tradable_asset_classes"],
                "verified": payload["verified_asset_classes"],
                "weekend": payload["session_gate"].get("weekend_tehran"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
