#!/usr/bin/env python3
"""Populate ahos_knowledge.sqlite from empirical sync + real M49/M65 lesson snapshots."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.knowledge.sync import KnowledgeSyncBridge
from config.paths import connect_sqlite_ro, get_knowledge_db_path


def main() -> int:
    bridge = KnowledgeSyncBridge()
    empirical = bridge.sync_all_empirical_knowledge()
    lessons = bridge.sync_documented_lessons(ROOT)
    db = get_knowledge_db_path()
    conn = connect_sqlite_ro(db)
    n = conn.execute("SELECT COUNT(*) FROM knowledge_claims").fetchone()[0]
    conn.close()
    receipt = {
        "schema": "ahos.knowledge_sync_receipt.v1",
        "paper_only": True,
        "empirical": empirical,
        "lessons": lessons,
        "knowledge_claims_total": n,
        "db_path": db,
    }
    out = ROOT / "reports" / "grok" / "M16" / "knowledge_sync_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
