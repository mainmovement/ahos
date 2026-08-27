#!/usr/bin/env python3
"""Phase 2 — canonical decision store (atomic, versioned, fail-closed)."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.contract import CanonicalDecision
from architecture.canonical.decision_store import CanonicalDecisionStore
from architecture.security.gate import (
    VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS, CAP_AVOID, CAP_WATCH, CAP_PASS,
)


def _rec(tid, disposition=VERDICT_PASS, cap=CAP_PASS, eligible=True, score=80.0, ts=1_000_000.0):
    return CanonicalDecision(
        canonical_token_id=tid, chain="solana",
        normalized_contract_address=tid + "addr",
        security_disposition=disposition, recommendation_cap=cap,
        opportunity_eligible=eligible, opportunity_score=score,
        evidence_reference="sha:x", decision_timestamp=ts,
    )


def _store(tmp_path):
    return CanonicalDecisionStore(store_dir=tmp_path / "canon", freshness_budget_sec=900)


def test_write_and_read_roundtrip(tmp_path):
    s = _store(tmp_path)
    n = s.write_decisions([_rec("t_pass")], now=1_000_000.0)
    assert n == 1
    rec = s.get("t_pass", now=1_000_000.0)
    assert rec is not None and rec.opportunity_eligible is True
    assert s.is_positive_opportunity("t_pass", now=1_000_000.0) is True


def test_missing_record_fails_closed(tmp_path):
    s = _store(tmp_path)
    assert s.get("nope", now=1_000_000.0) is None
    assert s.is_positive_opportunity("nope", now=1_000_000.0) is False


def test_veto_and_unknown_never_positive(tmp_path):
    s = _store(tmp_path)
    s.write_decisions([
        _rec("t_veto", disposition=VERDICT_VETO, cap=CAP_AVOID, eligible=False),
        _rec("t_unk", disposition=VERDICT_PASS_WITH_UNKNOWN, cap=CAP_WATCH, eligible=False),
    ], now=1_000_000.0)
    assert s.is_positive_opportunity("t_veto", now=1_000_000.0) is False
    assert s.is_positive_opportunity("t_unk", now=1_000_000.0) is False


def test_invalid_decisions_are_not_written(tmp_path):
    s = _store(tmp_path)
    # eligible-but-VETO is invalid → dropped, never persisted
    bad = CanonicalDecision(
        canonical_token_id="bad", chain="solana", normalized_contract_address="a",
        security_disposition=VERDICT_VETO, recommendation_cap=CAP_AVOID,
        opportunity_eligible=True, opportunity_score=99.0,
        evidence_reference="x", decision_timestamp=1_000_000.0)
    assert s.write_decisions([bad], now=1_000_000.0) == 0
    assert s.get("bad", now=1_000_000.0) is None


def test_stale_record_fails_closed(tmp_path):
    s = _store(tmp_path)
    s.write_decisions([_rec("t_pass", ts=1_000_000.0)], now=1_000_000.0)
    # 2000s later, budget 900s → stale
    assert s.get("t_pass", now=1_000_000.0 + 2000) is None
    assert s.is_positive_opportunity("t_pass", now=1_000_000.0 + 2000) is False


def test_malformed_latest_json_fails_closed(tmp_path):
    s = _store(tmp_path)
    s.dir.mkdir(parents=True, exist_ok=True)
    s.latest_path.write_text("{ this is not json", encoding="utf-8")
    assert s.get("anything", now=1_000_000.0) is None


def test_version_mismatch_in_store_fails_closed(tmp_path):
    s = _store(tmp_path)
    s.dir.mkdir(parents=True, exist_ok=True)
    payload = _rec("t_pass").to_dict()
    payload["decision_version"] = 999
    s.latest_path.write_text(json.dumps({"t_pass": payload}), encoding="utf-8")
    assert s.get("t_pass", now=1_000_000.0) is None


def test_atomic_write_leaves_no_partial_and_latest_wins(tmp_path):
    s = _store(tmp_path)
    s.write_decisions([_rec("t", score=10.0, ts=1_000_000.0)], now=1_000_000.0)
    s.write_decisions([_rec("t", score=90.0, ts=1_000_100.0)], now=1_000_100.0)
    # no leftover temp files
    assert not list(s.dir.glob(".latest.*.tmp"))
    rec = s.get("t", now=1_000_100.0)
    assert rec is not None and rec.opportunity_score == 90.0
    # ledger retains both (audit trail)
    lines = s.ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_ts_cannot_manufacture_pass_via_reader(tmp_path):
    """The reader only exposes what the writer persisted; there is no adapter API
    to inject a canonical PASS."""
    s = _store(tmp_path)
    assert not hasattr(s, "set_eligible")
    assert not hasattr(s, "promote")
    # reading a token never creates a record
    assert s.is_positive_opportunity("ghost", now=1_000_000.0) is False
    assert not s.latest_path.exists()
