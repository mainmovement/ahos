"""Central-bank / energy event calendar from OFFICIAL pages only (no invented dates). PAPER_ONLY.

Sources (parsed live, cached to reports/grok/M19/macro_calendar.json):
  FOMC  federalreserve.gov/monetarypolicy/fomccalendars.htm  (statement 14:00 ET on the last meeting day)
  EIA   eia.gov/petroleum/supply/weekly/schedule.php          (WPSR Wed 10:30 ET + official holiday exceptions)
  BoE   bankofengland.co.uk/monetary-policy/upcoming-mpc-dates (decision 12:00 London)
  BoJ   boj.or.jp/en/mopo/mpmsche_minu/index.htm              (decision ~03:00 UTC on the second day; time approximate)
  ECB / OPEC: official sites refuse this host (TLS EOF / HTTP 403) -> reported UNAVAILABLE, never filled in by hand.
"""
from __future__ import annotations

import html as _html
import json
import re
import urllib.request
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
