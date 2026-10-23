#!/usr/bin/env python3
"""Export M43 pilot $100 gateway + high-leverage futures education snapshot."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.execution.live_ready_gateway import gateway_status, pilot_account_state
from architecture.markets.high_leverage_futures_engine import build_futures_engine_summary


def main() -> int:
    gateway = gateway_status(ROOT)
    account = pilot_account_state()
    futures = build_futures_engine_summary(wallet_equity_usd=account["current_equity_usd"])
    payload = {
        "schema": "ahos.pilot_100usd_gateway.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live": False,
        "gateway": gateway,
        "pilot_account": account,
        "high_leverage_futures": futures,
    }
    out = ROOT / "reports" / "grok" / "M43" / "pilot_100usd_gateway_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} equity={account['current_equity_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
