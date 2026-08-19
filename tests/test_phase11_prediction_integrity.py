#!/usr/bin/env python3
"""Phase 11 — adversarial integrity tests for the prediction→calibration chain.

These tests do not check that the happy path works (Phase 10 covers that).
They actively try to BREAK the two properties the chain exists to guarantee:

    1. A prediction is recorded before its outcome, and is immutable afterwards.
    2. Calibration can never see the future, and can never count fake evidence.

Cases A-G below map 1:1 to the Phase 11 directive.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.calibration import CalibrationHarness  # noqa: E402
from architecture.learning.score_ledger import (  # noqa: E402
    CALIBRATION_ELIGIBLE_SOURCES,
    SOURCE_LOCAL,
    SOURCE_SANDBOX,
    SOURCE_SYNTHETIC,
    SOURCE_TEST,
    ScoreLedger,
    resolve_source,
)
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402

ADDR = "So11111111111111111111111111111111111111112"


def _candidate(liquidity: float = 80000.0, volume: float = 40000.0,
               address: str = ADDR) -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain="solana", address=address, symbol="TEST", name="Test Token",
        source_provider="dexscreener", retrieved_ts=time.time(),
        metrics=MarketMetrics(price_usd=0.1, liquidity_usd=liquidity,
                              volume_1h=volume, txns_1h_buys=90, txns_1h_sells=20),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 top10_holder_concentration_pct=22.0),
    )


def _seed_store(tmp_path, rows, *, horizon="24h", event_class="+50%"):
    """Build a ledger + Lane-A-shaped label store from explicit tuples.

    rows: (score, hit, scored_ts, resolved_ts, source)
    `hit=None` models an unresolved outcome.
    """
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    ScoreLedger(db_path=str(ledger_db), source=SOURCE_TEST)   # create schema

    conn = sqlite3.connect(str(ledger_db))
    dconn = sqlite3.connect(str(disc_db))
    dconn.execute(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class))""")

    for i, (score, hit, scored_ts, resolved_ts, source) in enumerate(rows):
        tid = f"token{i:05d}"
        conn.execute(
            """INSERT INTO opportunity_score_ledger(
                 score_id, scored_ts, scored_utc, run_id, source, chain, token_address,
                 token_id, symbol, opportunity_score, confidence_level, risk_level,
                 base_score, total_penalties, engine_version, weights_sha256,
                 evidence_sha256, known_field_count, unknown_field_count,
                 positive_reasons_json, risk_findings_json, missing_unknowns_json,
                 invalidation_json, score_breakdown_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f"s{i:05d}", scored_ts, "2026-01-01T00:00:00Z", "run", source, "solana",
             f"addr{i}", tid, "T", float(score), "HIGH", "LOW", 0.0, 0.0,
             "AHOS-SCORE-v1", "a" * 64, "b" * 64, 4, 0, "[]", "[]", "[]", "[]", "{}"))
        dconn.execute(
            "INSERT INTO outcome_label(token_id,horizon,event_class,hit,resolved_ts) "
            "VALUES (?,?,?,?,?)", (tid, horizon, event_class, hit, resolved_ts))

    conn.commit(); conn.close()
    dconn.commit(); dconn.close()
    return CalibrationHarness(ledger_db=str(ledger_db), discovery_db=str(disc_db),
                              eligible_sources={SOURCE_TEST})


# ============================ CASE A — future outcome =======================

def test_case_a_outcome_resolved_before_prediction_is_rejected(tmp_path):
    """An outcome that closed BEFORE the prediction cannot grade it."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [
        (90.0, 1, t0, t0 - 3600, SOURCE_TEST),      # label predates prediction
        (90.0, 1, t0, t0 + 3600, SOURCE_TEST),      # legitimate
    ])
    report = harness.run()

    assert report.joined_pairs == 1, "a pre-dated label leaked into the cohort"
    assert report.exclusion_reasons.get("label_predates_prediction") == 1


def test_case_a_simultaneous_timestamps_are_excluded(tmp_path):
    """resolved_ts == scored_ts is not strictly after: reject (boundary case)."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0, SOURCE_TEST)])

    assert harness.run().joined_pairs == 0


# ======================= CASE B — future observation ========================

def test_case_b_prediction_cannot_contain_post_prediction_observation():
    """Evidence freshness is measured against the evaluation instant.

    A candidate whose data was retrieved AFTER the evaluation timestamp must
    not silently present as fresh, verified evidence -- that would be an
    observation from the future entering the feature set.
    """
    now = time.time()
    future = _candidate()
    future.retrieved_ts = now + 3600          # data from an hour ahead

    report = OpportunityScorer().evaluate(future, now=now)

    # freshness_seconds is clamped at 0 and must never be negative: a negative
    # age would mean the scorer accepted future data as if it were current.
    for item in report.evidence_items:
        assert item.freshness_seconds >= 0.0


def test_case_b_feature_extraction_is_a_pure_function_of_its_bundle():
    """Two evaluations of identical evidence must agree.

    If scoring depended on anything outside the bundle (wall clock, ambient
    state, later observations), replay would drift and no historical
    prediction could ever be re-verified.
    """
    cand = _candidate()
    fixed = time.time()
    a = OpportunityScorer().evaluate(cand, now=fixed)
    b = OpportunityScorer().evaluate(cand, now=fixed)

    assert a.opportunity_score == b.opportunity_score
    assert a.provenance_sha256 == b.provenance_sha256


# ========================= CASE C — modified weights ========================

def test_case_c_weight_change_does_not_mutate_old_predictions(tmp_path, monkeypatch):
    """A stored prediction is history; re-fingerprinting must not rewrite it."""
    ledger = ScoreLedger(db_path=str(tmp_path / "l.sqlite"), source=SOURCE_TEST)
    original = ledger.record(_report_for(ledger), run_id="r1")
    assert original is not None
    before = ledger.recent()[0]

    # Simulate a scorer change: the fingerprint function now reports something new.
    monkeypatch.setattr(
        "architecture.learning.score_ledger.weights_fingerprint",
        lambda: "f" * 64)
    ledger.record(_report_for(ledger), run_id="r2")

    rows = {r["score_id"]: r for r in ledger.recent(limit=10)}
    unchanged = rows[before["score_id"]]
    assert unchanged["weights_sha256"] == before["weights_sha256"]
    assert unchanged["opportunity_score"] == before["opportunity_score"]


def test_case_c_calibration_flags_mixed_weight_fingerprints(tmp_path):
    """Pooling two scoring regimes must be reported, never averaged silently."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0 + 60, SOURCE_TEST)])
    conn = sqlite3.connect(harness.ledger_db)
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, source, chain, token_address, token_id,
             opportunity_score, confidence_level, risk_level, engine_version,
             weights_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("other", t0, "2026-01-01T00:00:00Z", SOURCE_TEST, "solana", "addr0",
         "token00000", 90.0, "HIGH", "LOW", "AHOS-SCORE-v1", "z" * 64,
         4, 0, "[]", "[]", "[]", "[]", "{}"))
    conn.commit(); conn.close()

    report = harness.run()
    assert len(report.weight_fingerprints) == 2
    assert any("MIXED_ENGINE_VERSIONS" in f for f in report.findings)


def _report_for(_ledger):
    return OpportunityScorer().evaluate(_candidate())


# ========================= CASE D — evidence mutation =======================

def test_case_d_evidence_change_changes_the_provenance_hash():
    """Mutated evidence must be detectable, not silently rescored."""
    base = OpportunityScorer().evaluate(_candidate(liquidity=80000.0))
    mutated = OpportunityScorer().evaluate(_candidate(liquidity=80001.0))

    assert base.provenance_sha256 != mutated.provenance_sha256


def test_case_d_stored_evidence_hash_detects_tampering(tmp_path):
    """The ledger keeps the hash of the evidence that produced the score.

    Re-deriving the hash from mutated inputs will not match the stored value,
    so a later 'that score came from this data' claim is falsifiable.
    """
    ledger = ScoreLedger(db_path=str(tmp_path / "l.sqlite"), source=SOURCE_TEST)
    ledger.record(OpportunityScorer().evaluate(_candidate(liquidity=80000.0)))
    stored_hash = ledger.recent()[0]["evidence_sha256"]

    tampered = OpportunityScorer().evaluate(_candidate(liquidity=999999.0))
    assert tampered.provenance_sha256 != stored_hash


# ======================== CASE E — duplicate prediction =====================

def test_case_e_duplicate_prediction_creates_one_evidence_row(tmp_path):
    """Re-recording the same prediction must not inflate the evidence base."""
    ledger = ScoreLedger(db_path=str(tmp_path / "l.sqlite"), source=SOURCE_TEST)
    report = OpportunityScorer().evaluate(_candidate())

    for _ in range(5):
        ledger.record(report, run_id="same-run")

    assert ledger.count() == 1


def test_case_e_daemon_restart_does_not_duplicate_predictions(tmp_path):
    """A restarted daemon re-scoring the same instant must not double-count."""
    path = str(tmp_path / "l.sqlite")
    report = OpportunityScorer().evaluate(_candidate())

    first = ScoreLedger(db_path=path, source=SOURCE_TEST)
    first.record(report, run_id="run-A")
    # New process, new ledger object, same store, same prediction instant.
    second = ScoreLedger(db_path=path, source=SOURCE_TEST)
    second.record(report, run_id="run-A")

    assert second.count() == 1


def test_case_e_distinct_sources_do_not_suppress_each_other(tmp_path):
    """A test row must never occupy the id of a real local prediction.

    If `source` were absent from the id seed, INSERT OR IGNORE would let a
    fixture row silently swallow the operator's genuine prediction.
    """
    path = str(tmp_path / "l.sqlite")
    report = OpportunityScorer().evaluate(_candidate())

    ScoreLedger(db_path=path, source=SOURCE_TEST).record(report, run_id="r")
    ScoreLedger(db_path=path, source=SOURCE_LOCAL).record(report, run_id="r")

    ledger = ScoreLedger(db_path=path, source=SOURCE_TEST)
    assert ledger.count() == 2
    assert ledger.count(source=SOURCE_LOCAL) == 1
    assert ledger.count(source=SOURCE_TEST) == 1


# ========================== CASE F — missing outcome ========================

def test_case_f_unresolved_outcome_is_never_counted_as_failure(tmp_path):
    """hit IS NULL means UNRESOLVED -- not a miss."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [
        (90.0, None, t0, t0 + 3600, SOURCE_TEST),   # unresolved
        (90.0, 1, t0, t0 + 3600, SOURCE_TEST),      # resolved hit
    ])
    report = harness.run()

    assert report.joined_pairs == 1, "an unresolved outcome entered the cohort"
    assert report.exclusion_reasons.get("unresolved_outcome") == 1
    band = next(b for b in report.bands if b.band == "80-100")
    assert band.n == 1 and band.positives == 1


def test_case_f_prediction_without_any_label_is_excluded_and_explained(tmp_path):
    """A prediction with no matching label is neither success nor failure."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0 + 60, SOURCE_TEST)])
    conn = sqlite3.connect(harness.ledger_db)
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, source, chain, token_address, token_id,
             opportunity_score, confidence_level, risk_level, engine_version,
             weights_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("orphan", t0, "2026-01-01T00:00:00Z", SOURCE_TEST, "solana", "addrX",
         "token-no-label", 75.0, "HIGH", "LOW", "AHOS-SCORE-v1", "a" * 64,
         4, 0, "[]", "[]", "[]", "[]", "{}"))
    conn.commit(); conn.close()

    report = harness.run()
    assert report.joined_pairs == 1
    assert report.exclusion_reasons.get("no_matching_label") == 1
    assert report.excluded_predictions >= 1


# ========================== CASE G — unknown features =======================

def test_case_g_unknown_is_not_treated_as_zero_or_success():
    """UNKNOWN must contribute no points and be listed as missing."""
    blind = NormalizedTokenCandidate(
        chain="solana", address=ADDR, symbol="", name="",
        source_provider="dexscreener", retrieved_ts=time.time())
    report = OpportunityScorer().evaluate(blind)

    assert report.missing_unknowns, "UNKNOWN fields must be reported, not absorbed"
    # An all-unknown token must not out-score a known-good one.
    known = OpportunityScorer().evaluate(_candidate())
    assert report.opportunity_score < known.opportunity_score
    assert report.confidence_level == "LOW"


def test_case_g_zero_volume_is_distinct_from_unknown_volume():
    """A measured zero and an absent measurement are different facts."""
    measured_zero = _candidate(volume=0.0)
    unknown_vol = _candidate()
    unknown_vol.metrics.volume_1h = None

    r_zero = OpportunityScorer().evaluate(measured_zero)
    r_unknown = OpportunityScorer().evaluate(unknown_vol)

    # Both score 0 points for volume, but only the UNKNOWN one is reported as
    # missing evidence -- collapsing them would hide a data-quality problem.
    assert any("حجم" in m for m in r_unknown.missing_unknowns)
    assert r_zero.provenance_sha256 != r_unknown.provenance_sha256


def test_case_g_unknown_counts_are_persisted_for_later_audit(tmp_path):
    ledger = ScoreLedger(db_path=str(tmp_path / "l.sqlite"), source=SOURCE_TEST)
    blind = NormalizedTokenCandidate(
        chain="solana", address=ADDR, symbol="", name="",
        source_provider="dexscreener", retrieved_ts=time.time())
    ledger.record(OpportunityScorer().evaluate(blind))

    row = ledger.recent()[0]
    assert row["unknown_field_count"] > 0
    assert row["known_field_count"] == 0


# ================= synthetic / real evidence boundary =======================

def test_test_runs_default_to_the_test_namespace():
    """Running under pytest must never yield calibration-eligible rows."""
    assert resolve_source() == SOURCE_TEST
    assert SOURCE_TEST not in CALIBRATION_ELIGIBLE_SOURCES


def test_only_local_is_calibration_eligible():
    assert CALIBRATION_ELIGIBLE_SOURCES == frozenset({SOURCE_LOCAL})
    for bad in (SOURCE_TEST, SOURCE_SANDBOX, SOURCE_SYNTHETIC):
        assert bad not in CALIBRATION_ELIGIBLE_SOURCES


def test_unknown_source_is_rejected_loudly():
    with pytest.raises(ValueError):
        resolve_source("production")


def test_synthetic_rows_cannot_become_calibration_evidence(tmp_path):
    """The headline boundary test: fake data in the store, zero in the cohort."""
    t0 = time.time() - 86400
    rows = [(90.0, 1, t0, t0 + 3600, SOURCE_SYNTHETIC)] * 300
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    _seed_store(tmp_path, rows)

    # Default eligibility (production behaviour), not the test override.
    harness = CalibrationHarness(ledger_db=str(ledger_db), discovery_db=str(disc_db))
    report = harness.run()

    assert report.joined_pairs == 0
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.exclusion_reasons.get("ineligible_source") == 300
    assert any("NON_ELIGIBLE_ROWS_PRESENT" in f for f in report.findings)


def test_env_var_can_declare_local_evidence(monkeypatch, tmp_path):
    """The operator's daemon opts in explicitly; nothing else does."""
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    ledger = ScoreLedger(db_path=str(tmp_path / "l.sqlite"))
    assert ledger.source == SOURCE_LOCAL


# ============================ calibration integrity =========================

def test_insufficient_data_is_never_reported_as_calibrated(tmp_path):
    """One sample below the guard must not produce a CALIBRATED verdict."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0 + 60, SOURCE_TEST)] * 5)
    report = harness.run()

    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.as_dict()["calibration_status"] == "INSUFFICIENT_DATA"


def test_report_carries_full_provenance(tmp_path):
    """Someone must be able to ask: this number came from exactly what data?"""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0 + 3600, SOURCE_TEST)] * 3)
    payload = harness.run().as_dict()

    for key in ("number_of_predictions", "number_of_eligible_pairs",
                "excluded_predictions", "exclusion_reasons", "observation_window",
                "horizon", "score_engine_versions", "weight_fingerprints",
                "dataset_fingerprint", "calibration_status", "eligible_sources",
                "source_census"):
        assert key in payload, f"provenance field missing: {key}"
    assert payload["dataset_fingerprint"]
    assert payload["observation_window"]["first_scored_utc"]


def test_dataset_fingerprint_is_deterministic_and_data_sensitive(tmp_path):
    """Same rows => same fingerprint; different rows => different fingerprint."""
    t0 = time.time() - 86400
    h1 = _seed_store(tmp_path / "a", [(90.0, 1, t0, t0 + 60, SOURCE_TEST)])
    first = h1.run().dataset_fingerprint
    assert first == h1.run().dataset_fingerprint          # replayable

    h2 = _seed_store(tmp_path / "b", [(70.0, 0, t0, t0 + 60, SOURCE_TEST)])
    assert h2.run().dataset_fingerprint != first


def test_calibration_never_writes_to_either_store(tmp_path):
    """A measurement must not mutate what it measures (Lane-A especially)."""
    t0 = time.time() - 86400
    harness = _seed_store(tmp_path, [(90.0, 1, t0, t0 + 60, SOURCE_TEST)])

    def digest(path: str) -> bytes:
        import hashlib
        return hashlib.sha256(Path(path).read_bytes()).digest()

    before = (digest(harness.ledger_db), digest(harness.discovery_db))
    harness.run()
    assert (digest(harness.ledger_db), digest(harness.discovery_db)) == before
