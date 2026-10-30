#!/usr/bin/env python3
"""Verify M18 registry (100+ candidates) and export live newsroom snapshot."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.scheduled_jobs import run_scheduled_job
from architecture.continuation.next_tranche import build_didehban_receipt
from config.paths import get_project_root


def _job(root: Path) -> dict:
    subprocess.run(
        [sys.executable, str(root / "scripts" / "export_newsroom_snapshot.py"), "--verify"],
        cwd=str(root),
        check=True,
        timeout=900,
    )
    return build_didehban_receipt(root)


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_didehban_newsroom", _job))
