#!/usr/bin/env python3
"""Write tier gate reports for gold/oil using REPLAY_NOT_LIVE inputs (scratch ledger only)."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.gate_inputs import LABEL, load_replay_inputs, tier_gate_kwargs
from architecture.markets.gold_paper import GOLD_PAPER_MISSION, paper_history
from architecture.markets.oil_paper import OIL_PAPER_MISSION
from architecture.markets.tier_gate import evaluate_tier_gate, write_gate_report
from architecture.mission.ledger import MissionLedger, default_ledger_path


def _oil_months(ledger: MissionLedger) -> float | None:
    from architecture.markets.gold_paper import _ledger_ts_to_epoch

    first = last = None
    for entry in ledger.history(OIL_PAPER_MISSION):
        ts = _ledger_ts_to_epoch(entry.get("ts"))
        if ts is None:
            continue
        if first is None:
            first = ts
        last = ts
    if first is None or last is None or last <= first:
        return None
    return (last - first) / (30.0 * 24.0 * 3600.0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export replay-fed tier gate evidence")
    ap.add_argument("--gold-ledger", type=Path, help="scratch gold ledger (copied from live)")
    ap.add_argument("--oil-ledger", type=Path, help="oil scratch ledger")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "reports" / "grok" / "M13_REPLAY" / "tier_gate_exports",
    )
    args = ap.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    replay = load_replay_inputs()
    summary: dict = {"label": LABEL, "markets": {}}

    if args.gold_ledger:
        gpath = Path(args.gold_ledger).resolve()
        if gpath == default_ledger_path(create=False).resolve():
            print("refusing live gold ledger path", file=sys.stderr)
            return 2
        ledger = MissionLedger(gpath)
        hist = paper_history(ledger)
        report = evaluate_tier_gate(
            market="gold",
            trades=list(hist.trades),
            months_of_data=hist.months_of_data,
            **tier_gate_kwargs(market="gold"),
        )
        md = out_dir / "gold_tier_gate_replay.md"
        write_gate_report(report, md)
        summary["markets"]["gold"] = {
            "ledger": str(gpath),
            "tier": report.tier_today,
            "measurable_pass": f"{report.measurable_and_passed}/{report.measurable_total}",
            "unmeasurable": list(report.unmeasurable),
            "report": str(md.relative_to(ROOT)),
        }

    oil_path = args.oil_ledger
    if oil_path is None:
        oil_path = ROOT / "data" / "mission_ledger" / "oil_paper_scratch.jsonl"
    oil_path = Path(oil_path)
    if oil_path.is_file():
        ledger = MissionLedger(oil_path)
        report = evaluate_tier_gate(
            market="oil",
            trades=[],
            months_of_data=_oil_months(ledger),
            **tier_gate_kwargs(market="oil"),
        )
        md = out_dir / "oil_tier_gate_replay.md"
        write_gate_report(report, md)
        summary["markets"]["oil"] = {
            "ledger": str(oil_path),
            "tier": report.tier_today,
            "measurable_pass": f"{report.measurable_and_passed}/{report.measurable_total}",
            "unmeasurable": list(report.unmeasurable),
            "report": str(md.relative_to(ROOT)),
        }

    summary["replay"] = {
        "verdict": replay.get("verdict"),
        "source": replay.get("source"),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
