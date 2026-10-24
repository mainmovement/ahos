"""Central-bank / energy event calendar from OFFICIAL pages only (no invented dates). PAPER_ONLY.

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

UA = {"User-Agent": "Mozilla/5.0 (AHOS macro calendar)"}
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
    "ECB_GNEWS": "https://news.google.com/rss/search?q=ECB+Governing+Council+monetary+policy&hl=en-US&gl=US&ceid=US:en",
    "OPEC_RSS_A": "https://news.google.com/rss/search?q=OPEC+ministerial+meeting&hl=en-US&gl=US&ceid=US:en",
    "OPEC_RSS_B": "https://news.google.com/rss/search?q=OPEC+conference+date&hl=en-US&gl=US&ceid=US:en",
    "OPEC_EIA_RSS": "https://www.eia.gov/rss/todayinenergy.xml",
}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def _get(url: str, timeout: float = 25.0) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
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
        for mon, days in re.findall(r"fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/]+)</strong>.*?fomc-meeting__date[^>]*>([0-9\-\*\s]+)<", parts[i + 1], re.S):
            days = days.strip()
            if "-" not in days:          # single-day entries are notation votes / unscheduled, not statements
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
        exc[wd + timedelta(days=5)] = (ad, hr, int(mm))   # week ends Friday -> normal release the next Wednesday
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
    for blk in re.split(r"Table : (\d{4}) Date of MPM", t)[1:]:
        pass
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
            out.add(dt.astimezone(timezone.utc).date())
        except (TypeError, ValueError, OverflowError):
            continue
    return out


def _dates_from_rss_titles(text: str, *, keywords: tuple[str, ...]) -> set[date]:
    out: set[date] = set()
    out |= _dates_from_rss_pubdates(text, keywords=keywords)
    blob = _text(text)
    for m in re.finditer(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        blob,
        re.I,
    ):
        mon, dd, yy = m.group(1), m.group(2), m.group(3)
        mo = MONTHS.get(mon.lower())
        if mo:
            out.add(date(int(yy), mo, int(dd)))
    for title in re.findall(r"<title>([^<]+)</title>", text, re.I):
        low = title.lower()
        if not any(k in low for k in keywords):
            continue
        for m in re.finditer(r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", title, re.I):
            mo = MONTHS.get(m.group(2).lower())
            if mo:
                out.add(date(int(m.group(3)), mo, int(m.group(1))))
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


def _best_ecb_mirror_agreement(getter: Callable[[str], str | None]) -> list[date]:
    """Pick the largest two-source date intersection across legal ECB RSS mirrors (no hand dates)."""
    kw = ("monetary policy", "governing council", "ecb", "interest rate")
    feeds: list[set[date]] = []
    for key in ("ECB_RSS", "ECB_BLOG", "ECB_GNEWS", "ECB_FRED_BLOG"):
        raw = getter(MIRROR_URLS[key])
        if raw:
            feeds.append(_dates_from_rss_titles(raw, keywords=kw))
    bis = getter(MIRROR_URLS["ECB_BIS"])
    if bis:
        feeds.append(_dates_from_bis_xml(bis))
    best: list[date] = []
    for i, a in enumerate(feeds):
        for b in feeds[i + 1 :]:
            agreed = two_source_agreed_dates(a, b)
            if len(agreed) > len(best):
                best = agreed
    return best


def ingest_ecb_opec_mirrors(
    getter: Callable[[str], str | None],
    *,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    now = now or datetime.now(timezone.utc)
    events: list[dict[str, Any]] = []
    status: dict[str, str] = {}
    agreed = _best_ecb_mirror_agreement(getter)
    if agreed:
        future = [d for d in agreed if d >= now.date()]
        if future:
            events += build_ecb_events(future[:12])
            status["ECB"] = f"OK {len(future[:12])} (two-source mirrors)"
        else:
            status["ECB"] = "UNAVAILABLE (two-source agreed but no upcoming dates)"
    else:
        status["ECB"] = "UNAVAILABLE (mirror dates disagree or fetch failed — not filled by hand)"
    op_a = getter(MIRROR_URLS["OPEC_RSS_A"])
    op_b = getter(MIRROR_URLS["OPEC_RSS_B"])
    op_c = getter(MIRROR_URLS["OPEC_EIA_RSS"])
    if op_a and op_b:
        da = _dates_from_rss_titles(op_a, keywords=("opec", "ministerial", "meeting"))
        db = _dates_from_rss_titles(op_b, keywords=("opec", "conference", "meeting"))
        if op_c:
            dc = _dates_from_rss_titles(op_c, keywords=("opec", "oil", "production"))
            db = db | dc
        agreed = two_source_agreed_dates(da, db)
        if agreed:
            future = [d for d in agreed if d >= now.date()]
            if future:
                events += build_opec_events(future[:8])
                status["OPEC"] = f"OK {len(future[:8])} (two-source mirrors)"
            else:
                status["OPEC"] = "UNAVAILABLE (two-source agreed but no upcoming dates)"
        else:
            status["OPEC"] = "UNAVAILABLE (mirror dates disagree — not filled by hand)"
    else:
        status["OPEC"] = "UNAVAILABLE (mirror fetch failed — not filled by hand)"
    return events, status


def build_calendar(root: Path | None = None, *, getter: Callable[[str], str | None] | None = None,
                   now: datetime | None = None) -> dict[str, Any]:
    g = getter or _get
    now = now or datetime.now(timezone.utc)
    raw = {k: g(u) for k, u in URLS.items()}
    events: list[dict[str, Any]] = []
    status = {}
    if raw["FOMC"]:
        e = parse_fomc(raw["FOMC"]); events += e; status["FOMC"] = f"OK {len(e)}"
    if raw["EIA"]:
        e = parse_eia(raw["EIA"], date(now.year - 2, 1, 1), (now + timedelta(days=120)).date()); events += e; status["EIA"] = f"OK {len(e)}"
    if raw["BOE"]:
        e = parse_boe(raw["BOE"], [now.year, now.year + 1]); events += e; status["BOE"] = f"OK {len(e)}"
    if raw["BOJ"]:
        e = parse_boj(raw["BOJ"]); events += e; status["BOJ"] = f"OK {len(e)}"
    mirror_events, mirror_status = ingest_ecb_opec_mirrors(g, now=now)
    events += mirror_events
    status.update(mirror_status)
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


def upcoming(snap: dict[str, Any], desk: str, now: datetime | None = None, horizon_h: float = 72.0) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    out = []
    for e in snap.get("events") or []:
        t = datetime.fromisoformat(e["at_utc"])
        h = (t - now).total_seconds() / 3600
        if -2 <= h <= horizon_h and desk in e["desks"]:
            out.append({**e, "hours_until": round(h, 2)})
    return out
