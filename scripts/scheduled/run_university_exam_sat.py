#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.scheduled_jobs import run_scheduled_job
from architecture.continuation.next_tranche import build_university_exam_receipt
from architecture.learning.exam import build_live_exam_receipt, run_heldout_5domain_exam
from config.paths import get_project_root


def _job(root: Path) -> dict:
    heldout = run_heldout_5domain_exam(root=root)
    live = build_live_exam_receipt(root)
    receipt = build_university_exam_receipt(root)
    m50 = root / "reports" / "grok" / "M50"
    m50.mkdir(parents=True, exist_ok=True)
    (m50 / "heldout_exam_receipt.json").write_text(
        json.dumps({k: heldout.get(k) for k in ("overall_score", "leaked", "status", "generated_at")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (m50 / "live_exam_receipt.json").write_text(json.dumps(live, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(root / "scripts" / "export_university_exam_radar_snapshots.py")],
        cwd=str(root),
        check=False,
    )
    return {"heldout_score": heldout.get("overall_score"), "receipt_schema": receipt.get("schema")}


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_university_exam_sat", _job))
