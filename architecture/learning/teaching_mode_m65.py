"""M65 Persian Teaching Mode & Hooman Decision Journal.
Transforms paper trades and market cycles across Gold (M13), Oil (M13.1), and Multi-Market (M19)
into plain-Persian educational cards (`TeachingLessonFa`) and structured Hooman post-mortem
decision journal entries (`HoomanDecisionJournalEntry`).
Strictly PAPER_ONLY = True.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

PAPER_ONLY: bool = True

PERSIAN_QUANT_GLOSSARY: dict[str, dict[str, str]] = {
    "ATR": {
        "term": "ATR (میانگین محدودهٔ واقعی نوسان)",
        "simple_fa": "شاخصی که نشان می‌دهد قیمت یک دارایی در هر کندل یا روز به‌طور میانگین چقدر بالا و پایین می‌شود؛ از آن برای تنظیم فاصلهٔ حد ضرر (Stop-Loss) استفاده می‌کنیم تا با نوسان عادی بازار از معامله خارج نشویم.",
    },
    "Two-Source Witness": {
        "term": "Two-Source Witness (قانون شاهد دومنبعی)",
        "simple_fa": "قانون امنیتی AHOS که می‌گوید هیچ قیمتی یا خبری معتبر نیست مگر اینکه حداقل ۲ منبع مستقل (مثلاً قیمت لحظه‌ای اسپات و قرارداد آتی بورس شیکاگو) با اختلاف کمتر از ۰.۵٪ آن را تأیید کنند.",
    },
    "Drawdown": {
        "term": "Max Drawdown (حداکثر افت سرمایه از قله)",
        "simple_fa": "بیشترین درصد کاهش ارزش سبد کاغذی از بالاترین نقطه (قله) تا پایین‌ترین نقطه (دره) قبل از ثبت قلهٔ جدید؛ معیار اصلی سنجش درد و ریسک استراتژی.",
    },
    "DSR": {
        "term": "DSR (نسبت شارپ تعدیل‌شده برای آزمون‌های مکرر)",
        "simple_fa": "نسخهٔ سخت‌گیرانهٔ نسبت بازده به ریسک (Sharpe) که شانس تصادفی بودن سود در تست‌های متعدد (Backtest Overfitting) را جریمه و حذف می‌کند.",
    },
    "Brier Score": {
        "term": "Brier Score (امتیاز کالیبراسیون احتمال بریر)",
        "simple_fa": "معیار دقت پیش‌بینی‌های احتمالی بین ۰ تا ۱ (هرچه کمتر و نزدیک‌تر به صفر باشد یعنی احتمال‌های اعلام‌شده توسط سیستم به واقعیت نزدیک‌تر بوده‌اند).",
    },
}


@dataclass(frozen=True, slots=True)
class TeachingLessonFa:
    lesson_id: str
    market: str
    symbol: str
    regime_tag: str
    title_fa: str
    why_entered_fa: str
    what_happened_fa: str
    mistake_or_strength_fa: str
    key_takeaway_fa: str
    glossary_keys: tuple[str, ...]
    paper_only: bool = True


@dataclass(frozen=True, slots=True)
class HoomanDecisionJournalEntry:
    journal_id: str
    timestamp_iso: str
    market: str
    symbol: str
    decision_type: str  # "PAPER_ENTRY" | "PAPER_EXIT" | "WITNESS_HOLD" | "SAFETY_VETO"
    rationale_fa: str
    counterfactual_fa: str
    devils_advocate_note_fa: str
    emotion_bias_guard_fa: str
    outcome_status: str
    paper_only: bool = True


def build_teaching_lesson_from_cycle(cycle: Mapping[str, Any]) -> TeachingLessonFa:
    lid = str(cycle.get("lesson_id") or f"m65-{cycle.get('market', 'gold').lower()}-{cycle.get('cycle', 1)}")
    market = str(cycle.get("market") or "GOLD").upper()
    symbol = str(cycle.get("symbol") or "XAUUSD").upper()
    regime = str(cycle.get("regime_tag") or "BULL_TREND").upper()
    pnl = float(cycle.get("pnl_usd", 0.0))
    witness = str(cycle.get("witness_state") or "VERIFIED").upper()

    if witness != "VERIFIED":
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag=regime,
            title_fa=f"توقف هوشمند در بازار {market} ({symbol}) به دلیل عدم تطابق دو منبع قیمت",
            why_entered_fa="ورودی انجام نشد؛ قانون شاهد دومنبعی (Two-Source Witness) وضعیت را تأیید نکرد.",
            what_happened_fa=f"وضعیت شاهد روی {witness} قرار گرفت (تغییر اسپرد یا تعطیلی پایان هفتهٔ بازار).",
            mistake_or_strength_fa="نقطهٔ قوت سیستم: جلوگیری از ورود کاغذی بر اساس دادهٔ تک‌منبعی یا مبهم.",
            key_takeaway_fa="صبر کردن در زمان ابهام داده، مهم‌ترین اصل حفظ سرمایه است (UNKNOWN != SAFE).",
            glossary_keys=("Two-Source Witness", "Drawdown"),
            paper_only=True,
        )

    if pnl >= 0:
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag=regime,
            title_fa=f"تحلیل آموزشی چرخهٔ کاغذی {market} ({symbol}) در رژیم {regime}",
            why_entered_fa=f"تأیید هم‌زمان دو منبع مستقل قیمت ({witness}) و هم‌جهتی روند در رژیم {regime} با رعایت حد ضرر مبتنی بر ATR.",
            what_happened_fa=f"قیمت پس از ثبت سفارش کاغذی در مسیر پیش‌بینی حرکت کرد و نتیجهٔ کاغذی {pnl:+.2f} دلار ثبت شد.",
            mistake_or_strength_fa="نقطهٔ قوت: رعایت کامل حجم مجاز کاغذی (سقف ۱۰۰ دلار) و ثبت نظر مخالف وکیل مدافع شیطان پیش از ورود.",
            key_takeaway_fa="حتی معاملات موفق کاغذی نیز تا زمان تکمیل نمونهٔ آماری ۶ماهه و عبور از معیار DSR مجوز ورود به پول واقعی ندارند.",
            glossary_keys=("ATR", "Two-Source Witness", "DSR"),
            paper_only=True,
        )

    return TeachingLessonFa(
        lesson_id=lid,
        market=market,
        symbol=symbol,
        regime_tag=regime,
        title_fa=f"کالبدشکافی آموزشی ضرر کاغذی در {market} ({symbol}) — رژیم {regime}",
        why_entered_fa=f"ورود کاغذی پس از تأیید قیمت دومنبعی ({witness}) انجام شد اما بازار دچار برگشت سریع در رژیم {regime} گردید.",
        what_happened_fa=f"برخورد قیمت به حد ضرر محافظتی (ATR Stop) و ثبت نتیجهٔ کاغذی {pnl:+.2f} دلار بدون نقض سقف ریسک روزانه.",
        mistake_or_strength_fa="درس اصلاحی: در رژیم‌های پرنوسان یا چرخشی، فیلتر هم‌گرایی چند تایم‌فریم و بررسی فشار کلان (DXY و بهرهٔ حقیقی) باید سخت‌گیرانه‌تر شود.",
        key_takeaway_fa="حد ضرر کاغذی دقیقاً وظیفهٔ خود را انجام داد؛ یک ضرر کوچک و کنترل‌شده بسیار بهتر از رها کردن معامله بدون حد ضرر است.",
        glossary_keys=("ATR", "Drawdown", "Brier Score"),
        paper_only=True,
    )


def default_teaching_journal_fixtures() -> tuple[list[TeachingLessonFa], list[HoomanDecisionJournalEntry]]:
    raw_cycles = [
        {
            "lesson_id": "m65-gold-cycle-839",
            "market": "GOLD",
            "symbol": "XAUUSD",
            "regime_tag": "RANGE_CHOP",
            "pnl_usd": -24.80,
            "witness_state": "VERIFIED",
        },
        {
            "lesson_id": "m65-gold-cycle-846",
            "market": "GOLD",
            "symbol": "XAUUSD",
            "regime_tag": "BULL_TREND",
            "pnl_usd": 31.40,
            "witness_state": "VERIFIED",
        },
        {
            "lesson_id": "m65-oil-cycle-007",
            "market": "OIL",
            "symbol": "WTI",
            "regime_tag": "BULL_TREND",
            "pnl_usd": 14.20,
            "witness_state": "VERIFIED",
        },
        {
            "lesson_id": "m65-gold-weekend-guard",
            "market": "GOLD",
            "symbol": "XAUUSD",
            "regime_tag": "MACRO_SHOCK",
            "pnl_usd": 0.0,
            "witness_state": "UNRESOLVED",
        },
    ]
    lessons = [build_teaching_lesson_from_cycle(c) for c in raw_cycles]
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    journal = [
        HoomanDecisionJournalEntry(
            journal_id="hooman-jrnl-01",
            timestamp_iso=now_iso,
            market="GOLD",
            symbol="XAUUSD",
            decision_type="PAPER_EXIT",
            rationale_fa="خروج منظم در چرخهٔ ۸۳۹ پس از فعال شدن حد ضرر ATR؛ ثبت خودکار در دفتر درس‌های M49 و کالیبراسیون M58.",
            counterfactual_fa="اگر فیلتر رژیم چرخشی (RANGE_CHOP) فعال بود، از ورود در سقف کانال خودداری می‌شد.",
            devils_advocate_note_fa="هشدار وکیل مدافع شیطان (M58.3): احتمال بازگشت دلار (DXY) در ساعات پایانی بازار نیویورک.",
            emotion_bias_guard_fa="صفر درصد دخالت احساسی؛ عدم انجام معاملهٔ انتقامی (Revenge Trade) پس از بسته شدن موقعیت کاغذی.",
            outcome_status="LOGGED_AND_CONVERTED_TO_EVAL_FIXTURE",
            paper_only=True,
        ),
        HoomanDecisionJournalEntry(
            journal_id="hooman-jrnl-02",
            timestamp_iso=now_iso,
            market="OIL",
            symbol="WTI",
            decision_type="PAPER_ENTRY",
            rationale_fa="تأیید کاهش موجودی نفت خام آمریکا در گزارش هفتگی EIA و هم‌خوانی شاهد دومنبعی WTI.",
            counterfactual_fa="در صورت افزایش ناگهانی شاخص دلار یا تصمیم اوپک‌پلاس، حد ضرر ۱.۵ برابر ATR فعال خواهد شد.",
            devils_advocate_note_fa="ریسک کندی تقاضای پالایشگاهی در صورت تضعیف شاخص‌های صنعتی.",
            emotion_bias_guard_fa="حفظ سقف اندازهٔ موقعیت ۱۰۰ دلاری کاغذی (سهم ۱٪ از بانک‌رول ۱۰٬۰۰۰ دلاری).",
            outcome_status="CLEAN_PAPER_CYCLE",
            paper_only=True,
        ),
        HoomanDecisionJournalEntry(
            journal_id="hooman-jrnl-03",
            timestamp_iso=now_iso,
            market="DEX_TOKENS",
            symbol="RUGMEME",
            decision_type="SAFETY_VETO",
            rationale_fa="وتوی قطعی توسط شکارچی ۲۴مرحله‌ای توکن (M33) به دلیل قفل نبودن نقدینگی و مالیات فروش ۴۵٪.",
            counterfactual_fa="ورود به توکن‌های بدون قفل نقدینگی و قرارداد تأییدنشده منجر به زیان ۱۰۰٪ (Honeypot/Rug) می‌شود.",
            devils_advocate_note_fa="حجم معاملات ۲۴ساعته ساختگی (Wash Trading) و متمرکز در ۱۴ کیف پول بود.",
            emotion_bias_guard_fa="ایمنی در برابر FOMO (ترس از جا ماندن از پامپ‌های ظاهری).",
            outcome_status="VETO_UNSAFE_ENFORCED",
            paper_only=True,
        ),
    ]
    return lessons, journal


def generate_teaching_journal_snapshot(
    cycles: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    default_lessons, journal = default_teaching_journal_fixtures()
    lessons = [build_teaching_lesson_from_cycle(c) for c in cycles] if cycles is not None else default_lessons

    return {
        "schema": "ahos.teaching_mode_m65.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "lessons_count": len(lessons),
        "journal_entries_count": len(journal),
        "glossary_count": len(PERSIAN_QUANT_GLOSSARY),
        "latest_lesson_title_fa": lessons[0].title_fa if lessons else "",
        "latest_key_takeaway_fa": lessons[0].key_takeaway_fa if lessons else "",
        "lessons": [
            {
                "lesson_id": l.lesson_id,
                "market": l.market,
                "symbol": l.symbol,
                "regime_tag": l.regime_tag,
                "title_fa": l.title_fa,
                "why_entered_fa": l.why_entered_fa,
                "what_happened_fa": l.what_happened_fa,
                "mistake_or_strength_fa": l.mistake_or_strength_fa,
                "key_takeaway_fa": l.key_takeaway_fa,
                "glossary_keys": list(l.glossary_keys),
                "paper_only": l.paper_only,
            }
            for l in lessons
        ],
        "hooman_journal": [
            {
                "journal_id": j.journal_id,
                "timestamp_iso": j.timestamp_iso,
                "market": j.market,
                "symbol": j.symbol,
                "decision_type": j.decision_type,
                "rationale_fa": j.rationale_fa,
                "counterfactual_fa": j.counterfactual_fa,
                "devils_advocate_note_fa": j.devils_advocate_note_fa,
                "emotion_bias_guard_fa": j.emotion_bias_guard_fa,
                "outcome_status": j.outcome_status,
                "paper_only": j.paper_only,
            }
            for j in journal
        ],
        "glossary_fa": PERSIAN_QUANT_GLOSSARY,
    }
