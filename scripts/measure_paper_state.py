"""Paper measurements that finish. The data walk is capped and does not follow links."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from architecture.markets.desk_expectancy_pause import export_pause
from architecture.markets.paper_account import load_paper_trades
from architecture.mission.vision_live import export_live_proofs
from architecture.persistence.bounded_walk import find_files
from architecture.university.lesson_shadow import export_lesson_shadow, export_promotion


def main(root: Path) -> int:
    closes = load_paper_trades(root)
    lesson = export_lesson_shadow(root, closes)
    promotion = export_promotion(root, closes)
    pause = export_pause(root, closes)
    proofs = export_live_proofs(root, closes)
    stores = find_files(root / "data", (".sqlite", ".db"), max_depth=3, timeout_s=5.0)
    print(json.dumps({
        "lesson_delta": lesson.get("delta_expectancy_usd"),
        "oos_delta": lesson.get("oos_delta_expectancy_usd"),
        "promotion": promotion.get("decision"),
        "promotion_reasons": promotion.get("reasons"),
        "further_closes": promotion.get("further_closes"),
        "applied_to_live_weights": promotion.get("applied_to_live_weights"),
        "paused": pause.get("paused_desks"),
        "early_warning": pause.get("early_warning_desks"),
        "sqlite_files": len(stores["files"]),
        "sqlite_timed_out": stores["timed_out"],
        "sqlite_seen": stores["seen_entries"],
        "proofs": proofs,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]))
