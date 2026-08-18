#!/usr/bin/env python3
"""GAP-002 regression: collector-level provider failures must be durable & visible.

Discovered during the Month-1 soak pilot: provider outages were swallowed by
`CollectorEngine.collect_candidates` (no log, no persisted record) — making
"providers down" indistinguishable from "market honestly empty". These tests pin
the fix: fail closed AND explicitly observable.
"""
import logging
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.collector.engine import CollectorEngine
from architecture.providers.registry import ProviderRouter


class ExplodingTransport:
    def __call__(self, req, timeout=10):
        raise ConnectionError("network unreachable (injected)")


def _events(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT kind, provider_id, error_class FROM provider_failure_events").fetchall()]
    conn.close()
    return rows


def test_provider_failure_is_durable_and_logged(tmp_path, caplog):
    db = tmp_path / "discovery.sqlite"
    engine = CollectorEngine(db_path=str(db),
                             router=ProviderRouter(transport=ExplodingTransport()))
    with caplog.at_level(logging.WARNING, logger="ahos.collector"):
        records = engine.collect_candidates("solana", limit=5)

    assert records == []  # fail closed — zero candidates, never fabricated
    events = _events(db)
    fetch_errors = [e for e in events if e["kind"] == "FETCH_ERROR"]
    assert {e["provider_id"] for e in fetch_errors} == {"dexscreener", "geckoterminal"}
    assert all(e["error_class"] == "ConnectionError" for e in fetch_errors)
    # visible in logs too (not just the DB)
    assert any("collector provider failure" in r.message for r in caplog.records)


def test_breaker_open_skip_is_durable(tmp_path):
    db = tmp_path / "discovery.sqlite"
    engine = CollectorEngine(db_path=str(db),
                             router=ProviderRouter(transport=ExplodingTransport()))
    # Trip both breakers (threshold 3), then one more cycle which must be skipped
    for _ in range(3):
        engine.collect_candidates("solana", limit=2)
    engine.collect_candidates("solana", limit=2)  # breakers now OPEN -> fail-fast skip
    skips = [e for e in _events(db) if e["kind"] == "BREAKER_OPEN_SKIP"]
    assert skips, "breaker-open skips must also be recorded (silent zero is forbidden)"
    assert {e["provider_id"] for e in skips} == {"dexscreener", "geckoterminal"}


def test_failure_events_survive_process_replacement(tmp_path):
    db = tmp_path / "discovery.sqlite"
    engine = CollectorEngine(db_path=str(db),
                             router=ProviderRouter(transport=ExplodingTransport()))
    engine.collect_candidates("solana", limit=2)
    del engine  # process dies

    engine2 = CollectorEngine(db_path=str(db),
                              router=ProviderRouter(transport=ExplodingTransport()))
    engine2.collect_candidates("solana", limit=2)
    events = _events(db)
    assert len([e for e in events if e["kind"] == "FETCH_ERROR"]) >= 4  # history intact + appended
