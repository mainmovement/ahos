#!/usr/bin/env python3
"""System-state snapshot must not invent operational success."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import system_state_snapshot as sss  # noqa: E402


def test_snapshot_schema_and_honest_missing_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    report = sss.build_snapshot(probe_providers=False, window_hours=1.0)
    assert report["schema"] == sss.SCHEMA
    assert report["result"] == "RECORDED"
    assert "command" in report and report["git"]["commit_sha"]
    assert "environment" in report and report["environment"]["fingerprint_sha256"]
    assert report["watchdog"]["status"] == "NO_HEARTBEATS"
    for name, st in report["stores"].items():
        assert st["exists"] is False, name
        assert st["integrity_check"] == "NO_DATA"
    assert report["events"], "every snapshot must emit observation events"
    for ev in report["events"]:
        assert ev["timestamp_utc"]
        assert ev["commit_sha"]
        assert ev["event_type"]
        assert ev["severity"] in {"INFO", "WARN", "ERROR"}
        assert ev["evidence_path"]


def test_snapshot_write_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    dest = tmp_path / "system_state_snapshot.json"
    rc = sss.main(["--out", str(dest)])
    assert rc == 0
    loaded = json.loads(dest.read_text(encoding="utf-8"))
    assert loaded["result"] == "RECORDED"
    assert loaded["lane_a"]["ok"] is True


def test_snapshot_probe_delegates_to_canonical_probe(monkeypatch):
    """The snapshot must use the one canonical probe implementation
    (architecture/providers/probe.py, M-GAP-016 statuses) — not a private
    2-provider subset with raw exception class names."""
    from architecture.providers.probe import ProbeReport, ProbeResult

    report = ProbeReport(probed_at_utc="2026-08-20T00:00:00Z", chain="solana")
    report.results = [
        ProbeResult(provider_id="dexscreener", status="SUCCESS", token_count=2,
                    chain="solana", latency_ms=1.5, probed_at_utc="2026-08-20T00:00:00Z"),
        ProbeResult(provider_id="pumpfun", status="UNSUPPORTED", chain="solana",
                    latency_ms=0.0, probed_at_utc="2026-08-20T00:00:00Z"),
    ]
    monkeypatch.setattr("architecture.providers.probe.probe_providers",
                        lambda chain="solana": report)

    rows = sss._probe_providers()
    assert [r["provider_id"] for r in rows] == ["dexscreener", "pumpfun"]
    assert rows[0]["status"] == "SUCCESS" and rows[0]["token_count"] == 2
    assert rows[0]["latency_ms"] == 1.5
    assert rows[1]["status"] == "UNSUPPORTED"
    # canonical probe must be the one wired in (source-level guard)
    import inspect
    src = inspect.getsource(sss._probe_providers)
    assert "architecture.providers.probe" in src or "probe_providers" in src
    assert "DexScreenerAdapter" not in src, "snapshot must not hardcode a provider subset"
