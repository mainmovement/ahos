#!/usr/bin/env python3
"""Register AHOS Windows scheduled tasks and write registry receipt."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.windows_scheduler import query_schtasks, register_windows_tasks


def main() -> int:
    reg = register_windows_tasks(ROOT)
    print(query_schtasks())
    print(f"wrote {ROOT / 'reports/grok/CONTINUATION/windows_scheduled_tasks.json'} tasks={len(reg.get('tasks') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
