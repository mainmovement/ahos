#!/usr/bin/env python3
"""Final One-Brain lock — the TS opportunity brain is retired.

Locks the retirement so a future change cannot silently reintroduce a second
TS intelligence: scoring.ts is deleted, council.ts has no runCouncil authority,
engine.ts is context-only, and nothing imports the retired intelligence.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _prod_ts():
    files = list(ROOT.glob("*.ts")) + list(ROOT.glob("*.tsx"))
    for sub in ("app", "components", "lib"):
        d = ROOT / sub
        if d.exists():
            files += list(d.rglob("*.ts")) + list(d.rglob("*.tsx"))
    return [f for f in files if "node_modules" not in str(f) and "/tests/" not in str(f)]


def test_scoring_ts_is_deleted():
    assert not (ROOT / "scoring.ts").exists(), "scoring.ts (TS opportunity brain) must be deleted"


def test_no_production_import_of_retired_intelligence():
    for f in _prod_ts():
        txt = f.read_text(encoding="utf-8", errors="ignore")
        assert 'from "./scoring"' not in txt and 'from "../scoring"' not in txt, f"{f.name} imports deleted scoring.ts"
        # runCouncil / fetchSecurity must have no importer (they are retired/dead).
        assert "import { runCouncil" not in txt, f"{f.name} imports retired runCouncil"
        assert re.search(r"import\s*\{[^}]*\bfetchSecurity\b", txt) is None, f"{f.name} imports retired fetchSecurity"


def test_engine_is_context_only():
    engine = (ROOT / "engine.ts").read_text(encoding="utf-8")
    for forbidden in ("scoreToken(", "rankOpportunities(", "fetchSecurity(", "runCouncil(", "processOpportunityAlerts("):
        assert forbidden not in engine, f"engine.ts still calls {forbidden} (must be context-only)"


def test_council_ts_has_no_runcouncil_authority():
    council = (ROOT / "council.ts").read_text(encoding="utf-8")
    assert "export function runCouncil" not in council
    assert "TEAM_META" in council  # presentation metadata preserved


def test_snapshot_opportunities_are_canonical():
    snap = (ROOT / "snapshot.ts").read_text(encoding="utf-8")
    assert "listCanonicalOpportunities" in snap
    assert "from(opportunities)" not in snap
