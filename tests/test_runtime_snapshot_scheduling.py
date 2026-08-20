#!/usr/bin/env python3
"""Daemon automatic soak-snapshot scheduling (M-GAP-003 support).

`architecture/runtime/__main__.py::write_soak_snapshots` is the first
production consumer of the soak/system-state snapshot scripts: it turns the
168h protocol's manual 6h snapshot cadence into an automatic daemon feature.

Pinned here:
  * Both snapshots are written with timestamped filenames and returned.
  * A failure in ONE snapshot never blocks the other, never raises.
  * A total failure returns an empty list (the daemon logs and continues).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.runtime import __main__ as runtime_main  # noqa: E402


def _fake_soak(monkeypatch, snapshot=None, raise_exc=False):
    def _snap(local_db=None, discovery_db=None, window_hours=24.0, now=None):
        if raise_exc:
            raise RuntimeError("soak snapshot boom (injected)")
        return snapshot or {
            "snapshot_utc": "2026-08-20T12:00:00Z",
            "window_hours": window_hours,
            "integrity": {"local_db": "ok", "discovery_db": "ok"},
        }
    monkeypatch.setattr("scripts.soak_snapshot.snapshot", _snap)


def _fake_state(monkeypatch, report=None, raise_exc=False):
    def _build(probe_providers=False, window_hours=24.0):
        if raise_exc:
            raise RuntimeError("state snapshot boom (injected)")
        return report or {
            "schema": "ahos.system_state.v1",
            "timestamp_utc": "2026-08-20T12:00:00Z",
            "result": "RECORDED",
            "lane_a": {"ok": True},
            "watchdog": {"status": "NO_HEARTBEATS"},
            "events": [],
        }
    monkeypatch.setattr("scripts.system_state_snapshot.build_snapshot", _build)


def test_write_soak_snapshots_writes_both_artifacts(tmp_path, monkeypatch):
    _fake_soak(monkeypatch)
    _fake_state(monkeypatch)

    paths = runtime_main.write_soak_snapshots(
        local_db=str(tmp_path / "l.sqlite"),
        discovery_db=str(tmp_path / "d.sqlite"),
        window_hours=6.0,
        probe_providers=False,
        reports_dir=tmp_path / "reports",
        now=1755700000.0,
    )

    assert len(paths) == 2
    assert all(p.exists() for p in paths)
    names = {p.name for p in paths}
    assert any(n.startswith("soak_snapshot_") for n in names)
    assert any(n.startswith("system_state_snapshot_") for n in names)

    soak = json.loads(paths[0].read_text(encoding="utf-8"))
    assert soak["snapshot_utc"] == "2026-08-20T12:00:00Z"
    assert soak["window_hours"] == 6.0

    state = json.loads(paths[1].read_text(encoding="utf-8"))
    assert state["result"] == "RECORDED"


def test_one_failure_does_not_block_the_other(tmp_path, monkeypatch):
    _fake_soak(monkeypatch, raise_exc=True)
    _fake_state(monkeypatch)

    paths = runtime_main.write_soak_snapshots(
        local_db=str(tmp_path / "l.sqlite"),
        discovery_db=str(tmp_path / "d.sqlite"),
        window_hours=6.0,
        probe_providers=False,
        reports_dir=tmp_path / "reports",
        now=1755700000.0,
    )

    assert len(paths) == 1
    assert paths[0].name.startswith("system_state_snapshot_")


def test_total_failure_returns_empty_without_raising(tmp_path, monkeypatch):
    _fake_soak(monkeypatch, raise_exc=True)
    _fake_state(monkeypatch, raise_exc=True)

    paths = runtime_main.write_soak_snapshots(
        local_db=str(tmp_path / "l.sqlite"),
        discovery_db=str(tmp_path / "d.sqlite"),
        window_hours=6.0,
        probe_providers=False,
        reports_dir=tmp_path / "reports",
        now=1755700000.0,
    )
    assert paths == []


def test_snapshot_flags_exist_on_the_runtime_entrypoint():
    import argparse
    import inspect

    src = inspect.getsource(runtime_main.main)
    assert "--snapshot-interval-hours" in src
    assert "--snapshot-probe-providers" in src
