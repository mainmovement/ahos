"""NEXT TRANCHE: scheduling receipt, M58 promote loop telemetry, University exam, Didehban, Negahban, ideas shelf.

PAPER_ONLY — receipts and read-model exports only; no auto-promotion or live trading.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRANCHE_REL = Path("reports") / "grok" / "CONTINUATION" / "next_tranche_receipt.json"
M58_PROMOTE_REL = Path("reports") / "grok" / "M58" / "promote_loop_receipt.json"
DIDEHBAN_REL = Path("reports") / "grok" / "M18" / "didehban_desk_receipt.json"
IDEAS_REL = Path("reports") / "grok" / "M57" / "ideas_shelf_receipt.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(root: Path, rel: Path | str) -> dict[str, Any] | None:
    try:
        doc = json.loads((root / rel).read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def build_scheduling_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    from config.paths import get_local_db_path

    db = Path(get_local_db_path())
    sched_py = root / "architecture" / "scheduling" / "engine.py"
    task_reg = _read_json(root, Path("reports") / "grok" / "CONTINUATION" / "windows_scheduled_tasks.json") or {}
    return {
        "schema": "ahos.scheduling_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "production_scheduler_module": str(sched_py.relative_to(root)).replace("\\", "/") if sched_py.is_file() else None,
        "scheduler_db_exists": db.is_file(),
        "scheduler_db_path": str(db),
        "snapshot_schedule_windows": ["s+15m", "s+1h", "s+4h", "s+12h", "s+24h", "s+48h", "s+72h", "s+7d"],
        "windows_tasks": task_reg.get("tasks"),
        "windows_tasks_registered_at": task_reg.get("registered_at"),
        "authority": "observation_windows_only",
        "note": "Production cadence is Windows Task Scheduler (AHOS_* tasks); this receipt mirrors registration state.",
    }


def build_m58_promote_loop_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    from architecture.learning.strategy_switch import load as load_switch
    from architecture.university.science_to_desk_pipeline import build_aci_agi_si_loop_status

    sw = load_switch(root)
    loop = build_aci_agi_si_loop_status(root)
    red = _read_json(root, Path("reports") / "grok" / "M56" / "red_team_audit.json") or {}
    eligible = list(red.get("promotion_eligible") or [])
    doc = {
        "schema": "ahos.m58_promote_loop_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "auto_promote_enabled": False,
        "strategy_switch_version": sw.get("version"),
        "active_promotions": sw.get("active") or {},
        "promotion_eligible_candidates": eligible,
        "aci_agi_si_loop_status": loop.get("loop_status"),
        "promote_fn": "architecture.learning.strategy_switch.promote (human/agent explicit only)",
        "gates_required": ["PASS_STATS", "SURVIVED_RED_TEAM", "oos_trades>=30"],
        "next_human_actions": [
            "Review promotion_eligible vs live UNPROVEN_EDGE book",
            "Never promote from shadow hit_rate alone",
        ],
    }
    out = root / M58_PROMOTE_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def build_didehban_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    news = _read_json(root, Path("reports") / "grok" / "M18" / "newsroom_snapshot.json") or {}
    corr = _read_json(root, Path("reports") / "grok" / "M18" / "news_corroboration_snapshot.json") or {}
    clusters = news.get("rssClusters") or news.get("rss_clusters") or []
    corroborated = sum(1 for c in clusters if c.get("state") == "CORROBORATED")
    reg = _read_json(root, Path("reports") / "grok" / "M18" / "news_registry.json") or {}
    stats = news.get("stats") if isinstance(news.get("stats"), dict) else {}
    doc = {
        "schema": "ahos.didehban_desk_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "organ": "Didehban OSINT (M18 / news_desk)",
        "newsroom_generated_at": news.get("generated_at"),
        "corroborated_clusters": corroborated,
        "feeds_used": stats.get("feeds_used"),
        "registry_candidates": reg.get("candidates"),
        "registry_verified_any": sum(1 for s in (reg.get("sources") or []) if s.get("verified_any")),
        "registry_generated_at": reg.get("generated_at"),
        "corroboration_snapshot_at": corr.get("generated_at"),
        "two_source_rule": "CORROBORATED requires >=2 independent domains",
        "authority": "evidence_for_council_and_macro_only",
    }
    out = root / DIDEHBAN_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def build_negahban_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    from architecture.security.negahban import run_whitehat_security_audit

    audit = run_whitehat_security_audit(root)
    out = root / Path("reports") / "grok" / "M64" / "whitehat_security_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks = audit.get("checks") or []
    doc = {
        "schema": "ahos.negahban_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "organ": "Negahban Security (M64/M80-B)",
        "overall_verdict": audit.get("overall_verdict"),
        "checks_passed": sum(1 for c in checks if c.get("verdict") == "CLEAN"),
        "checks_total": len(checks),
        "python_cve_findings": (
            (next((c for c in checks if c.get("check") == "cve_supply_chain_audit"), {}) or {}).get(
                "python_runtime_vulnerabilities"
            )
            or []
        ),
        "npm_advisories_noted": (
            (next((c for c in checks if c.get("check") == "cve_supply_chain_audit"), {}) or {}).get(
                "npm_advisories_noted"
            )
            or []
        ),
        "audit_path": "reports/grok/M64/whitehat_security_audit.json",
        "authority": "defensive_audit_only",
    }
    return doc


def build_ideas_shelf_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    props = sorted((root / "proposals").glob("prop_*.json")) if (root / "proposals").is_dir() else []
    ideas: list[dict[str, Any]] = []
    for p in props[:40]:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ideas.append(
            {
                "file": p.name,
                "title": doc.get("title") or doc.get("name") or p.stem,
                "status": doc.get("status", "PROPOSED"),
                "paper_only": True,
            }
        )
    reg = _read_json(root, Path("strategy_lab") / "registry.json") or {}
    not_run = sum(1 for c in (reg.get("candidates") or {}).values() if c.get("verdict") == "NOT_RUN")
    doc = {
        "schema": "ahos.ideas_shelf_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "proposals_count": len(props),
        "proposals_sample": ideas[:12],
        "registry_not_run": not_run,
        "note": "Ideas shelf is advisory; promotion remains gated.",
    }
    out = root / IDEAS_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def build_university_exam_receipt(root: Path) -> dict[str, Any]:
    root = Path(root)
    from architecture.learning.exam import build_live_exam_receipt, run_heldout_5domain_exam

    heldout = run_heldout_5domain_exam(root=root)
    live = build_live_exam_receipt(root)
    return {
        "schema": "ahos.university_exam_tranche_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "heldout_5domain": {k: heldout.get(k) for k in ("overall_score", "leaked", "status", "generated_at")},
        "live_exam_receipt": {
            k: (live.get(k) if isinstance(live, dict) else None)
            for k in ("live_daemon_episodes", "historical_oos_episodes")
        },
        "paths": [
            "reports/grok/M50/weekly_exam_snapshot.json",
            "reports/grok/M50/live_conflict_exam_items.json",
            "reports/grok/M50/live_exam_receipt.json",
        ],
    }


def run_next_tranche(root: Path | None = None) -> dict[str, Any]:
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    from architecture.university.research_prediction_scoring import M57_WEEKLY_REL, export_weekly_shadow_scorecard_to_m57

    weekly = export_weekly_shadow_scorecard_to_m57(root)
    doc = {
        "schema": "ahos.next_tranche_receipt.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "iso_week": weekly.get("iso_week"),
        "tracks": {
            "scheduling": build_scheduling_receipt(root),
            "m58_promote_loop": build_m58_promote_loop_receipt(root),
            "university_exam": build_university_exam_receipt(root),
            "didehban": build_didehban_receipt(root),
            "negahban": build_negahban_receipt(root),
            "ideas_shelf": build_ideas_shelf_receipt(root),
            "m57_weekly_shadow_scorecard": {
                "path": str(M57_WEEKLY_REL.as_posix()).replace("\\", "/"),
                "hypotheses_tracked": weekly.get("hypotheses_tracked"),
                "outcomes_total": weekly.get("outcomes_total"),
            },
        },
    }
    out = root / TRANCHE_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
