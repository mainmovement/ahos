#!/usr/bin/env python3
"""Phase A lock — the web opportunity display is sourced from the canonical store.

Governance guard so a future change cannot silently re-point the web opportunity
table back at the TS/PostgreSQL scoring path (recreating the second brain).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_snapshot_sources_opportunities_from_canonical_store():
    snap = (ROOT / "snapshot.ts").read_text(encoding="utf-8")
    # Opportunities come from the canonical store, read-only, fail-closed.
    assert "loadCanonicalSnapshot" in snap
    assert "listCanonicalOpportunities" in snap
    assert "canonicalOpps" in snap
    # It must NOT read the legacy PostgreSQL opportunities table for the display.
    assert "from(opportunities)" not in snap
    # And must not import that table symbol anymore.
    assert "\n  opportunities,\n" not in snap


def test_command_route_serves_canonical_snapshot():
    route = (ROOT / "app" / "api" / "command" / "route.ts").read_text(encoding="utf-8")
    assert "commandSnapshot" in route


def test_canonical_api_route_is_read_only_thin_adapter():
    route = (ROOT / "app" / "api" / "canonical" / "route.ts").read_text(encoding="utf-8")
    assert "listCanonicalOpportunities" in route
    for forbidden in ("scoreToken", "fetchSecurity", "rankOpportunities", "runCouncil", "collectMarket"):
        assert forbidden not in route
