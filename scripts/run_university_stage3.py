#!/usr/bin/env python3
"""Stage 3 university dry-run: weekly scorecard, win claims, help desk, L0–L4, loss cases."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.knowledge.sync import KnowledgeSyncBridge
from architecture.learning.mistakes import record_losing_close
from architecture.university.certification_ladder import export_l0_l4_dry_run
from architecture.university.helpdesk import ask
from architecture.university.research_prediction_scoring import export_weekly_shadow_scorecard_to_m57
from config.paths import connect_sqlite_ro, get_knowledge_db_path


def _backfill_losses() -> int:
    log = ROOT / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not log.is_file():
        return 0
    n = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") != "CLOSE":
            continue
        pnl = float(row.get("realized_pnl_usd") or 0)
        if pnl >= 0:
            continue
        closed = str(row.get("closed_at") or row.get("ts") or "")
        symbol = str(row.get("symbol") or "UNKNOWN")
        rec = record_losing_close(
            ROOT,
            case_id=f"PT-{symbol}-{closed}",
            pnl_usd=pnl,
            symbol=symbol,
            desk=str(row.get("desk") or ""),
            closed_at=closed,
        )
        n += int(bool(rec.get("appended")))
    return n


def _tasks() -> list[str]:
    sch = Path(r"C:\Windows\System32\schtasks.exe")
    names = [
        "AHOS_arxiv_scout_daily",
        "AHOS_pipeline_6h",
        "AHOS_university_exam_sat",
        "AHOS_negahban_daily",
    ]
    present = []
    for name in names:
        proc = subprocess.run([str(sch), "/Query", "/TN", name], capture_output=True, text=True)
        if proc.returncode == 0:
            present.append(name)
    return present


def main() -> int:
    weekly = export_weekly_shadow_scorecard_to_m57(ROOT)
    wins = KnowledgeSyncBridge().sync_winning_paper_closes(ROOT)
    losses = _backfill_losses()
    ladder = export_l0_l4_dry_run(ROOT)
    desk = ask("UNPROVEN_EDGE paper lesson calibration", root=ROOT)
    conn = connect_sqlite_ro(get_knowledge_db_path())
    claims = conn.execute("SELECT COUNT(*) FROM knowledge_claims").fetchone()[0]
    conn.close()
    receipt = {
        "schema": "ahos.university_stage3_receipt.v1",
        "paper_only": True,
        "weekly_hypotheses_tracked": weekly.get("hypotheses_tracked"),
        "weekly_outcomes_total": weekly.get("outcomes_total"),
        "winning_closes_inserted": wins,
        "loss_eval_cases_appended": losses,
        "knowledge_claims_total": claims,
        "helpdesk_asku_ref": desk.get("asku_ref"),
        "helpdesk_decides": desk.get("decides"),
        "helpdesk_knowledge_hits": len(desk.get("knowledge_hits") or []),
        "autonomy_ceiling": ladder.get("autonomy_ceiling"),
        "scheduled_tasks_present": _tasks(),
    }
    out = ROOT / "reports" / "grok" / "M59" / "university_stage3_receipt.json"
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
