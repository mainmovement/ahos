"""A short nightly paper note for Mehrdad. No trade alert and no live order."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TEHRAN = timezone(timedelta(hours=3, minutes=30))
SOAK_GOAL_H = 72.0

_DIGITS = str.maketrans("0123456789.-", "۰۱۲۳۴۵۶۷۸۹٫−")
_NAMES = {
    "XAU": "طلا",
    "GC": "طلا",
    "BRENT": "نفت",
    "WTI": "نفت",
    "BZ": "نفت",
    "CL": "نفت",
    "SPX": "شاخص آمریکا",
    "ES": "شاخص آمریکا",
    "NDX": "نزدک",
    "NQ": "نزدک",
    "QQQ": "نزدک",
    "HSI": "هنگ‌کنگ",
    "NKD": "ژاپن",
    "DAX": "آلمان",
    "BTC-SWAP": "بیت‌کوین",
    "ETH-SWAP": "اتریوم",
    "SOL-SWAP": "سولانا",
}
_LEARNED = {
    "NEWS_TRAP": "باخت‌ها بیشتر از دنبال کردن خبر آمده‌اند، و وزن خبر را عوض نکرد.",
    "BAD_TIMING": "یکی از باخت‌ها از زمان خروج آمده، و حد زمان را عوض نکرد.",
    "FEE_DRAG": "کارمزد بخشی از نتیجه را خورده، و همان درگاه کارمزد سر جایش مانده.",
    "BAD_DATA": "یک داده ناسازگار بوده و همان معامله کنار گذاشته شده.",
    "WRONG_FAMILY": "یک خانوادهٔ سیگنال اشتباه بوده و وزنش عوض نشده.",
    "REGIME": "حال بازار اندازه را کوچک کرده و قانون اندازه همان مانده.",
    "UNKNOWN": "علت باخت امروز هنوز روشن نیست.",
}


def _fa(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".translate(_DIGITS)


def _fa_int(value: int) -> str:
    return str(value).translate(_DIGITS)


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return doc if isinstance(doc, dict) else {}


def _tehran_day(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(TEHRAN).date().isoformat()


def _parse_utc(stamp: str | None) -> datetime | None:
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _today_realized(root: Path, day: str) -> float | None:
    path = root / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return None
    total = 0.0
    seen = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or row.get("event") != "CLOSE":
            continue
        closed = _parse_utc(row.get("closed_at") if isinstance(row.get("closed_at"), str) else None)
        if closed is None or _tehran_day(closed) != day:
            continue
        pnl = row.get("realized_pnl_usd")
        if isinstance(pnl, (int, float)) and not isinstance(pnl, bool):
            total += float(pnl)
            seen = True
    if not seen:
        return 0.0
    return round(total, 4)


def _names(opens: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for symbol in opens:
        label = _NAMES.get(str(symbol), "یک بازار دیگر")
        if label not in seen:
            seen.append(label)
    return seen


def _greeting(moment: datetime) -> str:
    hour = moment.astimezone(TEHRAN).hour
    if hour < 12:
        return "صبح بخیر"
    if hour < 18:
        return "عصر بخیر"
    return "شب بخیر"


_FA_STRATEGY = {
    "ts_momentum": "مومنتوم زمانی",
    "donchian_turtle": "شکست کانال",
    "dual_ma": "دو میانگین",
    "short_term_reversal": "بازگشت کوتاه",
    "rsi2_connors": "قدرت دو روزه",
    "bollinger_fade": "محو باند",
    "vol_breakout": "شکست نوسان",
    "cs_momentum": "مومنتوم مقطعی",
    "pairs_zscore": "جفت‌بازگشت",
    "turn_of_month": "چرخش ماه",
    "vol_target": "هدف نوسان",
    "low_vol": "نوسان پایین",
    "pre_fomc": "پیش از نشست",
    "wick_sweep": "جاروب سایه",
    "overnight_intraday": "بازده شب",
    "news_shock": "شوک خبر",
    "pump_token": "نام توکن",
}


_FA_FIX = {
    "news_cooldown_15": "درنگ خبر",
    "news_cooldown_30": "درنگ خبر",
    "news_cooldown_60": "درنگ خبر",
    "fade_first_spike_15": "محو جهش",
    "gold_atr_trail": "دنباله‌رو نوسان",
    "gold_time_stop": "توقف زمانی",
    "gold_partial_1r": "برداشت جزئی",
    "capital_tilt": "چرخش سرمایه",
    "entry_mtf_plus_family": "کیفیت ورود",
}


def _running_counts(root: Path) -> str:
    from architecture.markets.shadow_cycle import running_counts_fa

    return running_counts_fa(root)


def _helping(root: Path) -> str:
    """Which shadow fix is ahead on fresh closes. No Latin identifiers."""
    path = Path(root) / "reports" / "grok" / "PAPER" / "mega12_shadow.json"
    if not path.is_file():
        return "در آزمون تازه هنوز هیچ اصلاحی از بقیه جلو نیست."
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "در آزمون تازه هنوز هیچ اصلاحی از بقیه جلو نیست."
    name = _FA_FIX.get(str(doc.get("helping") or ""))
    fresh = doc.get("fresh_closes")
    if not name or not isinstance(fresh, int) or fresh <= 0:
        return "در آزمون تازه هنوز هیچ اصلاحی از بقیه جلو نیست."
    return f"در آزمون تازه، {_fa_int(fresh)} معاملهٔ تازه بررسی شد و جلوتر از بقیه {name} است و هنوز زنده نشده است."


def _shadow_leaders(root: Path) -> str:
    """One Persian line. Latin strategy ids never enter the note."""
    path = Path(root) / "reports" / "grok" / "PAPER" / "strategy_leaderboard.json"
    totals: dict[str, int] = {}
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        for row in doc.get("rows") or []:
            if not isinstance(row, dict):
                continue
            name = _FA_STRATEGY.get(str(row.get("id") or ""))
            if not name:
                continue
            totals[name] = totals.get(name, 0) + int(row.get("closes") or 0)
    leaders = [name for name, count in sorted(totals.items(), key=lambda item: (-item[1], item[0])) if count > 0][:3]
    if not leaders:
        return "در سایه هنوز راهبردی با معاملهٔ بسته‌شده پیشتاز نیست."
    return "پیشتازهای سایه: " + "، ".join(leaders) + ". هیچ‌کدام زنده نشده‌اند."


def compose_mehrdad_digest(root: Path, *, now: datetime | None = None) -> str:
    """Plain Persian. No codes, no order, no claim of a proven edge."""
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    day = _tehran_day(moment)
    paper = root / "reports" / "grok" / "PAPER"
    trader = _read(paper / "paper_trader_status.json")
    diagnosis = _read(paper / "daily_diagnosis.json")
    soak = _read(root / "reports" / "grok" / "M13_SOAK" / "soak_status.json")
    from architecture.mission.mehrdad_status import build_mehrdad_status

    status = build_mehrdad_status(root)
    equity = trader.get("mark_to_market_equity_usd")
    if not isinstance(equity, (int, float)) or isinstance(equity, bool):
        equity = status.get("equity_usd")
    opens = trader.get("open_positions") if isinstance(trader.get("open_positions"), dict) else {}
    change = _today_realized(root, day)
    cause = str(diagnosis.get("primary_cause") or "") if str(diagnosis.get("day") or "") == day else ""
    learned = _LEARNED.get(cause, "درس تازه‌ای برای این روز در پرونده نیست، و چیزی را حدس نزده.")
    improved = (
        "قانون تازه‌ای به کار زنده نرفت و همان احتیاط دیروز سر جایش ماند."
        if diagnosis.get("applied_to_live") is not True
        else "یک اصلاح روی کاغذ ثبت شده و هنوز به پول واقعی وصل نیست."
    )
    started = _parse_utc(soak.get("window_started_utc") if isinstance(soak.get("window_started_utc"), str) else None)
    hours = None if started is None else round((moment - started).total_seconds() / 3600.0, 1)
    pct = status.get("readiness_pct")
    names = _names(opens)
    name_text = "، ".join(names) if names else "هیچ"
    if isinstance(equity, (int, float)) and not isinstance(equity, bool):
        equity_line = f"سرمایهٔ کاغذی الان {_fa(float(equity))} دلار است."
    else:
        equity_line = "سرمایهٔ کاغذی الان در پرونده نیست."
    if change is None:
        change_line = "تغییر امروز در دفتر نیست."
    elif change > 0:
        change_line = f"معامله‌های بسته‌شدهٔ امروز {_fa(change)} دلار روی هم مثبت بوده‌اند."
    elif change < 0:
        change_line = f"معامله‌های بسته‌شدهٔ امروز {_fa(abs(change))} دلار روی هم منفی بوده‌اند."
    else:
        change_line = "امروز معاملهٔ بسته‌شده‌ای با نتیجهٔ ثبت‌شده نبوده است."
    if hours is None:
        soak_line = "ساعت آزمون پیوسته در پرونده نیست."
        problem = "ساعت آزمون پیوسته روشن نیست و به پول واقعی نمی‌رسیم."
    else:
        soak_line = f"آزمون پیوسته حدود {_fa(hours, 1)} ساعت از {_fa_int(int(SOAK_GOAL_H))} ساعت را آمده است."
        problem = "سود کاغذی هنوز پایدار نشده و به پول واقعی نمی‌رسیم."
    pct_text = _fa(float(pct), 0) if isinstance(pct, (int, float)) and not isinstance(pct, bool) else "نامشخص"
    return "\n".join([
        f"مهراد جان، {_greeting(moment)}.",
        "",
        equity_line,
        change_line,
        f"{_fa_int(len(opens))} موقعیت کاغذی باز است: {name_text}.",
        "",
        f"امروز یاد گرفت که {learned}",
        improved,
        "",
        f"آمادگی پول واقعی {pct_text} درصد است و کلید زنده خاموش است.",
        soak_line,
        "چند روش تازه در حال آزمایش‌اند و هنوز به معاملهٔ واقعی نرسیده‌اند.",
        "درس‌ها روی سایه ماندند و وزن زنده عوض نشد.",
        "اندازهٔ کاغذی طلا و توکن کوچک‌تر شد و هیچ وزنی بالا نرفت.",
        _helping(root),
        _running_counts(root),
        "اگر مدل پاسخ‌گو قطع باشد، وضعیت از پرونده خوانده می‌شود و معامله‌ای باز نمی‌شود.",
        "",
        f"مشکل: {problem}",
    ])
