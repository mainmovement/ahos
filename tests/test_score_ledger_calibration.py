#!/usr/bin/env python3
"""Learning-loop persistence + calibration tests.

Proves the previously-missing `Prediction` node of the loop:

    Observation → Prediction → Outcome → Label → Lesson

Covers: append-only enforcement, version fingerprinting, the no-peeking join,
pre-registered statistical guards, honest INSUFFICIENT_DATA, pipeline wiring,
and the law that recording a score never alters the score.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.calibration import (  # noqa: E402
    MIN_N_PER_BAND,
    MIN_POSITIVES,
    SCORE_BANDS,
    CalibrationHarness,
)
from architecture.learning.score_ledger import (  # noqa: E402
    SCORING_ENGINE_VERSION,
    SOURCE_TEST,
    ScoreLedger,
    weights_fingerprint,
)
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402


# --------------------------------------------------------------------- helpers

def _candidate(address: str = "So11111111111111111111111111111111111111112",
               liquidity: float = 80000.0, volume: float = 40000.0,
               chain: str = "solana") -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain=chain, address=address, symbol="TEST", name="Test Token",
        source_provider="dexscreener", retrieved_ts=time.time(),
        metrics=MarketMetrics(price_usd=0.1, liquidity_usd=liquidity,
                              volume_1h=volume, txns_1h_buys=90, txns_1h_sells=20),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 top10_holder_concentration_pct=22.0),
    )


def _report(candidate=None):
    return OpportunityScorer().evaluate(candidate or _candidate())


def _ledger(tmp_path) -> ScoreLedger:
    return ScoreLedger(db_path=str(tmp_path / "ledger.sqlite"))


# ------------------------------------------------------- persistence contract

def test_prediction_persists_source_provider(tmp_path):
    """Q8 'performance by provider' requires the provider to survive at
    prediction time — the report must carry it into the ledger row."""
    cand = _candidate()
    cand.source_provider = "geckoterminal"
    report = _report(cand)
    assert report.source_provider == "geckoterminal"

    ledger = _ledger(tmp_path)
    ledger.record(report, source="test")
    rows = ledger.recent(1)
    assert rows[0]["source_provider"] == "geckoterminal"


def test_report_without_provider_defaults_to_unknown(tmp_path):
    """A report stamped by an old code path must not fabricate a provider."""
    cand = _candidate()
    cand.source_provider = ""
    report = _report(cand)
    assert report.source_provider == ""

    ledger = _ledger(tmp_path)
    ledger.record(report, source="test")
    assert ledger.recent(1)[0]["source_provider"] == ""


def test_legacy_ledger_db_is_migrated_additively(tmp_path):
    """A store created before source_provider existed must gain the column on
    open, keep every existing row, and keep the append-only guards. The legacy
    fixture is the real pre-migration schema (current schema minus the
    source_provider column), so indexes/triggers are present as in production."""
    from architecture.learning import score_ledger as sl

    legacy_schema = sl.SCHEMA_SCORE_LEDGER.replace(
        "  score_breakdown_json TEXT NOT NULL,\n"
        "  source_provider    TEXT              -- discovery provider (calibration Q8 segment)",
        "  score_breakdown_json TEXT NOT NULL")
    assert "source_provider" not in legacy_schema

    db = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript(legacy_schema)
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, source, chain, token_address,
             token_id, symbol, opportunity_score, confidence_level, risk_level,
             base_score, total_penalties, engine_version, weights_sha256,
             evidence_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES ('old1', 1.0, '2026-01-01T00:00:00Z', 'sandbox', 'solana',
                   'addr1', 'tok1', 'T', 50.0, 'MED', 'LOW', 0.0, 0.0,
                   'v1', 'a'*64, 'b'*64, 3, 1,
                   '[]', '[]', '[]', '[]', '{}')""")
    conn.commit(); conn.close()

    ledger = ScoreLedger(db_path=str(db))
    assert ledger.write_failures == 0
    assert ledger.count() == 1, "migration must preserve existing rows"
    row = ledger.recent(1)[0]
    assert row["score_id"] == "old1"
    # NULL, not '' — the legacy row has no provider recorded; the calibration
    # harness buckets it UNKNOWN rather than fabricating one.
    assert row["source_provider"] is None

    # the append-only guard survives the migration
    with pytest.raises(sqlite3.IntegrityError):
        conn = sqlite3.connect(str(db))
        conn.execute("UPDATE opportunity_score_ledger SET chain='x'")
        conn.commit()


def test_prediction_is_persisted_with_full_provenance(tmp_path):
    """The gap this closes: a score must survive the call that produced it."""
    ledger = _ledger(tmp_path)
    report = _report()

    rec = ledger.record(report, run_id="run-1")

    assert rec is not None
    assert ledger.count() == 1
    stored = ledger.recent()[0]
    assert stored["opportunity_score"] == pytest.approx(report.opportunity_score)
    assert stored["confidence_level"] == report.confidence_level
    assert stored["risk_level"] == report.risk_level
    # Provenance is what makes the row judgeable later.
    assert stored["engine_version"] == SCORING_ENGINE_VERSION
    assert stored["weights_sha256"] and not stored["weights_sha256"].startswith("UNKNOWN")
    assert stored["evidence_sha256"] == report.provenance_sha256
    assert stored["token_id"], "canonical Lane-A token_id is the join key to outcomes"


def test_recording_never_mutates_the_report(tmp_path):
    """Law: a sink must not alter what it records."""
    ledger = _ledger(tmp_path)
    report = _report()
    before = (report.opportunity_score, report.confidence_level,
              report.risk_level, report.provenance_sha256,
              list(report.positive_reasons))

    ledger.record(report)

    assert (report.opportunity_score, report.confidence_level,
            report.risk_level, report.provenance_sha256,
            list(report.positive_reasons)) == before


def test_ledger_is_append_only(tmp_path):
    """A prediction is history: UPDATE and DELETE must be refused by the DB."""
    ledger = _ledger(tmp_path)
    ledger.record(_report())

    conn = sqlite3.connect(ledger.db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE opportunity_score_ledger SET opportunity_score = 99.0")
    conn.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM opportunity_score_ledger")
    conn.rollback()
    conn.close()


def test_guards_do_not_impersonate_the_f1s1_migration(tmp_path):
    """Guard provenance is evidence too.

    Naming these triggers `f1s1_guard_*` would silently enrol this table in the
    F1-S1 migration's live census, making that migration's committed evidence
    report describe a table it never touched.
    """
    ledger = _ledger(tmp_path)
    conn = sqlite3.connect(f"file:{ledger.db_path}?mode=ro", uri=True)
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'")]
    conn.close()

    assert names, "append-only guards must exist"
    assert all(n.startswith("ahos_guard_") for n in names)
    assert not any(n.startswith("f1s1_guard_") for n in names)


def test_rescoring_appends_a_new_row_rather_than_overwriting(tmp_path):
    """History of predictions over time is exactly what calibration needs."""
    ledger = _ledger(tmp_path)
    t0 = time.time()
    ledger.record(_report(), run_id="r1", now=t0)
    ledger.record(_report(), run_id="r2", now=t0 + 3600)

    assert ledger.count() == 2


def test_duplicate_identical_prediction_is_ignored_not_duplicated(tmp_path):
    """Same token, same instant, same run => one historical fact."""
    ledger = _ledger(tmp_path)
    report = _report()
    ledger.record(report, run_id="r1")
    ledger.record(report, run_id="r1")

    assert ledger.count() == 1


def test_write_failure_is_counted_and_never_raises(tmp_path):
    """A disk problem must not end a collection cycle, but must stay visible."""
    ledger = _ledger(tmp_path)
    ledger.db_path = str(tmp_path / "nonexistent-dir" / "x.sqlite")

    assert ledger.record(_report()) is None       # no exception escapes
    assert ledger.write_failures >= 1             # and it is not silent


def test_weights_fingerprint_tracks_scoring_logic():
    """Deterministic per build, and never a fake-stable value."""
    fp = weights_fingerprint()
    assert fp == weights_fingerprint()
    assert len(fp) == 64 and not fp.startswith("UNKNOWN")


def test_unknown_heavy_prediction_records_its_own_ignorance(tmp_path):
    """A confident-looking score on near-total ignorance must be detectable."""
    ledger = _ledger(tmp_path)
    blind = NormalizedTokenCandidate(
        chain="solana", address="So11111111111111111111111111111111111111112",
        symbol="", name="", source_provider="dexscreener", retrieved_ts=time.time(),
    )
    ledger.record(OpportunityScorer().evaluate(blind))

    stored = ledger.recent()[0]
    assert stored["unknown_field_count"] > 0
    assert stored["known_field_count"] == 0


# -------------------------------------------------------------- pipeline wiring

def test_orchestrator_never_writes_predictions_unless_a_ledger_is_injected(tmp_path):
    """Anti-contamination law.

    If the orchestrator defaulted to a live ScoreLedger(), every test and
    ad-hoc run would append fixture rows to the operator's real prediction
    store, and those rows would later be graded as calibration evidence. A
    measurement corrupted by its own test suite is worse than no measurement,
    so persistence must be explicitly requested.
    """
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator

    orch = OpportunityPipelineOrchestrator()
    assert orch.score_ledger is None


def test_pipeline_persists_every_score_it_generates(tmp_path):
    """End-to-end: the orchestrator must write predictions, not drop them."""
    from architecture.collector.engine import CollectorEngine
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from architecture.providers.contracts import ProviderResponse
    from architecture.providers.registry import ProviderRouter

    class _Provider:
        provider_id = "dexscreener"
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse(self.provider_id, "OK", tokens=[_candidate()])

        def fetch_token_metrics(self, chain, address):
            return ProviderResponse(self.provider_id, "OK", tokens=[])

    router = ProviderRouter()
    router.providers = {"dexscreener": _Provider()}
    collector = CollectorEngine(db_path=str(tmp_path / "disc.sqlite"), router=router)
    ledger = _ledger(tmp_path)

    orch = OpportunityPipelineOrchestrator(collector=collector, score_ledger=ledger)
    rep = orch.run_pipeline(chain="solana", limit=5)

    assert rep.scores_generated > 0
    assert rep.scores_persisted == rep.scores_generated
    assert ledger.count() == rep.scores_generated


# -------------------------------------------------------- calibration harness

def _seed(tmp_path, pairs, *, resolved_offset: float = 3600.0):
    """Seed a ledger + a Lane-A-shaped outcome_label store.

    pairs: list of (score, hit). Each gets a distinct token_id.
    """
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    ledger = ScoreLedger(db_path=str(ledger_db))

    t0 = time.time() - 86400
    conn = sqlite3.connect(str(ledger_db))
    dconn = sqlite3.connect(str(disc_db))
    dconn.execute(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class))""")

    for i, (score, hit) in enumerate(pairs):
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
            (f"s{i:05d}", t0, "2026-01-01T00:00:00Z", "run", SOURCE_TEST, "solana",
             f"addr{i}",
             tid, "T", float(score), "HIGH", "LOW", 0.0, 0.0,
             SCORING_ENGINE_VERSION, "a" * 64, "b" * 64, 4, 0,
             "[]", "[]", "[]", "[]", "{}"))
        dconn.execute(
            "INSERT INTO outcome_label(token_id,horizon,event_class,hit,resolved_ts) "
            "VALUES (?,?,?,?,?)", (tid, "24h", "+50%", int(hit), t0 + resolved_offset))

    conn.commit(); conn.close()
    dconn.commit(); dconn.close()
    # Fixtures are stamped `test`, which is NOT calibration-eligible in
    # production. The override is what lets these tests exercise the band maths
    # at all -- and its necessity is itself the proof that real calibration
    # cannot silently consume test data.
    return CalibrationHarness(ledger_db=str(ledger_db), discovery_db=str(disc_db),
                              eligible_sources={SOURCE_TEST})


def test_calibration_is_insufficient_data_on_a_young_cohort(tmp_path):
    """The expected honest answer during Month 1-2 -- not a failure."""
    harness = _seed(tmp_path, [(85.0, 1), (85.0, 0), (10.0, 0)])
    report = harness.run()

    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.joined_pairs == 3
    assert all(b.verdict == "INSUFFICIENT_DATA" for b in report.bands)
    assert any("guards" in f or "pre-registered" in f for f in report.findings)


def test_calibration_measures_bands_once_guards_are_met(tmp_path):
    """With enough real pairs the harness reports rates and a monotonicity call."""
    pairs = []
    pairs += [(90.0, 1)] * 150 + [(90.0, 0)] * 100      # 80-100 band: 60% hit
    pairs += [(10.0, 1)] * 30 + [(10.0, 0)] * 220       # 0-20 band:   12% hit
    harness = _seed(tmp_path, pairs)
    report = harness.run()

    assert report.verdict == "DESCRIPTIVE_OK"
    top = next(b for b in report.bands if b.band == "80-100")
    bottom = next(b for b in report.bands if b.band == "0-20")
    assert top.verdict == "DESCRIPTIVE_OK" and bottom.verdict == "DESCRIPTIVE_OK"
    assert top.rate == pytest.approx(0.60, abs=0.01)
    assert bottom.rate == pytest.approx(0.12, abs=0.01)
    assert top.ci_low is not None and top.ci_high is not None
    assert report.monotonicity == "MONOTONIC_INCREASING"


def test_calibration_reports_non_monotonic_honestly(tmp_path):
    """If high scores do NOT do better, the report must say so."""
    pairs = []
    pairs += [(90.0, 1)] * 30 + [(90.0, 0)] * 220       # top band does WORSE
    pairs += [(10.0, 1)] * 150 + [(10.0, 0)] * 100
    report = _seed(tmp_path, pairs).run()

    assert report.monotonicity == "NOT_MONOTONIC"
    assert any("not rank" in f.lower() or "NOT monotonic" in f for f in report.findings)


def test_no_peeking_label_resolved_before_prediction_is_excluded(tmp_path):
    """A label that closed BEFORE the score was computed must never grade it."""
    harness = _seed(tmp_path, [(90.0, 1)] * 10, resolved_offset=-3600.0)
    report = harness.run()

    assert report.joined_pairs == 0, "hindsight leaked into the calibration join"


def test_mixed_engine_versions_are_flagged_not_averaged(tmp_path):
    """Pooling different scoring logic describes a system that never existed."""
    harness = _seed(tmp_path, [(90.0, 1)] * 5)
    conn = sqlite3.connect(harness.ledger_db)
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, source, chain, token_address, token_id,
             opportunity_score, confidence_level, risk_level, engine_version,
             weights_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("other", time.time() - 86400, "2026-01-01T00:00:00Z", SOURCE_TEST, "solana",
         "addrX", "token00000", 90.0, "HIGH", "LOW", "AHOS-SCORE-v2", "c" * 64,
         4, 0, "[]", "[]", "[]", "[]", "{}"))
    conn.commit(); conn.close()

    report = harness.run()
    assert len(report.engine_versions) > 1
    assert any("MIXED_ENGINE_VERSIONS" in f for f in report.findings)


def test_guards_match_the_projects_pre_registered_bar():
    """This harness must never be more permissive than research/baseline_stats."""
    from research import baseline_stats

    assert MIN_N_PER_BAND >= baseline_stats.MIN_N_STRATUM
    assert MIN_POSITIVES >= baseline_stats.MIN_POSITIVES


def test_score_bands_are_contiguous_and_cover_the_full_range():
    """Pre-declared bands must not leave a score unclassifiable."""
    assert SCORE_BANDS[0][1] == 0.0
    assert SCORE_BANDS[-1][2] > 100.0
    for lower, upper in zip(SCORE_BANDS, SCORE_BANDS[1:]):
        assert lower[2] == upper[1], "gap or overlap between score bands"


def test_calibration_on_empty_stores_is_insufficient_not_a_crash(tmp_path):
    """A fresh laptop install must produce an honest report, not an exception."""
    harness = CalibrationHarness(
        ledger_db=str(tmp_path / "missing.sqlite"),
        discovery_db=str(tmp_path / "also_missing.sqlite"))
    report = harness.run()

    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.joined_pairs == 0
