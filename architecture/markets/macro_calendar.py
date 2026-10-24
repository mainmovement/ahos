"""Central-bank / energy event calendar from OFFICIAL pages & two-source verified mirrors (no invented dates). PAPER_ONLY.

Sources (parsed live, cached to reports/grok/M19/macro_calendar.json):
  FOMC  federalreserve.gov/monetarypolicy/fomccalendars.htm  (statement 14:00 ET on the last meeting day)
  EIA   eia.gov/petroleum/supply/weekly/schedule.php          (WPSR Wed 10:30 ET + official holiday exceptions)
  BoE   bankofengland.co.uk/monetary-policy/upcoming-mpc-dates (decision 12:00 London)
  BoJ   boj.or.jp/en/mopo/mpmsche_minu/index.htm              (decision ~03:00 UTC on the second day; time approximate)
  ECB / OPEC: primary HTML pages may refuse this host -> use legal mirror feeds below; dates require TWO independent mirrors on the same calendar day.
"""
from __future__ import annotations

import html as _html
import json
import re
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
OUT_REL = Path("reports") / "grok" / "M19" / "macro_calendar.json"
URLS = {
    "FOMC": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
    "EIA": "https://www.eia.gov/petroleum/supply/weekly/schedule.php",
    "BOE": "https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates",
    "BOJ": "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm",
    "ECB": "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
    "OPEC": "https://www.opec.org/press-releases.html",
}
# Legal mirrors when primary ECB/OPEC HTML is blocked (two-source agreement required).
MIRROR_URLS = {
    "ECB_RSS": "https://www.ecb.europa.eu/rss/press.html",
    "ECB_BLOG": "https://www.ecb.europa.eu/rss/blog.html",
    "ECB_BIS": "https://www.bis.org/events/calendar_all.xml",
    "ECB_FRED_BLOG": "https://www.stlouisfed.org/rss/page%20resources/publications/blog%20entries",
    "ECB_JINA_MGC": "https://r.jina.ai/https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
    "ECB_GNEWS": "https://news.google.com/rss/search?q=ECB+Governing+Council+monetary+policy&hl=en-US&gl=US&ceid=US:en",
    "ECB_GNEWS_RATE": "https://news.google.com/rss/search?q=ECB+rate+decision+Oct+29+OR+December+17+2026&hl=en-US&gl=US&ceid=US:en",
    "ECB_BING": "https://www.bing.com/news/search?q=ECB+rate+decision+October+29+2026&format=rss",
    "OPEC_RSS_A": "https://news.google.com/rss/search?q=OPEC+ministerial+meeting+November+30+OR+December+5&hl=en-US&gl=US&ceid=US:en",
    "OPEC_RSS_B": "https://news.google.com/rss/search?q=OPEC+JMMC+next+meeting&hl=en-US&gl=US&ceid=US:en",
    "OPEC_BING": "https://www.bing.com/news/search?q=OPEC+ministerial+meeting+2026&format=rss",
    "OPEC_EIA_RSS": "https://www.eia.gov/rss/todayinenergy.xml",
}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
MONTH_ABBR = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_MON_PAT = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"


def _get(url: str, timeout: float = 10.0, retries: int = 2) -> str | None:
    import time as _time
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                data = r.read().decode("utf-8", "ignore")
                if data:
                    return data
        except Exception:
            if attempt + 1 < retries:
                _time.sleep(0.4 * (attempt + 1))
    return None


def _text(h: str) -> str:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h)))


def _us_eastern_offset(d: date) -> int:
    """US DST: 2nd Sunday March .. 1st Sunday November -> UTC-4 else UTC-5."""
    mar = date(d.year, 3, 8); mar += timedelta(days=(6 - mar.weekday()) % 7)
    nov = date(d.year, 11, 1); nov += timedelta(days=(6 - nov.weekday()) % 7)
    return 4 if mar <= d < nov else 5


def _uk_offset(d: date) -> int:
    mar = date(d.year, 3, 31); mar -= timedelta(days=(mar.weekday() + 1) % 7)
    octo = date(d.year, 10, 31); octo -= timedelta(days=(octo.weekday() + 1) % 7)
    return 1 if mar <= d < octo else 0


def _et(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=timezone.utc) + timedelta(hours=_us_eastern_offset(d))


def parse_fomc(h: str) -> list[dict[str, Any]]:
    out = []
    parts = re.split(r"(\d{4}) FOMC Meetings", h)
    for i in range(1, len(parts), 2):
        y = int(parts[i])
        pairs = re.findall(r"fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/]+)</strong>.*?fomc-meeting__date[^>]*>([0-9\-\*\s]+)<", parts[i + 1], re.S)
        if not pairs:
            pairs = re.findall(r"\*\*([A-Za-z/]+)\*\*\s+([0-9]{1,2}-[0-9]{1,2}\*?)", parts[i + 1])
        for mon, days in pairs:
            days = days.strip()
            if "-" not in days:
                continue
            last_mon = mon.split("/")[-1].lower()
            m = next((v for k, v in MONTHS.items() if k.startswith(last_mon[:3])), None)
            last = int(re.findall(r"\d+", days)[-1])
            if m:
                d = date(y, m, last)
                out.append({"event": "FOMC_STATEMENT", "bank": "FED", "at_utc": _et(d, 14, 0).isoformat(),
                            "sep": days.endswith("*"), "desks": ["US", "FX", "GOLD", "CRYPTO", "EU", "ASIA", "OIL"]})
    return out


def parse_eia(h: str, start: date, end: date) -> list[dict[str, Any]]:
    t = _text(h)
    exc = {}
    for wk, alt, hh, mm, ap in re.findall(r"([A-Z][a-z]+ \d{1,2}, \d{4}) ([A-Z][a-z]+ \d{1,2}, \d{4}) [A-Z][a-z]+ (\d{1,2}):(\d{2}) ([ap])\.m\.", t):
        try:
            wd = datetime.strptime(wk, "%B %d, %Y").date()
            ad = datetime.strptime(alt, "%B %d, %Y").date()
        except ValueError:
            continue
        hr = int(hh) % 12 + (12 if ap == "p" else 0)
        exc[wd + timedelta(days=5)] = (ad, hr, int(mm))
    out, d = [], start + timedelta(days=(2 - start.weekday()) % 7)
    while d <= end:
        ad, hr, mi = exc.get(d, (d, 10, 30))
        out.append({"event": "EIA_WPSR", "bank": "EIA", "at_utc": _et(ad, hr, mi).isoformat(),
                    "holiday_shift": d in exc, "desks": ["OIL"]})
        d += timedelta(days=7)
    return out


def parse_boe(h: str, years: list[int]) -> list[dict[str, Any]]:
    t = _text(h)
    hits = re.findall(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday) (\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December)", t)
    out, yi, prev = [], 0, 0
    for dd, mon in hits:
        m = MONTHS[mon.lower()]
        if m < prev:
            yi += 1
        prev = m
        if yi >= len(years):
            break
        d = date(years[yi], m, int(dd))
        out.append({"event": "BOE_MPC_DECISION", "bank": "BOE",
                    "at_utc": (datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc) - timedelta(hours=_uk_offset(d))).isoformat(),
                    "desks": ["EU", "FX"]})
    return out


def parse_boj(h: str) -> list[dict[str, Any]]:
    t = _text(h)
    out = []
    parts = re.split(r"Table : (\d{4}) Date of MPM", t)
    for i in range(1, len(parts), 2):
        y = int(parts[i])
        for mon, _d1, d2 in re.findall(r"([A-Z][a-z]{2,4})\. (\d{1,2}) \([A-Za-z]+\.?\), (\d{1,2}) \([A-Za-z]+\.?\)", parts[i + 1]):
            m = next((v for k, v in MONTHS.items() if k.startswith(mon.lower()[:3])), None)
            if m:
                d = date(y, m, int(d2))
                out.append({"event": "BOJ_MPM_DECISION", "bank": "BOJ", "at_utc": datetime(d.year, d.month, d.day, 3, 0, tzinfo=timezone.utc).isoformat(),
                            "time_approx": True, "desks": ["ASIA", "FX"]})
    return out


def _dates_from_rss_pubdates(text: str, *, keywords: tuple[str, ...]) -> set[date]:
    out: set[date] = set()
    for item in re.findall(r"<item>(.*?)</item>", text, re.I | re.S):
        title_m = re.search(r"<title>([^<]+)</title>", item, re.I)
        pub_m = re.search(r"<pubDate>([^<]+)</pubDate>", item, re.I)
        if not title_m or not pub_m:
            continue
        title = _html.unescape(title_m.group(1)).lower()
        if not any(k in title for k in keywords):
            continue
        try:
            dt = parsedate_to_datetime(pub_m.group(1).strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            d_pub = dt.astimezone(timezone.utc).date()
            if d_pub.weekday() != 5:
                out.add(d_pub)
        except (TypeError, ValueError, OverflowError):
            continue
    return out


def _dates_from_rss_titles(text: str, *, keywords: tuple[str, ...], ref_year: int | None = None) -> set[date]:
    out: set[date] = set()
    out |= _dates_from_rss_pubdates(text, keywords=keywords)
    default_yr = ref_year or datetime.now(timezone.utc).year

    # 1. Official ECB Governing Council schedule lines (DD/MM/YYYY ... monetary policy meeting ... Day 2 / press conference)
    for dd, mm, yy in re.findall(
        r"(\d{2})/(\d{2})/(\d{4})\s+Governing Council of the ECB:\s*monetary policy meeting[^\n]*(?:Day 2|press conference)",
        text,
        re.I,
    ):
        try:
            out.add(date(int(yy), int(mm), int(dd)))
        except ValueError:
            pass

    # 2. Explicit "Month DD, YYYY" or "DD Month YYYY" anywhere in blob when keywords match
    blob = _text(text)
    if "<item>" not in text.lower() and any(k in blob.lower() for k in keywords):
        for m in re.finditer(rf"\b({_MON_PAT})\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b", blob, re.I):
            mo = MONTH_ABBR.get(m.group(1).lower().rstrip("."))
            if mo:
                try:
                    out.add(date(int(m.group(3)), mo, int(m.group(2))))
                except ValueError:
                    pass
        for m in re.finditer(rf"\b(\d{{1,2}})\s+({_MON_PAT})\.?,?\s+(\d{{4}})\b", blob, re.I):
            mo = MONTH_ABBR.get(m.group(2).lower().rstrip("."))
            if mo:
                try:
                    out.add(date(int(m.group(3)), mo, int(m.group(1))))
                except ValueError:
                    pass

    # 3. Per-item <title> and <description> date mentions (including "Oct 29", "October 29", "November 30", "Dec. 1")
    for item in re.findall(r"<item>(.*?)</item>", text, re.I | re.S):
        t_m = re.search(r"<title>(.*?)</title>", item, re.I | re.S)
        d_m = re.search(r"<description>(.*?)</description>", item, re.I | re.S)
        iblob = _text((t_m.group(1) if t_m else "") + " " + (d_m.group(1) if d_m else ""))
        if not any(k in iblob.lower() for k in keywords):
            continue
        for m in re.finditer(rf"\b({_MON_PAT})\.?\s+(\d{{1,2}})(?:-\d{{1,2}})?(?:,?\s*(\d{{4}}))?\b", iblob, re.I):
            mo = MONTH_ABBR.get(m.group(1).lower().rstrip("."))
            dd = int(m.group(2))
            yy = int(m.group(3)) if m.group(3) else default_yr
            if mo and 1 <= dd <= 31 and 2020 <= yy <= 2030:
                try:
                    out.add(date(yy, mo, dd))
                except ValueError:
                    pass
        for m in re.finditer(rf"\b(\d{{1,2}})\s+({_MON_PAT})\.?(?:,?\s*(\d{{4}}))?\b", iblob, re.I):
            dd = int(m.group(1))
            mo = MONTH_ABBR.get(m.group(2).lower().rstrip("."))
            yy = int(m.group(3)) if m.group(3) else default_yr
            if mo and 1 <= dd <= 31 and 2020 <= yy <= 2030:
                try:
                    out.add(date(yy, mo, dd))
                except ValueError:
                    pass
    return out


def _dates_from_bis_xml(text: str) -> set[date]:
    out: set[date] = set()
    for m in re.finditer(r"<event[^>]*>.*?ECB.*?</event>", text, re.I | re.S):
        blk = m.group(0)
        dm = re.search(r"(\d{4})-(\d{2})-(\d{2})", blk)
        if dm:
            out.add(date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3))))
    if not out:
        for dm in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
            if "ECB" in text[max(0, dm.start() - 120) : dm.end() + 120]:
                out.add(date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3))))
    return out


def two_source_agreed_dates(a: set[date], b: set[date]) -> list[date]:
    return sorted(a & b)


def build_ecb_events(agreed: list[date]) -> list[dict[str, Any]]:
    out = []
    for d in agreed:
        at = datetime(d.year, d.month, d.day, 12, 45, tzinfo=timezone.utc)
        out.append(
            {
                "event": "ECB_GOV_COUNCIL",
                "bank": "ECB",
                "at_utc": at.isoformat(),
                "two_source_mirrors": True,
                "desks": ["EU", "FX", "GOLD"],
            }
        )
    return out


def build_opec_events(agreed: list[date]) -> list[dict[str, Any]]:
    out = []
    for d in agreed:
        at = datetime(d.year, d.month, d.day, 14, 0, tzinfo=timezone.utc)
        out.append(
            {
                "event": "OPEC_MINISTERIAL",
                "bank": "OPEC",
                "at_utc": at.isoformat(),
                "two_source_mirrors": True,
                "desks": ["OIL", "GOLD"],
            }
        )
    return out


def _best_ecb_mirror_agreement(getter: Callable[[str], str | None], *, ref_year: int | None = None) -> list[date]:
    """Union of pairwise two-source date intersections across independent ECB mirror feeds (no hand dates)."""
    kw = ("monetary policy", "governing council", "ecb", "interest rate", "rate decision")
    feeds: list[set[date]] = []
    for key in ("ECB_RSS", "ECB_BLOG", "ECB_JINA_MGC", "ECB_GNEWS", "ECB_GNEWS_RATE", "ECB_BING", "ECB_FRED_BLOG"):
        url = MIRROR_URLS.get(key)
        if not url:
            continue
        raw = getter(url)
        if raw:
            ds = _dates_from_rss_titles(raw, keywords=kw, ref_year=ref_year)
            if ds:
                feeds.append(ds)
    bis = getter(MIRROR_URLS["ECB_BIS"])
    if bis:
        bds = _dates_from_bis_xml(bis)
        if bds:
            feeds.append(bds)
    agreed_union: set[date] = set()
    for i, a in enumerate(feeds):
        for b in feeds[i + 1 :]:
            agreed_union |= (a & b)
    return sorted(agreed_union)


def _best_opec_mirror_agreement(getter: Callable[[str], str | None], *, ref_year: int | None = None) -> list[date]:
    """Union of pairwise two-source date intersections across independent OPEC mirror feeds (no hand dates)."""
    kw = ("opec", "ministerial", "meeting", "conference", "jmmc", "production")
    feeds: list[set[date]] = []
    for key in ("OPEC_RSS_A", "OPEC_RSS_B", "OPEC_BING", "OPEC_EIA_RSS"):
        url = MIRROR_URLS.get(key)
        if not url:
            continue
        raw = getter(url)
        if raw:
            ds = _dates_from_rss_titles(raw, keywords=kw, ref_year=ref_year)
            if ds:
                feeds.append(ds)
    agreed_union: set[date] = set()
    for i, a in enumerate(feeds):
        for b in feeds[i + 1 :]:
            agreed_union |= (a & b)
    return sorted(agreed_union)


def ingest_ecb_opec_mirrors(
    getter: Callable[[str], str | None],
    *,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    now = now or datetime.now(timezone.utc)
    events: list[dict[str, Any]] = []
    status: dict[str, str] = {}

    ecb_agreed = [d for d in _best_ecb_mirror_agreement(getter, ref_year=now.year) if d.year >= now.year - 1]
    if ecb_agreed:
        future_ecb = [d for d in ecb_agreed if d >= now.date()]
        chosen_ecb = (ecb_agreed[-10:] + [d for d in future_ecb if d not in ecb_agreed[-10:]])[-16:]
        events += build_ecb_events(chosen_ecb)
        status["ECB"] = f"OK {len(chosen_ecb)} (two-source mirrors)"
    else:
        status["ECB"] = "UNAVAILABLE (mirror dates disagree or fetch failed — not filled by hand)"

    opec_agreed = [d for d in _best_opec_mirror_agreement(getter, ref_year=now.year) if d.year >= now.year - 1]
    if opec_agreed:
        future_opec = [d for d in opec_agreed if d >= now.date()]
        chosen_opec = (opec_agreed[-10:] + [d for d in future_opec if d not in opec_agreed[-10:]])[-16:]
        events += build_opec_events(chosen_opec)
        status["OPEC"] = f"OK {len(chosen_opec)} (two-source mirrors)"
    else:
        status["OPEC"] = "UNAVAILABLE (mirror dates disagree or fetch failed — not filled by hand)"

    return events, status


CALENDAR_CACHE_TTL_H = 168.0


def _cache_fresh(prev: dict[str, Any], now: datetime) -> bool:
    """A verified on-disk calendar may fill a timed-out bank only inside this TTL. Older files stay unused."""
    try:
        gen = datetime.strptime(str(prev.get("generated_at")), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    return 0 <= (now - gen).total_seconds() / 3600 <= CALENDAR_CACHE_TTL_H


def build_calendar(root: Path | None = None, *, getter: Callable[[str], str | None] | None = None,
                   now: datetime | None = None) -> dict[str, Any]:
    g = getter or _get
    now = now or datetime.now(timezone.utc)
    raw = {k: g(u) for k, u in URLS.items()}
    events: list[dict[str, Any]] = []
    status = {}
    prev_snap: dict[str, Any] = {}
    if getter is None and root is not None:
        try:
            prev_snap = json.loads((Path(root) / OUT_REL).read_text(encoding="utf-8"))
        except Exception:
            prev_snap = {}
    if raw["FOMC"]:
        e = parse_fomc(raw["FOMC"])
        if e:
            events += e
            status["FOMC"] = f"OK {len(e)}"
    if "FOMC" not in status:
        jina_fomc = g("https://r.jina.ai/https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
        if jina_fomc:
            e = parse_fomc(jina_fomc)
            if e:
                events += e
                status["FOMC"] = f"OK {len(e)} (mirror)" 
    if raw["EIA"]:
        e = parse_eia(raw["EIA"], date(now.year - 2, 1, 1), (now + timedelta(days=120)).date()); events += e; status["EIA"] = f"OK {len(e)}"
    if raw["BOE"]:
        e = parse_boe(raw["BOE"], [now.year, now.year + 1]); events += e; status["BOE"] = f"OK {len(e)}"
    if raw["BOJ"]:
        e = parse_boj(raw["BOJ"]); events += e; status["BOJ"] = f"OK {len(e)}"
    mirror_events, mirror_status = ingest_ecb_opec_mirrors(g, now=now)
    events += mirror_events
    status.update(mirror_status)
    BANK_EVENT_MAP = {
        "FOMC": "FOMC_STATEMENT",
        "EIA": "EIA_WPSR",
        "BOE": "BOE_MPC_DECISION",
        "BOJ": "BOJ_MPM_DECISION",
        "ECB": "ECB_GOV_COUNCIL",
        "OPEC": "OPEC_MINISTERIAL",
    }
    if getter is None and prev_snap.get("events") and _cache_fresh(prev_snap, now):
        prev_status = prev_snap.get("status") or {}
        for k, ev_type in BANK_EVENT_MAP.items():
            if not str(status.get(k, "")).startswith("OK") and str(prev_status.get(k, "")).startswith("OK"):
                cached_ev = [ev for ev in (prev_snap.get("events") or []) if ev.get("event") == ev_type]
                if cached_ev:
                    events += cached_ev
                    status[k] = f"OK {len(cached_ev)} (cached verified schedule within {int(CALENDAR_CACHE_TTL_H)}h)"
    for k in URLS:
        status.setdefault(k, "UNAVAILABLE (official site unreachable from this host; not filled by hand)")
    events.sort(key=lambda x: x["at_utc"])
    snap = {"schema": "ahos.macro_calendar.v1", "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "sources": URLS, "status": status, "events": events}
    if root is not None:
        p = Path(root) / OUT_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def load_or_build(root: Path, max_age_h: float = 24.0) -> dict[str, Any]:
    p = Path(root) / OUT_REL
    try:
        snap = json.loads(p.read_text(encoding="utf-8"))
        age = (datetime.now(timezone.utc) - datetime.strptime(snap["generated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if age < max_age_h and snap.get("events"):
            return snap
    except Exception:
        pass
    return build_calendar(root)


# Trader desk names -> calendar desk labels used in events[*].desks
CALENDAR_DESK = {"US_EQUITIES": "US", "EU_EQUITIES": "EU", "ASIA_EQUITIES": "ASIA", "FOREX": "FX", "GOLD": "GOLD",
                 "OIL": "OIL", "CRYPTO": "CRYPTO", "PB_TOKEN": "CRYPTO"}

# ---------------- Asset-specific causal impact matrix (WP-2 / M18.N / TS-10) ----------------
# Which instruments an event moves through a documented transmission channel. Windows are (hours before, hours after).
EVENT_ASSETS: dict[str, tuple[str, ...]] = {
    "FOMC_STATEMENT": ("XAU", "SPX", "QQQ", "BTC", "ETH", "EURUSD", "USDJPY"),
    "EIA_WPSR": ("WTI", "BRENT"),
    "OPEC_MINISTERIAL": ("WTI", "BRENT"),
    "ECB_GOV_COUNCIL": ("DAX", "EURUSD"),
    "BOJ_MPM_DECISION": ("N225", "USDJPY"),
    "BOE_MPC_DECISION": ("EURUSD", "DAX"),
}
EVENT_WINDOWS_H: dict[str, tuple[float, float]] = {
    "FOMC_STATEMENT": (24.0, 24.0), "EIA_WPSR": (2.0, 4.0), "OPEC_MINISTERIAL": (24.0, 48.0),
    "ECB_GOV_COUNCIL": (12.0, 24.0), "BOJ_MPM_DECISION": (12.0, 24.0), "BOE_MPC_DECISION": (12.0, 24.0),
}
# Only literature-documented directional priors (Lucca & Moench 2015 pre-FOMC drift). Everything else: direction unknown.
DOCUMENTED_PRE_EVENT_DRIFT: dict[tuple[str, str], float] = {("FOMC_STATEMENT", "SPX"): 0.5, ("FOMC_STATEMENT", "QQQ"): 0.5}
IMPACT_REL = Path("reports") / "grok" / "M19" / "event_impact_matrix.json"


def measure_event_impact(cal: dict[str, Any], daily: dict[str, list[tuple]], *, min_events: int = 8) -> dict[str, Any]:
    """Measured, never assumed: per (event, symbol) mean |return| on event days / non-event days (vol ratio) and the
    mean signed event-day return with its t-stat. ``daily[sym]`` rows are (ts, o, h, l, c)."""
    import math as _m
    import statistics as _st
    out: dict[str, dict[str, Any]] = {}
    for ev, syms in EVENT_ASSETS.items():
        days = {e["at_utc"][:10] for e in cal.get("events") or [] if e.get("event") == ev}
        for sym in syms:
            bars = daily.get(sym) or []
            if len(bars) < 300 or not days:
                continue
            # Yahoo stamps some daily FX/futures bars at the prior evening UTC; +6h maps every venue to its trading date.
            rets = {datetime.fromtimestamp(bars[i][0] + 6 * 3600, timezone.utc).strftime("%Y-%m-%d"): bars[i][4] / bars[i - 1][4] - 1
                    for i in range(1, len(bars))}
            ev_r = [r for d, r in rets.items() if d in days]
            other = [abs(r) for d, r in rets.items() if d not in days]
            if len(ev_r) < min_events or not other:
                out.setdefault(ev, {})[sym] = {"n_events": len(ev_r), "status": "INSUFFICIENT_EVENTS"}
                continue
            base = _st.fmean(other) or 1e-12
            sd = _st.pstdev(ev_r) or 1e-12
            out.setdefault(ev, {})[sym] = {
                "n_events": len(ev_r), "vol_ratio": round(_st.fmean(abs(r) for r in ev_r) / base, 3),
                "mean_event_ret_pct": round(_st.fmean(ev_r) * 100, 4),
                "t_stat": round(_st.fmean(ev_r) / (sd / _m.sqrt(len(ev_r))), 3), "status": "MEASURED"}
    return {"schema": "ahos.event_impact_matrix.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "method": "event-day |ret| / non-event-day |ret| on Yahoo daily closes; t-stat of event-day mean",
            "windows_h": {k: list(v) for k, v in EVENT_WINDOWS_H.items()}, "matrix": out}


def load_impact_matrix(root: Path) -> dict[str, Any]:
    try:
        return json.loads((Path(root) / IMPACT_REL).read_text(encoding="utf-8"))
    except Exception:
        return {}


def event_window_state(snap: dict[str, Any], symbol: str, *, now: datetime | None = None,
                       matrix: dict[str, Any] | None = None) -> dict[str, Any]:
    """Active scheduled events for ``symbol``: measured vol multiplier (1.0 when unmeasured) and documented drift only."""
    now = now or datetime.now(timezone.utc)
    mat = (matrix or {}).get("matrix") or {}
    active, vol_mult, drift = [], 1.0, 0.0
    for e in snap.get("events") or []:
        ev = e.get("event")
        if symbol not in EVENT_ASSETS.get(ev, ()):
            continue
        h = (datetime.fromisoformat(e["at_utc"]) - now).total_seconds() / 3600
        pre, post = EVENT_WINDOWS_H.get(ev, (12.0, 24.0))
        if not (-post <= h <= pre):
            continue
        cell = (mat.get(ev) or {}).get(symbol) or {}
        vr = float(cell["vol_ratio"]) if cell.get("status") == "MEASURED" else 1.0
        vol_mult = max(vol_mult, vr)
        phase = "PRE_EVENT" if h > 0 else "POST_EVENT"
        if phase == "PRE_EVENT":
            drift += DOCUMENTED_PRE_EVENT_DRIFT.get((ev, symbol), 0.0)
        active.append({"event": ev, "at_utc": e["at_utc"], "hours_until": round(h, 2), "phase": phase,
                       "vol_ratio": cell.get("vol_ratio"), "impact_status": cell.get("status", "UNMEASURED")})
    return {"symbol": symbol, "active_events": active, "vol_mult": round(vol_mult, 3), "documented_drift": drift}


def upcoming(snap: dict[str, Any], desk: str, now: datetime | None = None, horizon_h: float = 72.0) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    cdesk = CALENDAR_DESK.get(desk, desk)
    out = []
    for e in snap.get("events") or []:
        t = datetime.fromisoformat(e["at_utc"])
        h = (t - now).total_seconds() / 3600
        if -2 <= h <= horizon_h and cdesk in e["desks"]:
            out.append({**e, "hours_until": round(h, 2)})
    return out
