import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from architecture.learning import strategy_switch as sw
from architecture.learning.walk_forward import hrp_weights, _hold_trades
from architecture.markets import macro_calendar as mc


def _write(root: Path, rel: Path, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")


def test_switch_refuses_unproven_and_rolls_back(tmp_path):
    _write(tmp_path, sw.B4_REL, {"candidates": [
        {"strategy_id": "b4-X", "gate": "FAIL", "gate_detail": "DSR=0.2"},
        {"strategy_id": "b4-Y", "gate": "PASS_STATS", "gate_detail": "ok"}]})
    _write(tmp_path, sw.RED_REL, {"reports": [{"strategy_id": "b4-Y", "verdict": "SURVIVED_RED_TEAM"}]})
    with pytest.raises(PermissionError):
        sw.promote(tmp_path, "b4-X", "stablecoin_impulse", 0.05, actor="test")
    s = sw.promote(tmp_path, "b4-Y", "stablecoin_impulse", 0.05, actor="test")
    assert s["version"] == 1 and s["active"] == {"stablecoin_impulse": 0.05}
    w, v = sw.apply({"mtf_trend": 0.3, "stablecoin_impulse": 0.0}, tmp_path)
    assert w["stablecoin_impulse"] == 0.05 and v == 1
    s = sw.rollback(tmp_path, 0, actor="test")
    assert s["active"] == {} and s["version"] == 2


def test_switch_default_is_empty(tmp_path):
    w, v = sw.apply({"a": 1.0}, tmp_path)
    assert w == {"a": 1.0} and v == 0


def test_hrp_weights_valid():
    import numpy as np
    rng = np.random.default_rng(1)
    r = rng.normal(0, [0.01, 0.02, 0.03, 0.01], size=(300, 4))
    cov = np.cov(r.T); sd = np.sqrt(np.diag(cov)); corr = cov / np.outer(sd, sd)
    w = hrp_weights(cov, corr)
    assert abs(w.sum() - 1) < 1e-9 and (w > 0).all() and w[0] > w[2]


def test_hold_trades_non_overlapping():
    bars = [(i * 86400, 1, 1, 1, 100 + i) for i in range(20)]
    tr = _hold_trades(bars, {1: 1, 2: 1, 5: -1}, 3, 0.0)
    assert [t["t_open"] for t in tr] == [1, 5]
    assert tr[0]["ret"] == pytest.approx(104 / 101 - 1)


FOMC_HTML = ('<h4><a id="1">2026 FOMC Meetings</a></h4><div class="fomc-meeting__month"><strong>October</strong></div>'
             '<div class="fomc-meeting__date">27-28</div><div class="fomc-meeting__month"><strong>August</strong></div>'
             '<div class="fomc-meeting__date">22</div>')


def test_fomc_parser_and_upcoming():
    ev = mc.parse_fomc(FOMC_HTML)
    assert len(ev) == 1 and ev[0]["at_utc"].startswith("2026-10-28T18:00")
    snap = {"events": ev}
    up = mc.upcoming(snap, "US", now=datetime(2026, 10, 28, 0, 0, tzinfo=timezone.utc))
    assert up and up[0]["hours_until"] == 18.0


def test_calendar_unavailable_is_reported_not_invented(tmp_path):
    snap = mc.build_calendar(tmp_path, getter=lambda u: None, now=datetime(2026, 10, 24, tzinfo=timezone.utc))
    assert snap["events"] == [] and all(v.startswith("UNAVAILABLE") for v in snap["status"].values())


def test_ecb_two_source_mirror_agreement():
    ecb_rss = """<rss><channel><item><title>ECB Governing Council monetary policy meeting on 12 December 2026</title></item></channel></rss>"""
    bis = '<events><event><name>ECB policy</name><date>2026-12-12</date></event></events>'
    da = mc._dates_from_rss_titles(ecb_rss, keywords=("monetary policy", "ecb"))
    db = mc._dates_from_bis_xml(bis)
    agreed = mc.two_source_agreed_dates(da, db)
    assert agreed == [date(2026, 12, 12)]
    ev = mc.build_ecb_events(agreed)
    assert ev[0]["event"] == "ECB_GOV_COUNCIL" and ev[0]["two_source_mirrors"] is True


def test_ecb_best_mirror_pair_across_feeds():
    press = """<rss><channel><item><title>ECB monetary policy meeting on 12 December 2026</title></item></channel></rss>"""
    gnews = """<rss><channel><item><title>ECB Governing Council decision 12 December 2026</title></item></channel></rss>"""

    def getter(url: str) -> str | None:
        if "press.html" in url:
            return press
        if "gnews" in url or "ECB+Governing" in url:
            return gnews
        return None

    agreed = mc._best_ecb_mirror_agreement(getter)
    assert date(2026, 12, 12) in agreed


def test_opec_mirror_requires_overlap():
    a = mc._dates_from_rss_titles(
        "<title>OPEC ministerial meeting set for 5 March 2027</title>",
        keywords=("opec", "ministerial"),
    )
    b = mc._dates_from_rss_titles(
        "<title>OPEC conference date confirmed 5 March 2027</title>",
        keywords=("opec", "conference"),
    )
    assert mc.two_source_agreed_dates(a, b) == [date(2027, 3, 5)]


RSS = b"""<?xml version="1.0"?><rss><channel><item><title>Oil prices jump on OPEC cut talk</title><link>http://a/1</link>
<pubDate>%s</pubDate></item><item><title>No date item</title></item></channel></rss>"""


def test_parse_feed_rss_and_atom():
    from email.utils import format_datetime
    from architecture.markets.news_registry import parse_feed
    now = datetime.now(timezone.utc)
    items = parse_feed(RSS % format_datetime(now).encode())
    assert items[0]["title"].startswith("Oil") and items[0]["published"] is not None
    atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Gold hits record</title><link href="http://b"/><updated>2026-10-24T00:00:00Z</updated></entry></feed>'
    a = parse_feed(atom)
    assert a[0]["link"] == "http://b" and a[0]["published"].year == 2026


def test_live_newsroom_two_source_rule(tmp_path):
    from architecture.markets import news_registry as nr
    from architecture.markets.news_desk import build_live_newsroom
    now = datetime.now(timezone.utc)
    reg = {"sources": [
        {"id": "a", "category": "energy", "url": "u1", "domain": "a.com", "hosts": {"t": {"verified": True}}, "verified_any": True},
        {"id": "b", "category": "energy", "url": "u2", "domain": "b.com", "hosts": {"t": {"verified": True}}, "verified_any": True},
        {"id": "c", "category": "energy", "url": "u3", "domain": "c.com", "hosts": {"t": {"verified": False}}, "verified_any": False}]}
    _write(tmp_path, nr.OUT_REL, reg)
    feed = {"u1": [{"title": "Oil prices jump as OPEC weighs deeper output cut", "published": now}],
            "u2": [{"title": "OPEC weighs deeper output cut, oil prices jump", "published": now},
                   {"title": "Gold edges up in quiet trade", "published": now}]}
    live = build_live_newsroom(tmp_path, "t", fetch=lambda f: feed.get(f["url"], []))
    assert live["feeds_used"] == 2
    states = {s["headlineEn"][:4]: s["state"] for s in live["stories"]}
    assert "CORROBORATED" in states.values() and "SINGLE_SOURCE" in states.values()
