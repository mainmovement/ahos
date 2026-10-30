"""Paper drills for the kill switch and the judge. They do not arm live trading."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.judge import BROKEN_CHAIN, judge_paper_ledger
from architecture.markets.paper_trader import DAILY_LOSS_LIMIT, kill_switch
from architecture.mission.ledger import MissionLedger

OUT_REL = Path("reports") / "grok" / "PAPER" / "operator_drills.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def kill_switch_drill(live_trades: list[dict[str, Any]], equity: float, now: float) -> dict[str, Any]:
    """A synthetic daily loss must trip. The live book is reported beside it and is not edited."""
    tripped, reason = kill_switch(
        [{"realized_pnl_usd": -(DAILY_LOSS_LIMIT * equity) - 1.0, "closed_at": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}],
        equity,
        now,
    )
    live_tripped, live_reason = kill_switch(live_trades, equity, now)
    return {
        "name": "kill_switch",
        "synthetic_tripped": tripped,
        "synthetic_reason": reason,
        "live_book_tripped": live_tripped,
        "live_reason": live_reason,
        "passed": tripped is True and live_tripped is False,
        "live_book_edited": False,
    }


def judge_drill() -> dict[str, Any]:
    """A torn ledger is a broken chain. The judge has no promotion verdict."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "broken.jsonl"
        path.write_text('{"not": "a ledger row"}\n', encoding="utf-8")
        report = judge_paper_ledger(MissionLedger(path), "M13-GOLD-PAPER")
    return {
        "name": "judge",
        "verdict": report.verdict,
        "passed": report.verdict == BROKEN_CHAIN,
        "promoted": False,
        "live_switch": False,
    }


def export_drills(root: Path, live_trades: list[dict[str, Any]], equity: float, now: float) -> dict[str, Any]:
    root = Path(root)
    kill = kill_switch_drill(live_trades, equity, now)
    judge = judge_drill()
    doc = {
        "schema": "ahos.operator_drills.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "kill_switch": kill,
        "judge": judge,
        "live_switch": False,
        "decides": False,
    }
    path = root / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc
