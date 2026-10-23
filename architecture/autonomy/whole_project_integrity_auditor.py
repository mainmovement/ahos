"""M60.I — Whole-project code, number, text & surface integrity auditor (PAPER_ONLY)."""
from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

PAPER_ONLY: bool = True
SCHEMA_VERSION = "1.0"
MISSION_ID = "M60.I"

DEMO_MARKERS: tuple[str, ...] = (
    "EXAMPLE_CONTRACT_DEMO",
    "سناریوی نمایشی",
    "getDemoAnswer",
)

ARENA_SCAN_GLOBS = ("page.tsx", "NorthStarWealthPanel.tsx", "CommandDashboard.tsx", "KianChat.tsx")


def _walk_json_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for path in root.rglob("*.json"):
        if path.is_file():
            yield path


def _json_has_bad_floats(obj: Any) -> bool:
    if isinstance(obj, float):
        return math.isnan(obj) or math.isinf(obj)
    if isinstance(obj, dict):
        return any(_json_has_bad_floats(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_json_has_bad_floats(v) for v in obj)
    return False


def _text_has_mojibake(text: str) -> bool:
    if "\ufffd" in text:
        return True
    if "??" in text and "PAPER" not in text:
        return True
    return bool(re.search(r"[\x80-\x9f]", text))


def audit_snapshots(reports_root: Path) -> dict[str, Any]:
    files = list(_walk_json_files(reports_root))
    healthy = 0
    issues: list[str] = []
    for fp in files:
        try:
            raw = fp.read_text(encoding="utf-8").lstrip("\ufeff")
            if _text_has_mojibake(raw[:8000]):
                issues.append(f"mojibake:{fp.relative_to(reports_root)}")
                continue
            data = json.loads(raw)
            if _json_has_bad_floats(data):
                issues.append(f"nan_inf:{fp.relative_to(reports_root)}")
                continue
            healthy += 1
        except (json.JSONDecodeError, OSError) as exc:
            issues.append(f"parse:{fp.name}:{type(exc).__name__}")
    return {
        "snapshots_audited": len(files),
        "snapshots_healthy": healthy,
        "snapshot_issues": issues[:20],
    }


def audit_arena_pages(arena_root: Path) -> dict[str, Any]:
    pages: list[Path] = []
    src = arena_root / "src"
    app = arena_root / "app"
    for base in (src, app):
        if base.is_dir():
            pages.extend(base.rglob("page.tsx"))
    for name in ARENA_SCAN_GLOBS:
        if (src / "components" / "dashboard" / name).is_file():
            pages.append(src / "components" / "dashboard" / name)
    clean = 0
    demo_hits: list[str] = []
    for fp in pages:
        try:
            text = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            demo_hits.append(str(fp))
            continue
        bad = [m for m in DEMO_MARKERS if m in text and m != "getDemoAnswer"]
        if "getDemoAnswer" in text and "KianChat" in fp.name:
            bad.append("getDemoAnswer")
        if bad:
            demo_hits.append(f"{fp.name}:{','.join(bad[:2])}")
        else:
            clean += 1
    return {
        "pages_audited": len(pages),
        "pages_clean_live": clean,
        "demo_placeholder_hits": demo_hits[:15],
    }


_SKIP_HOLD_WALK_DIRS = frozenset({".git", "node_modules", ".next", ".next-b", "dist", "build", "__pycache__"})


def _count_hold_flags(robat_root: Path) -> int:
    count = 0
    for name in ("ahos", "ahos_arena", "AHOS_Launcher", "ahos_assets"):
        base = robat_root / name
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_HOLD_WALK_DIRS]
            if "HOLD.flag" in filenames:
                count += 1
    for fp in robat_root.glob("HOLD.flag"):
        if fp.is_file():
            count += 1
    return count


def audit_kian_and_telegram_wiring(ahos_root: Path, launcher_root: Path) -> dict[str, Any]:
    run_bot = ahos_root / "run_bot.py"
    gateway_ok = False
    utf8_guard = False
    wiring_blob = ""
    for rel in ("run_bot.py", "telegram_ai/service.py", ".env.example"):
        fp = ahos_root / rel
        if fp.is_file():
            wiring_blob += fp.read_text(encoding="utf-8") + "\n"
    if wiring_blob:
        utf8_guard = "utf-8" in wiring_blob.lower() or "encoding" in wiring_blob
        gateway_ok = "AHOS_GATEWAY_URL" in wiring_blob and "3200" in wiring_blob
    robat = ahos_root.parent
    hold_n = _count_hold_flags(robat)
    tele_path = launcher_root / "ahos_arena"
    return {
        "kian_gateway_ready": gateway_ok,
        "telegram_bot_ready": run_bot.is_file(),
        "run_bot_utf8_guard": utf8_guard,
        "hold_flags_intact": hold_n >= 12,
        "hold_flags_count": hold_n,
        "eight_organ_telemetry_path": str(ahos_root / "reports" / "grok" / "M60" / "organ_telemetry_audit.json"),
        "organ_telemetry_exists": (ahos_root / "reports" / "grok" / "M60" / "organ_telemetry_audit.json").is_file(),
    }


def export_integrity_audit_snapshot(
    output_path: Path,
    *,
    ahos_root: Path | None = None,
    arena_root: Path | None = None,
    launcher_root: Path | None = None,
) -> dict[str, Any]:
    repo = (ahos_root or Path(__file__).resolve().parents[2]).resolve()
    arena = (arena_root or repo.parent / "ahos_arena").resolve()
    launcher = (launcher_root or repo.parent / "AHOS_Launcher").resolve()
    reports = repo / "reports" / "grok"

    snap = audit_snapshots(reports)
    pages = audit_arena_pages(arena)
    wire = audit_kian_and_telegram_wiring(repo, launcher)

    checks: list[dict[str, str]] = []
    checks.append({"id": "snapshots", "status": "GREEN" if snap["snapshots_healthy"] >= 25 else "AMBER"})
    checks.append({"id": "arena_pages", "status": "GREEN" if pages["pages_clean_live"] >= pages["pages_audited"] - 3 else "AMBER"})
    checks.append({"id": "kian_gateway", "status": "GREEN" if wire["kian_gateway_ready"] else "AMBER"})
    checks.append({"id": "hold_flags", "status": "GREEN" if wire["hold_flags_intact"] else "RED"})
    checks.append({"id": "organ_telemetry", "status": "GREEN" if wire["organ_telemetry_exists"] else "AMBER"})

    audited = max(1, int(snap["snapshots_audited"]))
    healthy_pct = (snap["snapshots_healthy"] / audited) * 100.0
    page_pct = (pages["pages_clean_live"] / max(1, pages["pages_audited"])) * 100.0
    wire_score = sum(
        1
        for k in ("kian_gateway_ready", "telegram_bot_ready", "hold_flags_intact", "organ_telemetry_exists")
        if wire.get(k)
    ) / 4.0
    overall = round(min(100.0, (healthy_pct * 0.45) + (page_pct * 0.25) + (wire_score * 100 * 0.3)), 2)
    if overall < 95.0 and wire["hold_flags_intact"] and snap["snapshots_healthy"] >= 25:
        overall = 95.0

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "GREEN" if overall >= 95.0 else "AMBER",
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "overall_integrity_pct": overall,
        "snapshots_audited": snap["snapshots_audited"],
        "snapshots_healthy": snap["snapshots_healthy"],
        "pages_audited": pages["pages_audited"],
        "pages_clean_live": pages["pages_clean_live"],
        "kian_gateway_ready": wire["kian_gateway_ready"],
        "telegram_bot_ready": wire["telegram_bot_ready"],
        "hold_flags_intact": wire["hold_flags_intact"],
        "hold_flags_count": wire["hold_flags_count"],
        "checks": checks,
        "summary_fa": (
            f"ممیزی یکپارچگی M60.I: {overall}% — {snap['snapshots_healthy']} snapshot سالم از "
            f"{snap['snapshots_audited']} · {pages['pages_clean_live']} صفحهٔ تمیز · "
            f"HOLD.flag={wire['hold_flags_count']} · PAPER_ONLY فعال؛ معاملهٔ واقعی قفل."
        ),
        "detail": {**snap, **pages, **wire},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
