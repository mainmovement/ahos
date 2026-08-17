#!/usr/bin/env python3
"""AHOS Cognitive Panel (Wave-26) — the 100-mind council, made executable.

The registry of great thinkers was, until now, decoration: a YAML file nothing
read and a test that only counted it. This module turns it into working
analysis.

THE DESIGN DECISION THAT MATTERS
--------------------------------
There are two ways to build a "council of 100 great minds":

  (a) Ask an LLM to role-play Kahneman and report what "he" thinks.
  (b) Take the man's actual published finding -- losses loom ~2x larger than
      gains -- and execute it as a deterministic check against real numbers.

(a) is theatre. It fabricates opinions, cannot be audited, produces a different
answer every run, and collapses entirely when the network is filtered. (b) is
analysis: it runs offline, gives the same answer twice, and every verdict cites
the principle and publication it came from.

This module does (b). Each lens is a pure function over measured evidence,
derived from a principle in `lenses.LENS_PILOT_REGISTRY`. No lens may invent a
number, and a lens with insufficient input returns ABSTAIN -- never a guess.

VOTING LAW
----------
Lenses do not average into a score. Averaging lets nine mild approvals drown
one lens shouting "this is a honeypot". Instead:

  * Any lens may raise a VETO, and a single VETO sinks the verdict. This is
    Munger's inversion principle applied to the panel itself.
  * ABSTAIN is recorded, never counted as approval. Gödel's lens exists
    precisely to keep unknowns from being laundered into confidence.
  * The panel is ADVISORY over the deterministic engine, exactly like the AI
    council: it can lower conviction, never raise it past the math.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from .lenses import LENS_PILOT_REGISTRY

PANEL_VERSION = "AHOS-PANEL-v1"

# A lens returns one of these stances.
STANCES = ("APPROVE", "CAUTION", "VETO", "ABSTAIN")


@dataclass
class LensOpinion:
    """One lens's reading of one token. Always traceable to a citation."""
    lens_id: str
    identity: str
    principle_id: str
    stance: str
    reason: str                      # Persian, user-facing
    citation_ref: str = ""
    metric: float | None = None      # the number the judgement rests on
    severity: int = 0                # 0..3; drives ordering, not averaging

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PanelVerdict:
    subject: str
    verdict: str                     # APPROVE | CAUTION | VETO | INSUFFICIENT_EVIDENCE
    opinions: list[LensOpinion] = field(default_factory=list)
    vetoes: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)
    abstentions: list[str] = field(default_factory=list)
    coverage: float = 0.0            # fraction of lenses with enough data to speak
    advisory_only: bool = True
    version: str = PANEL_VERSION
    computed_ts: float = 0.0

    @property
    def is_blocking(self) -> bool:
        return self.verdict == "VETO"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["opinions"] = [o.to_dict() for o in self.opinions]
        return d

    def summary_persian(self) -> str:
        icon = {"APPROVE": "🟢", "CAUTION": "🟡",
                "VETO": "🔴", "INSUFFICIENT_EVIDENCE": "⚪"}
        lines = [f"{icon.get(self.verdict, '⚪')} شورای تحلیلی — {self.subject}",
                 "",
                 f"حکم: **{self.verdict}** "
                 f"(پوشش داده: {self.coverage:.0%})",
                 f"موافق: {len(self.approvals)} | احتیاط: {len(self.cautions)} | "
                 f"وتو: {len(self.vetoes)} | سکوت: {len(self.abstentions)}"]
        blocking = [o for o in self.opinions if o.stance == "VETO"]
        warned = [o for o in self.opinions if o.stance == "CAUTION"]
        if blocking:
            lines += ["", "🚫 وتوها:"]
            lines += [f" • {o.identity.split('(')[0].strip()}: {o.reason}"
                      for o in blocking]
        if warned:
            lines += ["", "⚠️ هشدارها:"]
            lines += [f" • {o.identity.split('(')[0].strip()}: {o.reason}"
                      for o in warned[:5]]
        if self.abstentions:
            lines += ["", f"❓ {len(self.abstentions)} دیدگاه به دلیل نبود داده "
                          f"سکوت کردند (سکوت = تأیید نیست)."]
        lines += ["", "این شورا مشورتی است و بر موتور قطعی اولویت ندارد."]
        return "\n".join(lines)


# ---------------------------------------------------------------- helpers --

def _f(x: Any) -> float | None:
    """Coerce to float, but keep None as None. Never turn missing into zero."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def _m(cand, name: str) -> float | None:
    return _f(getattr(getattr(cand, "metrics", None), name, None))


def _s(cand, name: str) -> Any:
    return getattr(getattr(cand, "security", None), name, None)


def _op(lens_id: str, principle_id: str, stance: str, reason: str,
        metric: float | None = None, severity: int = 0) -> LensOpinion:
    card = LENS_PILOT_REGISTRY.get(lens_id)
    citation = ""
    identity = lens_id
    if card is not None:
        identity = card.identity
        for p in card.verified_principles:
            if p.get("principle_id") == principle_id:
                citation = p.get("citation_ref", "")
                break
        # An unresolved principle_id means the lens cites something the card
        # does not contain. Mark it explicitly rather than emitting a blank
        # citation that looks like an oversight.
        if not citation and principle_id != "ERROR":
            citation = f"UNRESOLVED:{lens_id}:{principle_id}"
    return LensOpinion(lens_id=lens_id, identity=identity,
                       principle_id=principle_id, stance=stance, reason=reason,
                       citation_ref=citation, metric=metric, severity=severity)


# ------------------------------------------------------------------ lenses --
# Each function: (candidate, context) -> LensOpinion
# `context` may carry score_report, exitability, virality, whale, narrative.

def lens_munger_inversion(cand, ctx) -> LensOpinion:
    """Inversion: enumerate the ways this kills you BEFORE admiring the upside."""
    ex = ctx.get("exitability")
    fatal: list[str] = []
    if _s(cand, "is_honeypot") is True:
        fatal.append("هانی‌پات")
    tax = _f(_s(cand, "sell_tax_pct"))
    if tax is not None and tax >= 25.0:
        fatal.append(f"مالیات فروش {tax:.0f}٪")
    if _s(cand, "has_mint_authority") is True:
        fatal.append("اختیار ضرب فعال")
    if ex is not None and getattr(ex, "hard_vetoes", None):
        fatal.extend(list(ex.hard_vetoes)[:2])

    if fatal:
        return _op("LENS-MUNGER", "INVERSION-01", "VETO",
                   "پیش از سود، راه‌های نابودی بررسی شد و یافت شد: "
                   + "، ".join(fatal[:3]), severity=3)
    if _s(cand, "is_honeypot") is None and tax is None:
        return _op("LENS-MUNGER", "INVERSION-01", "ABSTAIN",
                   "داده امنیتی برای وارونه‌سازی در دسترس نیست")
    return _op("LENS-MUNGER", "INVERSION-01", "APPROVE",
               "هیچ‌یک از مسیرهای شناخته‌شده نابودی فعال نیست")


def lens_taleb_ruin(cand, ctx) -> LensOpinion:
    """Non-ergodicity: a position you cannot exit is a ruin risk, not a trade."""
    ex = ctx.get("exitability")
    if ex is None:
        return _op("LENS-TALEB", "CONVEXITY-01", "ABSTAIN",
                   "بدون محاسبه خروج، ریسک ورشکستگی قابل ارزیابی نیست")
    frac = _f(getattr(ex, "realizable_fraction", None))
    if getattr(ex, "verdict", "") == "TRAPPED":
        return _op("LENS-TALEB", "CONVEXITY-01", "VETO",
                   "سرمایه‌ای که خارج نمی‌شود، ریسک ویرانی است نه معامله",
                   metric=frac, severity=3)
    if frac is None:
        return _op("LENS-TALEB", "CONVEXITY-01", "ABSTAIN",
                   "کسر قابل بازیافت نامعلوم است")
    if frac < 0.75:
        return _op("LENS-TALEB", "CONVEXITY-01", "CAUTION",
                   f"تنها {frac:.0%} از ارزش نمایشی قابل برداشت است",
                   metric=frac, severity=2)
    return _op("LENS-TALEB", "CONVEXITY-01", "APPROVE",
               f"مسیر خروج باز است ({frac:.0%} قابل بازیافت)", metric=frac)


def lens_nash_equilibrium(cand, ctx) -> LensOpinion:
    """Pool stability as an N-player withdrawal game: who runs for the door first?"""
    liq = _m(cand, "liquidity_usd")
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if liq is None or top10 is None:
        return _op("LENS-NASH", "NASH-01", "ABSTAIN",
                   "بدون نقدینگی و تمرکز مالکیت، تعادل خروج مدل‌سازی نمی‌شود")
    if top10 >= 80.0:
        return _op("LENS-NASH", "NASH-01", "VETO",
                   f"{top10:.0f}٪ در دست ۱۰ کیف‌پول: تعادل ناپایدار، "
                   f"هر خروج زودهنگام بقیه را به فرار وامی‌دارد",
                   metric=top10, severity=3)
    if top10 >= 60.0:
        return _op("LENS-NASH", "NASH-01", "CAUTION",
                   f"تمرکز {top10:.0f}٪ — انگیزه خروج یک‌جانبه بالاست",
                   metric=top10, severity=2)
    return _op("LENS-NASH", "NASH-01", "APPROVE",
               f"توزیع مالکیت تعادل خروج را پایدار نگه می‌دارد ({top10:.0f}٪)",
               metric=top10)


def lens_kahneman_fomo(cand, ctx) -> LensOpinion:
    """Loss aversion / anti-FOMO: hype rising while the exit door narrows."""
    viral = ctx.get("virality")
    liq = _m(cand, "liquidity_usd")
    if viral is None or liq is None:
        return _op("LENS-KAHNEMAN", "BEHAV-01", "ABSTAIN",
                   "برای سنجش هیجان خرید، داده کافی نیست")
    label = getattr(viral, "label", "UNKNOWN")
    if getattr(viral, "wash_suspected", False):
        return _op("LENS-KAHNEMAN", "BEHAV-01", "VETO",
                   "الگوی معامله صوری: هیجان ساختگی است", severity=3)
    if label == "VIRAL" and liq < 20_000.0:
        return _op("LENS-KAHNEMAN", "BEHAV-01", "CAUTION",
                   f"هیجان بالا اما نقدینگی فقط ${liq:,.0f} — "
                   f"الگوی کلاسیک خستگی خریدار خرد",
                   metric=liq, severity=2)
    if getattr(viral, "is_paid_promotion", False):
        return _op("LENS-KAHNEMAN", "BEHAV-01", "CAUTION",
                   "توجه خریداری‌شده است، نه ارگانیک", severity=1)
    return _op("LENS-KAHNEMAN", "BEHAV-01", "APPROVE",
               "نشانه‌ای از هیجان‌زدگی مصنوعی دیده نمی‌شود")


def lens_mandelbrot_tails(cand, ctx) -> LensOpinion:
    """Fat tails: thin pools do not move normally, they gap."""
    liq = _m(cand, "liquidity_usd")
    ch1h = _m(cand, "price_change_1h")
    if liq is None:
        return _op("LENS-MANDELBROT", "FRACTAL-01", "ABSTAIN",
                   "بدون نقدینگی، دامنه نوسان قابل کران‌گذاری نیست")
    if ch1h is not None and abs(ch1h) >= 100.0 and liq < 50_000.0:
        return _op("LENS-MANDELBROT", "FRACTAL-01", "CAUTION",
                   f"نوسان {ch1h:+.0f}٪ در استخر ${liq:,.0f}: "
                   f"دم‌های سنگین، نه توزیع نرمال",
                   metric=ch1h, severity=2)
    if liq < 10_000.0:
        return _op("LENS-MANDELBROT", "FRACTAL-01", "CAUTION",
                   f"استخر کم‌عمق (${liq:,.0f}) — شوک قیمتی جهشی است نه پیوسته",
                   metric=liq, severity=2)
    return _op("LENS-MANDELBROT", "FRACTAL-01", "APPROVE",
               f"عمق استخر برای جذب شوک کافی است (${liq:,.0f})", metric=liq)


def lens_schneier_weakest_link(cand, ctx) -> LensOpinion:
    """Security is a chain: the unverified link decides the strength."""
    checks = {
        "قرارداد تأییدنشده": _s(cand, "is_contract_verified") is False,
        "اختیار انجماد فعال": _s(cand, "has_freeze_authority") is True,
        "اختیار ضرب فعال": _s(cand, "has_mint_authority") is True,
    }
    failed = [k for k, v in checks.items() if v]
    unknown = sum(1 for n in ("is_contract_verified", "has_freeze_authority",
                              "has_mint_authority") if _s(cand, n) is None)
    rug = _f(_s(cand, "deployer_past_rug_count"))
    if rug is not None and rug > 0:
        return _op("LENS-SCHNEIER", "SEC-PROCESS-01", "VETO",
                   f"سازنده قرارداد {rug:.0f} سابقه رواگ دارد",
                   metric=rug, severity=3)
    if failed:
        return _op("LENS-SCHNEIER", "SEC-PROCESS-01", "CAUTION",
                   "ضعیف‌ترین حلقه زنجیره: " + "، ".join(failed), severity=2)
    if unknown >= 2:
        return _op("LENS-SCHNEIER", "SEC-PROCESS-01", "ABSTAIN",
                   f"{unknown} بررسی امنیتی بی‌پاسخ مانده — زنجیره ناقص است")
    return _op("LENS-SCHNEIER", "SEC-PROCESS-01", "APPROVE",
               "حلقه‌های امنیتی بررسی‌شده سالم‌اند")


def lens_godel_unknowns(cand, ctx) -> LensOpinion:
    """Incompleteness: know what the system cannot know, and refuse to fill it in."""
    report = ctx.get("score_report")
    unknowns = list(getattr(report, "missing_unknowns", []) or []) if report else []
    core = [n for n in ("price_usd", "liquidity_usd") if _m(cand, n) is None]
    if core:
        return _op("LENS-GODEL", "GODEL-01", "VETO",
                   f"داده‌های بنیادی غایب‌اند ({'، '.join(core)}) — "
                   f"هر امتیازی روی این پایه توهم دقت است",
                   severity=3)
    if len(unknowns) >= 5:
        return _op("LENS-GODEL", "GODEL-01", "CAUTION",
                   f"{len(unknowns)} مجهول ثبت شده — "
                   f"اطمینان باید متناسب کاهش یابد",
                   metric=float(len(unknowns)), severity=2)
    return _op("LENS-GODEL", "GODEL-01", "APPROVE",
               "مجهولات صریح و در حد قابل قبول‌اند")


def lens_marks_second_level(cand, ctx) -> LensOpinion:
    """Second-level thinking: is the quality already in the price?"""
    report = ctx.get("score_report")
    viral = ctx.get("virality")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    if score is None or viral is None:
        return _op("LENS-MARKS", "SECOND-LEVEL-01", "ABSTAIN",
                   "برای مقایسه امتیاز با هیجان جمعی، داده کافی نیست")
    vscore = _f(getattr(viral, "score", None)) or 0.0
    if vscore >= 60.0 and score < 55.0:
        return _op("LENS-MARKS", "SECOND-LEVEL-01", "CAUTION",
                   f"جمع هیجان‌زده است ({vscore:.0f}) اما کیفیت پایین است "
                   f"({score:.0f}) — خریدن از دست جمعیت",
                   metric=score, severity=2)
    if vscore <= 30.0 and score >= 70.0:
        return _op("LENS-MARKS", "SECOND-LEVEL-01", "APPROVE",
                   f"کیفیت بالا ({score:.0f}) بدون ازدحام — "
                   f"سطح دوم تفکر این را می‌پسندد", metric=score)
    return _op("LENS-MARKS", "SECOND-LEVEL-01", "APPROVE",
               f"نسبت کیفیت به هیجان متعادل است ({score:.0f}/{vscore:.0f})",
               metric=score)


def lens_bayes_base_rate(cand, ctx) -> LensOpinion:
    """Base rates: most new micro-caps fail. Evidence must overcome that prior."""
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    if score is None:
        return _op("LENS-BAYES", "BAYES-01", "ABSTAIN",
                   "بدون امتیاز، به‌روزرسانی احتمال پسین ممکن نیست")
    # Deliberately harsh prior: the overwhelming majority of new pairs die.
    if score < 40.0:
        return _op("LENS-BAYES", "BAYES-01", "CAUTION",
                   f"شواهد ({score:.0f}) برای غلبه بر نرخ پایه بالای شکست "
                   f"در توکن‌های نوظهور کافی نیست",
                   metric=score, severity=2)
    return _op("LENS-BAYES", "BAYES-01", "APPROVE",
               f"شواهد به اندازه کافی از نرخ پایه فاصله دارد ({score:.0f})",
               metric=score)


def lens_shannon_signal(cand, ctx) -> LensOpinion:
    """Signal vs noise: too few transactions carry no information at all."""
    b5 = _m(cand, "txns_5m_buys")
    s5 = _m(cand, "txns_5m_sells")
    b1 = _m(cand, "txns_1h_buys")
    s1 = _m(cand, "txns_1h_sells")
    if None in (b1, s1):
        return _op("LENS-SHANNON", "INFO-01", "ABSTAIN",
                   "شمار تراکنش‌ها ثبت نشده — نسبت سیگنال به نویز نامعلوم")
    total_1h = (b1 or 0) + (s1 or 0)
    if total_1h < 10:
        return _op("LENS-SHANNON", "INFO-01", "CAUTION",
                   f"تنها {total_1h:.0f} تراکنش در یک ساعت — "
                   f"نمونه برای استنتاج بسیار کوچک است",
                   metric=total_1h, severity=2)
    if None not in (b5, s5):
        tot5 = (b5 or 0) + (s5 or 0)
        if tot5 > 0 and total_1h > 0 and (tot5 / total_1h) > 0.9:
            return _op("LENS-SHANNON", "INFO-01", "CAUTION",
                       "تقریباً تمام فعالیت ساعت اخیر در ۵ دقیقه رخ داده — "
                       "احتمال انفجار مصنوعی",
                       metric=tot5, severity=2)
    return _op("LENS-SHANNON", "INFO-01", "APPROVE",
               f"حجم نمونه برای استنتاج کافی است ({total_1h:.0f} تراکنش)",
               metric=total_1h)


# The executable panel. Order is stable so output is reproducible.
PANEL_LENSES: list[tuple[str, Callable]] = [
    ("LENS-MUNGER", lens_munger_inversion),
    ("LENS-TALEB", lens_taleb_ruin),
    ("LENS-GODEL", lens_godel_unknowns),
    ("LENS-SCHNEIER", lens_schneier_weakest_link),
    ("LENS-NASH", lens_nash_equilibrium),
    ("LENS-KAHNEMAN", lens_kahneman_fomo),
    ("LENS-MANDELBROT", lens_mandelbrot_tails),
    ("LENS-MARKS", lens_marks_second_level),
    ("LENS-BAYES", lens_bayes_base_rate),
    ("LENS-SHANNON", lens_shannon_signal),
]


class CognitivePanel:
    """Runs every executable lens over one candidate and reconciles the votes."""

    def __init__(self, lenses: list[tuple[str, Callable]] | None = None):
        self.lenses = lenses if lenses is not None else PANEL_LENSES

    def deliberate(self, candidate, score_report=None, exitability=None,
                   virality=None, whale=None, narrative=None,
                   now: float | None = None) -> PanelVerdict:
        ctx = {"score_report": score_report, "exitability": exitability,
               "virality": virality, "whale": whale, "narrative": narrative}

        opinions: list[LensOpinion] = []
        for lens_id, fn in self.lenses:
            try:
                op = fn(candidate, ctx)
            except Exception as e:
                # A broken lens must never take the panel down, and must never
                # be silently counted as approval.
                op = _op(lens_id, "ERROR", "ABSTAIN",
                         f"این دیدگاه اجرا نشد ({type(e).__name__})")
            opinions.append(op)

        vetoes = [o.reason for o in opinions if o.stance == "VETO"]
        cautions = [o.reason for o in opinions if o.stance == "CAUTION"]
        approvals = [o.reason for o in opinions if o.stance == "APPROVE"]
        abstentions = [o.reason for o in opinions if o.stance == "ABSTAIN"]

        spoke = len(opinions) - len(abstentions)
        coverage = spoke / len(opinions) if opinions else 0.0

        if vetoes:
            verdict = "VETO"
        elif coverage < 0.5:
            # Half the panel silent is not consensus, it is a data gap.
            verdict = "INSUFFICIENT_EVIDENCE"
        elif cautions:
            verdict = "CAUTION"
        else:
            verdict = "APPROVE"

        # Highest severity first, so the most serious finding is never buried.
        opinions.sort(key=lambda o: (-o.severity, o.lens_id))

        return PanelVerdict(
            subject=getattr(candidate, "symbol", "UNKNOWN"),
            verdict=verdict, opinions=opinions,
            vetoes=vetoes, cautions=cautions,
            approvals=approvals, abstentions=abstentions,
            coverage=coverage, advisory_only=True,
            computed_ts=time.time() if now is None else now,
        )
