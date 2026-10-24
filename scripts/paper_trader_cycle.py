"""Run the $100 paper trader: one cycle (--once) or a light loop (default every 300s). PAPER_ONLY."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from architecture.markets.paper_trader import run_cycle  # noqa: E402

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    a = ap.parse_args()
    while True:
        try:
            s = run_cycle(ROOT)
            print(json.dumps({k: s[k] for k in ("updated_at", "mark_to_market_equity_usd", "closed_trades", "last_cycle")}, ensure_ascii=False), flush=True)
        except Exception as exc:  # keep the loop alive; next cycle retries
            print(json.dumps({"error": repr(exc)[:300]}), flush=True)
        if a.once:
            return 0
        time.sleep(max(60, a.interval))

if __name__ == "__main__":
    raise SystemExit(main())
