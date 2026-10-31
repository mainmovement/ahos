"""One session-range sample, or a five-minute loop. The range is an estimate, not a quote."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.equity_universe import fetch_tradingview_session_ranges  # noqa: E402
from architecture.markets.spread_sampler import sample, shortlist  # noqa: E402


def once() -> int:
    names = shortlist(ROOT)
    ranges = fetch_tradingview_session_ranges(names)
    doc = sample(ROOT, ranges, symbols=names)
    filled = sum(1 for row in doc["rows"] if row.get("estimated_spread_pct") is not None)
    print("sampled", doc["n"], "filled", filled)
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
