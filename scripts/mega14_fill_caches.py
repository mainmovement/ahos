"""Fill one free-data cache. Pass a single job name. Does not restart a process."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.free_data_cache import (  # noqa: E402
    assemble,
    fetch_cot_local,
    fetch_earnings_dates,
    fetch_fred_actuals,
    fetch_french_factors,
    fetch_funding_oi,
    fetch_intraday,
    fetch_liquidations,
    fetch_second_contract,
    publish,
)

def _status(root: Path) -> dict:
    from science.memory import peak_rss_mb
    doc = assemble(root, peak_mb=peak_rss_mb())
    publish(root, doc)
    return doc


JOBS = {
    "funding": fetch_funding_oi,
    "fred": fetch_fred_actuals,
    "french": fetch_french_factors,
    "cot": fetch_cot_local,
    "second": fetch_second_contract,
    "ohlc": fetch_intraday,
    "earnings": fetch_earnings_dates,
    "liquidations": fetch_liquidations,
    "status": _status,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in JOBS:
        print("JOB " + ",".join(sorted(JOBS)))
        return 2
    doc = JOBS[sys.argv[1]](ROOT)
    from science.memory import peak_rss_mb
    print(sys.argv[1], doc.get("reason") or doc.get("status") or "ok", "n", doc.get("n") or doc.get("n_funding"), "peak_mb", peak_rss_mb())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
