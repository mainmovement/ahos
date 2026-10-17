"""M47 fault injection and M39 monthly paper halt suite.

Faults are observations. Nothing here kills a process, fills a disk, locks
PGlite, rewrites the live ledger, or clears HOLD.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import scripts.m13_gold_soak as soak
from architecture.health.faults import (
    DECISION_BUDGET_SEC,
    M39_FAULTS,
    M47_FAULTS,
    depeg_must_halt,
    owner_unhalt,
    refuse_log_deletion,
    respond,
    run_fault_suite,
)
from architecture.health.monitor import latch_halt


def test_four_m47_faults_halt_inside_budget():
    results = run_fault_suite(M47_FAULTS)
    assert len(results) == 4
    assert {r.fault for r in results} == set(M47_FAULTS)
    for row in results:
        assert row.level == "HALT"
        assert row.within_budget
        assert row.elapsed_sec < DECISION_BUDGET_SEC


def test_m39_monthly_faults_halt_and_reject_promotion():
    for name in M39_FAULTS:
        row = respond(name, requested="PROMOTE")
        assert row.level == "HALT"
        assert row.promotion_rejected is True
        assert row.within_budget


def test_ai_cannot_unhalt_or_promote():
    assert owner_unhalt(actor="ai", owner_signature="owner-signed-token", halt_active=True) is False
    assert owner_unhalt(actor="owner", owner_signature="short", halt_active=True) is False
    assert owner_unhalt(actor="owner", owner_signature=None, halt_active=True) is False
    assert owner_unhalt(
        actor="owner", owner_signature="owner-signed-token", halt_active=True
    ) is True
    promoted = respond("ledger_mismatch", requested="LIVE")
    assert promoted.level == "HALT"
    assert promoted.promotion_rejected is True


def test_monitor_cannot_delete_a_log(tmp_path: Path):
    log = tmp_path / "soak_runlog.jsonl"
    log.write_text('{"ok": true}\n', encoding="utf-8")
    before = log.read_bytes()
    assert refuse_log_deletion(log) == "refused: M47 cannot delete logs"
    assert log.read_bytes() == before
    source = (Path(__file__).resolve().parents[1] / "architecture" / "health" / "faults.py").read_text(encoding="utf-8")
    assert ".unlink(" not in source
    assert "rmtree" not in source
    assert "HOLD.flag" not in source


def test_depeg_threshold_is_half_percent():
    assert depeg_must_halt(0.5) is False
    assert depeg_must_halt(0.51) is True
    assert depeg_must_halt(-0.51) is True


def test_halt_latches_until_owner_and_downgrade_does_not():
    assert latch_halt(False, "READ") is False
    assert latch_halt(False, "DOWNGRADE") is False
    assert latch_halt(False, "HALT") is True
    assert latch_halt(True, "READ") is True


def test_soak_once_records_read_health(monkeypatch, tmp_path: Path):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _cycle(_path):
        return {
            "ts": now,
            "kind": "cycle",
            "ok": True,
            "duration_s": 0.0,
            "cycle": 1,
            "breaker": {"allowed": True, "state": "ARMED"},
        }

    monkeypatch.setattr(soak, "_cycle", _cycle)
    monkeypatch.setattr(soak, "_daily_report", lambda *a, **k: {"verdict": "CLEAN", "findings": 0})
    monkeypatch.setattr(
        soak, "_tier_report",
        lambda *a, **k: {
            "ok": True, "tier": "T0", "measurable_passed": 0,
            "measurable_total": 6, "unmeasurable": [],
        },
    )
    monkeypatch.setattr(
        soak, "_reconcile_report",
        lambda *a, **k: {
            "ok": True, "verdict": "OK", "findings": 0, "halt_recorded": False,
        },
    )
    monkeypatch.setattr(soak, "_latest_state", lambda _path: None)

    dest = tmp_path / "M13_SOAK"
    rc = soak.run_soak(
        interval_sec=900, days=1, soak_dir=dest, ledger_path=None, once=True,
    )
    assert rc == 0
    status = json.loads((dest / "soak_status.json").read_text(encoding="utf-8"))
    assert status["paper_only"] is True
    assert status["health"]["level"] == "READ"
    assert status["health"]["latched"] is False
    assert status["entries_allowed"] is True
