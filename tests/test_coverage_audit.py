"""Coverage guardrail pins (F12 lesson → Lane B invariant law):
bundle completeness · classifier behavior on constructed fixtures ·
freshness improvement is MEASURED (owner success condition #2) · never token-count-only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from discovery import observations as obs  # noqa: E402
from discovery import lifecycle  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import coverage_audit as ca  # noqa: E402

NOW = 1_786_600_000.0


def _store(tmp_path, obs_specs):
    """obs_specs: [{chain,addr,t0,points:[(ts,price)...]}]"""
    conn = obs.open_store(tmp_path / "fx.sqlite")
    for i, s in enumerate(obs_specs):
        tid = obs.upsert_token(conn, s["chain"], s["addr"], first_seen_ts=s["t0"],
                               provider="fx", symbol=f"F{i}")
        raw = obs.store_raw(conn, "fx", f"/fx/{s['addr']}", s["t0"], 200, {"fx": i})
        lifecycle.register_discovery(conn, tid, s["t0"])
        for ts, price in s.get("points", []):
            obs.record_observation(conn, tid, "fx", ts, raw, metrics={"price_usd": price})
            lifecycle.on_observation(conn, tid, ts)
    conn.commit()
    conn.close()
    return tmp_path / "fx.sqlite"


def test_bundle_has_all_five_blocks(tmp_path):
    st = _store(tmp_path, [{"chain": "solana", "addr": "A", "t0": NOW - 3600,
                            "points": [(NOW - 60, 1.0)]}])
    rep = ca.coverage_report(st, now=NOW, reports_dir=tmp_path / "nope")
    for block in ("collection_health", "observation_freshness", "horizon_coverage",
                  "gap_detection", "recovery_status"):
        assert block in rep["blocks"], block
    assert rep["verdict"] in {"HEALTHY", "DEGRADED", "STARVING"}


def test_starving_fixture_is_called_starving(tmp_path):
    """Discovery continues but observations stopped 3 days ago and gaps accumulated."""
    st = _store(tmp_path, [{"chain": "solana", "addr": a, "t0": NOW - 3 * 86400,
                            "points": [(NOW - 3 * 86400 + 60, 1.0)]} for a in "ABCD"])
    conn = obs.open_store(st)
    for a in "ABCD":
        lifecycle.register_gap(conn, f"{a}-id", "missed:s+24h", NOW - 86400, NOW - 80000, "x")
    conn.commit(); conn.close()
    rep = ca.coverage_report(st, now=NOW, reports_dir=tmp_path / "nope")
    assert rep["verdict"] == "STARVING"
    assert rep["blocks"]["observation_freshness"]["share_latest_obs_within_24h"] == 0.0


def test_freshness_improvement_is_measurable(tmp_path):
    """Simulated PRE→POST_FIX: adding fresh points must move the freshness metrics, measurably
    (owner success condition #2: freshness improves MEASURABLY — the audit must SEE it)."""
    specs = [{"chain": "solana", "addr": a, "t0": NOW - 2 * 86400,
              "points": [(NOW - 2 * 86400 + 60, 1.0)]} for a in "AB"]
    st = _store(tmp_path, specs)
    before = ca.coverage_report(st, now=NOW, reports_dir=tmp_path / "nope")
    conn = obs.open_store(st)
    for a in "AB":
        tid = conn.execute("SELECT token_id FROM tokens WHERE address=?", (a,)).fetchone()["token_id"]
        raw = obs.store_raw(conn, "fx", f"/fx2/{a}", NOW, 200, {"fx2": a})
        obs.record_observation(conn, tid, "fx", NOW, raw, metrics={"price_usd": 1.1})
        lifecycle.on_observation(conn, tid, NOW)
    conn.commit(); conn.close()
    after = ca.coverage_report(st, now=NOW, reports_dir=tmp_path / "nope")
    b = before["blocks"]["observation_freshness"]["share_latest_obs_within_24h"]
    a = after["blocks"]["observation_freshness"]["share_latest_obs_within_24h"]
    assert b == 0.0 and a == 1.0
    assert after["blocks"]["collection_health"]["successful_observations_last_24h"] == 2


def test_missing_store_is_unknown_never_fabricated(tmp_path):
    rep = ca.coverage_report(tmp_path / "gone.sqlite", now=NOW, reports_dir=tmp_path)
    assert rep["verdict"] == "UNKNOWN"
