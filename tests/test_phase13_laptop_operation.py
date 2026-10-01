#!/usr/bin/env python3
"""Phase 13 — laptop operation gate regressions.

The value of this phase is entirely in what the tooling REFUSES to certify.
These tests pin those refusals so a later change cannot quietly turn a sandbox
run into "the official soak", which would silently invalidate every downstream
claim about uptime, provider success and calibration.
"""
from __future__ import annotations

import json
import platform
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.score_ledger import SCHEMA_SCORE_LEDGER  # noqa: E402
from scripts import record_local_laptop_baseline as baseline  # noqa: E402
from scripts import soak_t0_snapshot as t0  # noqa: E402

# outcome_label lives in the Lane-A discovery store. The harness joins it by
# name, so the fixture restates the schema here; test_fixture_outcome_label_matches
# the live store pins the two together so a drift in either direction is caught.
SCHEMA_OUTCOME_LABEL = """
CREATE TABLE IF NOT EXISTS outcome_label (
  token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
  hit INTEGER, max_favorable REAL, max_adverse REAL,
  entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
  PRIMARY KEY (token_id, horizon, event_class)
);
"""



# ------------------------------------------------------------ baseline gate

def test_non_windows_host_can_never_be_eligible():
    """The core Phase 13 refusal: sandbox hours must never count."""
    report = baseline.build()

    if platform.system() != "Windows":
        assert report["official_168h_eligible"] is False
        assert report["checks"]["windows_host"] is False


def test_baseline_names_every_failed_check():
    """A refusal without a reason is not actionable evidence."""
    report = baseline.build()
    failed = [k for k, v in report["checks"].items() if not v]

    if not report["official_168h_eligible"]:
        assert failed, "ineligible baseline must name at least one failed check"


def test_baseline_records_the_mandated_fields():
    """Task 1 fields must come from the artifact, not from prose."""
    report = baseline.build()

    assert report["os"]["system"]
    assert report["python"]["version"]
    assert report["dependency_hash"]["requirements_txt_sha256"]
    assert report["dependency_hash"]["lane_a_freeze_sha256"]
    assert set(report["databases"]["integrity"]) == {
        "e01_discovery", "paper_trading", "ahos_local", "ahos_knowledge"}
    assert report["safety"]["mode"] == "observation-only"


def test_live_trading_env_flags_block_eligibility(monkeypatch):
    monkeypatch.setenv("AHOS_EXECUTE_LIVE_TRADES", "1")
    report = baseline.build()

    assert report["checks"]["execution_flags_disabled"] is False
    assert report["official_168h_eligible"] is False


# ------------------------------------------------------------------ t0 gate

def _valid_context():
    """Patches representing a correctly-prepared Windows laptop."""
    return (
        patch.object(platform, "system", return_value="Windows"),
        patch.object(t0, "_baseline_status",
                     return_value={"present": True, "official_168h_eligible": True,
                                   "failed_checks": []}),
        patch.object(t0, "_watchdog_status",
                     return_value={"status": "OK", "stale_components": []}),
        patch.object(t0, "_provider_status",
                     return_value={"probed": True, "any_success": True,
                                   "status_counts": {"SUCCESS": 2}}),
    )


def test_t0_is_invalid_on_this_sandbox():
    snap = t0.build_snapshot(do_probe=False)

    if platform.system() != "Windows":
        assert snap["t0_valid"] is False
        assert snap["soak_status"] == "NOT_STARTED"
        assert any("not Windows" in r for r in snap["t0_invalid_reasons"])


def test_t0_contains_every_mandated_field():
    """Task 5 names the required contents explicitly."""
    snap = t0.build_snapshot(do_probe=False)

    for key in ("timestamp_utc", "git", "environment", "watchdog",
                "heartbeats", "providers"):
        assert key in snap, f"t0 snapshot missing mandated field: {key}"
    assert snap["git"]["commit_sha"]
    assert snap["environment"]["fingerprint_sha256"]


def test_t0_valid_only_when_all_four_conditions_hold(monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    p1, p2, p3, p4 = _valid_context()
    with p1, p2, p3, p4:
        snap = t0.build_snapshot()

    assert snap["t0_valid"] is True
    assert snap["soak_status"] == "LOCAL_SOAK_RUNNING"
    assert snap["t0_invalid_reasons"] == []


@pytest.mark.parametrize("broken", ["windows", "baseline", "watchdog", "source"])
def test_each_missing_condition_alone_invalidates_t0(monkeypatch, broken):
    """No single condition may be dropped without invalidating t0."""
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE",
                       "sandbox" if broken == "source" else "local")

    sys_val = "Linux" if broken == "windows" else "Windows"
    base_val = ({"present": True, "official_168h_eligible": False,
                 "failed_checks": ["windows_host"]}
                if broken == "baseline"
                else {"present": True, "official_168h_eligible": True,
                      "failed_checks": []})
    wd_val = ({"status": "NO_HEARTBEATS"} if broken == "watchdog"
              else {"status": "OK", "stale_components": []})

    with patch.object(platform, "system", return_value=sys_val), \
         patch.object(t0, "_baseline_status", return_value=base_val), \
         patch.object(t0, "_watchdog_status", return_value=wd_val), \
         patch.object(t0, "_provider_status",
                      return_value={"probed": True, "any_success": True,
                                    "status_counts": {"SUCCESS": 2}}):
        snap = t0.build_snapshot()

    assert snap["t0_valid"] is False, f"t0 wrongly valid with {broken} broken"
    assert snap["soak_status"] == "NOT_STARTED"


def test_t0_writes_an_artifact_even_when_refusing(tmp_path):
    """A refusal that leaves no record is not evidence."""
    out = tmp_path / "soak" / "system_state_t0.json"
    rc = t0.main(["--no-probe", "--out", str(out)])

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.soak_t0.v1"
    if platform.system() != "Windows":
        assert rc == 3 and payload["t0_valid"] is False


def test_t0_snapshot_is_read_only():
    import hashlib
    from config.paths import get_discovery_db_path, get_local_db_path

    def digest(p: str) -> bytes:
        return hashlib.sha256(Path(p).read_bytes()).digest()

    before = (digest(get_local_db_path()), digest(get_discovery_db_path()))
    t0.build_snapshot(do_probe=False)
    assert (digest(get_local_db_path()), digest(get_discovery_db_path())) == before


# --------------------------------------------------------- operation report

def test_operation_report_exists_and_covers_mandated_sections():
    doc = ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")

    for section in ("Hardware environment", "Operating system", "Python version",
                    "Dependency hash", "Database integrity", "Lane-A freeze",
                    "Evidence source"):
        assert section in text, f"operation report missing section: {section}"


def test_operation_report_does_not_claim_a_running_soak():
    text = (ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())

    assert "AWAITING_LAPTOP_EXECUTION" in flat
    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY"):
        assert forbidden not in flat
    # It must state plainly that the daemon was not started.
    assert "NOT PERFORMED" in flat


def test_operation_report_dependency_hashes_are_real():
    """Documented hashes must match the repository, not be placeholders."""
    import hashlib

    text = (ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md").read_text(encoding="utf-8")
    for rel in ("requirements.txt", "config/lane_a_freeze.sha256"):
        digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert digest in text, f"operation report lacks the real sha256 of {rel}"


# Byte-hashed evidence files must be byte-identical to their committed blob, or
# the sha256 above is a property of the host rather than the repository.
@pytest.mark.parametrize("rel", ["requirements.txt", "config/lane_a_freeze.sha256"])
def test_byte_hashed_evidence_files_are_canonical_on_this_host(rel):
    """The working-tree bytes must equal the committed blob (M-GAP-042).

    `config/lane_a_freeze.sha256` and `requirements.txt` are pinned by sha256
    over raw bytes, so their byte content must not be rewritten on checkout.
    core.autocrlf=true did exactly that on Windows -- the freeze manifest is
    committed with LF and was checked out with CRLF, so its working-tree sha256
    (8d35cd2b...) stopped matching the documented one (2f5d67dd...) and the test
    above went red on a clean tree for want of a `.gitattributes` rule.

    The rule is now `*.sha256 -text` / `requirements.txt -text`, which pins the
    bytes in both directions. This pins the invariant itself, so a future
    `.gitattributes` edit that reintroduces end-of-line conversion for either
    path fails here on Windows -- the only host where the drift is visible --
    rather than silently changing a hash the operation report depends on.
    """
    import subprocess

    blob = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    assert (ROOT / rel).read_bytes() == blob, (
        f"{rel} was rewritten on checkout; its byte hash is host-dependent")


def test_progress_snapshot_has_not_advanced_to_running_soak():
    """LOCAL_SOAK_RUNNING may only appear once the laptop actually runs it."""
    text = (ROOT / "AHOS_PHASE_PROGRESS_SNAPSHOT.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())

    assert "READY_FOR_REAL_LOCAL_DATA" in flat
    # The phrase may be discussed, but never asserted as the current state.
    assert "Classification:** `LOCAL_SOAK_RUNNING`" not in flat


def test_fixture_outcome_label_matches_the_live_store():
    """The restated fixture schema must track the Lane-A store it imitates.

    The calibration fixtures below build an outcome_label table from a copied
    schema. If the live store's columns drift, the fixtures would silently
    stop modelling the join the harness really performs -- so the two are
    compared structurally, column by column, rather than as strings.
    """
    import sqlite3

    from config.paths import get_discovery_db_path, sqlite_ro_uri

    conn = sqlite3.connect(sqlite_ro_uri(get_discovery_db_path()), uri=True)
    live = conn.execute(
        "SELECT name FROM pragma_table_info('outcome_label')").fetchall()
    conn.close()

    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA_OUTCOME_LABEL)
    fixture = con.execute(
        "SELECT name FROM pragma_table_info('outcome_label')").fetchall()
    con.close()

    assert [r[0] for r in fixture] == [r[0] for r in live], (
        f"fixture outcome_label columns { [r[0] for r in fixture] } no longer "
        f"match the live store { [r[0] for r in live] }")


def test_no_fake_calibration_on_this_host():
    """Phase 13 acceptance: no calibration may be manufactured.

    This used to assert `verdict == INSUFFICIENT_DATA` and `joined_pairs == 0`.
    That pinned a transient property of an empty laptop, not the invariant it
    was written to protect: it would have started failing the moment the host
    accumulated enough REAL evidence to clear the pre-registered guards, which
    is the outcome the whole pipeline exists to produce. It went red for that
    reason (M-GAP-043) once 6,037 real local pairs existed.

    The durable form of "no calibration may be manufactured" is provenance, not
    emptiness: whatever cohort the harness reports must be independently
    reproducible from the stores by the same integrity rules, must contain only
    eligible real sources, and every pair must carry a real evidence hash. A
    harness that invented pairs could not satisfy all three. The empty-host case
    is pinned separately by test_calibration_fails_closed_when_no_evidence_exists
    and the source filter by
    test_synthetic_predictions_can_never_become_calibration_evidence.
    """
    from architecture.learning import calibration as calib
    from architecture.learning.calibration import CalibrationHarness
    from config.paths import connect_sqlite_ro, sqlite_ro_uri, get_local_db_path, get_discovery_db_path

    report = CalibrationHarness().run()

    # The verdict may only ever be one of the two pre-registered honest
    # outcomes. Anything else means the harness invented a third conclusion.
    assert report.verdict in ("INSUFFICIENT_DATA", "DESCRIPTIVE_OK"), (
        f"harness emitted a verdict outside the honest vocabulary: {report.verdict}")

    # Independently recompute the cohort straight from the stores, using the
    # harness's own published constants, so the harness cannot report a count
    # it did not derive. A different code path over the same rules.
    conn = connect_sqlite_ro(get_local_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("ATTACH DATABASE ? AS disc", (sqlite_ro_uri(get_discovery_db_path()),))
    placeholders = ",".join("?" for _ in sorted(calib.CalibrationHarness().eligible_sources))
    eligible = sorted(calib.CalibrationHarness().eligible_sources)
    rows = conn.execute(
        f"""SELECT s.score_id, s.evidence_sha256, s.source
              FROM opportunity_score_ledger s
              JOIN disc.outcome_label o ON o.token_id = s.token_id
             WHERE o.horizon = ? AND o.event_class = ?
               AND o.hit IS NOT NULL AND s.token_id IS NOT NULL
               AND s.source IN ({placeholders})
               AND o.resolved_ts > s.scored_ts""",
        (calib.DEFAULT_HORIZON, calib.DEFAULT_EVENT_CLASS, *eligible)).fetchall()
    # How many rows the eligible-source rule refused, by the same rules.
    ineligible_actual = conn.execute(
        f"""SELECT COUNT(*) FROM opportunity_score_ledger
            WHERE source NOT IN ({placeholders})""", tuple(eligible)).fetchone()[0]
    conn.close()

    assert len(rows) == report.joined_pairs, (
        f"harness reports {report.joined_pairs} pairs but the stores yield "
        f"{len(rows)} under the same rules -- the count is not reproducible")

    # Source provenance: only eligible sources are calibration evidence.
    ineligible = sorted({str(r["source"]) for r in rows}
                        - set(CalibrationHarness().eligible_sources))
    assert not ineligible, f"non-eligible sources inside the cohort: {ineligible}"

    # Evidence integrity: every pair must carry a real evidence hash. A
    # fabricated row would have to invent one, and there must be no shared
    # hash standing in for many predictions.
    shas = [str(r["evidence_sha256"] or "") for r in rows]
    assert all(len(s) == 64 and all(c in "0123456789abcdef" for c in s) for s in shas), (
        "some joined pairs lack a real 64-hex evidence_sha256")
    assert len(set(shas)) == len(shas), (
        f"{len(shas) - len(set(shas))} pairs share an evidence hash")

    # The fingerprint is what makes the cohort auditable later; it must be a
    # real digest over the pairs, not a placeholder.
    assert len(report.dataset_fingerprint) == 64, (
        f"dataset_fingerprint is not a sha256: {report.dataset_fingerprint!r}")

    # And the harness must account for the sources it refused rather than
    # quietly absorbing them. The count it reports has to equal the real number
    # of non-eligible rows in the store -- an accountability check, not a
    # mere presence check.
    ineligible_reported = report.exclusion_reasons.get("ineligible_source", 0)
    assert ineligible_reported == ineligible_actual, (
        f"harness reports {ineligible_reported} rows excluded as ineligible "
        f"source but the store contains {ineligible_actual}")


def test_calibration_fails_closed_when_no_evidence_exists(tmp_path):
    """The empty-host half of the anti-fabrication invariant.

    Whatever the original assertion was protecting, this is the case where it
    held: with no evidence at all the harness must still report
    INSUFFICIENT_DATA and zero pairs, never a rate invented to look useful.
    Pinned against empty stores so it stays true on any host, warm or cold.
    """
    from architecture.learning.calibration import CalibrationHarness

    ledger = tmp_path / "ledger.db"
    discovery = tmp_path / "discovery.db"

    con = sqlite3.connect(str(ledger))
    con.executescript(SCHEMA_SCORE_LEDGER)
    con.close()

    con = sqlite3.connect(str(discovery))
    con.executescript(SCHEMA_OUTCOME_LABEL)
    con.close()

    report = CalibrationHarness(
        ledger_db=str(ledger), discovery_db=str(discovery)).run()

    assert report.joined_pairs == 0
    assert report.verdict == "INSUFFICIENT_DATA"
    # No band may be awarded DESCRIPTIVE_OK when there is nothing to describe.
    assert all(b.verdict == "INSUFFICIENT_DATA" for b in report.bands), (
        "a score band cleared the sample guards on an empty store")


def test_synthetic_predictions_can_never_become_calibration_evidence(tmp_path):
    """The source filter is load-bearing, not decorative.

    Plants predictions from every non-eligible source (sandbox / test /
    synthetic) that DO have matching, non-peeking, resolved outcome labels --
    i.e. rows that would join perfectly if the source filter were dropped --
    and requires the harness to still yield zero pairs. If the eligible-source
    rule is ever relaxed, this cohort becomes 'evidence' and this test fails.
    """
    from architecture.learning.calibration import CalibrationHarness
    from architecture.learning.score_ledger import CALIBRATION_ELIGIBLE_SOURCES

    ledger = tmp_path / "ledger.db"
    discovery = tmp_path / "discovery.db"

    con = sqlite3.connect(str(ledger))
    con.executescript(SCHEMA_SCORE_LEDGER)
    con.executemany(
        """INSERT INTO opportunity_score_ledger (
             score_id, scored_ts, scored_utc, chain, token_address, token_id,
             symbol, opportunity_score, confidence_level, risk_level,
             engine_version, weights_sha256, evidence_sha256,
             known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json,
             missing_unknowns_json, invalidation_json, score_breakdown_json,
             source, source_provider)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(f"{src}-row-{i}", 1000.0 + i, "2026-01-01T00:00:00Z", "solana",
          f"addr{i}", f"tok{i}", f"SYM{i}", 75.0, "HIGH", "LOW",
          "AHOS-SCORE-v1", "w" * 64, "e" * 64, 10, 0, "[]", "[]", "[]", "{}",
          "{}", src, "dexscreener")
         for src in ("sandbox", "test", "synthetic") for i in range(50)])
    con.commit()
    con.close()

    # Labels that resolve strictly after each score, hit non-null -- a perfect
    # join partner in every respect except source eligibility.
    con = sqlite3.connect(str(discovery))
    con.executescript(SCHEMA_OUTCOME_LABEL)
    con.executemany(
        """INSERT INTO outcome_label (
             token_id, horizon, event_class, hit, max_favorable, max_adverse,
             entry_price, entry_price_ts, resolved_ts)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(f"tok{i}", "24h", "+50%", 1, 2.0, 0.5, 1.0, 900.0, 2000.0)
         for i in range(50)])
    con.commit()
    con.close()

    report = CalibrationHarness(
        ledger_db=str(ledger), discovery_db=str(discovery)).run()

    assert report.joined_pairs == 0, (
        f"{report.joined_pairs} non-eligible rows became calibration evidence")
    assert report.verdict == "INSUFFICIENT_DATA"
    assert CALIBRATION_ELIGIBLE_SOURCES == frozenset({"local"}), (
        "the eligible-source set was widened; sandbox/test/synthetic rows "
        "above would now count as real evidence")
