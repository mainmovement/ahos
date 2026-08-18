#!/usr/bin/env python3
"""Phase 12 — local activation readiness regressions.

Pins the activation evidence package and the operator checklist so the
"is this laptop ready for real data?" answer stays measured rather than
asserted, and so no future change can quietly make it optimistic.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import local_activation_report as lar  # noqa: E402


# ----------------------------------------------------------- report structure

def test_report_contains_every_mandated_field():
    """Task 4 of the directive names the required contents explicitly."""
    report = lar.build_report(do_probe=False)

    for key in ("git", "environment", "databases", "providers",
                "runtime", "evidence_source"):
        assert key in report, f"mandated field missing: {key}"

    assert report["git"]["commit_sha"]
    assert report["environment"]["python_version"]
    assert report["environment"]["fingerprint_sha256"]


def test_report_never_claims_production_or_soak():
    report = lar.build_report(do_probe=False)
    blob = json.dumps(report, ensure_ascii=False)

    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY",
                      "soak complete", "calibration complete"):
        assert forbidden not in blob
    # It must actively disclaim the things it cannot know.
    assert report["not_claimed"]


def test_skipping_the_probe_reports_unknown_not_success():
    """Absence of a measurement must never read as a passing measurement."""
    providers = lar.build_report(do_probe=False)["providers"]

    assert providers["probed"] is False
    assert not providers.get("any_success")
    assert "UNKNOWN" in providers["note"]


# ------------------------------------------------------------- classification

def _fake_probe(success: bool) -> dict:
    return {"probed": True, "any_success": success,
            "m_gap_007_live_success_proven": success,
            "status_counts": {"SUCCESS": 2} if success else {"TLS_ERROR": 2}}


def test_classification_requires_both_providers_and_local_evidence(monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    with patch.object(lar, "_provider_status", return_value=_fake_probe(True)):
        report = lar.build_report()

    assert report["classification"] == "READY_FOR_REAL_LOCAL_DATA"
    assert report["real_data_blockers"] == []


def test_dead_providers_block_real_data_classification(monkeypatch):
    """A host that reaches nothing cannot accumulate real predictions."""
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    with patch.object(lar, "_provider_status", return_value=_fake_probe(False)):
        report = lar.build_report()

    assert report["classification"] == "INSTALLED_AWAITING_REAL_DATA_PRECONDITIONS"
    assert any("M-GAP-007" in b for b in report["real_data_blockers"])


def test_sandbox_evidence_source_blocks_real_data_classification(monkeypatch):
    """Predictions stamped `sandbox` are not calibration evidence."""
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "sandbox")
    with patch.object(lar, "_provider_status", return_value=_fake_probe(True)):
        report = lar.build_report()

    assert report["classification"] != "READY_FOR_REAL_LOCAL_DATA"
    assert any("AHOS_EVIDENCE_SOURCE=local" in b for b in report["real_data_blockers"])


def test_missing_ledger_guards_is_an_installation_blocker(monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    broken = {"table_present": True, "guards_ok": False, "total_rows": 0,
              "source_census": {}, "resolved_source_for_this_process": "local"}
    with patch.object(lar, "_prediction_ledger_status", return_value=broken), \
         patch.object(lar, "_provider_status", return_value=_fake_probe(True)):
        report = lar.build_report()

    assert report["installation_ready"] is False
    assert report["classification"] == "NOT_READY"
    assert any("append-only guards" in b for b in report["installation_blockers"])


def test_lane_a_drift_is_an_installation_blocker(monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    with patch.object(lar, "_lane_a_status",
                      return_value={"ok": False, "drift": ["discovery/pal.py"],
                                    "missing": [], "untracked": []}), \
         patch.object(lar, "_provider_status", return_value=_fake_probe(True)):
        report = lar.build_report()

    assert report["classification"] == "NOT_READY"
    assert any("Lane-A" in b for b in report["installation_blockers"])


# ------------------------------------------------------- live-state reporting

def test_report_reflects_the_real_stores_on_this_host():
    report = lar.build_report(do_probe=False)
    names = {s["store"] for s in report["databases"]}

    assert names == {"e01_discovery", "paper_trading", "ahos_local", "ahos_knowledge"}
    for store in report["databases"]:
        assert store["ok"], f"{store['store']} unhealthy: {store['integrity_check']}"


def test_report_exposes_the_prediction_ledger_census():
    ledger = lar.build_report(do_probe=False)["prediction_ledger"]

    assert ledger["guards_ok"] is True
    assert ledger["calibration_eligible_sources"] == ["local"]
    assert "source_census" in ledger


def test_report_is_read_only_with_respect_to_stores():
    """Generating evidence must not mutate the state it describes."""
    import hashlib
    from config.paths import get_discovery_db_path, get_local_db_path

    def digest(p: str) -> bytes:
        return hashlib.sha256(Path(p).read_bytes()).digest()

    before = (digest(get_local_db_path()), digest(get_discovery_db_path()))
    lar.build_report(do_probe=False)
    assert (digest(get_local_db_path()), digest(get_discovery_db_path())) == before


def test_report_writes_artifact_and_signals_readiness_by_exit_code(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "sandbox")
    out = tmp_path / "activation.json"
    rc = lar.main(["--no-probe", "--out", str(out)])

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.local_activation.v1"
    # sandbox namespace => not ready for real data => non-zero
    assert rc == 3


# --------------------------------------------------------- operator checklist

def test_activation_checklist_exists_and_covers_every_mandated_item():
    doc = ROOT / "AHOS_LOCAL_ACTIVATION_CHECKLIST.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")

    for item in ("Python environment", "Dependency validation",
                 "Database initialization", "Sleep prevention",
                 "AC power", "Disk space", "Backup directory",
                 "AHOS_EVIDENCE_SOURCE"):
        assert item in text, f"checklist missing mandated section: {item}"


def test_checklist_commands_reference_scripts_that_exist():
    text = (ROOT / "AHOS_LOCAL_ACTIVATION_CHECKLIST.md").read_text(encoding="utf-8")

    for rel in ("scripts/validate_imports.py", "scripts/freeze_lane_a.py",
                "scripts/init_databases.py", "scripts/sqlite_backup_restore.py",
                "scripts/record_local_laptop_baseline.py",
                "scripts/local_activation_report.py"):
        assert (ROOT / rel).is_file(), f"missing script: {rel}"
        assert rel.replace("/", "\\") in text or rel in text, \
            f"checklist never references {rel}"


def test_checklist_forbids_forcing_a_green_provider_result():
    """A bypassed TLS error is a fabricated success."""
    text = (ROOT / "AHOS_LOCAL_ACTIVATION_CHECKLIST.md").read_text(encoding="utf-8")
    # Collapse newlines so the assertion survives markdown line wrapping.
    flat = " ".join(text.split())
    assert "Do **not** disable TLS verification" in flat
    assert "fabricated success" in flat


def test_no_tls_verification_bypass_exists_in_the_codebase():
    """Task 3: TLS errors are evidence and must never be worked around."""
    import re

    pattern = re.compile(
        r"verify\s*=\s*False|CERT_NONE|_create_unverified_context|"
        r"check_hostname\s*=\s*False")
    offenders = []
    for pkg in ("architecture", "discovery", "telegram_ai", "paper_trading"):
        for path in (ROOT / pkg).rglob("*.py"):
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(str(path.relative_to(ROOT)))

    assert not offenders, f"TLS verification bypass found in: {offenders}"


# --------------------------------------------------------- progress snapshot

def test_phase_progress_snapshot_exists_and_is_honest():
    doc = ROOT / "AHOS_PHASE_PROGRESS_SNAPSHOT.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")

    assert "Phase 11" in text
    assert "USER-ACTION-REQUIRED" in text
    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY"):
        assert forbidden not in text


# ------------------------------------------- end-to-end chain (Task 1 + 5)

def test_real_prediction_joins_a_real_outcome_label(tmp_path):
    """The closing link: a genuine prediction graded by a genuine Lane-A label."""
    from architecture.learning.calibration import CalibrationHarness
    from architecture.learning.score_ledger import SOURCE_LOCAL, ScoreLedger
    from architecture.providers.contracts import (
        MarketMetrics, NormalizedTokenCandidate, SecuritySignals)
    from architecture.scoring.engine import OpportunityScorer
    from discovery import observations as obs
    from discovery.identity import token_id
    from discovery.materialize import materialize_outcomes

    disc = tmp_path / "d.sqlite"
    led_db = tmp_path / "l.sqlite"
    t0 = time.time() - 8 * 86400
    addr = "ChainProofAddr"
    tid = token_id("solana", addr)

    conn = obs.open_store(str(disc))
    conn.execute("INSERT INTO raw_payloads(payload_sha256,provider,endpoint,"
                 "retrieved_ts,payload_json) VALUES('s1','dexscreener','p',?,'{}')", (t0,))
    conn.execute("INSERT INTO tokens(token_id,chain_id,address,first_seen_ts,"
                 "source_first_seen_provider) VALUES(?,?,?,?,'dexscreener')",
                 (tid, "solana", addr, t0))
    conn.execute("INSERT INTO observation_state(token_id,state,entered_ts,"
                 "first_seen_ts,last_obs_ts) VALUES(?,'OBSERVING',?,?,?)", (tid, t0, t0, t0))
    for i, (off, price) in enumerate(((60.0, 1.0), (3600.0, 1.6), (7200.0, 2.2))):
        conn.execute("INSERT INTO discovery_observations(obs_id,token_id,provider,"
                     "retrieved_ts,price_usd,raw_ref) VALUES(?,?,?,?,?,'s1')",
                     (f"o{i}", tid, "dexscreener", t0 + off, price))
    conn.commit()
    assert materialize_outcomes(conn, now=time.time())["outcome_rows_written"] > 0
    conn.close()

    candidate = NormalizedTokenCandidate(
        chain="solana", address=addr, symbol="T", name="T",
        source_provider="dexscreener", retrieved_ts=t0,
        metrics=MarketMetrics(price_usd=1.0, liquidity_usd=90000.0, volume_1h=50000.0,
                              txns_1h_buys=120, txns_1h_sells=30),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 top10_holder_concentration_pct=18.0))
    ledger = ScoreLedger(db_path=str(led_db), source=SOURCE_LOCAL)
    ledger.record(OpportunityScorer().evaluate(candidate, now=t0), run_id="e2e", now=t0)

    report = CalibrationHarness(ledger_db=str(led_db), discovery_db=str(disc)).run()
    assert report.joined_pairs == 1
    # One pair is nowhere near the guard: the verdict must stay honest.
    assert report.verdict == "INSUFFICIENT_DATA"


def test_synthetic_rows_cannot_dilute_a_real_cohort(tmp_path):
    """Task 5: fake data in the same store contributes exactly zero pairs."""
    from architecture.learning.calibration import CalibrationHarness
    from architecture.learning.score_ledger import (
        SOURCE_LOCAL, SOURCE_SYNTHETIC, ScoreLedger)

    led_db = tmp_path / "l.sqlite"
    disc = tmp_path / "d.sqlite"
    sqlite3.connect(str(disc)).executescript(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class));""")

    ScoreLedger(db_path=str(led_db), source=SOURCE_LOCAL)
    conn = sqlite3.connect(str(led_db))
    dconn = sqlite3.connect(str(disc))
    t0 = time.time() - 86400
    for i in range(300):
        tid = f"tok{i}"
        conn.execute(
            "INSERT INTO opportunity_score_ledger(score_id,scored_ts,scored_utc,source,"
            "chain,token_address,token_id,opportunity_score,confidence_level,risk_level,"
            "engine_version,weights_sha256,known_field_count,unknown_field_count,"
            "positive_reasons_json,risk_findings_json,missing_unknowns_json,"
            "invalidation_json,score_breakdown_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"s{i}", t0, "u", SOURCE_SYNTHETIC, "solana", f"a{i}", tid, 90.0,
             "HIGH", "LOW", "AHOS-SCORE-v1", "a" * 64, 4, 0, "[]", "[]", "[]", "[]", "{}"))
        dconn.execute("INSERT INTO outcome_label(token_id,horizon,event_class,hit,"
                      "resolved_ts) VALUES (?,?,?,?,?)", (tid, "24h", "+50%", 1, t0 + 60))
    conn.commit(); conn.close()
    dconn.commit(); dconn.close()

    report = CalibrationHarness(ledger_db=str(led_db), discovery_db=str(disc)).run()
    assert report.joined_pairs == 0
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.exclusion_reasons["ineligible_source"] == 300
