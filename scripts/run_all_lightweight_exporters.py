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
    ("M33_crypto_universe", "scripts.export_crypto_universe_snapshot", ["reports/grok/M33/crypto_universe_snapshot.json"]),
    ("M43_pilot_100usd", "scripts.export_pilot_100usd_gateway_snapshot", ["reports/grok/M43/pilot_100usd_gateway_snapshot.json"]),
    ("M57_science_pipeline", "scripts.export_science_to_desk_pipeline", ["reports/grok/M57/science_to_desk_pipeline_snapshot.json"]),
    (
        "M60_M70_brain_M57_organs",
        "scripts.export_aci_agi_si_brain_snapshot",
        [
            "reports/grok/M60/aci_agi_si_brain_snapshot.json",
            "reports/grok/M57/whole_ahos_organ_evolution.json",
        ],
    ),
    (
        "M35_M10_M45_closure",
        "scripts.export_m35_m10_m45_closure",
        [
            "reports/grok/M35/telegram_kian_closure.json",
            "reports/grok/M10/db_migration_closure.json",
            "reports/grok/M45/sandbox_isolation_snapshot.json",
        ],
    ),
    (
        "M60_autonomous_coder",
        "scripts.export_autonomous_coder_snapshot",
        ["reports/grok/M60/autonomous_coder_snapshot.json"],
    ),
    (
        "M60_hundred_dollar_compounding",
        "scripts.export_compounding_engine_snapshot",
        ["reports/grok/M60/hundred_dollar_compounding_snapshot.json"],
    ),
    (
        "M60_self_evolution_cycle",
        "scripts.export_self_evolution_cycle_snapshot",
        ["reports/grok/M60/self_evolution_cycle_snapshot.json"],
    ),
    (
        "M60_cross_asset_fusion",
        "scripts.export_cross_asset_fusion_snapshot",
        ["reports/grok/M60/cross_asset_fusion_snapshot.json"],
    ),
    (
        "M60_owner_live_switch",
        "scripts.export_owner_live_switch_readiness",
        ["reports/grok/M60/owner_live_switch_readiness.json"],
    ),
    (
        "M60_multi_horizon_risk_shield",
        "scripts.export_multi_horizon_risk_shield",
        ["reports/grok/M60/multi_horizon_risk_shield.json"],
    ),
    (
        "M60_organ_telemetry_audit",
        "scripts.export_organ_telemetry_audit",
        ["reports/grok/M60/organ_telemetry_audit.json"],
    ),
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
    assets_manifest = Path(r"G:\robat\ahos_assets\daily_exporter_manifest.json")
    if assets_manifest.parent.is_dir():
        assets_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
