"""On-chain whale and exchange-flow data from FREE public APIs (no keys). PAPER_ONLY.

  exchange flows : Coin Metrics community API (FlowInExNtv / FlowOutExNtv / SplyExNtv, daily, btc+eth).
                   Values for day d are published with a lag; we only use a value from d+LAG_DAYS 00:00 UTC
                   (causal in backtests, honest live).
  whale mempool  : blockchain.info unconfirmed-transactions (BTC transfers >= WHALE_BTC).
  stablecoins    : DefiLlama stablecoincharts/all (total USD-pegged supply, daily).
"""
from __future__ import annotations

import json
import statistics
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

UA = {"User-Agent": "Mozilla/5.0 (AHOS on-chain)"}
CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
LAG_DAYS = 2
WHALE_BTC = 100.0


def _json(url: str, timeout: float = 25.0) -> Any:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def exchange_flows_history(asset: str, start: str = "2019-01-01") -> list[dict[str, Any]]:
    """[{date, inflow, outflow, netflow, exchange_supply, usable_from_utc}] oldest first (native units)."""
    out, url = [], f"{CM}?assets={asset}&metrics=FlowInExNtv,FlowOutExNtv,SplyExNtv&frequency=1d&start_time={start}&page_size=10000"
    while url:
        d = _json(url)
        if not d:
            break
        for r in d.get("data") or []:
            if r.get("FlowInExNtv") is None or r.get("FlowOutExNtv") is None:
                continue
            day = datetime.strptime(r["time"][:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            fi, fo = float(r["FlowInExNtv"]), float(r["FlowOutExNtv"])
            out.append({"date": r["time"][:10], "inflow": fi, "outflow": fo, "netflow": fi - fo,
                        "exchange_supply": float(r["SplyExNtv"]) if r.get("SplyExNtv") else None,
                        "usable_from_ts": (day + timedelta(days=LAG_DAYS)).timestamp()})
        url = d.get("next_page_url")
    return out


def netflow_z(hist: list[dict[str, Any]], now_ts: float, window: int = 90) -> tuple[float | None, dict[str, Any] | None]:
    known = [h for h in hist if h["usable_from_ts"] <= now_ts]
    if len(known) < window + 1:
        return None, None
    w = [h["netflow"] for h in known[-window - 1:-1]]
    sd = statistics.pstdev(w) or 1e-12
    return (known[-1]["netflow"] - statistics.fmean(w)) / sd, known[-1]


def whale_mempool(min_btc: float = WHALE_BTC) -> dict[str, Any] | None:
    d = _json("https://blockchain.info/unconfirmed-transactions?format=json")
    if not d:
        return None
    big = []
    for t in d.get("txs") or []:
        v = sum(o.get("value", 0) for o in t.get("out") or []) / 1e8
        if v >= min_btc:
            big.append({"hash": t.get("hash"), "btc": round(v, 2)})
    return {"sampled_txs": len(d.get("txs") or []), "whale_txs": big, "min_btc": min_btc}


def stablecoin_supply_history() -> list[dict[str, Any]]:
    d = _json("https://stablecoins.llama.fi/stablecoincharts/all") or []
    out = []
    for r in d:
        try:
            out.append({"date": datetime.fromtimestamp(int(r["date"]), timezone.utc).strftime("%Y-%m-%d"),
                        "usd": float(r["totalCirculatingUSD"]["peggedUSD"]),
                        "usable_from_ts": int(r["date"]) + 86400})
        except (KeyError, TypeError, ValueError):
            continue
    return out
