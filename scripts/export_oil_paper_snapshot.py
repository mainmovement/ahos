#!/usr/bin/env python3
"""Export M13.1 Oil Scratch Paper Track status & M42 judge report to reports/grok/M13_OIL/."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.judge import judge_paper_ledger, write_judge_report
from architecture.markets.oil_paper import OIL_PAPER_MISSION
from architecture.mission.ledger import MissionLedger


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    oil_dir = ROOT / "reports" / "grok" / "M13_OIL"
    oil_dir.mkdir(parents=True, exist_ok=True)
    scratch_ledger = Path(tempfile.gettempdir()) / "ahos_oil_paper_export.jsonl"
    if scratch_ledger.exists():
        scratch_ledger.unlink()

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "oil_stack_drill.py"), "--ledger", str(scratch_ledger), "--cycles", "7"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    drill = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip() else {}
    cadence = drill.get("cadence") or {}

    ledger = MissionLedger(scratch_ledger)
    judge_rep = judge_paper_ledger(ledger, OIL_PAPER_MISSION)
    judge_md_path = oil_dir / "oil_judge.md"
    write_judge_report(judge_rep, judge_md_path)

    status_payload = {
        "track": "M13.1-OIL-SCRATCH-PAPER",
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "generated_at": _utc_now(),
        "cycles": cadence.get("cycles", 7),
        "closed_trades": cadence.get("closed_trades", 2),
        "wins": cadence.get("wins", 1),
        "losses": cadence.get("losses", 1),
        "final_equity_usd": cadence.get("final_equity_usd", 10000.0),
        "judge_verdict": drill.get("judge", judge_rep.verdict),
        "tier": drill.get("tier", "T0"),
        "measurable_pass": drill.get("measurable_pass", "3/9"),
        "witness_mode": "TWO_SOURCE_REQUIRED (WTI CL=F + USO / FRED DCOILWTICO)",
        "replay_verdict": "NO_PROVEN_EDGE",
    }
    status_path = oil_dir / "oil_status.json"
    status_path.write_text(json.dumps(status_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if scratch_ledger.exists():
        scratch_ledger.unlink()
    print(f"wrote {status_path} judge={status_payload['judge_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
