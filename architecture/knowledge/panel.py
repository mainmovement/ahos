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
from .lenses_teams import TEAM_LENS_REGISTRY

# One lookup over both card modules. The pilot cards and the team cards are
# kept in separate files for provenance, but a lens must never have to know
# which file it lives in.
ALL_LENS_CARDS: dict = {**LENS_PILOT_REGISTRY, **TEAM_LENS_REGISTRY}

PANEL_VERSION = "AHOS-PANEL-v1"

# A lens returns one of these stances.
STANCES = ("APPROVE", "CAUTION", "VETO", "ABSTAIN")

# --- Fisher effect-size floors ------------------------------------------------
# A z-test's power grows without bound in n, so on a busy token an
# economically meaningless deviation from 50/50 becomes "significant". These
# floors force the lens to speak about MAGNITUDE, which is what a trading
# decision actually depends on.
#
# 10 points (i.e. a 45/55 split) is the threshold below which the buy/sell
# ratio carries no actionable information: it sits inside the range an ordinary
# balanced order book wanders through minute to minute, and no position size in
# this system changes because of it.
FISHER_MIN_EFFECT = 0.10
# 20 points (a 30/70 split against you) is the point at which sell pressure
# stops being timing and becomes an exodus. Reserved for VETO because a veto in
# this panel means "unrecoverable", alongside honeypots and unlocked liquidity.
FISHER_ROUT_EFFECT = 0.20


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
    # Which measured facts this judgement rests on. The convergence rule
    # ("two independent lenses worried at once") is only meaningful if the
    # lenses are actually independent, and nothing enforced that: Buterin and
    # Nakamoto both cautioned off `liquidity_locked_pct < 80`, so ONE fact
    # about ONE token produced two votes and blocked it. Declaring the basis
    # lets convergence be counted over distinct evidence instead of over
    # opinions that happen to be numerous.
    evidence: tuple[str, ...] = ()

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
        # CONVERGENT_CAUTION blocks too. Several independent lenses raising a
        # concern at the same moment is evidence in its own right; if it only
        # trimmed conviction, the compound failures that no single lens calls
        # fatal would keep passing through.
        return self.verdict in ("VETO", "CONVERGENT_CAUTION")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["opinions"] = [o.to_dict() for o in self.opinions]
        return d

    def by_team(self) -> dict[str, list[LensOpinion]]:
        """Group the opinions by owning team.

        Thirty-nine individual opinions is a wall of text. Seven teams, each
        answering one question, is a report a person can act on.
        """
        try:
            from .teams import load_structure
            structure = load_structure()
        except Exception:  # noqa: BLE001 - grouping is presentation, never a blocker
            return {"ALL": list(self.opinions)}

        grouped: dict[str, list[LensOpinion]] = {}
        for op in self.opinions:
            team = structure.team_for_lens(op.lens_id)
            grouped.setdefault(team.team_id if team else "UNASSIGNED", []).append(op)
        return grouped

    def team_summary_persian(self) -> str:
        """Verdict per team, worst finding first within each."""
        try:
            from .teams import load_structure
            structure = load_structure()
        except Exception:  # noqa: BLE001
            return self.summary_persian()

        grouped = self.by_team()
        icon = {"APPROVE": "🟢", "CAUTION": "🟡", "CONVERGENT_CAUTION": "🟠",
                "VETO": "🔴", "INSUFFICIENT_EVIDENCE": "⚪"}
        lines = [f"{icon.get(self.verdict, '⚪')} شورای تخصصی — {self.subject}",
                 f"حکم نهایی: {self.verdict} (پوشش داده: {self.coverage:.0%})", ""]

        for team_id in structure.evaluation_order:
            ops = grouped.get(team_id)
            if not ops:
                continue
            team = structure.team(team_id)
            vetoes = [o for o in ops if o.stance == "VETO"]
            cautions = [o for o in ops if o.stance == "CAUTION"]
            silent = [o for o in ops if o.stance == "ABSTAIN"]
            if vetoes:
                mark, state = "🔴", "رد"
            elif cautions:
                mark, state = "🟡", "هشدار"
            elif len(silent) == len(ops):
                mark, state = "⚪", "بدون داده"
            else:
                mark, state = "🟢", "تأیید"
            name = team.name_fa if team else team_id
            lines.append(f"{mark} {name}: {state} "
                         f"({len(ops) - len(silent)}/{len(ops)} رأی)")
            for op in (vetoes + cautions)[:2]:
                who = op.identity.split("(")[0].strip()
                lines.append(f"     • {who}: {op.reason}")

        # The advisory disclaimer is not decoration -- it is the standing
        # guarantee that this council never overrides the deterministic
        # engine. The per-lens summary carries it and the team view dropped
        # it, which would have quietly changed what the output promises.
        lines += ["", "این شورا مشورتی است و بر موتور قطعی اولویت ندارد."]
        return "\n".join(lines)

    def summary_persian(self) -> str:
        icon = {"APPROVE": "🟢", "CAUTION": "🟡", "CONVERGENT_CAUTION": "🟠",
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
        metric: float | None = None, severity: int = 0,
        evidence: tuple[str, ...] | list[str] = ()) -> LensOpinion:
    card = ALL_LENS_CARDS.get(lens_id)
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
                       citation_ref=citation, metric=metric, severity=severity,
                       evidence=tuple(evidence))


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


# ---------------------------------------------------------------------------
# Wave-30: the second bench.
#
# Thirty lens data cards existed in `lenses.LENS_PILOT_REGISTRY`; ten of them
# had an executable opinion function and twenty were inert data. The panel was
# therefore a tenth of the bench it claimed, and the domains the specification
# asks for most loudly -- offensive security ("هکرها"), tokenomics, banking,
# pure mathematics, physics -- had no voice at all.
#
# Every lens below derives from a principle already carried on its card with a
# citation. None of them role-plays a person: each one reads a real field and
# applies one stated rule. Where the field is missing the lens ABSTAINS, which
# lowers panel coverage rather than manufacturing a vote -- silence is the
# honest output when the evidence is absent.
# ---------------------------------------------------------------------------

def lens_thompson_trusting_trust(cand, ctx) -> LensOpinion:
    """Trusting Trust: verified source proves nothing if the authority that can
    rewrite the rules is still held."""
    verified = _s(cand, "is_contract_verified")
    renounced = _s(cand, "is_ownership_renounced")
    mint = _s(cand, "has_mint_authority")
    freeze = _s(cand, "has_freeze_authority")

    if verified is None and renounced is None:
        return _op("LENS-THOMPSON", "TRUST-01", "ABSTAIN",
                   "وضعیت تأیید قرارداد و واگذاری مالکیت نامعلوم است")

    retained = [n for n, held in (("ضرب", mint is True), ("انجماد", freeze is True),
                                  ("مالکیت", renounced is False)) if held]
    if verified is True and retained:
        # The dangerous combination: the code reads clean and is therefore
        # trusted, while the deployer keeps the switch that makes the audited
        # text irrelevant.
        return _op("LENS-THOMPSON", "TRUST-01", "VETO",
                   "قرارداد تأییدشده اما اختیار " + "، ".join(retained)
                   + " هنوز نزد سازنده است — کد ممیزی‌شده قابل دور زدن است",
                   severity=3)
    if retained:
        return _op("LENS-THOMPSON", "TRUST-01", "CAUTION",
                   "اختیارات کنترلی واگذار نشده: " + "، ".join(retained), severity=2)
    if verified is False:
        return _op("LENS-THOMPSON", "TRUST-01", "CAUTION",
                   "کد قرارداد تأیید نشده است — رفتار واقعی قابل بازرسی نیست",
                   severity=2)
    return _op("LENS-THOMPSON", "TRUST-01", "APPROVE",
               "زنجیره اعتماد کامل است: کد تأییدشده و اختیارات واگذارشده")


def lens_buterin_trilemma(cand, ctx) -> LensOpinion:
    """Trilemma applied to a pool: depth, decentralisation and lock cannot all
    be waved away at once."""
    liq = _m(cand, "liquidity_usd")
    locked = _f(_s(cand, "liquidity_locked_pct"))
    burned = _f(_s(cand, "liquidity_burned_pct"))
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))

    secured = max([v for v in (locked, burned) if v is not None], default=None)
    if liq is None or secured is None:
        return _op("LENS-BUTERIN", "TRILEMMA-01", "ABSTAIN",
                   "عمق استخر یا وضعیت قفل نقدینگی نامعلوم است")

    unlocked_usd = liq * (1.0 - min(secured, 100.0) / 100.0)
    if secured < 50.0:
        return _op("LENS-BUTERIN", "TRILEMMA-01", "VETO",
                   f"تنها {secured:.0f}٪ نقدینگی قفل/سوزانده شده — "
                   f"${unlocked_usd:,.0f} قابل برداشت فوری توسط سازنده است",
                   metric=secured, severity=3,
                   evidence=("liquidity_lock",))
    if secured < 80.0 or (top10 is not None and top10 > 40.0):
        return _op("LENS-BUTERIN", "TRILEMMA-01", "CAUTION",
                   f"مصالحه سه‌گانه: قفل {secured:.0f}٪"
                   + (f" و تمرکز مالکیت {top10:.0f}٪" if top10 is not None else ""),
                   metric=secured, severity=2,
                   evidence=("liquidity_lock",) + (
                       ("holder_concentration",)
                       if top10 is not None and top10 > 40.0 else ()))
    return _op("LENS-BUTERIN", "TRILEMMA-01", "APPROVE",
               f"نقدینگی {secured:.0f}٪ تثبیت‌شده و توزیع مالکیت متعادل است",
               metric=secured)


def lens_von_neumann_minimax(cand, ctx) -> LensOpinion:
    """Minimax: value the position by its worst credible outcome, not its best.

    A memecoin exit is a zero-sum game against the holders who leave first, so
    the payoff that matters is what survives an adversarial exit -- realizable
    fraction against the concentrated stake that can move ahead of you.
    """
    ex = ctx.get("exitability")
    frac = _f(getattr(ex, "realizable_fraction", None)) if ex is not None else None
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if frac is None or top10 is None:
        return _op("LENS-VON-NEUMANN", "GAME-01", "ABSTAIN",
                   "بدون کسر قابل بازیافت و تمرکز مالکیت، بازی کمینه‌بیشینه حل نمی‌شود")

    # Worst credible case: the concentrated stake exits first and you realize
    # only what is left of the pool afterwards.
    adversarial = frac * (1.0 - min(top10, 100.0) / 100.0)
    if adversarial < 0.30:
        return _op("LENS-VON-NEUMANN", "GAME-01", "VETO",
                   f"در بدترین حالت معقول تنها {adversarial:.0%} سرمایه بازمی‌گردد "
                   f"(نهنگ‌ها پیش از شما خارج می‌شوند)",
                   metric=adversarial, severity=3)
    if adversarial < 0.55:
        return _op("LENS-VON-NEUMANN", "GAME-01", "CAUTION",
                   f"ارزش تضمین‌شده در برابر خروج رقبا: {adversarial:.0%}",
                   metric=adversarial, severity=2)
    return _op("LENS-VON-NEUMANN", "GAME-01", "APPROVE",
               f"حتی با خروج زودهنگام بزرگ‌ترین دارندگان، {adversarial:.0%} قابل بازیافت است",
               metric=adversarial)


def lens_fisher_significance(cand, ctx) -> LensOpinion:
    """Fisher: is the buy/sell imbalance beyond what coin-flipping produces?

    A 70% buy ratio over 20 trades is noise; over 2000 trades it is a fact.
    Uses the normal approximation to the binomial -- no scipy, no new
    dependency, and exact enough at these sample sizes.
    """
    buys = _m(cand, "txns_1h_buys")
    sells = _m(cand, "txns_1h_sells")
    if buys is None or sells is None:
        return _op("LENS-FISHER", "FISHER-01", "ABSTAIN",
                   "تعداد معاملات خرید/فروش برای آزمون معناداری در دسترس نیست")
    n = buys + sells
    if n < 30:
        # Not an abstention. Abstaining only lowers coverage silently, but a
        # token with two dozen trades in an hour is a concrete finding the
        # user must see: there is no market here yet, and every momentum
        # number computed from it is noise dressed as signal.
        return _op("LENS-FISHER", "FISHER-01", "CAUTION",
                   f"تنها {n:.0f} معامله در یک ساعت — نمونه برای هیچ استنتاج "
                   f"آماری کافی نیست و ارقام شتاب بی‌معنا هستند",
                   metric=n, severity=2)

    # Two-sided z against a fair 50/50 null.
    p_hat = buys / n
    z = (p_hat - 0.5) / ((0.25 / n) ** 0.5)
    effect = p_hat - 0.5

    # EFFECT SIZE IS CHECKED BEFORE SIGNIFICANCE, and that order is the whole
    # point. A z-test answers "is this imbalance distinguishable from a coin
    # flip", which is a question about EXISTENCE, not magnitude -- and its
    # power grows without bound in n. At 10,000 trades an hour the test turns
    # significant at a 49% buy ratio; at 50,000 it does so at 49.6%. The lens
    # used to answer that with a VETO, the single harshest verdict available,
    # applied to an ordinary balanced order book on the most liquid tokens in
    # the sample. Activity was being punished as pathology.
    #
    # Fisher's own card names this failure: the principle is "reject H0 only
    # when p < alpha", a test of existence. Reading a rejection as a statement
    # about size is the significance/importance conflation he spent his career
    # warning against.
    #
    # So a deviation smaller than MIN_EFFECT is reported as what it is -- a
    # balanced book -- however many trades stand behind it.
    if abs(effect) < FISHER_MIN_EFFECT:
        return _op("LENS-FISHER", "FISHER-01", "APPROVE",
                   f"دفتر سفارش متوازن است ({p_hat:.0%} خرید از {n:.0f} معامله) — "
                   f"انحراف کمتر از {FISHER_MIN_EFFECT:.0%} حتی اگر از نظر آماری "
                   f"معنادار باشد، از نظر عملی بی‌اهمیت است",
                   metric=effect)

    if abs(z) < 1.96:
        return _op("LENS-FISHER", "FISHER-01", "CAUTION",
                   f"عدم توازن خرید/فروش از تصادف قابل تفکیک نیست "
                   f"(z={z:.2f}، {p_hat:.0%} خرید)", metric=z, severity=1)

    if effect < 0:
        # A VETO must mean "unrecoverable" -- that is what the other vetoes in
        # this panel mean (honeypot, un-exitable tax, unlocked liquidity, a
        # worst case that returns under 30% of capital). Sell pressure is a
        # momentum reading, and momentum reverses; it is bad entry timing, not
        # a structural trap. Only an overwhelming, unambiguous exodus is
        # treated as fatal.
        if effect <= -FISHER_ROUT_EFFECT:
            return _op("LENS-FISHER", "FISHER-01", "VETO",
                       f"خروج گسترده و معنادار: تنها {p_hat:.0%} از "
                       f"{n:.0f} معامله خرید بوده است (z={z:.2f})",
                       metric=z, severity=3)
        return _op("LENS-FISHER", "FISHER-01", "CAUTION",
                   f"فشار فروش از نظر آماری معنادار است (z={z:.2f}، "
                   f"{p_hat:.0%} خرید) — زمان ورود نامناسب است",
                   metric=z, severity=2)

    return _op("LENS-FISHER", "FISHER-01", "APPROVE",
               f"برتری خریداران معنادار و قابل‌توجه است (z={z:.2f}، {p_hat:.0%} خرید)",
               metric=z)


def lens_pearl_causation(cand, ctx) -> LensOpinion:
    """Pearl: price and volume move together for two very different reasons.

    Real demand lifts price *and* leaves volume proportionate to the pool.
    Wash trading lifts volume with no pool to justify it. Distinguishing the
    two is a causal question, not a correlational one.
    """
    vol_1h = _m(cand, "volume_1h")
    liq = _m(cand, "liquidity_usd")
    chg_1h = _m(cand, "price_change_1h")
    if vol_1h is None or liq is None or liq <= 0:
        return _op("LENS-PEARL", "CAUSAL-01", "ABSTAIN",
                   "بدون حجم و عمق استخر، رابطه علّی قابل تفکیک نیست")

    turnover = vol_1h / liq
    if turnover > 5.0 and (chg_1h is None or abs(chg_1h) < 10.0):
        # Enormous churn that moves no price is the signature of trade
        # recycling, not of demand.
        return _op("LENS-PEARL", "CAUSAL-01", "VETO",
                   f"گردش {turnover:.1f} برابری استخر بدون حرکت قیمت — "
                   f"الگوی معاملات ساختگی (wash trading)",
                   metric=turnover, severity=3)
    if turnover > 3.0:
        return _op("LENS-PEARL", "CAUSAL-01", "CAUTION",
                   f"گردش غیرعادی {turnover:.1f} برابر عمق استخر در یک ساعت",
                   metric=turnover, severity=2)
    if turnover < 0.05:
        return _op("LENS-PEARL", "CAUSAL-01", "CAUTION",
                   f"حجم نسبت به عمق استخر ناچیز است ({turnover:.2%}) — "
                   f"تقاضای واقعی اثبات نشده", metric=turnover, severity=1)
    return _op("LENS-PEARL", "CAUSAL-01", "APPROVE",
               f"نسبت حجم به نقدینگی طبیعی است ({turnover:.2f})", metric=turnover)


def lens_knuth_asymptotics(cand, ctx) -> LensOpinion:
    """Knuth: check the growth term that dominates at scale.

    For an entry the dominant term is slippage, which grows with the square of
    your size relative to the pool in a constant-product AMM. A pool that
    looks adequate for $10 can be catastrophic for the position actually
    being proposed.
    """
    liq = _m(cand, "liquidity_usd")
    if liq is None or liq <= 0:
        return _op("LENS-KNUTH", "KNUTH-01", "ABSTAIN",
                   "بدون عمق استخر، لغزش قیمت محاسبه نمی‌شود")

    # Round-trip slippage for a 1%-of-pool position under x*y=k.
    share = 0.01
    slippage_pct = (2 * share / (1 + share)) * 100.0
    if liq < 10_000:
        return _op("LENS-KNUTH", "KNUTH-01", "VETO",
                   f"استخر ${liq:,.0f} — حتی سفارش‌های کوچک قیمت را جابه‌جا می‌کنند",
                   metric=liq, severity=3)
    if liq < 50_000:
        return _op("LENS-KNUTH", "KNUTH-01", "CAUTION",
                   f"عمق ${liq:,.0f}: لغزش رفت‌وبرگشت حدود {slippage_pct:.1f}٪ "
                   f"برای پوزیشن ۱٪ استخر", metric=liq, severity=2)
    return _op("LENS-KNUTH", "KNUTH-01", "APPROVE",
               f"عمق ${liq:,.0f} برای اندازه پوزیشن هدف کافی است", metric=liq)


def lens_hamilton_failure_priority(cand, ctx) -> LensOpinion:
    """Hamilton: Apollo shed low-priority tasks so the critical ones survived.

    Applied here: when several risk signals fire at once, the system must not
    average them into a middling score. It must recognise the overload and
    refuse, exactly as the guidance computer did at 1202.
    """
    faults = []
    if _s(cand, "is_honeypot") is True:
        faults.append("هانی‌پات")
    tax = _f(_s(cand, "sell_tax_pct"))
    if tax is not None and tax >= 10.0:
        faults.append(f"مالیات فروش {tax:.0f}٪")
    if _s(cand, "has_mint_authority") is True:
        faults.append("اختیار ضرب")
    if _s(cand, "has_freeze_authority") is True:
        faults.append("اختیار انجماد")
    rugs = _f(_s(cand, "deployer_past_rug_count"))
    if rugs is not None and rugs > 0:
        faults.append(f"{rugs:.0f} رگ‌پول پیشین سازنده")
    locked = _f(_s(cand, "liquidity_locked_pct"))
    if locked is not None and locked < 50.0:
        faults.append(f"قفل نقدینگی {locked:.0f}٪")
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if top10 is not None and top10 > 50.0:
        faults.append(f"تمرکز مالکیت {top10:.0f}٪")

    known = sum(1 for probe in (
        _s(cand, "is_honeypot"), tax, _s(cand, "has_mint_authority"),
        _s(cand, "has_freeze_authority"), rugs, locked, top10)
        if probe is not None)
    if known < 3:
        return _op("LENS-HAMILTON", "HAMILTON-01", "ABSTAIN",
                   "تعداد سیگنال‌های در دسترس برای ارزیابی بار خطا کافی نیست")

    if len(faults) >= 3:
        return _op("LENS-HAMILTON", "HAMILTON-01", "VETO",
                   f"سرریز خطا ({len(faults)} نقص هم‌زمان): "
                   + "، ".join(faults[:4]) + " — میانگین‌گیری روی این‌ها مجاز نیست",
                   metric=float(len(faults)), severity=3)
    if len(faults) == 2:
        return _op("LENS-HAMILTON", "HAMILTON-01", "CAUTION",
                   "دو نقص هم‌زمان: " + "، ".join(faults),
                   metric=2.0, severity=2)
    return _op("LENS-HAMILTON", "HAMILTON-01", "APPROVE",
               "بار خطا در محدوده قابل کنترل است"
               + (f" (تنها: {faults[0]})" if faults else ""),
               metric=float(len(faults)))


def lens_lamport_causal_order(cand, ctx) -> LensOpinion:
    """Lamport: events without a consistent ordering cannot be reasoned about.

    Applied to observation freshness. A candidate assembled from stale reads
    is a snapshot of a market that no longer exists; acting on it is acting on
    a message from the past.
    """
    retrieved = _f(getattr(cand, "retrieved_ts", None))
    now = _f((ctx or {}).get("now")) or time.time()
    if retrieved is None:
        return _op("LENS-LAMPORT", "LAMPORT-01", "ABSTAIN",
                   "زمان مشاهده ثبت نشده است — ترتیب رویدادها قابل بازسازی نیست")

    if retrieved <= 0:
        # A zero or negative timestamp is not "very old data", it is an
        # unset field. Reporting it as a 29-million-minute staleness would be
        # arithmetically true and analytically useless; the honest output is
        # that provenance is missing.
        return _op("LENS-LAMPORT", "LAMPORT-01", "ABSTAIN",
                   "مهر زمانی مشاهده ثبت نشده است (مقدار صفر) — "
                   "تازگی داده قابل ارزیابی نیست")

    age_min = (now - retrieved) / 60.0
    if age_min > 60.0:
        return _op("LENS-LAMPORT", "LAMPORT-01", "VETO",
                   f"داده {age_min:.0f} دقیقه قدیمی است — بازار سنجیده‌شده دیگر وجود ندارد",
                   metric=age_min, severity=3)
    if age_min > 15.0:
        return _op("LENS-LAMPORT", "LAMPORT-01", "CAUTION",
                   f"تازگی داده {age_min:.0f} دقیقه — برای بازار پرنوسان مرزی است",
                   metric=age_min, severity=2)
    if age_min < -1.0:
        # A future timestamp means clock skew somewhere in the pipeline.
        return _op("LENS-LAMPORT", "LAMPORT-01", "CAUTION",
                   "زمان مشاهده در آینده است — ناهماهنگی ساعت در مسیر داده",
                   metric=age_min, severity=2)
    return _op("LENS-LAMPORT", "LAMPORT-01", "APPROVE",
               f"داده تازه است ({max(age_min, 0):.0f} دقیقه)", metric=age_min)


def lens_brewer_partition(cand, ctx) -> LensOpinion:
    """CAP: under partition you choose consistency or availability.

    A candidate corroborated by one provider is available but not consistent.
    The lens reports which side of the trade-off the evidence sits on rather
    than pretending a single source is confirmation.
    """
    confidence = getattr(cand, "confidence_level", None)
    provider = getattr(cand, "source_provider", None)
    if not provider:
        return _op("LENS-BREWER", "CAP-01", "ABSTAIN",
                   "منبع داده مشخص نیست")

    # Count only fields whose absence actually changes a decision. A healthy
    # DexScreener candidate is always missing ~10 optional fields (5m windows,
    # socials, market cap); flagging those produced a CAUTION on a perfectly
    # clean token, and a warning that fires on everything trains the user to
    # ignore warnings.
    critical = {
        "metrics.liquidity_usd": _m(cand, "liquidity_usd"),
        "metrics.volume_1h": _m(cand, "volume_1h"),
        "metrics.price_usd": _m(cand, "price_usd"),
        "security.is_honeypot": _s(cand, "is_honeypot"),
        "security.sell_tax_pct": _s(cand, "sell_tax_pct"),
        "security.liquidity_locked_pct": _s(cand, "liquidity_locked_pct"),
        "security.top10_holder_concentration_pct":
            _s(cand, "top10_holder_concentration_pct"),
    }
    missing = [name.split(".")[-1] for name, value in critical.items()
               if value is None]

    if confidence == "LOW":
        return _op("LENS-BREWER", "CAP-01", "CAUTION",
                   f"اعتماد داده پایین از منبع «{provider}» — "
                   f"دسترس‌پذیری بر سازگاری ترجیح داده شده", severity=2)
    if len(missing) >= 3:
        return _op("LENS-BREWER", "CAP-01", "VETO",
                   f"{len(missing)} میدان حیاتی غایب است ("
                   + "، ".join(missing[:3]) + ") — تصمیم بر داده ناقص ممنوع",
                   metric=float(len(missing)), severity=3)
    if missing:
        return _op("LENS-BREWER", "CAP-01", "CAUTION",
                   "میدان حیاتی غایب: " + "، ".join(missing),
                   metric=float(len(missing)), severity=2)
    return _op("LENS-BREWER", "CAP-01", "APPROVE",
               f"تمام میدان‌های حیاتی از «{provider}» در دسترس‌اند", metric=0.0)


def lens_nakamoto_trust_minimization(cand, ctx) -> LensOpinion:
    """Nakamoto: the point is to not need a trusted third party.

    Every retained privilege reintroduces exactly the trusted party the
    architecture was built to remove. This lens counts how much of the
    position's safety rests on the deployer simply choosing to behave.
    """
    trust_points = []
    basis: list[str] = []
    if _s(cand, "is_ownership_renounced") is False:
        trust_points.append("مالکیت واگذار نشده")
        basis.append("deployer_authority")
    if _s(cand, "has_mint_authority") is True:
        trust_points.append("امکان ضرب نامحدود")
        basis.append("deployer_authority")
    if _s(cand, "has_freeze_authority") is True:
        trust_points.append("امکان انجماد دارایی شما")
        basis.append("deployer_authority")
    locked = _f(_s(cand, "liquidity_locked_pct"))
    burned = _f(_s(cand, "liquidity_burned_pct"))
    secured = max([v for v in (locked, burned) if v is not None], default=None)
    # Only unlocked liquidity large enough to matter counts as a trust
    # dependency. Firing on 5% free liquidity made this lens caution on every
    # healthy token, and a warning that is always on is not information.
    if secured is not None and secured < 80.0:
        trust_points.append(f"{100.0 - secured:.0f}٪ نقدینگی آزاد")
        # Same fact Buterin's trilemma reads. Declaring it means the panel
        # will not mistake two readings of one lock percentage for two
        # independent findings.
        basis.append("liquidity_lock")

    probes = [_s(cand, "is_ownership_renounced"), _s(cand, "has_mint_authority"),
              _s(cand, "has_freeze_authority"), secured]
    if all(p is None for p in probes):
        return _op("LENS-NAKAMOTO", "CRYPTO-01", "ABSTAIN",
                   "هیچ داده‌ای درباره اختیارات سازنده در دسترس نیست")

    if len(trust_points) >= 3:
        return _op("LENS-NAKAMOTO", "CRYPTO-01", "VETO",
                   "امنیت پوزیشن کاملاً به حسن‌نیت سازنده وابسته است: "
                   + "، ".join(trust_points[:3]),
                   metric=float(len(trust_points)), severity=3,
                   evidence=tuple(dict.fromkeys(basis)))
    if trust_points:
        return _op("LENS-NAKAMOTO", "CRYPTO-01", "CAUTION",
                   "نقاط اتکا به شخص ثالث: " + "، ".join(trust_points),
                   metric=float(len(trust_points)), severity=2,
                   evidence=tuple(dict.fromkeys(basis)))
    return _op("LENS-NAKAMOTO", "CRYPTO-01", "APPROVE",
               "هیچ اختیار ویژه‌ای نزد سازنده باقی نمانده است", metric=0.0)


# Which verified principle each executable lens actually applies. The roster
# report previously showed each card's FIRST principle, which for Thompson
# meant advertising "Orthogonal Tool Composition" while the lens really
# reasons from the Trusting Trust problem -- a small lie about our own basis.
LENS_APPLIED_PRINCIPLE: dict[str, str] = {
    "LENS-MUNGER": "INVERSION-01", "LENS-TALEB": "CONVEXITY-01",
    "LENS-GODEL": "GODEL-01", "LENS-SCHNEIER": "SEC-PROCESS-01",
    "LENS-NASH": "NASH-01", "LENS-KAHNEMAN": "BEHAV-01",
    "LENS-MANDELBROT": "FRACTAL-01", "LENS-MARKS": "SECOND-LEVEL-01",
    "LENS-BAYES": "BAYES-01", "LENS-SHANNON": "INFO-01",
    "LENS-THOMPSON": "TRUST-01", "LENS-BUTERIN": "TRILEMMA-01",
    "LENS-VON-NEUMANN": "GAME-01", "LENS-FISHER": "FISHER-01",
    "LENS-PEARL": "CAUSAL-01", "LENS-KNUTH": "KNUTH-01",
    "LENS-HAMILTON": "HAMILTON-01", "LENS-LAMPORT": "LAMPORT-01",
    "LENS-BREWER": "CAP-01", "LENS-NAKAMOTO": "CRYPTO-01",
}


# Number of simultaneous independent cautions that escalates the panel from
# "note the risk" to "do not proceed". Derived from a null simulation over
# 3000 healthy candidates, whose p99.9 caution count was 1. See the comment in
# `deliberate` for the reasoning; do not adjust this by intuition -- re-run the
# simulation.
CONVERGENT_CAUTION_THRESHOLD = 2


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
    # Wave-30: the twenty inert lens cards get their first executable voices.
    ("LENS-THOMPSON", lens_thompson_trusting_trust),
    ("LENS-BUTERIN", lens_buterin_trilemma),
    ("LENS-VON-NEUMANN", lens_von_neumann_minimax),
    ("LENS-FISHER", lens_fisher_significance),
    ("LENS-PEARL", lens_pearl_causation),
    ("LENS-KNUTH", lens_knuth_asymptotics),
    ("LENS-HAMILTON", lens_hamilton_failure_priority),
    ("LENS-LAMPORT", lens_lamport_causal_order),
    ("LENS-BREWER", lens_brewer_partition),
    ("LENS-NAKAMOTO", lens_nakamoto_trust_minimization),
]


def register_lenses(pairs) -> None:
    """Add lenses to the bench, ignoring any already present.

    Idempotent by lens_id. Registration happens from two directions (see
    below), and a lens registered twice would vote twice -- turning one
    opinion into a fake second corroborating one, which is exactly what the
    CONVERGENT_CAUTION rule must never be fed.
    """
    have = {lid for lid, _ in PANEL_LENSES}
    for lens_id, fn in pairs:
        if lens_id not in have:
            PANEL_LENSES.append((lens_id, fn))
            have.add(lens_id)


def _load_team_lenses() -> None:
    """Attach the Wave-31 team bench.

    `team_lenses` imports `_op` and friends from this module, so the two are
    mutually dependent and the import order decides which one wins the race.
    Previously this was a bare `from .team_lenses import ...` at the bottom of
    panel.py, which worked only when panel.py was imported FIRST. Importing
    `architecture.knowledge.team_lenses` directly -- as any test, script or new
    caller would naturally do -- raised:

        ImportError: cannot import name 'TEAM_PANEL_LENSES' from partially
        initialized module ... (most likely due to a circular import)

    The fix makes registration work from whichever side loads first: this
    module tries to pull the bench in, and `team_lenses` pushes it back at the
    end of its own import. Whichever runs second is a no-op, because
    `register_lenses` deduplicates.
    """
    try:
        from .team_lenses import TEAM_PANEL_LENSES
    except ImportError:
        # team_lenses is mid-import and will register itself when it finishes.
        return
    register_lenses(TEAM_PANEL_LENSES)


_load_team_lenses()


class CognitivePanel:
    """Runs every executable lens over one candidate and reconciles the votes."""

    def __init__(self, lenses: list[tuple[str, Callable]] | None = None):
        self.lenses = lenses if lenses is not None else PANEL_LENSES

    def deliberate(self, candidate, score_report=None, exitability=None,
                   virality=None, whale=None, narrative=None,
                   calibration=None, now: float | None = None) -> PanelVerdict:
        # `now` is part of the context because freshness is a first-class
        # signal: a lens that judges staleness must not silently fall back to
        # wall-clock time when the caller supplied a reference instant.
        #
        # `calibration` was the missing key. LENS-THORP -- the lead of the
        # SIZING team, whose published life's work is position sizing -- reads
        # ctx["calibration"] and ABSTAINs without it. The key was never set by
        # anyone, so that lens had never cast a vote in production: not a
        # dormant feature, an unreachable one. Passing None is still legitimate
        # and still yields an honest abstention; what was wrong was that no
        # caller could supply it even when the data existed.
        ctx = {"score_report": score_report, "exitability": exitability,
               "virality": virality, "whale": whale, "narrative": narrative,
               "calibration": calibration,
               "now": time.time() if now is None else now}

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

        # Convergence is counted over DISTINCT EVIDENCE, not over opinions.
        #
        # The rule's whole justification is that independent lenses reaching
        # for the alarm at once means more than one lens doing so. Nothing
        # enforced the independence. Buterin's trilemma and Nakamoto's trust
        # minimisation both caution when `liquidity_locked_pct` falls below
        # 80, so a single fact about a single token -- "79% locked" -- produced
        # two cautions and blocked it as though two separate problems had been
        # found. Measured on the healthy population, that one collision
        # accounted for 125 of the rejections.
        #
        # A lens that declares no basis is counted on its own identity: an
        # undeclared opinion is treated as its own evidence rather than being
        # silently merged with someone else's, so failing to tag a lens can
        # never make the panel more permissive than it was.
        caution_ops = [o for o in opinions if o.stance == "CAUTION"]
        distinct_evidence: set[str] = set()
        for o in caution_ops:
            distinct_evidence.update(o.evidence or (f"lens:{o.lens_id}",))

        if vetoes:
            verdict = "VETO"
        elif coverage < 0.5:
            # Half the panel silent is not consensus, it is a data gap.
            verdict = "INSUFFICIENT_EVIDENCE"
        elif len(distinct_evidence) >= CONVERGENT_CAUTION_THRESHOLD:
            # Independent lenses reaching for the alarm at the same time is a
            # different fact from one lens doing so, and the panel must not
            # flatten the two into the same word.
            #
            # The threshold is not a taste judgement. Simulating 3000 healthy
            # candidates -- varied liquidity, volume, tax, lock and holder
            # spread, no injected defect -- produced at most ONE caution, with
            # p99.9 at one. Two independent cautions therefore sit above the
            # p99.9 of the null, so treating convergence as blocking costs
            # almost no true opportunities while catching the compound cases
            # that no single lens rates as fatal on its own.
            verdict = "CONVERGENT_CAUTION"
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
