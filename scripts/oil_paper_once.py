#!/usr/bin/env python3
"""One oil paper checkpoint cycle. Separate mission id; never the live gold ledger."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.oil_paper import run_oil_cycle
from architecture.mission.ledger import MissionLedger, default_ledger_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Oil paper quote + OMS checkpoint (PAPER_ONLY)")
    ap.add_argument("--ledger", required=True, help="scratch ledger path (not live default)")
    ap.add_argument("--left", type=float, default=75.0, help="left oil quote USD")
    ap.add_argument("--right", type=float, default=75.05, help="right oil quote USD")
    args = ap.parse_args(argv)
    path = Path(args.ledger)
    if path.resolve() == default_ledger_path(create=False).resolve():
        print("refusing the live default ledger path", file=sys.stderr)
        return 2
    ledger = MissionLedger(path)
    cycle = run_oil_cycle(ledger, left=args.left, right=args.right)
    print(f"quote={cycle.quote.state} oms={cycle.oms} live={cycle.live}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
