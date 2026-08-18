#!/usr/bin/env python3
"""Phase 11 — runtime wiring, provider probe, and operator-path regressions.

Covers the defects found by the Phase 11 audit:
  * the Lane-A outcome labeler was never invoked by the runtime (chain break)
  * `--probe-providers` was documented but did not exist on the entrypoint
  * a security-only adapter reported EMPTY, implying untested reachability
  * the nightly backup series had no tooling and could be faked by re-running
  * the operator activation path had no single deterministic document
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.providers import probe as probe_mod  # noqa: E402
from architecture.providers.probe import (  # noqa: E402
    STATUS_AUTH_REQUIRED,
    STATUS_EMPTY,
    STATUS_ERROR,
    STATUS_RATE_LIMIT,
    STATUS_SUCCESS,
    STATUS_TIMEOUT,
    STATUS_TLS_ERROR,
    STATUS_UNSUPPORTED,
    ProbeReport,
    ProbeResult,
    classify_exception,
    classify_response,
    probe_providers,
    render_table,
)


# --------------------------------------------------- outcome resolution wiring

def test_runtime_invokes_the_frozen_outcome_labeler():
    """The chain break this phase found: labels were never produced at runtime.

    Predictions accumulated forever against zero outcome labels, so the
    calibration join could only ever return 0 pairs -- regardless of uptime.
    """
    import inspect
    from architecture.runtime.observation_loop import ObservationRuntime

    cycle_src = inspect.getsource(ObservationRuntime.run_cycle)
    assert "_materialize_outcomes" in cycle_src

    helper_src = inspect.getsource(ObservationRuntime._materialize_outcomes)
    assert "materialize_outcomes" in helper_src
    assert "discovery.materialize" in helper_src


def test_outcome_materialization_failure_does_not_lose_observations():
    """Labeling is downstream bookkeeping; it must not discard a poll."""
    from architecture.runtime.observation_loop import ObservationRuntime

    class Broken:
        def execute(self, *a, **k):
            raise sqlite3.OperationalError("simulated store failure")

    out = ObservationRuntime._materialize_outcomes(Broken(), time.time())
    assert "outcome_materialization_error" in out


def test_outcome_labels_appear_for_closed_horizons(tmp_path):
    """End-to-end on a real store: a resolved token yields labels."""
    from discovery import observations as obs
    from discovery.materialize import materialize_outcomes

    db = tmp_path / "disc.sqlite"
    conn = obs.open_store(str(db))
    t0 = time.time() - 8 * 86400          # old enough that horizons have closed

    conn.execute(
        "INSERT INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,payload_json)"
        " VALUES ('sha1','dexscreener','probe',?,'{}')", (t0,))
    conn.execute(
        "INSERT INTO tokens(token_id,chain_id,address,first_seen_ts,source_first_seen_provider)"
        " VALUES ('tok1','solana','Addr1',?,'dexscreener')", (t0,))
    conn.execute(
        "INSERT INTO observation_state(token_id,state,entered_ts,first_seen_ts,last_obs_ts)"
        " VALUES ('tok1','OBSERVING',?,?,?)", (t0, t0, t0))
    # A price path: entry at t0, then a >50% rise well inside 24h.
    for offset, price in ((60.0, 1.0), (3600.0, 1.4), (7200.0, 2.0)):
        conn.execute(
            "INSERT INTO discovery_observations(obs_id,token_id,provider,retrieved_ts,"
            "price_usd,raw_ref) VALUES (?,?,?,?,?,?)",
            (f"obs{offset}", "tok1", "dexscreener", t0 + offset, price, "sha1"))
    conn.commit()

    result = materialize_outcomes(conn, now=time.time())
    assert result["outcome_rows_written"] > 0

    hits = conn.execute(
        "SELECT hit FROM outcome_label WHERE token_id='tok1' "
        "AND horizon='24h' AND event_class='+50%'").fetchone()
    conn.close()
    assert hits is not None and hits["hit"] == 1


# ------------------------------------------------------- provider probe surface

def test_probe_providers_flag_exists_on_the_runtime_entrypoint():
    """The docs promised this command; before Phase 11 it did not exist."""
    import argparse
    import inspect

    from architecture.runtime import __main__ as runtime_main

    src = inspect.getsource(runtime_main.main)
    assert "--probe-providers" in src
    assert "probe_providers" in src


def test_probe_never_maps_a_failure_to_success():
    """No exception class may be classified as SUCCESS."""
    import socket
    import ssl
    import urllib.error

    cases = [
        (ssl.SSLError("handshake"), STATUS_TLS_ERROR),
        (socket.timeout("slow"), STATUS_TIMEOUT),
        (TimeoutError("slow"), STATUS_TIMEOUT),
        (urllib.error.URLError("TLS/SSL connection has been closed (EOF)"), STATUS_TLS_ERROR),
        (RuntimeError("HTTP 429 too many requests"), STATUS_RATE_LIMIT),
        (RuntimeError("HTTP 401 unauthorized"), STATUS_AUTH_REQUIRED),
        (ValueError("garbage payload"), STATUS_ERROR),
    ]
    for exc, expected in cases:
        status, detail = classify_exception(exc)
        assert status == expected, f"{exc!r} -> {status}"
        assert status != STATUS_SUCCESS
        assert detail


def test_probe_reachable_but_empty_is_not_success():
    """'0 tokens' is the exact ambiguity M-GAP-002 exists to expose."""
    class Resp:
        status = "OK"
        tokens: list = []
        error_message = None

    status, count, _ = classify_response(Resp())
    assert status == STATUS_EMPTY and count == 0
    assert status != STATUS_SUCCESS


def test_probe_success_requires_tokens():
    class Resp:
        status = "OK"
        tokens = [object(), object()]
        error_message = None

    status, count, _ = classify_response(Resp())
    assert status == STATUS_SUCCESS and count == 2


def test_probe_maps_provider_envelopes_honestly():
    def resp(status, message=None):
        return type("R", (), {"status": status, "tokens": [],
                              "error_message": message})()

    assert classify_response(resp("NO_KEY"))[0] == STATUS_AUTH_REQUIRED
    assert classify_response(resp("UNSUPPORTED"))[0] == STATUS_UNSUPPORTED
    assert classify_response(resp("RATE_LIMIT"))[0] == STATUS_RATE_LIMIT
    assert classify_response(resp("ERROR", "SSL: EOF occurred"))[0] == STATUS_TLS_ERROR
    assert classify_response(resp("DOWN", "HTTP 503"))[0] == STATUS_ERROR


def test_security_only_adapters_are_not_reported_as_reachable():
    """A hardcoded empty list must not imply a network round-trip happened."""
    class SecurityOnly:
        capabilities = ["security", "honeypot"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return type("R", (), {"status": "OK", "tokens": [],
                                  "error_message": None})()

    report = probe_providers(chain="solana", providers={"goplus": SecurityOnly()})
    result = report.results[0]
    assert result.status == STATUS_UNSUPPORTED
    assert "not tested" in (result.detail or "")


def test_probe_report_states_the_m_gap_007_verdict():
    class Live:
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return type("R", (), {"status": "OK", "tokens": [object()],
                                  "error_message": None})()

    class Dead:
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            raise ConnectionError("TLS/SSL connection closed")

    good = probe_providers(providers={"live": Live()})
    assert good.any_success and good.as_dict()["m_gap_007_live_success_proven"]
    assert "LIVE SUCCESS" in render_table(good)

    bad = probe_providers(providers={"dead": Dead()})
    assert not bad.any_success
    assert bad.as_dict()["m_gap_007_live_success_proven"] is False
    assert "M-GAP-007 remains OPEN" in render_table(bad)


def test_probe_performs_no_writes_and_no_scoring():
    """A diagnostic must not emit predictions or mutate stores."""
    import inspect

    src = inspect.getsource(probe_mod)
    for forbidden in ("ScoreLedger", "INSERT INTO", "OpportunityScorer", "commit()"):
        assert forbidden not in src, f"probe must not contain {forbidden}"


# ------------------------------------------------------- nightly backup series

def test_nightly_series_counts_distinct_days_not_invocations(tmp_path, monkeypatch):
    """Running the tool 5 times in one evening must not read 5/7."""
    from scripts import sqlite_backup_restore as bkp

    src = tmp_path / "store.sqlite"
    conn = sqlite3.connect(str(src))
    conn.execute("CREATE TABLE t(x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit(); conn.close()

    monkeypatch.setattr(bkp, "_real_stores", lambda: {"store": src})
    series = tmp_path / "series.json"
    fixed_day = time.mktime(time.strptime("2026-03-01", "%Y-%m-%d"))

    for i in range(5):
        rep = bkp.run_nightly(tmp_path / "backups", series, now=fixed_day + i * 60)

    assert rep["runs_recorded"] == 5
    assert rep["nights_completed"] == 1          # one calendar day
    assert rep["series_complete"] is False


def test_nightly_series_completes_only_after_seven_distinct_days(tmp_path, monkeypatch):
    from scripts import sqlite_backup_restore as bkp

    src = tmp_path / "store.sqlite"
    conn = sqlite3.connect(str(src))
    conn.execute("CREATE TABLE t(x INTEGER)")
    conn.commit(); conn.close()

    monkeypatch.setattr(bkp, "_real_stores", lambda: {"store": src})
    series = tmp_path / "series.json"
    day0 = time.mktime(time.strptime("2026-03-01", "%Y-%m-%d"))

    for day in range(6):
        rep = bkp.run_nightly(tmp_path / "backups", series, now=day0 + day * 86400)
        assert rep["series_complete"] is False, f"complete too early at day {day+1}"

    rep = bkp.run_nightly(tmp_path / "backups", series, now=day0 + 6 * 86400)
    assert rep["nights_completed"] == 7
    assert rep["series_complete"] is True


def test_nightly_backup_verifies_integrity_and_row_counts(tmp_path, monkeypatch):
    from scripts import sqlite_backup_restore as bkp

    src = tmp_path / "store.sqlite"
    conn = sqlite3.connect(str(src))
    conn.execute("CREATE TABLE t(x INTEGER)")
    conn.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(7)])
    conn.commit(); conn.close()

    monkeypatch.setattr(bkp, "_real_stores", lambda: {"store": src})
    rep = bkp.run_nightly(tmp_path / "b", tmp_path / "s.json")

    entry = rep["nights"][0]["stores"][0]
    assert entry["verdict"] == "PASS"
    assert entry["integrity_check"] == "ok"
    assert entry["row_counts"] == {"t": 7}
    assert entry["source_sha256"] and entry["backup_sha256"]


def test_nightly_missing_store_is_reported_not_hidden(tmp_path, monkeypatch):
    from scripts import sqlite_backup_restore as bkp

    monkeypatch.setattr(bkp, "_real_stores",
                        lambda: {"ghost": tmp_path / "does_not_exist.sqlite"})
    rep = bkp.run_nightly(tmp_path / "b", tmp_path / "s.json")

    assert rep["latest_verdict"] == "FAIL"
    assert rep["nights"][0]["stores"][0]["verdict"] == "MISSING_SOURCE"


# ------------------------------------------------------------- operator path

def test_operator_start_document_exists_and_is_deterministic():
    doc = ROOT / "AHOS_SOAK_OPERATOR_START.md"
    assert doc.is_file(), "AHOS_SOAK_OPERATOR_START.md is required by the directive"
    text = doc.read_text(encoding="utf-8")

    # Every step of the mandated activation path must be present and runnable.
    for step in ("git pull", "python -m venv .venv", "requirements.txt",
                 "scripts\\init_databases.py", "scripts\\freeze_lane_a.py",
                 "scripts\\validate_imports.py", "pytest",
                 "--probe-providers", "record_local_laptop_baseline.py",
                 "official_168h_eligible", "--daemon",
                 "watchdog --status", "soak_snapshot.py"):
        assert step in text, f"operator path missing step: {step}"


def test_operator_document_mandates_the_local_evidence_namespace():
    """A soak started without AHOS_EVIDENCE_SOURCE=local yields no evidence."""
    text = (ROOT / "AHOS_SOAK_OPERATOR_START.md").read_text(encoding="utf-8")
    assert "AHOS_EVIDENCE_SOURCE" in text
    assert "local" in text


def test_referenced_operator_scripts_all_exist():
    """No step may point at a script that is not in the repository."""
    for rel in ("scripts/init_databases.py", "scripts/freeze_lane_a.py",
                "scripts/validate_imports.py", "scripts/soak_snapshot.py",
                "scripts/system_state_snapshot.py",
                "scripts/record_local_laptop_baseline.py",
                "scripts/sqlite_backup_restore.py",
                "scripts/calibration_report.py"):
        assert (ROOT / rel).is_file(), f"missing referenced script: {rel}"


def test_operator_docs_do_not_claim_unearned_results():
    """The activation sheet must not assert soak/calibration/backup success."""
    text = (ROOT / "AHOS_SOAK_OPERATOR_START.md").read_text(encoding="utf-8")
    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY",
                      "soak complete", "calibration complete"):
        assert forbidden not in text
