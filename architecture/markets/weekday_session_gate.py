"""Cash-market session honesty for paper trader (Asia/Tehran display, UTC math). PAPER_ONLY."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

# Weekday cash desks (crypto runs 24/7 but still needs fresh quotes).
CASH_DESKS = frozenset({"GOLD", "OIL", "US_EQUITIES", "EU_EQUITIES", "ASIA_EQUITIES", "FOREX"})
CRYPTO_DESKS = frozenset({"CRYPTO", "PB_TOKEN"})


def tehran_now(utc: datetime | None = None) -> datetime:
    u = utc or datetime.now(timezone.utc)
    return u.astimezone(TEHRAN)


def is_weekend_tehran(utc: datetime | None = None) -> bool:
    wd = tehran_now(utc).weekday()
    return wd >= 5  # Sat=5 Sun=6 in Python


def session_report(utc: datetime | None = None) -> dict[str, object]:
    """Honest gate: weekend => cash desks expected CLOSED unless live witness proves fresh quotes."""
    now = utc or datetime.now(timezone.utc)
    t = tehran_now(now)
    weekend = is_weekend_tehran(now)
    return {
        "paper_only": True,
        "utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tehran": t.strftime("%Y-%m-%d %H:%M %Z"),
        "tehran_weekday": t.strftime("%A"),
        "weekend_tehran": weekend,
        "cash_desks_expected": "CLOSED_OR_STALE" if weekend else "OPEN_IF_VERIFIED",
        "crypto_desks_expected": "OPEN_IF_VERIFIED",
        "summary_fa": (
            f"زمان تهران: {t.strftime('%Y-%m-%d %H:%M')} ({t.strftime('%A')}). "
            + (
                "شنبه/یکشنبه: میزهای نقدی (طلا، نفت، سهام، FX) معمولاً بسته یا قیمت منقضی — بدون GREEN جعلی."
                if weekend
                else "روز کاری: فقط با شاهد VERIFIED و قیمت تازه معاملهٔ کاغذی مجاز است."
            )
        ),
    }
