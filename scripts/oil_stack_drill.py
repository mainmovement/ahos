#!/usr/bin/env python3
"""Oil cadence + M42 judge + tier gate on scratch ledger. Step 8 drill."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.judge import judge_paper_ledger
from architecture.markets.oil_paper import OIL_PAPER_MISSION
from architecture.markets.tier_gate import evaluate_tier_gate
from architecture.mission.ledger import MissionLedger, default_ledger_path


def _months_span(ledger: MissionLedger) -> float | None:
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
    ap = argparse.ArgumentParser(description="Oil stack drill (cadence + judge + tier)")
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--cycles", type=int, default=7)
    args = ap.parse_args(argv)
    path = args.ledger or Path(tempfile.gettempdir()) / "ahos_oil_stack_drill.jsonl"
    path = path.resolve()
    if path == default_ledger_path(create=False).resolve():
        print("refusing live gold ledger path", file=sys.stderr)
        return 2

    py = sys.executable
    proc = subprocess.run(
        [
            py,
            str(ROOT / "scripts" / "oil_paper_cadence.py"),
            "--ledger",
            str(path),
            "--cycles",
            str(args.cycles),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode

    ledger = MissionLedger(path)
    judge = judge_paper_ledger(ledger, OIL_PAPER_MISSION)
    from architecture.markets.gate_inputs import tier_gate_kwargs

    gate = evaluate_tier_gate(
        market="oil",
        trades=[],
        months_of_data=_months_span(ledger),
        **tier_gate_kwargs(market="oil"),
    )
    out = {
        "ledger": str(path),
        "cadence": json.loads(proc.stdout),
        "judge": judge.verdict,
        "tier": gate.tier_today,
        "measurable_pass": f"{gate.measurable_and_passed}/{gate.measurable_total}",
        "unmeasurable": list(gate.unmeasurable),
        "replay_verdict": "NO_PROVEN_EDGE",
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if judge.verdict == "CLEAN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
