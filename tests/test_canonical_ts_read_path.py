#!/usr/bin/env python3
"""Phase 4 / Phase 8 — TS canonical read path is fail-closed and non-authoritative.

Runs the REAL TypeScript `canonical_store.ts` under tsx against a store written by
the Python canonical writer, proving cross-runtime adversarial invariants:
  * Python PASS+eligible  → TS shows opportunity
  * Python VETO / UNKNOWN → TS never shows opportunity
  * missing / stale / malformed record → fail closed
Plus source-governance: alerts.ts consumes the canonical authority (not a TS
security computation) and has no write/promote API.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.contract import CanonicalDecision
from architecture.canonical.decision_store import CanonicalDecisionStore
from architecture.canonical.identity import canonical_token_id
from architecture.security.gate import (
    VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS, CAP_AVOID, CAP_WATCH, CAP_PASS,
)

TSX = ROOT / "node_modules" / ".bin" / "tsx"

_RUNNER = """
import { loadCanonicalSnapshot, isCanonicalPositiveOpportunity } from "%s/canonical_store.ts";
const cwd = process.argv[2];
const checks = JSON.parse(process.argv[3]);
(async () => {
  const snap = await loadCanonicalSnapshot(cwd);
  console.log(JSON.stringify(checks.map((c) => isCanonicalPositiveOpportunity(snap, c[0], c[1]))));
})();
"""


def _rec(cid, disp, cap, eligible, ts=1_000_000.0):
    return CanonicalDecision(
        canonical_token_id=cid, chain="solana", normalized_contract_address=cid + "a",
        security_disposition=disp, recommendation_cap=cap, opportunity_eligible=eligible,
        opportunity_score=88.0, evidence_reference="sha:x", decision_timestamp=ts)


def _run_ts(cwd: Path, checks, tmp_path) -> list:
    runner = tmp_path / "reader.ts"
    runner.write_text(_RUNNER % ROOT.as_posix(), encoding="utf-8")
    proc = subprocess.run(
        [str(TSX), str(runner), str(cwd), json.dumps(checks)],
        capture_output=True, text=True, timeout=90,
    )
    assert proc.returncode == 0, f"tsx failed: {proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(not TSX.exists(), reason="tsx not installed")
def test_ts_reader_honors_python_dispositions_fail_closed(tmp_path):
    cid_pass = canonical_token_id("solana", "SolPassAAAA1111111111111111111111111111")
    cid_veto = canonical_token_id("solana", "SolVetoBBBB1111111111111111111111111111")
    cid_unk = canonical_token_id("solana", "SolUnknCCCC1111111111111111111111111111")
    store = CanonicalDecisionStore(store_dir=tmp_path / "reports" / "canonical" / "decisions",
                                   freshness_budget_sec=900)
    store.write_decisions([
        _rec(cid_pass, VERDICT_PASS, CAP_PASS, True),
        _rec(cid_veto, VERDICT_VETO, CAP_AVOID, False),
        _rec(cid_unk, VERDICT_PASS_WITH_UNKNOWN, CAP_WATCH, False),
    ], now=1_000_000.0)

    fresh = 1_000_000.0 + 10
    stale = 1_000_000.0 + 2000  # > 900 budget
    res = _run_ts(tmp_path, [
        [cid_pass, fresh],   # 0: PASS+eligible+fresh → True
        [cid_veto, fresh],   # 1: VETO → False
        [cid_unk, fresh],    # 2: UNKNOWN → False
        ["nonexistent_id", fresh],  # 3: missing → False
        [cid_pass, stale],   # 4: stale → False
    ], tmp_path)
    assert res == [True, False, False, False, False], res


@pytest.mark.skipif(not TSX.exists(), reason="tsx not installed")
def test_ts_reader_fails_closed_on_malformed_store(tmp_path):
    d = tmp_path / "reports" / "canonical" / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    (d / "latest.json").write_text("{ not valid json", encoding="utf-8")
    cid = canonical_token_id("solana", "SolPassAAAA1111111111111111111111111111")
    res = _run_ts(tmp_path, [[cid, 1_000_000.0]], tmp_path)
    assert res == [False]


@pytest.mark.skipif(not TSX.exists(), reason="tsx not installed")
def test_ts_reader_fails_closed_on_empty_cwd(tmp_path):
    cid = canonical_token_id("solana", "SolPassAAAA1111111111111111111111111111")
    res = _run_ts(tmp_path, [[cid, 1_000_000.0]], tmp_path)  # no store file at all
    assert res == [False]


# --------------------------------------------------------- source governance --
def test_alerts_ts_consumes_canonical_authority_only():
    alerts = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    assert "canonical_store" in alerts
    assert "isCanonicalPositiveOpportunity" in alerts
    assert "canonical_identity" in alerts
    # The removed P0 bypass and TS security-authority computations must be gone.
    assert "rankScore >= 0.8" not in alerts
    assert 's === "UNKNOWN"' not in alerts
    assert "function securityOk" not in alerts


def test_canonical_store_ts_is_read_only():
    store = (ROOT / "canonical_store.ts").read_text(encoding="utf-8")
    # No filesystem write / mutation operations may exist (read-only adapter).
    for forbidden in ("writeFile", "mkdir", "appendFile", ".write("):
        assert forbidden not in store, f"canonical_store.ts must be read-only; found {forbidden!r}"
