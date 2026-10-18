#!/usr/bin/env python3
"""Evaluate tier gate on a scratch ledger copy. Does not write into M13_SOAK runlogs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.gate_inputs import tier_gate_kwargs
from architecture.markets.gold_paper import paper_history
from architecture.markets.tier_gate import evaluate_tier_gate, write_gate_report
from architecture.mission.ledger import MissionLedger, default_ledger_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Tier gate on a copy ledger + replay inputs")
    ap.add_argument("--ledger", required=True, help="scratch ledger path")
    ap.add_argument("--out", type=Path, help="optional markdown report path")
    ap.add_argument("--market", default="gold", choices=("gold", "oil"))
    ap.add_argument("--replay-config", type=Path, help="override tier_gate_replay_inputs.json")
    args = ap.parse_args(argv)
    path = Path(args.ledger)
    if path.resolve() == default_ledger_path(create=False).resolve():
        print("refusing the live default ledger path", file=sys.stderr)
        return 2
    ledger = MissionLedger(path)
    kw = tier_gate_kwargs(args.replay_config, market=args.market)
    if args.market == "gold":
        history = paper_history(ledger)
        trades = list(history.trades)
        months = history.months_of_data
    else:
        from architecture.markets.oil_paper import OIL_PAPER_MISSION
        from architecture.markets.gold_paper import _ledger_ts_to_epoch

        trades = []
        first = last = None
        for entry in ledger.history(OIL_PAPER_MISSION):
            ts = _ledger_ts_to_epoch(entry.get("ts"))
            if ts is None:
                continue
            if first is None:
                first = ts
            last = ts
        months = None if first is None or last is None or last <= first else (last - first) / (30.0 * 24.0 * 3600.0)
    report = evaluate_tier_gate(
        market=args.market,
        trades=trades,
        months_of_data=months,
        **kw,
    )
    line = (
        f"tier={report.tier_today} measurable_pass={report.measurable_and_passed}/"
        f"{report.measurable_total} unmeasurable={len(report.unmeasurable)}"
    )
    print(line)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        write_gate_report(report, args.out)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
