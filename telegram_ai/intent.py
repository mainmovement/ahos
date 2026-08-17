#!/usr/bin/env python3
"""AHOS Persian-first intent parser — DETERMINISTIC-FIRST (Wave-7 directive §12/§16 & Wave-19).

Law:
  - This layer is authoritative for command routing. AI may assist phrasing,
    NEVER command semantics and NEVER financial-record mutation.
  - Ambiguous input => intent UNKNOWN (never guess a financial action).
  - Anaphora («این توکن») resolves ONLY to an explicit conversation-context
    token supplied by the caller; without context the slot is None (honest).
  - Persian digit/letter normalization is total and test-pinned.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ------------------------------------------------------------------ normalization
_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_DIGIT_MAP = {c: str(i) for i, c in enumerate(_FA_DIGITS)}
_DIGIT_MAP.update({c: str(i) for i, c in enumerate(_AR_DIGITS)})

TOMAN_UNIT = 10  # 1 تومان = 10 ریال
_WORD_SCALARS = {"میلیون": 1_000_000, "هزار": 1_000, "میلیارد": 1_000_000_000}
_CRYPTO_UNITS = {
    "اتریوم": "ETH", "اتر": "ETH", "ETH": "ETH",
    "بیتکوین": "BTC", "بیت‌کوین": "BTC", "بیت کوین": "BTC", "BTC": "BTC",
    "سولانا": "SOL", "سول": "SOL", "SOL": "SOL",
    "تتر": "USDT", "USDT": "USDT",
}
_FIAT_UNITS = {"تومان": "IRT", "تومن": "IRT", "ریال": "IRR", "دلار": "USD"}

EVM_RE = re.compile(r"\b0x[0-9a-fA-F]{40}\b")
SOL_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

THIS_TOKEN = "CONTEXT:THIS_TOKEN"


def normalize(text: str) -> str:
    t = text.strip()
    t = t.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").replace("ـ", "")
    for fa, en in _DIGIT_MAP.items():
        t = t.replace(fa, en)
    t = re.sub(r"\s+", " ", t)
    return t


def _parse_amount(norm: str) -> tuple[float | None, str | None]:
    """Parse '۵ میلیون تومان' / '2 اتریوم' / '۵ میلیون از این' → (value, currency)."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(میلیون|هزار|میلیارد)?\s*"
                  r"(تومان|تومن|ریال|دلار|اتریوم|اتر|بیتکوین|بیت کوین|سولانا|سول|تتر|ETH|BTC|SOL|USDT)?",
                  norm)
    if not m:
        return None, None
    val = float(m.group(1))
    scalar = _WORD_SCALARS.get(m.group(2) or "", 1)
    unit = m.group(3)
    cur = None
    if unit in _FIAT_UNITS:
        cur = _FIAT_UNITS[unit]
        if cur == "IRR":
            scalar /= TOMAN_UNIT  # ریال → تومان normalization; canonical unit = IRT
            cur = "IRT"
    elif unit:
        cur = _CRYPTO_UNITS.get(unit)
    return val * scalar, cur


def _extract_address(text_raw: str) -> tuple[str | None, str | None]:
    m = EVM_RE.search(text_raw)
    if m:
        return m.group(0).lower(), "evm"
    m = SOL_RE.search(text_raw)
    if m:
        return m.group(0), "solana"
    return None, None


def _portion(norm: str) -> float | None:
    if "نصف" in norm or "نیم" in norm:
        return 0.5
    if "همه" in norm or "کامل" in norm or "تمام" in norm:
        return 1.0
    if "ربع" in norm:
        return 0.25
    return None


@dataclass
class ParseResult:
    intent: str                     # Intent name or UNKNOWN
    confidence: str                 # HIGH (exact rule) | LOW (partial) | NONE
    rule_id: str                    # probe-able rule reference
    slots: dict = field(default_factory=dict)
    normalized: str = ""
    needs_context: bool = False     # anaphora present, caller must supply context token


# ------------------------------------------------------------------ rule table
def parse(text: str, context_token: dict | None = None) -> ParseResult:
    """context_token: {'address':..., 'chain':...} supplied by the deterministic session store."""
    norm = normalize(text)
    addr, chain = _extract_address(text)
    tok = {"address": addr, "chain": chain} if addr else None

    def token_slot() -> tuple[dict | None, bool]:
        if tok:
            return tok, False
        if "این" in norm or "اون" in norm or norm.rstrip("؟?").endswith("ش"):
            return (context_token or None), context_token is None
        return None, False

    def result(intent, conf, rule, **slots):
        token, needs = token_slot()
        if token is not None and "token" not in slots:
            slots["token"] = token
        return ParseResult(intent, conf, rule, slots, norm, needs)

    amount, cur = _parse_amount(norm)

    # --- BUY / position logging (deterministic ledger candidate) ---
    if re.search(r"خرید(م|یم|ه شده| کردم)?\b", norm) and amount is not None:
        return result("BUY_LOG", "HIGH", "R-BUY-01", amount=amount, currency=cur)

    # --- sell advice queries (INFO-ONLY policy enforced at response layer) ---
    if "بفروشم" in norm or "بفروشیم" in norm:
        return result("SELL_ADVICE_QUERY", "HIGH", "R-SELL-01", portion=_portion(norm))
    if "سیو سود" in norm or "سیو‌سود" in norm:
        return result("TAKE_PROFIT_QUERY", "HIGH", "R-TP-01", portion=_portion(norm))

    # --- P/L ---
    if re.search(r"(چند درصد|چقدر).*(سود|ضرر|زیان)", norm) or "سود دارم" in norm or "ضرر دارم" in norm:
        return result("PNL_QUERY", "HIGH", "R-PNL-01")

    # --- Why Scored (چرا امتیاز گرفته) ---
    if re.search(r"چرا.*(امتیاز|اسکور|نمره)", norm) or re.search(r"(علت|دلیل).*(امتیاز|اسکور|نمره)", norm):
        return result("WHY_SCORED", "HIGH", "R-WHY-SCORE-01")

    # --- Risk Analysis (ریسک این توکن چیست) ---
    if re.search(r"ریسک.*(چیست|چیه|چقدره|دارد|داره)", norm) or "ریسک این" in norm:
        return result("RISK_ANALYSIS", "HIGH", "R-RISK-01")

    # --- What is Unknown (چه چیزی نامعلوم است) ---
    if re.search(r"(چی|چه چیزی|چه فیلدی|چه فیلدهایی).*(نامعلوم|نامشخص|ناشناخته|کمبود|ناپیدا)", norm) or "نامعلوم" in norm or "نامشخص" in norm:
        return result("WHAT_IS_UNKNOWN", "HIGH", "R-UNKNOWN-01")

    # --- Position Status (وضعیت این پوزیشن) ---
    if re.search(r"(وضعیت|شرایط).*(پوزیشن|معامله|خرید من|پوزیشنم)", norm):
        return result("POSITION_STATUS", "HIGH", "R-POS-STAT-01")

    # --- Why Alerted (چرا هشدار صادر شد) ---
    if re.search(r"(چرا|علت|دلیل).*(هشدار|آلرت|پیام|اخطار)", norm):
        return result("WHY_ALERTED", "HIGH", "R-WHY-ALERT-01")

    # --- Invalidation Conditions (شرایط ابطال فرصت) ---
    if re.search(r"(چی|چه چیزی|چه شرطی).*(invalid|باطل|ابطال|بی اعتبار)", norm) or "شرط ابطال" in norm or "شرایط ابطال" in norm:
        return result("INVALIDATION_CONDITIONS", "HIGH", "R-INV-01")

    # --- Market Overview (آخرین وضعیت بازار) ---
    if re.search(r"(آخرین|وضعیت|خلاصه).*(بازار|مارکت|کلی)", norm) or "اوضاع بازار" in norm:
        return result("MARKET_OVERVIEW", "HIGH", "R-MKT-01")

    # --- System Health & Diagnostics (سلامت سامانه / وضعیت سیستم) ---
    if re.search(r"(وضعیت|سلامت).*(زمان‌بند|زمانبند|اسکجولر|قفل)", norm) or "وضعیت زمان بند" in norm:
        return result("SCHEDULER_STATUS", "HIGH", "R-SCHED-STAT-01")
    if re.search(r"(وضعیت|سلامت|چک).*(دیتابیس|دیتابیس‌ها|پایگاه داده|بانک اطلاعات)", norm):
        return result("DATABASE_STATUS", "HIGH", "R-DB-STAT-01")
    if re.search(r"(وضعیت|سلامت).*(پرووایدر|پرووایدرها|منابع داده|فید)", norm):
        return result("PROVIDERS_STATUS", "HIGH", "R-PROV-STAT-01")
    if re.search(r"(وضعیت|شکاف|گپ).*(رصد|مشاهده|مشاهدات|اسلات)", norm) or "شکاف های رصدی" in norm:
        return result("OBSERVATION_GAPS_STATUS", "HIGH", "R-GAPS-STAT-01")
    if re.search(r"(وضعیت|گیت).*(e01|e-01|اعتبارسنجی|آزمایش)", norm):
        return result("E01_STATUS", "HIGH", "R-E01-STAT-01")
    if re.search(r"(وضعیت|گزارش).*(معاملات کاغذی|پوزیشن ها|پورتفولیو|پیپر)", norm) or "معاملات کاغذی" in norm:
        return result("PAPER_TRADING_STATUS", "HIGH", "R-PT-STAT-01")
    if re.search(r"(وضعیت|روتر).*(هوش مصنوعی|مدل ها|ai|nvidia|nim)", norm):
        return result("AI_STATUS", "HIGH", "R-AI-STAT-01")
    if re.search(r"(آخرین|وضعیت).*(چرخه|سایکل|ران|اجرا)", norm):
        return result("LAST_CYCLE_STATUS", "HIGH", "R-CYCLE-STAT-01")
    if re.search(r"(سلامت|هلث|وضعیت|کارکرد).*(سیستم|سامانه|سرویس|سرور|اپلیکیشن)", norm) or "سلامت سیستم" in norm or "وضعیت سامانه" in norm:
        return result("SYSTEM_HEALTH", "HIGH", "R-HEALTH-01")

    # --- crypto news digest («امروز چه خبر؟» / «اخبار کریپتو») ---
    if re.search(r"(چه خبر|چیه خبر|خبرها|اخبار|نیوز)", norm):
        scope = "TOKEN" if tok else "MARKET"
        return result("NEWS_DIGEST", "HIGH", "R-NEWS-01", scope=scope)

    # --- open-ended "what should I buy?" advisory ---
    if re.search(r"(چی|چه چیزی|کدوم|کدام).*(بخرم|بخریم|وارد بشم|سرمایه)", norm) \
            or "چی بخرم" in norm or "پیشنهاد" in norm:
        return result("WHAT_TO_BUY", "HIGH", "R-ADVISE-01")

    # --- entry timing («کی وارد بشم؟») ---
    if re.search(r"(کی|چه زمانی|چه وقت).*(بخرم|وارد|ورود)", norm):
        return result("ENTRY_TIMING", "HIGH", "R-ENTRY-TIME-01")

    # --- exit feasibility («می‌تونم بفروشمش؟» / «نقدشوندگی») ---
    if re.search(r"(می ?تونم|میشه|امکان).*(بفروش|خارج|نقد)", norm) \
            or "نقدشوندگی" in norm or "قابل فروش" in norm:
        return result("EXITABILITY_QUERY", "HIGH", "R-EXIT-01")

    # --- whale / holder distribution («نهنگ‌ها») ---
    if re.search(r"(نهنگ|والی|هولدر|توزیع مالکیت|دارندگان)", norm):
        return result("WHALE_QUERY", "HIGH", "R-WHALE-01")

    # --- virality / hype («وایرال شده؟» / «چقدر ترند شده») ---
    # Deliberately NOT matching bare "پامپ": phrases like «حتماً پامپ میشه نه؟»
    # are leading statements seeking agreement, not questions about evidence.
    # Answering them as a data query would let the user's hope set the agenda.
    if re.search(r"(وایرال|ترند|هایپ)", norm) and not re.search(r"(حتما|قطعا|مطمئن)", norm):
        return result("VIRALITY_QUERY", "HIGH", "R-VIRAL-01")

    # --- AI council opinion («نظر هوش مصنوعی‌ها چیه؟») ---
    if re.search(r"(نظر|عقیده|رای).*(هوش مصنوعی|مدل|شورا|دستیار)", norm) \
            or "شورا چی میگه" in norm:
        return result("COUNCIL_OPINION", "HIGH", "R-COUNCIL-01")

    # --- greetings / smalltalk: answer warmly, then steer to capability ---
    if re.fullmatch(r"(سلام|درود|های|هی|سلام علیکم)[\s!.،؟?]*", norm) \
            or re.fullmatch(r"(خوبی|چطوری|حالت چطوره)[\s!.،؟?]*", norm):
        return result("GREETING", "HIGH", "R-GREET-01")

    # --- token check / status ---
    if "بررسی کن" in norm or "بررسیش کن" in norm or "چک کن" in norm or "چکش کن" in norm:
        return result("CHECK_TOKEN", "HIGH", "R-CHECK-01")
    if re.search(r"(وضعیت|شرایط).*(چطور|چجور|چیه|خوبه|اوکی)", norm) or "شرایطش چطوره" in norm:
        return result("TOKEN_STATUS", "HIGH", "R-STATUS-01")

    # --- watchlist ---
    if "زیر نظر بگیر" in norm or "واچ" in norm or "نظارت کن" in norm:
        return result("WATCH_TOKEN", "HIGH", "R-WATCH-01")

    # --- alerts ---
    if "خبر بده" in norm or "اطلاع بده" in norm or "هشدار بده" in norm:
        cond = "CONDITIONS_DETERIORATE" if re.search(r"خراب|بد شد|ریسک|افت", norm) else "GENERIC"
        return result("ALERT_SET", "HIGH", "R-ALERT-01", condition=cond)

    # --- why rejected ---
    if re.search(r"چرا.*رد", norm):
        return result("WHY_REJECTED", "HIGH", "R-WHY-01")

    # --- discovery queries ---
    if re.search(r"فرصت.*(جدید|تازه|نو)", norm):
        return result("NEW_OPPORTUNITIES", "HIGH", "R-NEW-01")
    if re.search(r"بهترین.*(فرصت|توکن)", norm) or "فرصت های امروز" in norm:
        tf = "today" if "امروز" in norm else "current"
        return result("TOP_OPPORTUNITIES", "HIGH", "R-TOP-01", timeframe=tf)
    if re.search(r"ریسک.*(پایین|کم)", norm) or ("امنیتی" in norm and "پایین" in norm):
        return result("LOW_RISK_FILTER", "HIGH", "R-LOWRISK-01")

    # --- bare address / symbol => check intent ---
    if addr:
        return result("CHECK_TOKEN", "HIGH", "R-CHECK-02")
    if "راهنما" in norm or "کمک" in norm:
        return result("HELP", "HIGH", "R-HELP-01")
    return ParseResult("UNKNOWN", "NONE", "R-UNKNOWN", {}, norm, False)


# Info-only policy (law): these intents must be answered WITHOUT buy/sell directives.
INFO_ONLY_INTENTS = {
    "SELL_ADVICE_QUERY", "TAKE_PROFIT_QUERY", "PNL_QUERY", "TOKEN_STATUS",
    "TOP_OPPORTUNITIES", "NEW_OPPORTUNITIES", "WHY_REJECTED", "WHY_SCORED",
    "RISK_ANALYSIS", "WHAT_IS_UNKNOWN", "POSITION_STATUS", "WHY_ALERTED",
    "INVALIDATION_CONDITIONS", "MARKET_OVERVIEW", "SYSTEM_HEALTH",
    "SCHEDULER_STATUS", "DATABASE_STATUS", "PROVIDERS_STATUS",
    "OBSERVATION_GAPS_STATUS", "E01_STATUS", "PAPER_TRADING_STATUS",
    "AI_STATUS", "LAST_CYCLE_STATUS",
    # Conversational advisory intents (Wave-25). All are strictly informational:
    # they explain evidence and options, and always end with the mandated footer
    # «تصمیم نهایی با کاربر است.» — never an executable order.
    "NEWS_DIGEST", "WHAT_TO_BUY", "ENTRY_TIMING", "EXITABILITY_QUERY",
    "WHALE_QUERY", "VIRALITY_QUERY", "COUNCIL_OPINION", "GREETING",
}
# Intents permitted to write the position ledger (deterministic command layer only).
LEDGER_MUTATING_INTENTS = {"BUY_LOG"}
