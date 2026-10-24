"""Cash-market session honesty for paper trader (Asia/Tehran display, UTC math). PAPER_ONLY.

Per-venue regular hours (exchange-published, DST via zoneinfo). Exchange holidays are NOT modeled: a venue shown
OPEN on a holiday is still gated by the VERIFIED-witness + fresh-quote rule, which fails closed on stale prices."""
from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

# Weekday cash desks (crypto runs 24/7 but still needs fresh quotes).
CASH_DESKS = frozenset({"GOLD", "OIL", "US_EQUITIES", "EU_EQUITIES", "ASIA_EQUITIES", "FOREX"})
CRYPTO_DESKS = frozenset({"CRYPTO", "PB_TOKEN"})

# kind "cash": sessions on Mon-Fri local dates. kind "24x5": opens at `open` on local Sun-Thu, closes at `close` on
# the next local date (CME daily halt 16:00-17:00 CT; FX rolls at 17:00 ET).
VENUES: dict[str, dict] = {
    "NYSE": {"tz": "America/New_York", "kind": "cash", "sessions": (("09:30", "16:00"),), "label_fa": "نیویورک (NYSE/Nasdaq)"},
    "XETRA": {"tz": "Europe/Berlin", "kind": "cash", "sessions": (("09:00", "17:30"),), "label_fa": "فرانکفورت (Xetra)"},
    "LSE": {"tz": "Europe/London", "kind": "cash", "sessions": (("08:00", "16:30"),), "label_fa": "لندن (LSE)"},
    "TSE": {"tz": "Asia/Tokyo", "kind": "cash", "sessions": (("09:00", "11:30"), ("12:30", "15:30")), "label_fa": "توکیو (TSE)"},
    "HKEX": {"tz": "Asia/Hong_Kong", "kind": "cash", "sessions": (("09:30", "12:00"), ("13:00", "16:00")), "label_fa": "هنگ‌کنگ (HKEX)"},
    "ICE_BRENT": {"tz": "Europe/London", "kind": "cash", "sessions": (("01:00", "23:00"),), "label_fa": "برنت (ICE Futures Europe)"},
    "CME_GLOBEX": {"tz": "America/Chicago", "kind": "24x5", "open": "17:00", "close": "16:00", "label_fa": "CME Globex (طلا/WTI)"},
    "FX_OTC": {"tz": "America/New_York", "kind": "24x5", "open": "17:00", "close": "17:00", "label_fa": "فارکس (OTC)"},
}
SYMBOL_VENUE: dict[str, str] = {
    "SPX": "NYSE", "QQQ": "NYSE", "DAX": "XETRA", "N225": "TSE", "HSI": "HKEX", "BRENT": "ICE_BRENT",
    "XAU": "CME_GLOBEX", "WTI": "CME_GLOBEX", "EURUSD": "FX_OTC", "USDJPY": "FX_OTC",
}
SCHEDULE_BASIS = "exchange-published regular hours; DST via zoneinfo; exchange holidays NOT modeled"


def tehran_now(utc: datetime | None = None) -> datetime:
    u = utc or datetime.now(timezone.utc)
    return u.astimezone(TEHRAN)


def is_weekend_tehran(utc: datetime | None = None) -> bool:
    wd = tehran_now(utc).weekday()
    return wd >= 5  # Sat=5 Sun=6 in Python


def _at(d: date, hhmm: str, tz: ZoneInfo) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(d, time(h, m), tzinfo=tz).astimezone(timezone.utc)


def venue_intervals(venue: str, now: datetime, *, days_back: int = 2, days_fwd: int = 9) -> list[tuple[datetime, datetime]]:
    v = VENUES[venue]
    tz = ZoneInfo(v["tz"])
    today = now.astimezone(tz).date()
    out = []
    for k in range(-days_back, days_fwd):
        d = today + timedelta(days=k)
        if v["kind"] == "24x5":
            if d.weekday() in (6, 0, 1, 2, 3):
                out.append((_at(d, v["open"], tz), _at(d + timedelta(days=1), v["close"], tz)))
        elif d.weekday() < 5:
            out.extend((_at(d, s, tz), _at(d, e, tz)) for s, e in v["sessions"])
    return sorted(out)


def venue_status(venue: str, utc: datetime | None = None) -> dict[str, object]:
    now = utc or datetime.now(timezone.utc)
    iv = venue_intervals(venue, now)
    cur = next(((o, c) for o, c in iv if o <= now < c), None)
    nxt = next((o for o, _ in iv if o > now), None)
    mins = 0 if cur else (math.ceil((nxt - now).total_seconds() / 60) if nxt else None)
    return {
        "venue": venue, "label_fa": VENUES[venue]["label_fa"], "open": cur is not None,
        "closes_utc": cur[1].strftime("%Y-%m-%dT%H:%M:%SZ") if cur else None,
        "next_open_utc": nxt.strftime("%Y-%m-%dT%H:%M:%SZ") if nxt else None,
        "next_open_tehran": nxt.astimezone(TEHRAN).strftime("%Y-%m-%d %H:%M") if nxt else None,
        "minutes_until_open": mins, "holidays_modeled": False,
    }


def symbol_session(symbol: str, utc: datetime | None = None) -> dict[str, object]:
    venue = SYMBOL_VENUE.get(symbol)
    if venue is None:
        return {"symbol": symbol, "venue": "CRYPTO_24_7", "open": True, "minutes_until_open": 0, "holidays_modeled": True}
    return {"symbol": symbol, **venue_status(venue, utc)}


def session_report(utc: datetime | None = None) -> dict[str, object]:
    """Honest gate: weekend => cash desks expected CLOSED unless live witness proves fresh quotes."""
    now = utc or datetime.now(timezone.utc)
    t = tehran_now(now)
    weekend = is_weekend_tehran(now)
    venues = {name: venue_status(name, now) for name in VENUES}
    open_now = sorted(n for n, s in venues.items() if s["open"])
    return {
        "paper_only": True,
        "utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tehran": t.strftime("%Y-%m-%d %H:%M %Z"),
        "tehran_weekday": t.strftime("%A"),
        "weekend_tehran": weekend,
        "cash_desks_expected": "CLOSED_OR_STALE" if weekend or not open_now else "OPEN_IF_VERIFIED",
        "crypto_desks_expected": "OPEN_IF_VERIFIED",
        "venues": venues,
        "venues_open_now": open_now,
        "symbols_open_now": sorted(s for s, v in SYMBOL_VENUE.items() if venues[v]["open"]),
        "schedule_basis": SCHEDULE_BASIS,
        "summary_fa": (
            f"زمان تهران: {t.strftime('%Y-%m-%d %H:%M')} ({t.strftime('%A')}). "
            + (
                "شنبه/یکشنبه: میزهای نقدی (طلا، نفت، سهام، FX) معمولاً بسته یا قیمت منقضی — بدون GREEN جعلی."
                if weekend
                else "روز کاری: فقط با شاهد VERIFIED و قیمت تازه معاملهٔ کاغذی مجاز است."
            )
            + (f" بازارهای باز اکنون: {', '.join(open_now)}." if open_now else " هیچ بازار نقدی‌ای اکنون باز نیست.")
        ),
    }
