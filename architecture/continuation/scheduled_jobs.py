"""Receipt helper for Windows scheduled AHOS jobs."""
from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.continuation.windows_scheduler import write_run_receipt


def run_scheduled_job(root: Path, task_name: str, fn: Callable[[Path], Any]) -> int:
    try:
        result = fn(root)
        write_run_receipt(root, task_name, {"status": "OK", "result": result})
        print(f"{task_name} OK")
        return 0
    except Exception as exc:
        write_run_receipt(
            root,
            task_name,
            {"status": "ERROR", "error": str(exc), "traceback": traceback.format_exc()[-4000:]},
        )
        print(f"{task_name} ERROR: {exc}")
        return 1
