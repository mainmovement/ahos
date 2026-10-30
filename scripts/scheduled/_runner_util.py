from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_task(task_name: str, fn) -> int:
    from architecture.continuation.windows_scheduler import write_run_receipt

    try:
        result = fn(ROOT)
        write_run_receipt(ROOT, task_name, {"status": "OK", "result": result})
        print(f"{task_name} OK")
        return 0
    except Exception as exc:
        write_run_receipt(
            ROOT,
            task_name,
            {"status": "ERROR", "error": str(exc), "traceback": traceback.format_exc()[-4000:]},
        )
        print(f"{task_name} ERROR: {exc}", file=sys.stderr)
        return 1
