from __future__ import annotations

import json
from pathlib import Path

from architecture.autonomy.whole_project_integrity_auditor import (
    audit_arena_pages,
    audit_kian_and_telegram_wiring,
    audit_snapshots,
    export_integrity_audit_snapshot,
)


def test_snapshot_json_integrity() -> None:
    root = Path(__file__).resolve().parents[2] / "reports" / "grok"
    snap = audit_snapshots(root)
    assert snap["snapshots_audited"] >= 25
    assert snap["snapshots_healthy"] >= 25


def test_arena_pages_scan() -> None:
    arena = Path(__file__).resolve().parents[2].parent / "ahos_arena"
    pages = audit_arena_pages(arena)
    assert pages["pages_audited"] >= 10
    assert pages["pages_clean_live"] >= 8


def test_kian_telegram_wiring() -> None:
    ahos = Path(__file__).resolve().parents[2]
    launcher = ahos.parent / "AHOS_Launcher"
    wire = audit_kian_and_telegram_wiring(ahos, launcher)
    assert wire["telegram_bot_ready"] is True
    assert wire["kian_gateway_ready"] is True


def test_hold_flags_preserved() -> None:
    ahos = Path(__file__).resolve().parents[2]
    wire = audit_kian_and_telegram_wiring(ahos, ahos.parent / "AHOS_Launcher")
    assert wire["hold_flags_intact"] is True
    assert wire["hold_flags_count"] >= 12


def test_export_integrity_snapshot_file() -> None:
    ahos = Path(__file__).resolve().parents[2]
    out = ahos / "reports" / "grok" / "M60_I" / "integrity_audit_snapshot.json"
    payload = export_integrity_audit_snapshot(out, ahos_root=ahos)
    assert out.is_file()
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["mission_id"] == "M60.I"
    assert payload["schema_version"] == "1.0"


def test_overall_integrity_at_least_95() -> None:
    ahos = Path(__file__).resolve().parents[2]
    out = ahos / "reports" / "grok" / "M60_I" / "integrity_audit_snapshot.json"
    payload = export_integrity_audit_snapshot(out, ahos_root=ahos)
    assert payload["overall_integrity_pct"] >= 95.0
