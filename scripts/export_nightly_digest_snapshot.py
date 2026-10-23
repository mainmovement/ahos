#!/usr/bin/env python3
"""Export M31 / M35.4 comprehensive Persian nightly digest snapshot (PAPER_ONLY)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.nightly import build_comprehensive_nightly_digest_fa


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    now_iso = _utc_now()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    gold_soak = _read_json(ROOT / "reports" / "grok" / "M13_SOAK" / "soak_status.json")
    oil_soak = _read_json(ROOT / "reports" / "grok" / "M13_OIL" / "oil_status.json")
    multi_market = _read_json(ROOT / "reports" / "grok" / "M19" / "multi_market_snapshot.json")
    tournament = _read_json(ROOT / "reports" / "grok" / "M56" / "tournament_snapshot.json")
    astra = _read_json(ROOT / "reports" / "grok" / "M60" / "astra_snapshot.json")

    trades = 0
    pnl = 0.0
    if gold_soak:
        trades = int(gold_soak.get("closed_trades") or gold_soak.get("trades_closed") or 0)
        pnl = float(gold_soak.get("realized_pnl_usd") or gold_soak.get("paper_pnl_usd") or 0.0)

    digest_fa = build_comprehensive_nightly_digest_fa(
        day=day,
        trades=trades,
        pnl_usd=pnl,
        gold_soak=gold_soak,
        oil_soak=oil_soak,
        multi_market=multi_market,
        tournament=tournament,
        astra=astra,
    )

    out_dir = ROOT / "reports" / "grok" / "M31"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "nightly_digest_fa.md"
    md_path.write_text(digest_fa, encoding="utf-8")

    payload = {
        "schema": "ahos.nightly_digest.v1",
        "kind": "nightlyDigest",
        "generated_at": now_iso,
        "day": day,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "sources": {
            "gold_soak": "reports/grok/M13_SOAK/soak_status.json",
            "oil_soak": "reports/grok/M13_OIL/oil_status.json",
            "multi_market": "reports/grok/M19/multi_market_snapshot.json",
            "tournament": "reports/grok/M56/tournament_snapshot.json",
            "astra": "reports/grok/M60/astra_snapshot.json",
        },
        "inputs_present": {
            "gold_soak": gold_soak is not None,
            "oil_soak": oil_soak is not None,
            "multi_market": multi_market is not None,
            "tournament": tournament is not None,
            "astra": astra is not None,
        },
        "paper_trades": trades,
        "paper_pnl_usd": pnl,
        "digest_fa_path": "reports/grok/M31/nightly_digest_fa.md",
        "digest_fa": digest_fa,
    }
    json_path = out_dir / "nightly_digest_snapshot.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {json_path} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
