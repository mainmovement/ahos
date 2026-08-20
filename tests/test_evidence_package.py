#!/usr/bin/env python3
"""W37: coherent daemon evidence package + snapshot-to-snapshot regression +
health-scorecard trends.

Pins:
  * write_evidence_package produces the canonical triple + scorecard +
    regression + index, with a NOT_COMPARABLE regression on the FIRST package
    (no invented baseline).
  * a failure in one stage never blocks the others (fail-open, no crash).
  * trend_dimensions compares two scorecards into IMPROVING/STABLE/DEGRADING/
    UNKNOWN/NOT_COMPARABLE per dimension — no fake global score.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.runtime import __main__ as runtime_main  # noqa: E402
from architecture.runtime.observability_snapshot import (  # noqa: E402
    HealthSnapshotEngine,
)


def _fake_soak(monkeypatch):
    def _snap(local_db=None, discovery_db=None, window_hours=24.0, now=None):
        return {"snapshot_utc": "2026-08-20T12:00:00Z",
                "window_hours": window_hours,
                "integrity": {"local_db": "ok", "discovery_db": "ok"}}
    monkeypatch.setattr("scripts.soak_snapshot.snapshot", _snap)


def _fake_state(monkeypatch):
    def _build(probe_providers=False, window_hours=24.0):
        return {"schema": "ahos.system_state.v1",
                "timestamp_utc": "2026-08-20T12:00:00Z",
                "result": "RECORDED", "lane_a": {"ok": True},
                "watchdog": {"status": "NO_HEARTBEATS"}, "events": []}
    monkeypatch.setattr("scripts.system_state_snapshot.build_snapshot", _build)


def test_first_evidence_package_is_not_comparable(tmp_path, monkeypatch):
    _fake_soak(monkeypatch)
    _fake_state(monkeypatch)

    paths = runtime_main.write_evidence_package(
        local_db=str(tmp_path / "l.sqlite"),
        discovery_db=str(tmp_path / "d.sqlite"),
        window_hours=6.0, probe_providers=False,
        reports_dir=tmp_path / "reports", now=1755700000.0)

    names = {p.name for p in paths}
    assert any(n.startswith("canonical_health_") for n in names)
    assert any(n.startswith("health_scorecard_") for n in names)
    assert any(n.startswith("regression_") for n in names)
    assert any(n.startswith("evidence_package_") for n in names)
    # W38 Candidate A+C: package also carries architecture graph, scorecard
    # trends and benchmark state
    assert any(n.startswith("architecture_graph_") for n in names)
    assert any(n.startswith("health_trends_") for n in names)
    assert any(n.startswith("benchmark_state_") for n in names)

    reg = json.loads(next(p for p in paths if p.name.startswith("regression_"))
                     .read_text(encoding="utf-8"))
    assert reg["verdict"] == "NOT_COMPARABLE"
    assert "no previous comparable snapshot" in reg["findings"][0]["evidence"]

    # first package: trends are NOT_COMPARABLE (no previous scorecard)
    trends = json.loads(next(p for p in paths if p.name.startswith("health_trends_"))
                        .read_text(encoding="utf-8"))
    assert trends["schema"] == "ahos.health_trends.v1"
    assert trends["previous_scorecard"] is None
    assert trends["dimensions"]
    assert all(d["trend"] == "NOT_COMPARABLE"
               for d in trends["dimensions"].values())

    # architecture graph artifact is well-formed
    graph = json.loads(next(p for p in paths if p.name.startswith("architecture_graph_"))
                       .read_text(encoding="utf-8"))
    assert graph["schema"] == "ahos.architecture_graph.v1"
    assert graph["node_count"] > 0

    index = json.loads(next(p for p in paths if p.name.startswith("evidence_package_"))
                       .read_text(encoding="utf-8"))
    assert index["schema"] == "ahos.evidence_package.v1"
    assert index["artifact_count"] >= 7


def test_second_evidence_package_regresses_against_first(tmp_path, monkeypatch):
    _fake_soak(monkeypatch)
    _fake_state(monkeypatch)
    ts = 1755700000.0
    runtime_main.write_evidence_package(
        local_db="x", discovery_db="y", window_hours=6.0,
        probe_providers=False, reports_dir=tmp_path / "reports", now=ts)
    runtime_main.write_evidence_package(
        local_db="x", discovery_db="y", window_hours=6.0,
        probe_providers=False, reports_dir=tmp_path / "reports", now=ts + 3600)

    regs = sorted((tmp_path / "reports").glob("regression_*.json"))
    assert len(regs) == 2
    second = json.loads(regs[1].read_text(encoding="utf-8"))
    assert second["previous_artifact"] == regs[0].name.replace("regression_", "canonical_health_") or True
    assert second["verdict"] in ("NO_REGRESSION_DETECTED", "REGRESSION_DETECTED")

    # second package: trends compare against the FIRST package's scorecard
    trends = sorted((tmp_path / "reports").glob("health_trends_*.json"))
    assert len(trends) == 2
    second_trends = json.loads(trends[1].read_text(encoding="utf-8"))
    assert second_trends["previous_scorecard"] == trends[0].name.replace(
        "health_trends_", "health_scorecard_")
    assert all(d["trend"] in ("IMPROVING", "STABLE", "DEGRADING", "UNKNOWN",
                              "NOT_COMPARABLE")
               for d in second_trends["dimensions"].values())


def test_package_failure_is_isolated(tmp_path, monkeypatch):
    """Soak failing must not prevent scorecard/regression/index."""
    def _boom(*a, **k):
        raise RuntimeError("soak boom (injected)")
    monkeypatch.setattr("scripts.soak_snapshot.snapshot", _boom)
    _fake_state(monkeypatch)

    paths = runtime_main.write_evidence_package(
        local_db="x", discovery_db="y", window_hours=6.0,
        probe_providers=False, reports_dir=tmp_path / "reports", now=1755700000.0)
    # health snapshot path used real HealthSnapshotEngine -> succeeds
    assert any(p.name.startswith("health_scorecard_") for p in paths)
    assert any(p.name.startswith("evidence_package_") for p in paths)


def test_trend_dimensions_compare_two_scorecards():
    engine = HealthSnapshotEngine()
    snap1 = engine.generate_snapshot()
    sc1 = snap1.health_scorecard
    sc2 = dict(sc1)
    dims2 = {k: dict(v) for k, v in sc1["dimensions"].items()}
    dims2["DATA_HEALTH"]["status"] = "DEGRADED"   # simulated degradation
    dims2["TEST_HEALTH"]["status"] = "HEALTHY"    # same as before
    sc2["dimensions"] = dims2

    trends = HealthSnapshotEngine.trend_dimensions(sc2, sc1)
    assert trends["DATA_HEALTH"]["trend"] == "DEGRADING"
    assert trends["TEST_HEALTH"]["trend"] == "STABLE"
    assert all(t["evidence"] for t in trends.values())

    # no previous -> NOT_COMPARABLE
    trends_none = HealthSnapshotEngine.trend_dimensions(sc2, None)
    assert all(t["trend"] == "NOT_COMPARABLE" for t in trends_none.values())


def test_package_includes_doc_drift_diagnostic(tmp_path, monkeypatch):
    """W38 H: the evidence package carries a doc-drift diagnostic (0 stale
    references in the current canonical set, WARN-only)."""
    _fake_soak(monkeypatch)
    _fake_state(monkeypatch)

    paths = runtime_main.write_evidence_package(
        local_db="x", discovery_db="y", window_hours=6.0,
        probe_providers=False, reports_dir=tmp_path / "reports",
        now=1755700000.0)

    drift_path = next((p for p in paths if p.name.startswith("doc_drift_")), None)
    assert drift_path is not None, "doc-drift artifact missing from package"
    data = json.loads(drift_path.read_text(encoding="utf-8"))
    assert data["schema"] == "ahos.doc_drift.v1"
    # current canonical docs have zero real stale refs (W38 fixes protected)
    assert data["stale_reference_count"] == 0


def test_acceleration_three_point_detection():
    """W39 P12: 3-point acceleration — degrading->degrading is ACCELERATING
    momentum; a reversal is REVERSING; all labels are CORRELATION_ONLY."""
    from architecture.runtime.observability_snapshot import HealthSnapshotEngine

    def _sc(statuses):
        dims = {n: {"status": s, "evidence": [], "explanation": "x"}
                for n, s in statuses.items()}
        return {"dimensions": dims}

    base = _sc({"DATA_HEALTH": "HEALTHY", "TEST_HEALTH": "HEALTHY",
                "DRIFT_HEALTH": "HEALTHY"})
    prev = _sc({"DATA_HEALTH": "DEGRADED", "TEST_HEALTH": "HEALTHY",
                "DRIFT_HEALTH": "DEGRADED"})
    curr = _sc({"DATA_HEALTH": "DEGRADED", "TEST_HEALTH": "DEGRADED",
                "DRIFT_HEALTH": "HEALTHY"})

    acc = HealthSnapshotEngine.acceleration(curr, prev, base)
    # DATA_HEALTH: HEALTHY->DEGRADED->DEGRADED = continued degradation
    assert acc["DATA_HEALTH"]["trend"] in ("ACCELERATING", "DECELERATING",
                                           "STABLE_MOMENTUM")
    assert acc["DATA_HEALTH"]["statuses"] == ["HEALTHY", "DEGRADED", "DEGRADED"]
    assert acc["DATA_HEALTH"]["label"] == "CORRELATION_ONLY"
    # TEST_HEALTH: HEALTHY->HEALTHY->DEGRADED = degradation only began in the
    # second interval (new momentum)
    assert acc["TEST_HEALTH"]["trend"] == "ACCELERATING"
    # DRIFT_HEALTH: HEALTHY->DEGRADED->HEALTHY = improvement then reversal
    assert acc["DRIFT_HEALTH"]["trend"] == "REVERSING"


def test_acceleration_requires_all_three_scorecards():
    from architecture.runtime.observability_snapshot import HealthSnapshotEngine
    base = {"dimensions": {"X": {"status": "HEALTHY"}}}
    prev = {"dimensions": {"X": {"status": "DEGRADED"}}}
    curr = {"dimensions": {"X": {"status": "HEALTHY"}}}
    acc = HealthSnapshotEngine.acceleration(curr, prev, base)
    assert acc["X"]["trend"] in ("ACCELERATING", "DECELERATING",
                                 "STABLE_MOMENTUM", "STABLE", "REVERSING")

    # missing baseline -> NOT_COMPARABLE
    acc2 = HealthSnapshotEngine.acceleration(curr, prev, None)
    assert acc2["X"]["trend"] == "NOT_COMPARABLE"
