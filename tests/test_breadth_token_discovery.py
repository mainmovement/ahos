"""Trending pairs still stop at the safety veto. A blocked DexScreener body adds nothing."""
from datetime import datetime, timezone

from architecture.markets.token_safety_live import discover_candidates, run_discovery_funnel

ADDR = "0x1111111111111111111111111111111111111111"
POOL = "0x2222222222222222222222222222222222222222"
NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


def _gecko(url: str):
    if "trending_pools" not in url:
        return "<html>blocked</html>" if "dexscreener" in url else None
    return {"data": [{
        "attributes": {
            "name": "RUG / WETH", "address": POOL, "pool_created_at": "2026-01-01T00:00:00Z",
            "volume_usd": {"h24": "900000"}, "reserve_in_usd": "400000", "fdv_usd": "5000000",
            "transactions": {"h24": {"buys": 80, "sells": 20}},
        },
        "relationships": {"base_token": {"data": {"id": f"eth_{ADDR}"}}},
    }]}


def test_gecko_trending_keeps_flow_and_a_honeypot_is_not_tradable() -> None:
    found = discover_candidates(_gecko, now=NOW)
    row = next(item for item in found["passed"] if item.get("buys_24h") == 80)
    assert row["sells_24h"] == 20
    assert row["liquidity_usd"] == 400000.0
    assert row["pool_age_days"] > 7

    def blocked(url: str):
        body = _gecko(url)
        if "goplus" in url:
            return {"result": {ADDR.lower(): {"is_honeypot": "1", "buy_tax": "0.2", "sell_tax": "0.2"}}}
        return body

    vetted = run_discovery_funnel(blocked, now=NOW)["vetted"]
    assert vetted
    assert vetted[0]["paper_tradable"] is False
    assert vetted[0]["allowed"] is False


def test_a_dexscreener_pair_records_buys_and_html_does_not() -> None:
    def search(url: str):
        if "dex/search" not in url:
            return "<html>blocked</html>" if "dexscreener" in url else None
        return {"pairs": [{
            "chainId": "ethereum",
            "baseToken": {"address": ADDR, "symbol": "FLOW"},
            "pairAddress": POOL,
            "pairCreatedAt": 1_700_000_000_000,
            "volume": {"h24": 900000},
            "liquidity": {"usd": 400000},
            "fdv": 1_000_000,
            "txns": {"h24": {"buys": 11, "sells": 7}},
        }]}

    found = discover_candidates(search, now=NOW)
    row = next(item for item in found["passed"])
    assert row["source"] == "dexscreener_search"
    assert row["buys_24h"] == 11 and row["sells_24h"] == 7

    html = discover_candidates(lambda url: "<html>403</html>", now=NOW)
    assert html["passed"] == []
    assert html["raw_count"] == 0
