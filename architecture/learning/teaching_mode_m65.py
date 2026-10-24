"""M65 Persian Teaching Mode & Hooman Decision Journal.
Transforms paper trades and market cycles across Gold (M13), Oil (M13.1), and Multi-Market (M19)
into plain-Persian educational cards (`TeachingLessonFa`) and structured Hooman post-mortem
decision journal entries (`HoomanDecisionJournalEntry`).
Strictly PAPER_ONLY = True.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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

    if regime == "MULTI_HORIZON_SHIELD" or symbol == "M60.R":
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag=regime,
            title_fa="سپر ضدضرر چندافقی ۱۰۰ دلاری (۳٪ روزانه · ۶٪ هفتگی · ۱۰٪ ماهانه)",
            why_entered_fa="قبل از هر برش LONG/SHORT با اهرم ۱۰×–۲۵×، سه سقف افت جداگانه از سرمایهٔ ۱۰۰ دلار محافظت می‌کند.",
            what_happened_fa="هیچ سقفی در ساک زنده شکسته نشده؛ shield_verdict=ARMED_GREEN و ذخیرهٔ کیف پول ≥۴۰٪ حفظ شده است.",
            mistake_or_strength_fa="نقطهٔ قوت: توقف خودکار و قرنطینهٔ کاغذی بدون نیاز به معاملهٔ واقعی.",
            key_takeaway_fa="حد ضرر روزانه ۳٪، هفتگی ۶٪ و ماهانه ۱۰٪ — PAPER_ONLY تا اثبات لبه.",
            glossary_keys=("Drawdown", "ATR"),
            paper_only=True,
        )

    if regime == "CROSS_ASSET_CONFLUENCE" or market == "MULTI_DESK":
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag=regime,
            title_fa="همگرایی سیگنال‌های ۷ بازار و ۶ قفل قبل از حساب واقعی (M60.F / M60.G)",
            why_entered_fa=(
                "فقط وقتی ماتریس همگرایی LONG/SHORT (طلا، نفت، کریپتو، سهام، FX و کلان) با شاهد دومنبعی "
                "و E>0 هم‌راستا باشد، پایلوت ۱۰۰ دلاری کاغذی ورود می‌زند."
            ),
            what_happened_fa="۶ قفل آمادگی (مأموریت‌ها، ساک/تطبیق، لبه/تیم قرمز، برش و پلهٔ سود، ۸ اندام/۴ مغز، HOLD) بررسی شد.",
            mistake_or_strength_fa="نقطهٔ قوت: معاملهٔ زنده بدون رفع صریح HOLD.flag ممکن نیست حتی اگر همهٔ قفل‌ها سبز باشند.",
            key_takeaway_fa="همگرایی ≠ اجازهٔ زنده؛ HOLD قانون نهایی است.",
            glossary_keys=("Two-Source Witness", "Drawdown"),
            paper_only=True,
        )

    if regime == "COMPOUNDING_LADDER" or market == "PILOT_100USD":
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag=regime,
            title_fa="پلهٔ قفل سود و برش‌های ایزولهٔ ۱۰۰ دلاری (M60.P)",
            why_entered_fa=(
                "پایلوت ۱۰۰ دلاری فقط با برش‌های ۱۰–۲۰ دلاری و اهرم ۱۰× تا ۲۵× (LONG/SHORT) و حداقل ۴۰٪ ذخیرهٔ کیف پول "
                "اجازهٔ ورود کاغذی دارد؛ لولهٔ زنده هنوز READY_LOCKED_BY_HOLD_FLAG است."
            ),
            what_happened_fa=(
                f"ارزش کاغذی فعلی {100 + pnl:.2f} دلار است (لبهٔ سودآوری اثبات‌نشده؛ ۰ معاملهٔ بسته از حداقل ۳۰ معامله)؛ پلهٔ قفل سود فقط پس از سود واقعی فعال می‌شود."
            ),
            mistake_or_strength_fa="نقطهٔ قوت: جدا کردن سود انباشته از اصل سرمایه قبل از افزایش ریسک.",
            key_takeaway_fa="رشد مرکب پله‌ای بدون قفل سود، اصل ۱۰۰ دلار را در معرض یک برش بد قرار می‌دهد — M60.P این را کاغذی ثبت می‌کند.",
            glossary_keys=("Drawdown", "ATR"),
            paper_only=True,
        )

    if str(cycle.get("regime_tag") or "").upper() == "WEEKEND_SESSION_GATE":
        return TeachingLessonFa(
            lesson_id=lid,
            market=market,
            symbol=symbol,
            regime_tag="WEEKEND_SESSION_GATE",
            title_fa="شنبه/یکشنبه: میزهای نقدی بدون قیمت تازه معامله نمی‌کنند",
            why_entered_fa="قانون سشن: طلا، نفت، سهام و FX در آخر هفته معمولاً بسته یا قیمت منقضی دارند.",
            what_happened_fa="سیستم به‌جای GREEN جعلی، رویداد SKIP با دلیل MARKET_CLOSED_OR_STALE ثبت کرد.",
            mistake_or_strength_fa="نقطهٔ قوت: صبر تا دوشنبه و شاهد VERIFIED واقعی.",
            key_takeaway_fa="کریپتو ممکن است باز باشد، اما لبهٔ سود هنوز اثبات‌نشده (۳۰ معاملهٔ بسته).",
            glossary_keys=("Two-Source Witness", "UNPROVEN_EDGE"),
            paper_only=True,
        )

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
        {
            "lesson_id": "m65-m60p-compounding-ladder",
            "market": "PILOT_100USD",
            "symbol": "M60.P",
            "regime_tag": "COMPOUNDING_LADDER",
            "pnl_usd": 0.0,
            "witness_state": "VERIFIED",
        },
        {
            "lesson_id": "m65-m60f-cross-asset-confluence",
            "market": "MULTI_DESK",
            "symbol": "M60.F",
            "regime_tag": "CROSS_ASSET_CONFLUENCE",
            "pnl_usd": 0.0,
            "witness_state": "VERIFIED",
        },
        {
            "lesson_id": "m65-m60r-risk-shield",
            "market": "PILOT_100USD",
            "symbol": "M60.R",
            "regime_tag": "MULTI_HORIZON_SHIELD",
            "pnl_usd": 0.0,
            "witness_state": "VERIFIED",
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


def _load_live_paper_cycles(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    st_path = root / "reports" / "grok" / "PAPER" / "paper_trader_status.json"
    if st_path.is_file():
        try:
            st = json.loads(st_path.read_text(encoding="utf-8"))
            for sym, pos in (st.get("open_positions") or {}).items():
                out.append({
                    "lesson_id": f"m65-live-open-{sym.lower()}",
                    "market": str(pos.get("desk") or "CRYPTO"),
                    "symbol": sym,
                    "regime_tag": "LIVE_PAPER_OPEN",
                    "pnl_usd": 0.0,
                    "witness_state": str(((st.get("witness") or {}).get(sym) or {}).get("verdict") or "VERIFIED"),
                })
            for sym, wit in (st.get("witness") or {}).items():
                if wit.get("verdict") in ("CONFLICT", "UNRESOLVED"):
                    out.append({
                        "lesson_id": f"m65-live-witness-{sym.lower()}",
                        "market": "OIL" if sym in ("BRENT", "WTI") else "MULTI_DESK",
                        "symbol": sym,
                        "regime_tag": "WITNESS_GUARD",
                        "pnl_usd": 0.0,
                        "witness_state": str(wit.get("verdict")),
                    })
                    break
        except Exception:
            pass
    probe_path = root / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    if probe_path.is_file():
        try:
            probe = json.loads(probe_path.read_text(encoding="utf-8"))
            if probe.get("session_gate", {}).get("weekend_tehran"):
                out.append({
                    "lesson_id": "m65-weekend-session-gate",
                    "market": "MULTI_DESK",
                    "symbol": "SESSION",
                    "regime_tag": "WEEKEND_SESSION_GATE",
                    "pnl_usd": 0.0,
                    "witness_state": "VERIFIED",
                })
        except Exception:
            pass
    return out


def _lessons_from_live_conflict_exam(repo: "Path") -> list[TeachingLessonFa]:
    import json
    from pathlib import Path

    path = Path(repo) / "reports" / "grok" / "M50" / "live_conflict_exam_items.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[TeachingLessonFa] = []
    for it in (payload.get("cards_fa") or [])[-6:]:
        iid = str(it.get("item_id") or "live-exam")
        prompt = str(it.get("prompt_fa") or "سؤال آزمون held-out")
        out.append(
            TeachingLessonFa(
                lesson_id=f"m65-exam-{iid}",
                market=str(it.get("desk") or "MULTI_DESK"),
                symbol=str(it.get("symbol") or "EXAM"),
                regime_tag="LIVE_HELDOUT_EXAM",
                title_fa=f"کارت آزمون held-out: {it.get('verdict_fa', '')} — {it.get('symbol', '')}",
                why_entered_fa=prompt,
                what_happened_fa=str(it.get("outcome_fa") or ""),
                mistake_or_strength_fa=str(it.get("verdict_fa") or ""),
                key_takeaway_fa=str(it.get("lesson_fa") or "") + " لبهٔ سود هنوز اثبات‌نشده (UNPROVEN_EDGE).",
                glossary_keys=("Brier Score", "DSR"),
            )
        )
    return out


def _lessons_from_historical_exam(repo: "Path") -> list[TeachingLessonFa]:
    path = Path(repo) / "reports" / "grok" / "M50" / "live_exam_receipt.json"
    if not path.is_file():
        return []
    try:
        hist = json.loads(path.read_text(encoding="utf-8")).get("historical_oos_episodes") or {}
    except Exception:
        return []
    out = []
    for i, card in enumerate((hist.get("cards_fa") or [])[:4]):
        if card.get("verdict_fa") != "نادرست":
            continue
        out.append(TeachingLessonFa(
            lesson_id=f"m65-hist-{i}", market="MACRO", symbol="EVENT", regime_tag="HISTORICAL_OOS",
            title_fa=f"درس تاریخی: {card.get('prompt_fa', '')}",
            why_entered_fa=str(card.get("prompt_fa") or ""),
            what_happened_fa="جهت ۲۰ جلسهٔ قبل با جلسهٔ بعد از رویداد نخواند.",
            mistake_or_strength_fa="نادرست",
            key_takeaway_fa=str(card.get("lesson_fa") or "") + " این نمره جدا از معامله‌گر زنده است.",
            glossary_keys=("DSR",),
        ))
    bss = hist.get("brier_skill_score")
    if bss is not None:
        out.append(TeachingLessonFa(
            lesson_id="m65-hist-brier", market="MACRO", symbol="EVENT", regime_tag="HISTORICAL_OOS",
            title_fa="کالیبراسیون احتمال روی رویدادهای تاریخی",
            why_entered_fa="احتمال ثابت ۰٫۵ همیشه بریر ۰٫۲۵ می‌دهد، حتی اگر برخی پیش‌بینی‌ها درست باشند.",
            what_happened_fa=f"بریر کالیبره‌شده {hist.get('brier_calibrated')} و مهارت نسبت به ۰٫۲۵ برابر {bss} است.",
            mistake_or_strength_fa="مهارت مثبت" if bss > 0 else "مهارتی بهتر از سکه دیده نشد",
            key_takeaway_fa="این نمره از روی داده‌های قبل از آزمون ساخته شده و معامله‌گر زنده را ارتقا نمی‌دهد.",
            glossary_keys=("Brier Score",),
        ))
    return out


def _lesson_source(lesson_id: str) -> str:
    if lesson_id.startswith("m65-hist-"):
        return "HISTORICAL_OOS"
    if lesson_id.startswith("m65-exam-"):
        return "LIVE_HELDOUT_EXAM"
    if lesson_id.startswith(("m65-live-", "m65-weekend-")):
        return "LIVE_PAPER_STATE"
    return "FIXTURE_ILLUSTRATIVE"


def _exam_summary(repo: "Path") -> dict[str, Any]:
    path = Path(repo) / "reports" / "grok" / "M50" / "live_conflict_exam_items.json"
    try:
        ex = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "NOT_RUN"}
    return {k: ex.get(k) for k in ("schema", "generated_at", "status", "method", "n_calibration_items", "n_heldout_items",
                                   "estimate_ability_theta", "theta_se", "theta_meaning", "heldout_accuracy",
                                   "abstain_baseline_accuracy", "skill_vs_abstain_baseline", "independent_episodes",
                                   "min_independent_episodes", "theta_at_bound", "item_types_heldout", "leaked",
                                   "promoted")} | {
        "cards_fa": (ex.get("cards_fa") or [])[-12:], "source": "reports/grok/M50/live_conflict_exam_items.json"}


def generate_teaching_journal_snapshot(
    cycles: Sequence[Mapping[str, Any]] | None = None,
    *,
    root: "Path | None" = None,
) -> dict[str, Any]:
    import json
    from pathlib import Path
    repo = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    default_lessons, journal = default_teaching_journal_fixtures()
    if cycles is not None:
        lessons = [build_teaching_lesson_from_cycle(c) for c in cycles]
    else:
        live_c = _load_live_paper_cycles(repo)
        exam_lessons = _lessons_from_live_conflict_exam(repo) + _lessons_from_historical_exam(repo)
        lessons = exam_lessons + [build_teaching_lesson_from_cycle(c) for c in live_c] + default_lessons

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
                "source": _lesson_source(l.lesson_id) if cycles is None else "CALLER_SUPPLIED_CYCLE",
            }
            for l in lessons
        ],
        "lesson_sources": {s: sum(1 for l in lessons if (_lesson_source(l.lesson_id) if cycles is None else "CALLER_SUPPLIED_CYCLE") == s)
                           for s in ("LIVE_HELDOUT_EXAM", "LIVE_PAPER_STATE", "FIXTURE_ILLUSTRATIVE", "CALLER_SUPPLIED_CYCLE")},
        "live_anomaly_exam": _exam_summary(repo),
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
