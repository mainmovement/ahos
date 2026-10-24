"""M18.N & M80 Part A (Didehban) OSINT news desk.
One source is UNKNOWN. Disagreement is CONFLICT. >=2 independent domains required for CORROBORATED.
Includes Asi's M80 v2 credibility/recency/priority math and SimHash deduplication.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class NewsView:
    state: str
    claim: str | None


@dataclass(frozen=True, slots=True)
class OsintClusterResult:
    state: str
    claim: str | None
    independent_domains: tuple[str, ...]
    credibility: float
    recency: float
    priority: float
    taint_labels: tuple[str, ...]
    injection_sanitized: bool


_INJECTION_RE = re.compile(
    r"(?:ignore\s+previous\s+instructions|disregard\s+everything|bypass\s+your\s+rules|act\s+as\s+root|execute\s+this\s+code|place\s+live\s+order)",
    re.IGNORECASE,
)


def corroborate(items: list[tuple[str, str]]) -> NewsView:
    if len({source for source, _claim in items}) < 2:
        return NewsView("UNKNOWN", None)
    claims = {claim for _source, claim in items}
    if len(claims) != 1:
        return NewsView("CONFLICT", None)
    return NewsView("CORROBORATED", next(iter(claims)))


def credibility_score(source_reliabilities: Sequence[float]) -> float:
    """Asi M80 v2 formula: C = 1 - prod_j (1 - r_j)."""
    if not source_reliabilities:
        return 0.0
    prod_complement = 1.0
    for r in source_reliabilities:
        clamped = max(0.0, min(1.0, float(r)))
        prod_complement *= 1.0 - clamped
    return round(1.0 - prod_complement, 6)


def recency_score(age_seconds: float, half_life_seconds: float = 14400.0) -> float:
    """Asi M80 v2 formula: R = exp(-lambda * dt), where lambda = ln(2) / half_life."""
    if half_life_seconds <= 0:
        return 0.0
    dt = max(0.0, float(age_seconds))
    lam = math.log(2.0) / float(half_life_seconds)
    return round(math.exp(-lam * dt), 6)


def priority_score(
    source_reliabilities: Sequence[float],
    age_seconds: float,
    impact: float,
    half_life_seconds: float = 14400.0,
) -> float:
    """Asi M80 v2 formula: Priority = C * R * I."""
    c = credibility_score(source_reliabilities)
    r = recency_score(age_seconds, half_life_seconds=half_life_seconds)
    i = max(0.0, min(1.0, float(impact)))
    return round(c * r * i, 6)


def simhash_64(text: str) -> int:
    """Deterministic 64-bit SimHash over normalized word shingles."""
    tokens = re.findall(r"[a-z0-9؀-ۿ]+", text.lower())
    if not tokens:
        return 0
    weights = [0] * 64
    for tok in tokens:
        digest = hashlib.md5(tok.encode("utf-8")).digest()
        h = int.from_bytes(digest[:8], "big")
        for bit in range(64):
            if (h >> bit) & 1:
                weights[bit] += 1
            else:
                weights[bit] -= 1
    out = 0
    for bit in range(64):
        if weights[bit] > 0:
            out |= 1 << bit
    return out


def hamming_distance_64(a: int, b: int) -> int:
    return ((a ^ b) & ((1 << 64) - 1)).bit_count()


def deduplicate_headlines(items: Sequence[dict[str, Any]], max_hamming: int = 6) -> list[dict[str, Any]]:
    """Deduplicate near-identical headlines using 64-bit SimHash."""
    kept: list[dict[str, Any]] = []
    hashes: list[int] = []
    for item in items:
        text = str(item.get("headline") or item.get("title") or item.get("summary") or "")
        sh = simhash_64(text)
        if any(hamming_distance_64(sh, existing) <= max_hamming for existing in hashes):
            continue
        hashes.append(sh)
        kept.append({**item, "simhash": f"{sh:016x}"})
    return kept


def _extract_domain(source: str) -> str:
    s = source.strip().lower()
    if "://" in s:
        return urlparse(s).hostname or s
    return s.split("/")[0]


def sanitize_untrusted_headline(text: str) -> tuple[str, bool]:
    """Treat all external OSINT text purely as data; strip/neutralize prompt-injection directives."""
    if _INJECTION_RE.search(text):
        cleaned = _INJECTION_RE.sub("[SANITIZED_UNTRUSTED_TEXT]", text)
        return cleaned, True
    return text, False


def evaluate_osint_cluster(
    reports: Sequence[dict[str, Any]],
    *,
    age_seconds: float = 600.0,
    impact: float = 0.8,
) -> OsintClusterResult:
    """Evaluate a cluster of OSINT reports under the strict Two-Source Witness Law."""
    domains: list[str] = []
    claims: set[str] = set()
    reliabilities: list[float] = []
    sanitized_any = False

    for rep in reports:
        src = _extract_domain(str(rep.get("source") or rep.get("domain") or ""))
        raw_claim = str(rep.get("claim") or rep.get("direction") or "").strip()
        clean_claim, was_inj = sanitize_untrusted_headline(raw_claim)
        if was_inj:
            sanitized_any = True
        raw_title = str(rep.get("headline") or "")
        _, was_title_inj = sanitize_untrusted_headline(raw_title)
        if was_title_inj:
            sanitized_any = True
        if src:
            if src not in domains:
                domains.append(src)
                reliabilities.append(float(rep.get("reliability", 0.75)))
        if clean_claim:
            claims.add(clean_claim)

    c = credibility_score(reliabilities)
    r = recency_score(age_seconds)
    p = priority_score(reliabilities, age_seconds, impact)
    taint = ("UNTRUSTED_OSINT_DATA", "INJECTION_NEUTRALIZED") if sanitized_any else ("UNTRUSTED_OSINT_DATA",)

    if len(domains) < 2:
        return OsintClusterResult(
            state="UNKNOWN",
            claim=None,
            independent_domains=tuple(domains),
            credibility=c,
            recency=r,
            priority=p,
            taint_labels=taint,
            injection_sanitized=sanitized_any,
        )
    if len(claims) != 1:
        return OsintClusterResult(
            state="CONFLICT",
            claim=None,
            independent_domains=tuple(domains),
            credibility=c,
            recency=r,
            priority=p,
            taint_labels=taint,
            injection_sanitized=sanitized_any,
        )
    return OsintClusterResult(
        state="CORROBORATED",
        claim=next(iter(claims)),
        independent_domains=tuple(domains),
        credibility=c,
        recency=r,
        priority=p,
        taint_labels=taint,
        injection_sanitized=sanitized_any,
    )


def ingest_rss_feeds(
    feed_xmls_or_fixtures: Sequence[dict[str, Any] | str] | None = None,
) -> list[dict[str, Any]]:
    """M18: Parse and corroborate multi-source RSS/Atom feed items or structured feed fixtures.
    Sanitizes all untrusted text, deduplicates via 64-bit SimHash, and groups by topic/claim
    to enforce the Two-Source Witness Law.
    """
    import xml.etree.ElementTree as ET

    raw_entries: list[dict[str, Any]] = []
    if feed_xmls_or_fixtures is None:
        raw_entries = [
            {
                "source": "https://fred.stlouisfed.org/feeds/gold",
                "topic": "GOLD",
                "claim": "gold_two_source_steady",
                "headline": "Gold spot and COMEX futures maintain two-source witness parity",
                "reliability": 0.90,
            },
            {
                "source": "https://finance.yahoo.com/rss/commodities",
                "topic": "GOLD",
                "claim": "gold_two_source_steady",
                "headline": "COMEX Gold futures corroborate spot bullion witness within 5 bps",
                "reliability": 0.86,
            },
            {
                "source": "https://www.eia.gov/rss/petroleum.xml",
                "topic": "OIL",
                "claim": "wti_inventory_draw_paper",
                "headline": "EIA weekly petroleum report shows crude draw on WTI paper track",
                "reliability": 0.92,
            },
            {
                "source": "https://fred.stlouisfed.org/feeds/oil",
                "topic": "OIL",
                "claim": "wti_inventory_draw_paper",
                "headline": "FRED DCOILWTICO corroborates EIA WTI crude reference price",
                "reliability": 0.90,
            },
            {
                "source": "https://www.ecb.europa.eu/rss/fx.xml",
                "topic": "MACRO",
                "claim": "fx_rates_corroborated",
                "headline": "ECB euro reference rates align with FRED macro FX series",
                "reliability": 0.91,
            },
            {
                "source": "https://stooq.com/rss/fx",
                "topic": "MACRO",
                "claim": "fx_rates_corroborated",
                "headline": "Stooq FX feed confirms EURUSD and USDJPY reference parity",
                "reliability": 0.85,
            },
        ]
    else:
        for entry in feed_xmls_or_fixtures:
            if isinstance(entry, str) and entry.lstrip().startswith("<"):
                try:
                    root = ET.fromstring(entry)
                    for item in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                        t1 = item.find("title")
                        title_el = t1 if t1 is not None else item.find("{http://www.w3.org/2005/Atom}title")
                        l1 = item.find("link")
                        link_el = l1 if l1 is not None else item.find("{http://www.w3.org/2005/Atom}link")
                        cat_el = item.find("category")
                        title_txt = (title_el.text if title_el is not None and title_el.text else "").strip()
                        link_txt = (
                            (link_el.text if link_el is not None and link_el.text else "")
                            or (link_el.attrib.get("href", "") if link_el is not None else "")
                        ).strip()
                        topic_txt = (cat_el.text if cat_el is not None and cat_el.text else "MACRO").strip().upper()
                        raw_entries.append(
                            {
                                "source": link_txt or "rss.local",
                                "topic": topic_txt,
                                "claim": topic_txt.lower() + "_rss_claim",
                                "headline": title_txt,
                                "reliability": 0.80,
                            }
                        )
                except ET.ParseError:
                    continue
            elif isinstance(entry, dict):
                raw_entries.append(dict(entry))

    sanitized_entries: list[dict[str, Any]] = []
    for item in raw_entries:
        clean_h, was_inj = sanitize_untrusted_headline(str(item.get("headline") or item.get("title") or ""))
        sanitized_entries.append({**item, "headline": clean_h, "injection_sanitized": was_inj})

    deduped = deduplicate_headlines(sanitized_entries, max_hamming=6)
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for d in deduped:
        t = str(d.get("topic") or "MACRO").upper()
        by_topic.setdefault(t, []).append(d)

    clusters: list[dict[str, Any]] = []
    for topic, group in by_topic.items():
        res = evaluate_osint_cluster(group, age_seconds=450.0, impact=0.85)
        clusters.append(
            {
                "topic": topic,
                "state": res.state,
                "claim": res.claim,
                "independent_domains": list(res.independent_domains),
                "credibility": res.credibility,
                "recency": res.recency,
                "priority": res.priority,
                "headlines": [g["headline"] for g in group],
                "paper_only": True,
            }
        )
    return clusters


def build_nightly_news_brief_fa(stories: Sequence[dict[str, Any]]) -> str:
    """M18: Generate the deterministic Persian nightly newsroom brief from corroborated stories."""
    if not stories:
        return "گزارش شبانهٔ دیده‌بان (M18): هیچ خبر دو‌منبعی تأییدشده‌ای در این چرخه ثبت نشد (PAPER_ONLY)."
    corroborated = [
        s for s in stories if str(s.get("state") or s.get("claimStrength") or "") in {"CORROBORATED", "STRONG", "MODERATE", "LIVE"}
    ]
    lines = [
        "گزارش شبانهٔ اتاق خبر دیده‌بان (M18 · صرفاً کاغذی / PAPER_ONLY):",
        f"- تعداد کل خوشه‌های بررسی‌شده: {len(stories)} | تأییدشده با حداقل دو منبع مستقل: {len(corroborated)}",
    ]
    for s in stories[:5]:
        topic = s.get("topic") or s.get("market") or "GLOBAL"
        headline = s.get("headlineFa") or (s.get("headlines") or [s.get("claim") or ""])[0]
        state = s.get("state") or s.get("status") or "UNKNOWN"
        lines.append(f"- [{topic}] ({state}): {headline}")
    return "\n".join(lines)


# ============================ Stage 3: LIVE newsroom from the verified registry ============================
TOPIC_FA = {"CRYPTO": "رمزارز", "GOLD": "طلا", "OIL": "نفت", "US_EQUITIES": "سهام آمریکا", "EU_EQUITIES": "سهام اروپا",
            "ASIA_EQUITIES": "سهام آسیا", "FOREX": "ارز", "MACRO": "اقتصاد کلان"}
_STOP = set("a an the of to in on for and or with at by from as is are be was were after amid over into its it this that new says say said will may could us u.s. than more".split())


def _publisher(item: dict[str, Any], feed_domain: str) -> str:
    """Independent-source key. Aggregators (news.google.com) -> the publisher named after ' - ' in the title."""
    if "news.google.com" in feed_domain and " - " in item.get("title", ""):
        return "gnews:" + item["title"].rsplit(" - ", 1)[-1].strip().lower()
    return feed_domain


def _tokens(title: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9$%.]+", title.lower()) if len(w) > 2 and w not in _STOP}


def build_live_newsroom(root: Any, host: str, *, max_feeds: int = 90, max_age_h: float = 24.0,
                        fetch: Any = None) -> dict[str, Any]:
    """Fetch verified feeds for this host, tag topics, cluster near-duplicate headlines, and mark a story
    CORROBORATED only when >= 2 independent publishers carry it (Two-Source Witness Law). No invented items."""
    import concurrent.futures as cf
    from datetime import datetime, timezone
    from architecture.markets import news_registry as nr
    from architecture.markets.signal_brain import ASSET_TERMS

    feeds = nr.verified_feeds(root, host)[:max_feeds]
    fetch = fetch or (lambda f: nr.parse_feed(urllib_get(f["url"])))
    now = datetime.now(timezone.utc)
    items: list[dict[str, Any]] = []
    errors = 0

    def one(f):
        try:
            return f, fetch(f)
        except Exception:
            return f, None
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for f, got in ex.map(one, feeds):
            if got is None:
                errors += 1
                continue
            for it in got:
                pub = it.get("published")
                if not pub or (now - pub).total_seconds() > max_age_h * 3600:
                    continue
                title, inj = sanitize_untrusted_headline(it["title"])
                topics = [t for t, rx in ASSET_TERMS.items() if re.search(rx, title, re.I)] or (["MACRO"] if f["category"] in ("macro", "central_bank", "official") else [])
                if not topics:
                    continue
                items.append({"title": title, "link": it.get("link"), "published": pub, "feed": f["id"],
                              "publisher": _publisher(it, f["domain"]), "category": f["category"], "topics": topics,
                              "tokens": _tokens(title), "injection_stripped": inj})
    clusters: list[dict[str, Any]] = []
    for it in sorted(items, key=lambda x: x["published"], reverse=True):
        for c in clusters:
            if set(it["topics"]) & set(c["topics"]):
                inter = len(it["tokens"] & c["tokens"])
                if inter >= 3 and inter / max(1, len(it["tokens"] | c["tokens"])) >= 0.3:
                    c["items"].append(it); c["publishers"].add(it["publisher"]); break
        else:
            clusters.append({"topics": list(it["topics"]), "tokens": set(it["tokens"]), "items": [it], "publishers": {it["publisher"]}})
    stories, rss_clusters, center = [], [], []
    for k, c in enumerate(sorted(clusters, key=lambda c: (-len(c["publishers"]), -c["items"][0]["published"].timestamp()))):
        lead = c["items"][0]
        n_pub = len(c["publishers"])
        state = "CORROBORATED" if n_pub >= 2 else "SINGLE_SOURCE"
        age_s = (now - lead["published"]).total_seconds()
        ev = evaluate_osint_cluster([{"source": p, "claim": lead["title"], "reliability": 0.8} for p in sorted(c["publishers"])],
                                    age_seconds=age_s, impact=0.7)
        topic = c["topics"][0]
        stories.append({"id": f"live-{k}", "headlineEn": lead["title"], "headlineFa": f"{TOPIC_FA.get(topic, topic)}: {lead['title']}",
                        "market": topic, "publishedAt": lead["published"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "claimStrength": "STRONG" if n_pub >= 3 else "MODERATE" if n_pub == 2 else "WEAK",
                        "state": state, "sourceIds": sorted(c["publishers"])[:8], "links": [i["link"] for i in c["items"][:4]],
                        "marketImpactNoteFa": f"{n_pub} ناشر مستقل · اعتبار C={ev.credibility:.2f}", "demo": False,
                        "status": "LIVE" if age_s < 6 * 3600 else "STALE", "conflictId": None})
        rss_clusters.append({"topic": topic, "state": state, "independent_domains": sorted(c["publishers"]),
                             "credibility": ev.credibility, "recency": ev.recency, "priority": ev.priority,
                             "headlines": [i["title"] for i in c["items"][:4]], "paper_only": True})
    for s in stories[:60]:
        center.append({"id": s["id"], "time": s["publishedAt"], "sourceName": ", ".join(s["sourceIds"][:3]),
                       "topic": s["market"], "summary": s["headlineEn"], "reliability": f"{s['state']} ({len(s['sourceIds'])} src)",
                       "demo": False})
    return {"feeds_used": len(feeds), "feed_errors": errors, "items_24h": len(items), "clusters": len(clusters),
            "corroborated": sum(1 for s in stories if s["state"] == "CORROBORATED"),
            "stories": stories[:120], "rss_clusters": rss_clusters[:120], "center_items": center}


# ============================ WP-2: causal news -> asset transmission matrix ============================
NEWSROOM_REL = "reports/grok/M18/newsroom_snapshot.json"
NEWS_HALF_LIFE_H = 6.0
_HAWK = re.compile(r"\b(rate hikes?|hikes? rates?|rais(e|es|ed|ing) rates?|hawkish|tighten\w*|higher for longer|"
                   r"hot(ter)? inflation|inflation (surges?|jumps?|accelerat\w*|rises?))\b", re.I)
_DOVE = re.compile(r"\b(rate cuts?|cuts? rates?|cutting rates|dovish|eas(e|es|ed|ing) policy|monetary easing|"
                   r"inflation (cools?|slows?|eases?|falls?))\b", re.I)
_BANK = {"FED": re.compile(r"\b(fed|fomc|powell|federal reserve)\b", re.I),
         "ECB": re.compile(r"\b(ecb|lagarde|european central bank)\b", re.I),
         "BOJ": re.compile(r"\b(boj|bank of japan|ueda)\b", re.I),
         "BOE": re.compile(r"\b(boe|bank of england|bailey)\b", re.I),
         "OPEC": re.compile(r"\b(opec\+?|saudi output|output cuts?)\b", re.I)}
# Sign of each asset's response to a HAWKISH surprise by that bank (standard rates/FX transmission). OPEC: supply cut.
POLICY_TRANSMISSION: dict[str, dict[str, float]] = {
    "FED": {"XAU": -1.0, "SPX": -1.0, "QQQ": -1.0, "BTC": -1.0, "ETH": -1.0, "SOL": -1.0, "EURUSD": -1.0, "USDJPY": 1.0},
    "ECB": {"EURUSD": 1.0, "DAX": -1.0},
    "BOJ": {"USDJPY": -1.0, "N225": -1.0},
    "BOE": {"EURUSD": -0.5},
}
_OPEC_CUT = re.compile(r"\b(output|production|supply) cuts?\b|\bcuts? (output|production|supply)\b", re.I)
_OPEC_HIKE = re.compile(r"\b(output|production|supply) (hikes?|increases?|boost)\b|\b(raise|boost|increase)s? (output|production)\b", re.I)


def load_corroborated_stories(root: Any) -> list[dict[str, Any]]:
    from pathlib import Path as _P
    try:
        snap = json.loads((_P(root) / NEWSROOM_REL).read_text(encoding="utf-8"))
    except Exception:
        return []
    return [s for s in snap.get("newsroomStories") or [] if s.get("state") == "CORROBORATED" and len(s.get("sourceIds") or []) >= 2]


def causal_news_impact(stories: Sequence[dict[str, Any]], symbol: str, *, now: Any = None) -> dict[str, Any]:
    """Signed drift for ``symbol`` from corroborated stories only: policy tone x bank transmission sign, OPEC supply
    direction for oil, 6h half-life decay, tanh-bounded. Single-publisher stories contribute nothing."""
    import math as _m
    from datetime import datetime as _dt, timezone as _tz
    now = now or _dt.now(_tz.utc)
    total, used, ev = 0.0, 0, []
    for s in stories:
        if s.get("state") != "CORROBORATED" or len(s.get("sourceIds") or []) < 2:
            continue
        try:
            age_h = (now - _dt.strptime(s["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_tz.utc)).total_seconds() / 3600
        except (KeyError, ValueError):
            continue
        if age_h < 0 or age_h > 48:
            continue
        title = str(s.get("headlineEn") or "")
        contrib = 0.0
        tone = (1 if _HAWK.search(title) else 0) - (1 if _DOVE.search(title) else 0)
        if tone:
            for bank, rx in _BANK.items():
                if bank != "OPEC" and rx.search(title):
                    contrib += tone * POLICY_TRANSMISSION.get(bank, {}).get(symbol, 0.0)
        if symbol in ("WTI", "BRENT") and _BANK["OPEC"].search(title):
            contrib += (1.0 if _OPEC_CUT.search(title) else 0.0) - (1.0 if _OPEC_HIKE.search(title) else 0.0)
        if not contrib:
            continue
        w = 0.5 ** (age_h / NEWS_HALF_LIFE_H) * min(2.0, len(s["sourceIds"]) / 2.0)
        total += contrib * w
        used += 1
        ev.append({"headline": title[:120], "publishers": len(s["sourceIds"]), "age_h": round(age_h, 1), "sign": contrib})
    return {"drift": round(_m.tanh(total / 2.0), 4), "clusters_used": used, "evidence": ev}


def urllib_get(url: str, timeout: float = 12.0) -> bytes:
    import urllib.request
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AHOS newsroom)"}), timeout=timeout) as r:
        return r.read(3_000_000)
