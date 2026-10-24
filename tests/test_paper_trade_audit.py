from __future__ import annotations

import json
from pathlib import Path

from architecture.markets import paper_trader as pt
from architecture.markets.paper_trade_audit import audit_paper_trades_jsonl, export_paper_trade_audit_snapshot


def _bars(start: float, step: float, n: int = 40):
    out, p = [], start
    for _ in range(n):
        out.append([p, p + step * 1.2 if step > 0 else p + 0.01, p - 0.01 if step > 0 else p + step * 1.2, p + step, 10.0])
        p += step
    return out


def _sig(score: float):
    return lambda sym, desk, q: [
        {"name": "mtf_trend", "score": score, "available": True, "source": "fx", "spec": "§2", "evidence": {"higher_tf_sign": 1 if score > 0 else -1}}
    ]


def test_audit_green_after_real_close(tmp_path: Path) -> None:
    import time

    t = [1_800_000_000.0]
    px = {"p": 120.0}
    mt = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t[0]))
    fetch = lambda: {
        "quotes": {
            "BTC": {"price": px["p"], "source": "A", "market_time": mt(), "ohlcv_5m": _bars(100, 0.5)},
        }
    }
    fb = lambda: {"BTC": {"price": px["p"], "source": "B"}}
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    t[0] += 300
    px["p"] = 130.0
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    aud = audit_paper_trades_jsonl(tmp_path)
    assert aud["status"] == "GREEN"
    assert aud["closes"] >= 1
    snap = export_paper_trade_audit_snapshot(tmp_path)
    assert snap["status"] == "GREEN"
    assert (tmp_path / "reports/grok/PAPER/paper_trade_audit.json").is_file()


def test_audit_empty_is_green(tmp_path: Path) -> None:
    aud = audit_paper_trades_jsonl(tmp_path)
    assert aud["status"] == "GREEN" and aud["closes"] == 0
