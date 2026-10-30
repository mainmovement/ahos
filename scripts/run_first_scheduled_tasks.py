#!/usr/bin/env python3
"""Run each AHOS_* scheduled job once and write scheduled_run receipts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import resolve_ahos_python_exe

JOBS = [
    "scripts/scheduled/run_arxiv_scout_daily.py",
    "scripts/scheduled/run_pipeline_6h.py",
    "scripts/scheduled/run_negahban_daily.py",
    "scripts/scheduled/run_university_exam_sat.py",
]


def main() -> int:
    py = resolve_ahos_python_exe(ROOT)
    rc = 0
    for rel in JOBS:
        print(f"--- {rel} ---")
        p = subprocess.run([str(py), str(ROOT / rel)], cwd=str(ROOT))
        if p.returncode != 0:
            rc = p.returncode
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
