"""Low-memory read-only path logger. One pass, or a five-minute loop. Never writes positions."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.gold_path_sidecar import bars_for, log_open_positions, read_positions  # noqa: E402


def once() -> int:
    positions = read_positions(ROOT)
    bars = {symbol: bars_for(symbol) for symbol in positions}
    rows = log_open_positions(ROOT, positions, bars=bars, pid=os.getpid())
    print("rows", len(rows), "pid", os.getpid())
    return 0


def main() -> int:
    if "--loop" not in sys.argv:
        return once()
    while True:
        once()
        time.sleep(300)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
