#!/usr/bin/env python3
"""Run all lightweight snapshot exporters in one process (<3s, PAPER_ONLY)."""
from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST_REL = "reports/grok/M36/daily_exporter_manifest.json"

# (label, module, main attr, relative output paths written)
EXPORT_STEPS: list[tuple[str, str, list[str]]] = [
    ("M19_multi_market", "scripts.export_multi_market_snapshot", ["reports/grok/M19/multi_market_snapshot.json"]),
    ("M33_token_hunter", "scripts.export_token_hunter_snapshot", ["reports/grok/M33/token_hunter_snapshot.json"]),
    ("M30_memory", "scripts.export_memory_consolidation", ["reports/grok/M30/memory_consolidation_snapshot.json"]),
    (
        "M56_M60_M32_M48_M36",
        "scripts.export_m56_m60_m36_snapshots",
        [
            "reports/grok/M56/tournament_snapshot.json",
            "reports/grok/M60/astra_snapshot.json",
            "reports/grok/M32/cross_desk_reconcile.json",
            "reports/grok/M48/dependency_audit.json",
            "reports/grok/M36/world_orchestration_snapshot.json",
        ],
    ),
    (
        "M16_M50_M59_M44",
        "scripts.export_university_exam_radar_snapshots",
        [
            "reports/grok/M59/university_snapshot.json",
            "reports/grok/M50/weekly_exam_snapshot.json",
            "reports/grok/M44/science_radar_snapshot.json",
        ],
    ),
    ("M18_newsroom", "scripts.export_newsroom_snapshot", ["reports/grok/M18/newsroom_snapshot.json"]),
    ("M65_teaching", "scripts.export_teaching_journal_snapshot", ["reports/grok/M65/teaching_journal_snapshot.json"]),
    ("M19_macro", "scripts.export_macro_overlays_snapshot", ["reports/grok/M19/macro_overlays_snapshot.json"]),
    ("M56_red_team", "scripts.export_strategy_red_team_snapshot", ["reports/grok/M56/strategy_red_team_snapshot.json"]),
    ("M_PORT", "scripts.export_portable_migration_pack", ["reports/grok/M62/portable_migration_pack.json"]),
    ("M31_nightly", "scripts.export_nightly_digest_snapshot", ["reports/grok/M31/nightly_digest_snapshot.json", "reports/grok/M31/nightly_digest_fa.md"]),
    ("M13_edge_margin", "scripts.export_edge_margin_snapshot", ["reports/grok/M13/edge_margin_sim_snapshot.json"]),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_entry(rel: str) -> dict:
    path = ROOT / Path(rel)
    if not path.is_file():
        return {"path": rel, "exists": False, "mtime_iso": None, "bytes": 0}
    st = path.stat()
    return {
        "path": rel,
        "exists": True,
        "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes": st.st_size,
    }


def run_all_exports() -> dict:
    started = _utc_now()
    step_results: list[dict] = []
    all_files: list[dict] = []

    for label, module_name, outputs in EXPORT_STEPS:
        mod = importlib.import_module(module_name)
        code = int(mod.main())
        files = [_file_entry(rel) for rel in outputs]
        all_files.extend(files)
        step_results.append({"step": label, "module": module_name, "exit_code": code, "outputs": files})

    manifest = {
        "schema": "ahos.daily_exporter_manifest.v1",
        "generated_at": _utc_now(),
        "started_at": started,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "steps_count": len(step_results),
        "files_count": len(all_files),
        "steps": step_results,
        "exports": all_files,
    }
    out_path = ROOT / MANIFEST_REL
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["manifest_path"] = MANIFEST_REL
    return manifest


def main() -> int:
    manifest = run_all_exports()
    failed = [s for s in manifest["steps"] if s["exit_code"] != 0]
    print(
        f"wrote {MANIFEST_REL} steps={manifest['steps_count']} files={manifest['files_count']} "
        f"failed={len(failed)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
