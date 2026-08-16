"""Tier-1 OSS audit tool pins (W13 / PART M): schema, honesty-on-failure, classifier
boundaries, archived-reject law, rate cap. CI is network-free: fetcher is always injected.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
import oss_audit as oa  # noqa: E402

NOW = oa.time.strptime("2026-08-13T04:00:00Z", "%Y-%m-%dT%H:%M:%SZ")


def _fetch_ok(url):
    return {"license": {"spdx_id": "MIT"}, "language": "Python", "stargazers_count": 100,
            "forks_count": 10, "open_issues_count": 3, "pushed_at": "2026-08-13T03:00:00Z",
            "archived": False}


def test_tier1_record_schema_and_honest_defaults():
    rec = oa.audit_repo("a/b", ["scheduler"], now=NOW, fetcher=_fetch_ok)
    assert rec["tier_reached"] == "T1_METADATA"
    assert rec["license"] == "MIT" and rec["maintenance"] == "ACTIVE"
    assert rec["security_posture"].startswith("UNVERIFIED")
    assert rec["dependency_posture"].startswith("UNVERIFIED")
    assert rec["verdict"] == "CANDIDATE_HELD_UNVERIFIED"   # tool never grants final acceptance


def test_api_error_records_unverified_never_fabricates():
    def boom(url):
        raise TimeoutError("no route")
    rec = oa.audit_repo("x/y", ["observability"], now=NOW, fetcher=boom)
    assert rec["verdict"].startswith("UNVERIFIED — API error")
    assert "stars" not in rec  # absent facts stay absent


def test_maintenance_classifier_boundaries():
    active = oa.classify_maintenance("2026-07-14T04:00:00Z", NOW)   # exactly 30 days
    stale = oa.classify_maintenance("2026-07-13T04:00:00Z", NOW)    # 31 days
    assert active == "ACTIVE" and stale == "STALE_OR_SLOW"
    assert oa.classify_maintenance(None, NOW) == "UNKNOWN"
    assert oa.classify_maintenance("garbage", NOW) == "UNKNOWN"


def test_archived_upstream_is_rejected():
    def f(url):
        d = _fetch_ok(url); d["archived"] = True; return d
    rec = oa.audit_repo("dead/repo", ["memory"], now=NOW, fetcher=f)
    assert rec["verdict"].startswith("REJECT")


def test_rate_cap_enforced():
    cands = {f"o/r{i}": ["l"] for i in range(21)}
    with pytest.raises(ValueError):
        oa.audit(cands, now=NOW, fetcher=_fetch_ok, sleep_s=0)
    rep = oa.audit(cands, now=NOW, fetcher=_fetch_ok, sleep_s=0, allow_large=True)
    assert len(rep["candidates"]) == 21
    assert rep["mode"].startswith("READ-ONLY")
