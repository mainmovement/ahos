#!/usr/bin/env python3
"""Export M13.1-M13.6 & M19 multi-market paper desks snapshot to reports/grok/M19/multi_market_snapshot.json."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.multi_market_desks import DESK_SPECS, evaluate_all_desks


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    now_iso = _utc_now()
    cycles = evaluate_all_desks()

    desks_summary: dict[str, dict] = {}
    for desk_name, spec in DESK_SPECS.items():
        desk_cycles = [c for c in cycles if c.desk == desk_name]
        verified_n = sum(1 for c in desk_cycles if c.witness.state == "VERIFIED")
        desks_summary[desk_name] = {
            "desk": desk_name,
            "mission_id": spec["mission_id"],
            "symbols_count": len(desk_cycles),
            "verified_count": verified_n,
            "status": "VERIFIED" if verified_n == len(desk_cycles) and desk_cycles else "PARTIAL",
            "paper_only": True,
            "live": False,
            "primary_sources": list(spec["primary_sources"]),
        }

    payload = {
        "schema": "ahos.multi_market_desks.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "desks_count": len(DESK_SPECS),
        "instruments_evaluated": len(cycles),
        "verified_instruments": sum(1 for c in cycles if c.witness.state == "VERIFIED"),
        "desks": desks_summary,
        "instruments": [
            {
                "desk": c.desk,
                "symbol": c.symbol,
                "mission_id": c.mission_id,
                "witness_state": c.witness.state,
                "consensus_price": c.witness.consensus_price,
                "spread_pct": c.witness.spread_pct,
                "spread_bps": c.witness.spread_bps,
                "sources": list(c.witness.sources),
                "oms_state": c.oms_state,
                "margin_event": c.margin_event,
                "notional_usd": c.notional_usd,
                "bankroll_usd": c.bankroll_usd,
                "paper_only": c.paper_only,
                "live": c.live,
            }
            for c in cycles
        ],
    }

    out_dir = ROOT / "reports" / "grok" / "M19"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "multi_market_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} desks={len(DESK_SPECS)} instruments={len(cycles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
