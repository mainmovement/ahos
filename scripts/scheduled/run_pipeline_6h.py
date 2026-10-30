#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.continuation.scheduled_jobs import run_scheduled_job
from architecture.continuation.next_tranche import build_m58_promote_loop_receipt
from architecture.learning.astra_engine import run_astra_evolution_cycle
from architecture.university.science_to_desk_pipeline import run_science_to_desk_pipeline
from config.paths import get_project_root


def _job(root: Path) -> dict:
    pipeline = run_science_to_desk_pipeline()
    out = root / "reports" / "grok" / "M57" / "science_to_desk_pipeline_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pipeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    m58 = build_m58_promote_loop_receipt(root)
    m60 = run_astra_evolution_cycle(root=root)
    m60_path = root / "reports" / "grok" / "M60" / "astra_snapshot.json"
    m60_path.parent.mkdir(parents=True, exist_ok=True)
    m60_path.write_text(json.dumps(m60, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "science_to_desk_sources": pipeline.get("sources_count"),
        "m58_auto_promote_enabled": m58.get("auto_promote_enabled"),
        "m60_status": m60.get("overall_status"),
    }


if __name__ == "__main__":
    raise SystemExit(run_scheduled_job(get_project_root(), "AHOS_pipeline_6h", _job))
