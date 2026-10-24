"""Cash-market session honesty for paper trader (Asia/Tehran display, UTC math). PAPER_ONLY.

Per-venue regular hours (exchange-published, DST via zoneinfo) plus official 2026–2027 exchange holiday calendars
for NYSE/NASDAQ, XETRA, LSE/ICE_BRENT, TSE, HKEX, CME_GLOBEX, and FX_OTC."""
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

# Official 2026–2027 full-day exchange holidays (ISO YYYY-MM-DD in the venue's local date; for 24x5 venues, the
# trade date d+1 corresponding to the session opening on evening d).
EXCHANGE_HOLIDAYS_2026_2027: dict[str, dict[str, str]] = {
    "NYSE": {
        "2026-01-01": "New Year's Day",
        "2026-01-19": "Martin Luther King Jr. Day",
        "2026-02-16": "Presidents' Day",
        "2026-04-03": "Good Friday",
        "2026-05-25": "Memorial Day",
        "2026-06-19": "Juneteenth National Independence Day",
        "2026-07-03": "Independence Day (Observed)",
        "2026-09-07": "Labor Day",
        "2026-11-26": "Thanksgiving Day",
        "2026-12-25": "Christmas Day",
        "2027-01-01": "New Year's Day",
        "2027-01-18": "Martin Luther King Jr. Day",
        "2027-02-15": "Presidents' Day",
        "2027-03-26": "Good Friday",
        "2027-05-31": "Memorial Day",
        "2027-06-18": "Juneteenth (Observed)",
        "2027-07-05": "Independence Day (Observed)",
        "2027-09-06": "Labor Day",
        "2027-11-25": "Thanksgiving Day",
        "2027-12-24": "Christmas Day (Observed)",
    },
    "XETRA": {
        "2026-01-01": "New Year's Day",
        "2026-04-03": "Good Friday",
        "2026-04-06": "Easter Monday",
        "2026-05-01": "Labour Day",
        "2026-12-24": "Christmas Eve",
        "2026-12-25": "Christmas Day",
        "2026-12-31": "New Year's Eve",
        "2027-01-01": "New Year's Day",
        "2027-03-26": "Good Friday",
        "2027-03-29": "Easter Monday",
        "2027-12-24": "Christmas Eve",
        "2027-12-31": "New Year's Eve",
    },
    "LSE": {
        "2026-01-01": "New Year's Day",
        "2026-04-03": "Good Friday",
        "2026-04-06": "Easter Monday",
        "2026-05-04": "Early May Bank Holiday",
        "2026-05-25": "Spring Bank Holiday",
        "2026-08-31": "Summer Bank Holiday",
        "2026-12-25": "Christmas Day",
        "2026-12-28": "Boxing Day (Observed)",
        "2027-01-01": "New Year's Day",
        "2027-03-26": "Good Friday",
        "2027-03-29": "Easter Monday",
        "2027-05-03": "Early May Bank Holiday",
        "2027-05-31": "Spring Bank Holiday",
        "2027-08-30": "Summer Bank Holiday",
        "2027-12-27": "Christmas Day (Observed)",
        "2027-12-28": "Boxing Day (Observed)",
    },
    "ICE_BRENT": {
        "2026-01-01": "New Year's Day",
        "2026-04-03": "Good Friday",
        "2026-12-25": "Christmas Day",
        "2027-01-01": "New Year's Day",
        "2027-03-26": "Good Friday",
        "2027-12-24": "Christmas Holiday",
    },
    "TSE": {
        "2026-01-01": "New Year's Day",
        "2026-01-02": "Market Holiday",
        "2026-01-12": "Coming of Age Day",
        "2026-02-11": "National Foundation Day",
        "2026-02-23": "Emperor's Birthday",
        "2026-03-20": "Vernal Equinox Day",
        "2026-04-29": "Showa Day",
        "2026-05-04": "Greenery Day",
        "2026-05-05": "Children's Day",
        "2026-05-06": "Constitution Memorial Day (Observed)",
        "2026-07-20": "Marine Day",
        "2026-08-11": "Mountain Day",
        "2026-09-21": "Respect for the Aged Day",
        "2026-09-22": "Citizens' Holiday",
        "2026-09-23": "Autumnal Equinox Day",
        "2026-10-12": "Sports Day",
        "2026-11-03": "Culture Day",
        "2026-11-23": "Labor Thanksgiving Day",
        "2026-12-31": "Exchange Holiday",
        "2027-01-01": "New Year's Day",
        "2027-01-11": "Coming of Age Day",
        "2027-02-11": "National Foundation Day",
        "2027-02-23": "Emperor's Birthday",
        "2027-03-22": "Vernal Equinox Day (Observed)",
        "2027-04-29": "Showa Day",
        "2027-05-03": "Constitution Memorial Day",
        "2027-05-04": "Greenery Day",
        "2027-05-05": "Children's Day",
        "2027-07-19": "Marine Day",
        "2027-08-11": "Mountain Day",
        "2027-09-20": "Respect for the Aged Day",
        "2027-09-23": "Autumnal Equinox Day",
        "2027-10-11": "Sports Day",
        "2027-11-03": "Culture Day",
        "2027-11-23": "Labor Thanksgiving Day",
        "2027-12-31": "Exchange Holiday",
    },
    "HKEX": {
        "2026-01-01": "New Year's Day",
        "2026-02-17": "Lunar New Year's Day",
        "2026-02-18": "Second Day of Lunar New Year",
        "2026-02-19": "Third Day of Lunar New Year",
        "2026-04-03": "Good Friday",
        "2026-04-06": "Easter Monday / Ching Ming Observed",
        "2026-04-07": "Day following Easter Monday",
        "2026-05-01": "Labour Day",
        "2026-05-25": "Day following Buddha's Birthday",
        "2026-06-19": "Tuen Ng Festival",
        "2026-07-01": "HKSAR Establishment Day",
        "2026-10-01": "National Day",
        "2026-10-19": "Day following Chung Yeung Festival",
        "2026-12-25": "Christmas Day",
        "2027-01-01": "New Year's Day",
        "2027-02-08": "Third Day of Lunar New Year",
        "2027-02-09": "Fourth Day of Lunar New Year",
        "2027-03-26": "Good Friday",
        "2027-03-29": "Easter Monday",
        "2027-04-05": "Ching Ming Festival",
        "2027-05-13": "Buddha's Birthday",
        "2027-06-09": "Tuen Ng Festival",
        "2027-07-01": "HKSAR Establishment Day",
        "2027-10-01": "National Day",
        "2027-10-08": "Chung Yeung Festival",
        "2027-12-27": "First Weekday after Christmas Day",
    },
    "CME_GLOBEX": {
        "2026-01-01": "New Year's Day",
        "2026-04-03": "Good Friday",
        "2026-12-25": "Christmas Day",
        "2027-01-01": "New Year's Day",
        "2027-03-26": "Good Friday",
        "2027-12-24": "Christmas Day (Observed)",
    },
    "FX_OTC": {
        "2026-01-01": "New Year's Day",
        "2026-12-25": "Christmas Day",
        "2027-01-01": "New Year's Day",
        "2027-12-24": "Christmas Holiday",
    },
}

SCHEDULE_BASIS = "exchange-published regular hours; DST via zoneinfo; 2026-2027 official exchange holidays modeled"


def tehran_now(utc: datetime | None = None) -> datetime:
    u = utc or datetime.now(timezone.utc)
    return u.astimezone(TEHRAN)


def is_weekend_tehran(utc: datetime | None = None) -> bool:
    wd = tehran_now(utc).weekday()
    return wd >= 5  # Sat=5 Sun=6 in Python


def holiday_name(venue: str, d: date) -> str | None:
    """Return the official holiday name if local date `d` is a full-day holiday for `venue`."""
    return (EXCHANGE_HOLIDAYS_2026_2027.get(venue) or {}).get(d.isoformat())


def is_holiday(venue: str, d: date) -> bool:
    """True when `d` is a modeled 2026–2027 official full-day holiday for `venue`."""
    return holiday_name(venue, d) is not None


def _at(d: date, hhmm: str, tz: ZoneInfo) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(d, time(h, m), tzinfo=tz).astimezone(timezone.utc)


def venue_intervals(venue: str, now: datetime, *, days_back: int = 2, days_fwd: int = 14) -> list[tuple[datetime, datetime]]:
    v = VENUES[venue]
    tz = ZoneInfo(v["tz"])
    today = now.astimezone(tz).date()
    out = []
    for k in range(-days_back, days_fwd):
        d = today + timedelta(days=k)
        if v["kind"] == "24x5":
            # Session opens on evening `d` (Sun-Thu) for trade date `d + 1 day` (Mon-Fri).
            trade_date = d + timedelta(days=1)
            if d.weekday() in (6, 0, 1, 2, 3) and not is_holiday(venue, trade_date):
                out.append((_at(d, v["open"], tz), _at(trade_date, v["close"], tz)))
        elif d.weekday() < 5 and not is_holiday(venue, d):
            out.extend((_at(d, s, tz), _at(d, e, tz)) for s, e in v["sessions"])
    return sorted(out)


def venue_status(venue: str, utc: datetime | None = None) -> dict[str, object]:
    now = utc or datetime.now(timezone.utc)
    v = VENUES[venue]
    tz = ZoneInfo(v["tz"])
    local_d = now.astimezone(tz).date()
    trade_d = local_d + timedelta(days=1) if v["kind"] == "24x5" and now.astimezone(tz).hour >= 17 else local_d
    hol = holiday_name(venue, trade_d) or holiday_name(venue, local_d)
    iv = venue_intervals(venue, now)
    cur = next(((o, c) for o, c in iv if o <= now < c), None)
    nxt = next((o for o, _ in iv if o > now), None)
    mins = 0 if cur else (math.ceil((nxt - now).total_seconds() / 60) if nxt else None)
    return {
        "venue": venue, "label_fa": v["label_fa"], "open": cur is not None,
        "closes_utc": cur[1].strftime("%Y-%m-%dT%H:%M:%SZ") if cur else None,
        "next_open_utc": nxt.strftime("%Y-%m-%dT%H:%M:%SZ") if nxt else None,
        "next_open_tehran": nxt.astimezone(TEHRAN).strftime("%Y-%m-%d %H:%M") if nxt else None,
        "minutes_until_open": mins, "holidays_modeled": True,
        "holiday_today": hol is not None and cur is None,
        "holiday_name": hol if cur is None else None,
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
