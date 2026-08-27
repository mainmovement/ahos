#!/usr/bin/env python3
"""Phase 6/7 — the canonical store is the single 'opportunities' source.

Covers the non-authoritative presentation payload, the Python `list_eligible`
reader, the TS `listCanonicalOpportunities` reader (via tsx, cross-runtime), and
governance for the read-only web canonical adapter route.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.contract import CanonicalDecision
from architecture.canonical.decision_store import CanonicalDecisionStore
from architecture.security.gate import (
    VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS, CAP_AVOID, CAP_WATCH, CAP_PASS,
)

TSX = ROOT / "node_modules" / ".bin" / "tsx"


def _rec(tid, disp, cap, eligible, score, pres=None, ts=1_000_000.0):
    return CanonicalDecision(
        canonical_token_id=tid, chain="solana", normalized_contract_address=tid + "a",
        security_disposition=disp, recommendation_cap=cap, opportunity_eligible=eligible,
        opportunity_score=score, evidence_reference="s", decision_timestamp=ts, presentation=pres)


def test_presentation_payload_roundtrip():
    pres = {"symbol": "PASS", "reasons_fa": ["نقدینگی خوب"], "risks_fa": [], "unknowns_fa": []}
    rec = _rec("t", VERDICT_PASS, CAP_PASS, True, 80.0, pres=pres)
    assert rec.validate() is True
    back = CanonicalDecision.from_dict(rec.to_dict())
    assert back is not None and back.presentation == pres
    # presentation is non-authoritative: a record with a rich payload but VETO
    # disposition is still invalid if marked eligible.
    bad = _rec("t", VERDICT_VETO, CAP_AVOID, True, 99.0, pres=pres)
    assert bad.validate() is False


def test_list_eligible_excludes_non_pass_and_sorts(tmp_path):
    s = CanonicalDecisionStore(store_dir=tmp_path / "c", freshness_budget_sec=900)
    s.write_decisions([
        _rec("t_hi", VERDICT_PASS, CAP_PASS, True, 90.0, pres={"symbol": "HI"}),
        _rec("t_lo", VERDICT_PASS, CAP_PASS, True, 60.0, pres={"symbol": "LO"}),
        _rec("t_veto", VERDICT_VETO, CAP_AVOID, False, 95.0),
        _rec("t_unk", VERDICT_PASS_WITH_UNKNOWN, CAP_WATCH, False, 99.0),
    ], now=1_000_000.0)
    elig = s.list_eligible(now=1_000_000.0)
    ids = [r.canonical_token_id for r in elig]
    assert ids == ["t_hi", "t_lo"]              # eligible only, score-desc
    assert elig[0].presentation == {"symbol": "HI"}


def test_list_eligible_fail_closed_when_stale(tmp_path):
    s = CanonicalDecisionStore(store_dir=tmp_path / "c", freshness_budget_sec=900)
    s.write_decisions([_rec("t", VERDICT_PASS, CAP_PASS, True, 80.0)], now=1_000_000.0)
    assert s.list_eligible(now=1_000_000.0 + 2000) == []


_RUNNER = """
import { loadCanonicalSnapshot, listCanonicalOpportunities } from "%s/canonical_store.ts";
const cwd = process.argv[2]; const now = Number(process.argv[3]);
(async () => {
  const s = await loadCanonicalSnapshot(cwd);
  const l = listCanonicalOpportunities(s, now);
  console.log(JSON.stringify(l.map((r) => [r.canonical_token_id, r.opportunity_score,
    r.presentation ? r.presentation.symbol : null])));
})();
"""


@pytest.mark.skipif(not TSX.exists(), reason="tsx not installed")
def test_ts_list_canonical_opportunities_matches_python(tmp_path):
    s = CanonicalDecisionStore(store_dir=tmp_path / "reports" / "canonical" / "decisions",
                               freshness_budget_sec=900)
    s.write_decisions([
        _rec("t_hi", VERDICT_PASS, CAP_PASS, True, 90.0, pres={"symbol": "HI"}),
        _rec("t_lo", VERDICT_PASS, CAP_PASS, True, 60.0, pres={"symbol": "LO"}),
        _rec("t_veto", VERDICT_VETO, CAP_AVOID, False, 95.0),
    ], now=1_000_000.0)
    runner = tmp_path / "list.ts"
    runner.write_text(_RUNNER % ROOT.as_posix(), encoding="utf-8")
    proc = subprocess.run([str(TSX), str(runner), str(tmp_path), "1000010"],
                          capture_output=True, text=True, timeout=90)
    assert proc.returncode == 0, proc.stderr
    got = json.loads(proc.stdout.strip().splitlines()[-1])
    assert got == [["t_hi", 90.0, "HI"], ["t_lo", 60.0, "LO"]]  # veto excluded, score-desc


def test_web_canonical_route_is_read_only_adapter():
    route = (ROOT / "app" / "api" / "canonical" / "route.ts").read_text(encoding="utf-8")
    assert "canonical_store" in route
    assert "listCanonicalOpportunities" in route
    # No independent intelligence in the adapter.
    for forbidden in ("scoreToken", "fetchSecurity", "rankOpportunities", "collectMarket", "runCouncil"):
        assert forbidden not in route, f"web canonical route must be a thin adapter; found {forbidden!r}"
