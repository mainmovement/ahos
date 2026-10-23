#!/usr/bin/env python3
"""Export M33 24-Step Token Hunter snapshot to reports/grok/M33/token_hunter_snapshot.json."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.token_hunter_24 import STEP_NAMES_24, screen_token_batch


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    now_iso = _utc_now()
    verdicts = screen_token_batch()
    eligible = [v for v in verdicts if v.state == "PAPER_WATCH_ELIGIBLE"]
    vetoed = [v for v in verdicts if v.state == "VETO_UNSAFE"]

    payload = {
        "schema": "ahos.token_hunter_24.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "steps_count": len(STEP_NAMES_24),
        "step_names": list(STEP_NAMES_24),
        "candidates_screened": len(verdicts),
        "paper_watch_eligible_count": len(eligible),
        "veto_unsafe_count": len(vetoed),
        "candidates": [
            {
                "symbol": v.symbol,
                "chain": v.chain,
                "contract_address": v.contract_address,
                "state": v.state,
                "steps_passed": v.steps_passed,
                "steps_total": v.steps_total,
                "corroborated_sources": list(v.corroborated_sources),
                "veto_reasons": list(v.veto_reasons),
                "paper_only": v.paper_only,
                "live": v.live,
                "trades": v.trades,
            }
            for v in verdicts
        ],
    }

    out_dir = ROOT / "reports" / "grok" / "M33"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "token_hunter_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} screened={len(verdicts)} eligible={len(eligible)} vetoed={len(vetoed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
