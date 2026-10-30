"""Per-desk news items from feeds this laptop could read. PAPER_ONLY.

Each source weight stays 0. A shadow sign needs two publishers on the same
side. The sign is logged and does not enter the entry gate. A missing
reliability stays null; the family scorecard's 24h hit rate is copied when it
exists and still does not change the weight.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from architecture.markets.news_desk import deduplicate_headlines
from architecture.markets.signal_brain import NEG, POS

SOURCE_WEIGHT = 0.0

# Publishers that failed from this laptop on 2026-10-30. They are not fetched.
DROPPED: dict[str, str] = {
    "ecb_press": "SSL certificate verify failed",
    "ecb_calendar": "SSL certificate verify failed",
    "kitco_rss": "HTTP 404",
    "opec_press": "SSL certificate verify failed",
    "reuters_rss": "HTTP 401",
    "yahoo_rssindex": "HTTP 404",
    "dexscreener_boosts": "HTTP 403",
    "dexscreener_profiles": "HTTP 403",
    "coingecko_new_coins": "HTTP 401",
    "pumpfun_api": "HTTP 403",
}

# EIA weekly page prints these clocks and does not print a weekday or timezone.
EIA_RELEASE_CLOCK = {
    "source": "eia",
    "text": "Released at 10:30 a.m. and 1:00 p.m.",
    "weekday": None,
    "timezone": None,
    "url": "https://www.eia.gov/petroleum/supply/weekly/",
}

SYMBOL_TERMS: dict[str, str] = {
    "BTC": r"bitcoin|\bbtc\b",
    "ETH": r"ethereum|\beth\b",
    "SOL": r"solana|\bsol\b",
    "XAU": r"\bgold\b|bullion",
    "GC": r"\bgold\b|bullion",
    "WTI": r"\bwti\b|\bcrude\b",
    "BRENT": r"\bbrent\b",
    "CL": r"\bwti\b|\bcrude\b",
    "BZ": r"\bbrent\b",
    "SPX": r"s&p|spx|s&p 500",
    "NDX": r"nasdaq|\bndx\b",
    "QQQ": r"\bqqq\b|nasdaq",
    "ES": r"s&p|spx|s&p 500",
    "NQ": r"nasdaq|\bndx\b",
    "DAX": r"\bdax\b",
    "N225": r"nikkei",
    "HSI": r"hang seng|hong kong",
    "NKD": r"nikkei",
    "EURUSD": r"\beuro\b|\beur\b",
    "USDJPY": r"\byen\b|bank of japan|\bboj\b",
}

DESK_SYMBOLS: dict[str, tuple[str, ...]] = {
    "GOLD": ("XAU", "GC"),
    "OIL": ("WTI", "BRENT", "CL", "BZ"),
    "US_EQUITIES": ("SPX", "NDX", "QQQ", "ES", "NQ"),
    "EU_EQUITIES": ("DAX",),
    "ASIA_EQUITIES": ("N225", "HSI", "NKD"),
    "FOREX": ("EURUSD", "USDJPY"),
    "CRYPTO": ("BTC", "ETH", "SOL"),
    "CRYPTO_FUTURES": ("BTC", "ETH", "SOL"),
    "PB_TOKEN": (),
}

FEEDS: list[dict[str, Any]] = [
    {"id": "fed_press", "publisher": "federalreserve", "kind": "rss",
     "desks": ("GOLD", "US_EQUITIES", "FOREX"),
     "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
    {"id": "fed_monetary", "publisher": "federalreserve", "kind": "rss",
     "desks": ("GOLD", "US_EQUITIES", "FOREX"),
     "url": "https://www.federalreserve.gov/feeds/press_monetary.xml"},
    {"id": "boj", "publisher": "boj", "kind": "rss",
     "desks": ("GOLD", "ASIA_EQUITIES", "FOREX"),
     "url": "https://www.boj.or.jp/en/rss/whatsnew.xml"},
    {"id": "fxstreet", "publisher": "fxstreet", "kind": "rss",
     "desks": ("GOLD", "FOREX"),
     "url": "https://www.fxstreet.com/rss/news"},
    {"id": "oilprice", "publisher": "oilprice", "kind": "rss",
     "desks": ("OIL",), "url": "https://oilprice.com/rss/main"},
    {"id": "rigzone", "publisher": "rigzone", "kind": "rss",
     "desks": ("OIL",), "url": "https://www.rigzone.com/news/rss/rigzone_latest.aspx"},
    {"id": "eia_press", "publisher": "eia", "kind": "rss",
     "desks": ("OIL",), "url": "https://www.eia.gov/rss/press_rss.xml"},
    {"id": "eia_today", "publisher": "eia", "kind": "rss",
     "desks": ("OIL",), "url": "https://www.eia.gov/rss/todayinenergy.xml"},
    {"id": "cnbc", "publisher": "cnbc", "kind": "rss",
     "desks": ("US_EQUITIES", "EU_EQUITIES", "ASIA_EQUITIES"),
     "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"id": "marketwatch", "publisher": "marketwatch", "kind": "rss",
     "desks": ("US_EQUITIES", "EU_EQUITIES"),
     "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"id": "nikkei", "publisher": "nikkei", "kind": "rss",
     "desks": ("ASIA_EQUITIES",),
     "url": "https://asia.nikkei.com/rss/feed/nar"},
    {"id": "yahoo_spx", "publisher": "yahoo", "kind": "rss",
     "desks": ("US_EQUITIES",),
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US"},
    {"id": "yahoo_ndx", "publisher": "yahoo", "kind": "rss",
     "desks": ("US_EQUITIES",),
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5ENDX&region=US&lang=en-US"},
    {"id": "yahoo_dax", "publisher": "yahoo", "kind": "rss",
     "desks": ("EU_EQUITIES",),
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGDAXI&region=US&lang=en-US"},
    {"id": "yahoo_n225", "publisher": "yahoo", "kind": "rss",
     "desks": ("ASIA_EQUITIES",),
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EN225&region=US&lang=en-US"},
    {"id": "coindesk", "publisher": "coindesk", "kind": "rss",
     "desks": ("CRYPTO", "CRYPTO_FUTURES"),
     "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"id": "cointelegraph", "publisher": "cointelegraph", "kind": "rss",
     "desks": ("CRYPTO", "CRYPTO_FUTURES"),
     "url": "https://cointelegraph.com/rss"},
    {"id": "theblock", "publisher": "theblock", "kind": "rss",
     "desks": ("CRYPTO", "CRYPTO_FUTURES"),
     "url": "https://www.theblock.co/rss.xml"},
    {"id": "decrypt", "publisher": "decrypt", "kind": "rss",
     "desks": ("CRYPTO", "CRYPTO_FUTURES"),
     "url": "https://decrypt.co/feed"},
    {"id": "binance_listings", "publisher": "binance", "kind": "binance",
     "desks": ("PB_TOKEN",),
     "url": "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=48&pageNo=1&pageSize=10"},
    {"id": "okx_listings", "publisher": "okx", "kind": "okx",
     "desks": ("PB_TOKEN",),
     "url": "https://www.okx.com/api/v5/support/announcements?annType=announcements-new-listings"},
    {"id": "gecko_new_pools", "publisher": "geckoterminal", "kind": "gecko",
     "desks": ("PB_TOKEN",),
     "url": "https://api.geckoterminal.com/api/v2/networks/eth/new_pools?page=1"},
    {"id": "telegram_binance", "publisher": "binance", "kind": "telegram",
     "desks": ("PB_TOKEN",),
     "url": "https://t.me/s/binance_announcements"},
    {"id": "telegram_okx", "publisher": "okx", "kind": "telegram",
     "desks": ("PB_TOKEN",),
     "url": "https://t.me/s/OKXAnnouncements"},
]

_POS = re.compile(POS, re.I)
_NEG = re.compile(NEG, re.I)
_ITEM = re.compile(r"<item[\s>].*?</item>", re.S | re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
_DATE = re.compile(r"<pubDate[^>]*>(.*?)</pubDate>|<dc:date[^>]*>(.*?)</dc:date>", re.S | re.I)
_TAG = re.compile(r"<!\[CDATA\[|\]\]>|<[^>]+>")


def sentiment_score(title: str) -> int:
    """Keyword sign. A title with both sides, or neither, is 0."""
    pos = _POS.search(title) is not None
    neg = _NEG.search(title) is not None
    if pos == neg:
        return 0
    return 1 if pos else -1


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub("", text)).strip()


def _epoch(raw: str | None) -> float | None:
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def _symbols(title: str, desks: tuple[str, ...]) -> list[str]:
    if desks == ("PB_TOKEN",):
        found = re.findall(r"\(([A-Z][A-Z0-9]{1,14})\)", title)
        if not found and " / " in title:
            head = title.split(" / ", 1)[0].strip()
            if re.fullmatch(r"[A-Z0-9]{2,15}", head):
                found = [head]
        return found[:5]
    allowed = [sym for desk in desks for sym in DESK_SYMBOLS.get(desk, ())]
    found = []
    for sym in allowed:
        if re.search(SYMBOL_TERMS[sym], title, re.I) and sym not in found:
            found.append(sym)
    return found


def _row(feed: dict[str, Any], title: str, ts: float | None) -> dict[str, Any]:
    return {
        "source": feed["publisher"],
        "feed": feed["id"],
        "title": title,
        "ts": ts,
        "desks": list(feed["desks"]),
        "symbols": _symbols(title, feed["desks"]),
        "sentiment": sentiment_score(title),
        "source_weight": SOURCE_WEIGHT,
        "counts_toward_entry_gate": False,
        "listing": feed["desks"] == ("PB_TOKEN",),
    }


def parse_rss(feed: dict[str, Any], xml: str) -> list[dict[str, Any]]:
    rows = []
    for block in _ITEM.findall(xml)[:40]:
        title_m = _TITLE.search(block)
        if not title_m:
            continue
        date_m = _DATE.search(block)
        raw = None
        if date_m:
            raw = date_m.group(1) or date_m.group(2)
        rows.append(_row(feed, _clean(title_m.group(1)), _epoch(raw)))
    return rows


def parse_binance(feed: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    articles = ((payload.get("data") or {}).get("articles") or []) if isinstance(payload, dict) else []
    rows = []
    for art in articles[:20]:
        if not isinstance(art, dict) or not art.get("title"):
            continue
        ts = _epoch(str(art.get("publishDate"))) if art.get("publishDate") else None
        if isinstance(art.get("publishDate"), (int, float)):
            ts = float(art["publishDate"]) / 1000.0 if art["publishDate"] > 1e12 else float(art["publishDate"])
        rows.append(_row(feed, str(art["title"]), ts))
    return rows


def parse_okx(feed: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for group in (payload.get("data") or []) if isinstance(payload, dict) else []:
        for detail in (group.get("details") or []) if isinstance(group, dict) else []:
            if not isinstance(detail, dict) or not detail.get("title"):
                continue
            raw = detail.get("pTime")
            ts = None
            if isinstance(raw, (int, float)):
                ts = float(raw) / 1000.0 if raw > 1e12 else float(raw)
            rows.append(_row(feed, str(detail["title"]), ts))
    return rows


def parse_gecko(feed: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for pool in (payload.get("data") or []) if isinstance(payload, dict) else []:
        attr = pool.get("attributes") if isinstance(pool, dict) else None
        if not isinstance(attr, dict) or not attr.get("name"):
            continue
        rows.append(_row(feed, str(attr["name"]), _epoch(str(attr.get("pool_created_at") or ""))))
    return rows


def parse_telegram(feed: dict[str, Any], html: str) -> list[dict[str, Any]]:
    times = re.findall(r'datetime="([^"]+)"', html)
    texts = re.findall(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.S)
    rows = []
    for raw_time, raw_text in zip(times, texts):
        title = _clean(raw_text)
        if title:
            rows.append(_row(feed, title, _epoch(raw_time)))
    return rows


def _parse_feed(feed: dict[str, Any], body: str) -> list[dict[str, Any]]:
    kind = feed["kind"]
    if kind == "rss":
        return parse_rss(feed, body)
    if kind == "telegram":
        return parse_telegram(feed, body)
    try:
        import json
        payload = json.loads(body)
    except ValueError:
        return []
    if kind == "binance":
        return parse_binance(feed, payload)
    if kind == "okx":
        return parse_okx(feed, payload)
    if kind == "gecko":
        return parse_gecko(feed, payload)
    return []


def dedup_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = deduplicate_headlines(items)
    for row in kept:
        row["novelty"] = True
    return kept


def reliability_from_scorecard(scorecard: dict[str, Any] | None) -> dict[str, Any]:
    cell = (((scorecard or {}).get("families") or {}).get("news") or {}).get("24h") or {}
    hits = int(cell.get("hits") or 0)
    misses = int(cell.get("misses") or 0)
    rate = cell.get("hit_rate")
    learned = rate if isinstance(rate, (int, float)) and not isinstance(rate, bool) and hits + misses > 0 else None
    return {"hit_rate_24h": learned, "resolved": hits + misses, "source_weight": SOURCE_WEIGHT}


def shadow_sign(items: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    """Two different publishers, same nonzero sign. One publisher is flat."""
    by_pub: dict[str, int] = {}
    for row in items:
        if symbol not in row.get("symbols", []) or row.get("listing"):
            continue
        sign = int(row.get("sentiment") or 0)
        if sign == 0:
            continue
        prev = by_pub.get(row["source"])
        if prev is None:
            by_pub[row["source"]] = sign
        elif prev != sign:
            by_pub[row["source"]] = 0
    longs = sorted(pub for pub, sign in by_pub.items() if sign > 0)
    shorts = sorted(pub for pub, sign in by_pub.items() if sign < 0)
    if len(longs) >= 2 and not shorts:
        side, pubs = "LONG", longs
    elif len(shorts) >= 2 and not longs:
        side, pubs = "SHORT", shorts
    else:
        side, pubs = "FLAT", sorted(pub for pub, sign in by_pub.items() if sign)
    return {
        "symbol": symbol,
        "sign": side,
        "publishers": pubs,
        "source_weight": SOURCE_WEIGHT,
        "counts_toward_entry_gate": False,
    }


def pump_news_block(vote_audit: dict[str, Any], safety: dict[str, Any] | None) -> str | None:
    """Listing or news sentiment cannot open a pump token by itself."""
    votes = vote_audit.get("votes") or []
    news_agrees = any(v.get("family") == "news" and v.get("vote") == "AGREE" for v in votes)
    others = [v for v in votes if v.get("family") != "news" and v.get("vote") == "AGREE"]
    if not news_agrees:
        return None
    if not others:
        return "PUMP_NEWS_ALONE"
    if not (isinstance(safety, dict) and safety.get("allowed") is True):
        return "PUMP_NEWS_NEEDS_SAFETY"
    return None


def attach_latency(item: dict[str, Any], *, price_ts: float | None, price: float | None, later_price: float | None) -> dict[str, Any]:
    out = dict(item)
    ts = item.get("ts")
    if isinstance(ts, (int, float)) and isinstance(price_ts, (int, float)):
        out["latency_s"] = round(float(price_ts) - float(ts), 1)
    else:
        out["latency_s"] = None
    if isinstance(price, (int, float)) and isinstance(later_price, (int, float)) and price:
        out["price_move_pct"] = round((float(later_price) - float(price)) / float(price) * 100.0, 4)
    else:
        out["price_move_pct"] = None
    return out


def items_from_bodies(bodies: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feed in FEEDS:
        body = bodies.get(feed["id"])
        if body:
            rows.extend(_parse_feed(feed, body))
    return dedup_items(rows)


def _with_latency(items: list[dict[str, Any]], quotes: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not quotes:
        return items
    out = []
    for item in items:
        quote = None
        for sym in item.get("symbols") or []:
            if isinstance(quotes.get(sym), dict):
                quote = quotes[sym]
                break
        if quote is None:
            out.append(item)
            continue
        out.append(attach_latency(
            item,
            price_ts=_epoch(str(quote.get("market_time") or "")) if quote.get("market_time") else None,
            price=quote.get("price") if isinstance(quote.get("price"), (int, float)) else None,
            later_price=None,
        ))
    return out


def load_live_snapshot(
    root: Any = None,
    quotes: dict[str, Any] | None = None,
    getter: Any = None,
    scorecard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch the verified feeds. A dead feed is skipped. Weights stay 0."""
    import concurrent.futures as cf
    import json
    from pathlib import Path

    fetch = getter or _live_get
    bodies: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(fetch, feed["url"]): feed["id"] for feed in FEEDS}
        for fut in cf.as_completed(future_map):
            body = fut.result()
            if isinstance(body, str) and body:
                bodies[future_map[fut]] = body
    if scorecard is None and root is not None:
        path = Path(root) / "reports" / "grok" / "PAPER" / "weekly_family_vote_scorecard.json"
        try:
            if path.is_file():
                scorecard = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            scorecard = None
    doc = build_snapshot(bodies, scorecard)
    doc["items"] = _with_latency(doc["items"], quotes)
    return doc


def _live_get(url: str) -> str | None:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AHOS paper research)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read(200_000).decode("utf-8", "replace")
    except Exception:
        return None


def build_snapshot(bodies: dict[str, str], scorecard: dict[str, Any] | None = None) -> dict[str, Any]:
    items = items_from_bodies(bodies)
    symbols = sorted({
        sym for row in items if not row.get("listing") for sym in row.get("symbols") or []
    })
    return {
        "schema": "ahos.desk_news.v1",
        "paper_only": True,
        "source_weight": SOURCE_WEIGHT,
        "counts_toward_entry_gate": False,
        "dropped": DROPPED,
        "eia_release_clock": EIA_RELEASE_CLOCK,
        "reliability": reliability_from_scorecard(scorecard),
        "items": items,
        "shadow_signs": [shadow_sign(items, sym) for sym in symbols],
    }
