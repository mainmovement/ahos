#!/usr/bin/env python3
"""Run N oil paper checkpoints on a dedicated scratch ledger. Never the gold default."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.oil_paper import OIL_PAPER_MISSION, run_oil_cycle
from architecture.mission.ledger import MissionLedger, default_ledger_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Oil paper cadence on scratch ledger")
    ap.add_argument("--ledger", required=True, help="dedicated oil scratch ledger path")
    ap.add_argument("--cycles", type=int, default=7, help="paper checkpoints (default 7)")
    ap.add_argument("--left", type=float, default=75.0)
    ap.add_argument("--right", type=float, default=75.05)
    ap.add_argument(
        "--break-cycle",
        type=int,
        default=0,
        help="1-based cycle index to feed UNKNOWN quote (0 = none)",
    )
    args = ap.parse_args(argv)
    path = Path(args.ledger).resolve()
    if path == default_ledger_path(create=False).resolve():
        print("refusing the live gold default ledger path", file=sys.stderr)
        return 2
    if args.cycles < 1:
        print("cycles must be >= 1", file=sys.stderr)
        return 2

    ledger = MissionLedger(path)
    summary: list[dict] = []
    for i in range(1, args.cycles + 1):
        if args.break_cycle == i:
            left, right = 75.0, None
        else:
            left, right = args.left, args.right
        cycle = run_oil_cycle(ledger, left=left, right=right)
        summary.append(
            {
                "cycle": i,
                "quote": cycle.quote.state,
                "oms": cycle.oms,
                "live": cycle.live,
            }
        )
    latest = (ledger.latest(OIL_PAPER_MISSION) or {}).get("CHECKPOINT") or {}
    out = {
        "ledger": str(path),
        "cycles": args.cycles,
        "last": summary[-1] if summary else None,
        "margin_event": latest.get("margin_event"),
        "gold_mission_present": ledger.latest("M13-GOLD-PAPER") is not None,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["last"] and out["last"]["live"] is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
