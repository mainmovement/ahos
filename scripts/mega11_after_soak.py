"""The soak restart stays closed until the 72-hour mark.

Running this before 2026-11-01T00:45:31Z does not stop a process and does not
install anything. The window start is not reset.
"""
from __future__ import annotations

from datetime import datetime, timezone

DEADLINE = datetime(2026, 11, 1, 0, 45, 31, tzinfo=timezone.utc)
MIN_FREE_MB = 2048


def main() -> int:
    now = datetime.now(timezone.utc)
    if now < DEADLINE:
        print("WAIT")
        return 0
    print("DUE")
    print("free_ram_min_mb", MIN_FREE_MB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
