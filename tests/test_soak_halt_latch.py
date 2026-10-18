"""Soak runner skips cycles after a latched HALT."""
from __future__ import annotations

import json

import scripts.m13_gold_soak as soak


def test_second_loop_iteration_is_skipped_after_breaker_halt(monkeypatch, tmp_path):
    soak_dir = tmp_path / "M13_SOAK"
    soak_dir.mkdir()
    calls = {"cycle": 0}

    def _cycle(_path):
        calls["cycle"] += 1
        return {
            "ts": "2026-10-18T00:00:00Z",
            "kind": "cycle",
            "ok": True,
            "duration_s": 0.0,
            "breaker": {"allowed": False, "state": "TRIPPED", "reasons": ["test trip"]},
        }

    sleeps = {"n": 0}

    def _sleep(_sec):
        sleeps["n"] += 1
        if sleeps["n"] >= 2:
            raise SystemExit(0)

    monkeypatch.setattr(soak, "_cycle", _cycle)
    monkeypatch.setattr(soak, "_daily_report", lambda *a, **k: {"verdict": "CLEAN", "findings": 0})
    monkeypatch.setattr(soak, "_tier_report", lambda *a, **k: {"ok": True, "tier": "T0", "measurable_passed": 0, "measurable_total": 6, "unmeasurable": []})
    monkeypatch.setattr(soak, "_reconcile_report", lambda *a, **k: {"ok": True, "verdict": "OK", "findings": 0, "halt_recorded": False})
    monkeypatch.setattr(soak, "_latest_state", lambda _p: None)
    monkeypatch.setattr(soak.time, "sleep", _sleep)

    try:
        soak.run_soak(interval_sec=1, days=1, soak_dir=soak_dir, ledger_path=None, once=False)
    except SystemExit:
        pass

    lines = (soak_dir / "soak_runlog.jsonl").read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines]
    cycles = [r for r in records if r.get("kind") == "cycle"]
    assert calls["cycle"] == 1
    assert len(cycles) >= 2
    assert cycles[1].get("skipped") is True
    status = json.loads((soak_dir / "soak_status.json").read_text(encoding="utf-8"))
    assert status["health"]["latched"] is True
    assert status["entries_allowed"] is False
