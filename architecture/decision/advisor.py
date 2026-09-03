#!/usr/bin/env python3
"""AHOS Decision Advisor — the "what do I actually do?" engine.

Fuses every evidence stream into a single actionable recommendation that always
carries its own justification:

    WHAT to do      ENTER / WAIT / AVOID / REDUCE / EXIT / HOLD
    HOW MUCH        a position size derived from pool depth and risk, not a guess
    WHEN to exit    concrete price targets + invalidation conditions, set BEFORE entry
    WHY             positive reasons, risk deductions and explicit UNKNOWNs

DESIGN LAWS
-----------
1. SECURITY VETO IS ABSOLUTE. A honeypot, live mint authority or untradeable exit
   produces AVOID regardless of score, hype, or unanimous AI enthusiasm.
2. EXITABILITY GATES ENTRY. If you cannot get out, you do not go in. This is
   checked before the opportunity score is even considered.
3. SIZE FROM DEPTH, NOT CONVICTION. Position size is capped by what the pool can
   actually absorb on the way out — never by how good the setup "feels".
4. EXITS ARE PLANNED BEFORE ENTRY. Take-profit, stop-loss and invalidation
   conditions are emitted with the entry advice, using the locked PT-X1-v1 rules.
5. UNKNOWN IS NOT ZERO. Missing data widens caution; it never silently defaults
   to a favourable assumption.
6. AI IS ADVISORY. The council can downgrade a recommendation (safety ratchet)
   but can never upgrade one past what the measured evidence supports.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from architecture.identity.gates import identity_allows_positive_decision
from architecture.identity.types import IdentityResolution
from paper_trading.exit_rules import EXIT_V1

# --- Locked advisory constants (pre-registered; change => new version) -------
ADVISOR_VERSION = "AHOS-ADVISOR-v1"

SCORE_STRONG = 70.0            # deterministic score for a full-conviction entry
SCORE_MODERATE = 55.0          # entry allowed, reduced size
SCORE_WEAK = 40.0              # watch only

MIN_LIQUIDITY_USD = 10_000.0   # below this, an early token is not investable
MIN_REALIZABLE_FRACTION = 0.75 # must recover >=75% of displayed value on exit

# Position sizing: never exceed this share of the pool, ever.
MAX_POOL_SHARE_PCT = 1.0
# Never risk more than this share of the bankroll on one idea.
MAX_BANKROLL_RISK_PCT = 10.0

ACTIONS = ("ENTER", "WAIT", "AVOID", "HOLD", "REDUCE", "EXIT")

FOOTER = "تصمیم نهایی با کاربر است."


@dataclass
class Advice:
    """A complete, self-justifying recommendation for a token."""
    symbol: str
    address: str
    chain: str
    action: str                                  # see ACTIONS
    conviction: str                              # HIGH | MEDIUM | LOW | NONE
    suggested_size_usd: float | None
    entry_price_usd: float | None
    take_profit_price: float | None
    stop_loss_price: float | None
    max_hold_hours: float | None
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)
    hard_vetoes: list[str] = field(default_factory=list)
    deterministic_score: float | None = None
    exit_verdict: str | None = None
    council: dict[str, Any] | None = None
    panel: dict[str, Any] | None = None
    identity_state: str | None = None
    identity_token_id: str | None = None
    identity_policy_version: str | None = None
    computed_ts: float = field(default_factory=time.time)
    version: str = ADVISOR_VERSION

    @property
    def is_actionable(self) -> bool:
        return self.action == "ENTER" and not self.hard_vetoes

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol, "address": self.address, "chain": self.chain,
            "action": self.action, "conviction": self.conviction,
            "suggested_size_usd": self.suggested_size_usd,
            "entry_price_usd": self.entry_price_usd,
            "take_profit_price": self.take_profit_price,
            "stop_loss_price": self.stop_loss_price,
            "max_hold_hours": self.max_hold_hours,
            "reasons": self.reasons, "risks": self.risks, "unknowns": self.unknowns,
            "invalidation": self.invalidation, "hard_vetoes": self.hard_vetoes,
            "deterministic_score": self.deterministic_score,
            "exit_verdict": self.exit_verdict,             "council": self.council,
            "panel": self.panel,
            "identity_state": self.identity_state,
            "identity_token_id": self.identity_token_id,
            "identity_policy_version": self.identity_policy_version,
            "computed_ts": self.computed_ts, "version": self.version,
        }


@dataclass
class PositionAdvice:
    """Advice for a position the user already holds."""
    symbol: str
    action: str                                  # HOLD | REDUCE | EXIT
    urgency: str                                 # IMMEDIATE | SOON | ROUTINE
    sell_fraction: float                         # 0.0 .. 1.0
    pnl_pct: float | None
    current_price: float | None
    entry_price: float | None
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol, "action": self.action, "urgency": self.urgency,
            "sell_fraction": self.sell_fraction, "pnl_pct": self.pnl_pct,
            "current_price": self.current_price, "entry_price": self.entry_price,
            "reasons": self.reasons, "risks": self.risks, "unknowns": self.unknowns,
            "computed_ts": self.computed_ts,
        }


class DecisionAdvisor:
    """Turns evidence into advice. Pure function of its inputs — no I/O, no state."""

    def __init__(self, bankroll_usd: float = 100.0, exit_cfg: dict | None = None):
        self.bankroll_usd = bankroll_usd
        self.exit_cfg = exit_cfg or EXIT_V1

    # ------------------------------------------------------------------ ENTRY
    def advise_entry(self, candidate, score_report,
                     exitability=None, virality=None, whale=None,
                     narrative=None, council=None, panel=None,
                     now: float | None = None,
                     identity: IdentityResolution | None = None) -> Advice:
        ts = time.time() if now is None else now
        m = candidate.metrics

        reasons: list[str] = []
        risks: list[str] = []
        unknowns: list[str] = list(score_report.missing_unknowns or [])
        vetoes: list[str] = []
        invalidation: list[str] = []

        symbol = score_report.token_symbol
        base = Advice(
            symbol=symbol, address=score_report.token_address,
            chain=score_report.token_chain, action="AVOID", conviction="NONE",
            suggested_size_usd=None, entry_price_usd=m.price_usd,
            take_profit_price=None, stop_loss_price=None, max_hold_hours=None,
            deterministic_score=score_report.opportunity_score,
            exit_verdict=exitability.verdict if exitability else None,
            council=council.to_dict() if council else None,
            panel=panel.to_dict() if panel else None,
            identity_state=(identity.token.state.value if identity is not None else "MISSING"),
            identity_token_id=(identity.token.token_id if identity is not None else None),
            identity_policy_version=(identity.policy_version if identity is not None else None),
            computed_ts=ts,
        )

        # ============ GATE 0 — CANONICAL IDENTITY (fail closed) =============
        if identity is None or not identity_allows_positive_decision(identity):
            state = identity.token.state.value if identity is not None else "MISSING"
            base.action = "AVOID"
            base.conviction = "NONE"
            base.hard_vetoes = [
                f"Identity gate: token state {state} cannot produce ENTER."
            ]
            base.reasons = ["ورود ممنوع — هویت کانونیکال توکن تأیید نشده است"]
            return base

        # ============ GATE 1 — SECURITY VETO (absolute) =====================
        if exitability is not None and exitability.hard_vetoes:
            vetoes.extend(exitability.hard_vetoes)

        sec = candidate.security
        if sec.is_honeypot is True:
            vetoes.append("قرارداد honeypot تشخیص داده شد — فروش مسدود است")
        if sec.deployer_past_rug_count is not None and sec.deployer_past_rug_count > 0:
            vetoes.append(
                f"سازنده قرارداد سابقه {sec.deployer_past_rug_count} بار رِراگ‌پول دارد"
            )
        if score_report.risk_level == "CRITICAL":
            vetoes.append("سطح ریسک بحرانی توسط موتور قطعی اعلام شد")

        # Cognitive panel vetoes are DETERMINISTIC checks derived from published
        # principles -- they are arithmetic over measured evidence, not model
        # opinion. That is why, unlike the AI council, the panel may block here
        # rather than only ratchet conviction downward later.
        if panel is not None and panel.is_blocking:
            for reason in panel.vetoes:
                vetoes.append(f"شورای تحلیلی: {reason}")

        if vetoes:
            base.action = "AVOID"
            base.conviction = "NONE"
            base.hard_vetoes = vetoes
            base.risks = [r.description for r in score_report.risk_deductions[:5]]
            base.unknowns = unknowns[:8]
            base.reasons = ["ورود ممنوع — حداقل یک وتوی امنیتی قطعی فعال است"]
            return base

        # ============ GATE 2 — EXITABILITY ==================================
        if exitability is not None:
            if exitability.verdict == "TRAPPED":
                base.action = "AVOID"
                base.risks = exitability.warnings[:4]
                base.unknowns = (unknowns + exitability.unknowns)[:8]
                base.reasons = ["خروج از این موقعیت عملاً ممکن نیست — ورود منتفی است"]
                return base
            if (exitability.realizable_fraction is not None
                    and exitability.realizable_fraction < MIN_REALIZABLE_FRACTION):
                risks.append(
                    f"تنها {exitability.realizable_fraction * 100:.0f}٪ ارزش در خروج "
                    f"بازیابی می‌شود (حد قابل قبول: {MIN_REALIZABLE_FRACTION * 100:.0f}٪)"
                )
            elif exitability.realizable_fraction is not None:
                reasons.append(
                    f"خروج قابل قبول: حدود {exitability.realizable_fraction * 100:.0f}٪ "
                    "ارزش قابل بازیابی است"
                )
            risks.extend(exitability.warnings[:3])
            unknowns.extend(exitability.unknowns)

        # ============ GATE 3 — LIQUIDITY FLOOR ==============================
        liq = m.liquidity_usd
        if liq is None:
            unknowns.append("عمق نقدینگی — بدون آن اندازه موقعیت قابل محاسبه نیست")
            base.action = "WAIT"
            base.reasons = ["نقدینگی نامعلوم است؛ تا روشن شدن داده، ورود توصیه نمی‌شود"]
            base.risks = risks[:5]
            base.unknowns = unknowns[:8]
            return base
        if liq < MIN_LIQUIDITY_USD:
            base.action = "AVOID"
            base.reasons = [
                f"نقدینگی ${liq:,.0f} زیر کف قابل سرمایه‌گذاری "
                f"(${MIN_LIQUIDITY_USD:,.0f}) است"
            ]
            base.risks = risks[:5]
            base.unknowns = unknowns[:8]
            return base
        reasons.append(f"عمق نقدینگی ${liq:,.0f}")

        # ============ GATE 4 — SCORE + MODIFIERS ============================
        score = score_report.opportunity_score
        reasons.extend(score_report.positive_reasons[:4])
        risks.extend(r.description for r in score_report.risk_deductions[:4])

        if whale is not None and whale.is_known:
            if whale.risk_penalty >= 25.0:
                risks.append(
                    f"تمرکز مالکیت خطرناک ({whale.top10_share_pct:.0f}٪ نزد ۱۰ کیف‌پول برتر)"
                )
            risks.extend(whale.warnings[:2])
            reasons.extend(whale.reasons[:2])
        elif whale is not None:
            unknowns.extend(whale.unknowns[:2])

        if virality is not None:
            if virality.wash_suspected:
                risks.append("الگوی معاملات صوری (wash trading) شناسایی شد")
            if virality.is_paid_promotion:
                risks.append("توجه این توکن خریداری شده است، نه ارگانیک")
            if virality.label in ("VIRAL", "BUILDING"):
                reasons.extend(virality.reasons[:2])
            risks.extend(virality.warnings[:2])
            unknowns.extend(virality.unknowns[:2])

        if narrative is not None and narrative.is_known:
            if narrative.label == "BEARISH":
                risks.append(f"فضای خبری منفی (احساسات {narrative.sentiment:+.2f})")
            elif narrative.label == "BULLISH":
                reasons.append(f"فضای خبری مثبت (احساسات {narrative.sentiment:+.2f})")

        # ============ DECISION ==============================================
        if score >= SCORE_STRONG:
            action, conviction = "ENTER", "HIGH"
        elif score >= SCORE_MODERATE:
            action, conviction = "ENTER", "MEDIUM"
        elif score >= SCORE_WEAK:
            action, conviction = "WAIT", "LOW"
        else:
            action, conviction = "AVOID", "NONE"

        # Data confidence can only ever REDUCE conviction.
        if score_report.confidence_level == "LOW" and action == "ENTER":
            conviction = "LOW"
            risks.append("اعتماد به داده پایین است — اندازه موقعیت محافظه‌کارانه شد")

        # AI council: advisory, one-directional (safety ratchet only).
        if council is not None and council.council_status == "ONLINE":
            if council.final_stance == "AVOID" and action == "ENTER":
                action, conviction = "WAIT", "LOW"
                risks.append("شورای هوش مصنوعی توصیه به اجتناب کرد — به «صبر» تنزل یافت")
            elif council.final_stance == "UNCLEAR" and conviction == "HIGH":
                conviction = "MEDIUM"
            if council.echo_suspected:
                risks.append("اتفاق‌نظر مدل‌ها ممکن است هم‌آوایی باشد، نه تأیید مستقل")

        # Cognitive panel: same one-directional safety ratchet.
        if panel is not None:
            if panel.verdict == "CAUTION" and conviction == "HIGH":
                conviction = "MEDIUM"
                risks.append("شورای تحلیلی هشدار داد — اطمینان کاهش یافت")
            elif panel.verdict == "INSUFFICIENT_EVIDENCE" and action == "ENTER":
                action, conviction = "WAIT", "LOW"
                risks.append(
                    "بیش از نیمی از دیدگاه‌های تحلیلی به دلیل نبود داده سکوت "
                    "کردند — سکوت تأیید نیست")
            for c in panel.cautions[:3]:
                if c not in risks:
                    risks.append(f"شورای تحلیلی: {c}")

        # ============ POSITION SIZING =======================================
        size: float | None = None
        tp = sl = None
        max_hold = None

        if action == "ENTER":
            pool_cap = liq * MAX_POOL_SHARE_PCT / 100.0
            bankroll_cap = self.bankroll_usd * MAX_BANKROLL_RISK_PCT / 100.0
            conviction_factor = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}[conviction]
            size = min(pool_cap, bankroll_cap) * conviction_factor

            if exitability is not None and exitability.max_safe_position_usd:
                size = min(size, exitability.max_safe_position_usd)

            size = round(max(size, 0.0), 2)
            if size <= 0.0:
                action, conviction, size = "WAIT", "LOW", None
                risks.append("اندازه امن موقعیت عملاً صفر است — استخر بیش از حد کم‌عمق")
            else:
                reasons.append(
                    f"اندازه پیشنهادی ${size:,.2f} — سقف‌گذاری‌شده توسط عمق استخر "
                    f"({MAX_POOL_SHARE_PCT}٪) و ریسک سرمایه ({MAX_BANKROLL_RISK_PCT}٪)"
                )

            price = m.price_usd
            if price:
                tp = round(price * (1 + self.exit_cfg["take_profit_pct"]), 12)
                sl = round(price * (1 - self.exit_cfg["stop_loss_pct"]), 12)
                max_hold = self.exit_cfg["max_hold_hours"]
                invalidation = [
                    f"قیمت به {sl:.8g} برسد (حد ضرر {self.exit_cfg['stop_loss_pct'] * 100:.0f}٪)",
                    f"نقدینگی زیر ${self.exit_cfg['liq_collapse_floor_usd']:,.0f} برای "
                    f"{self.exit_cfg['liq_collapse_consecutive']} مشاهده متوالی",
                    "هر شواهد امنیتی بحرانی جدید پس از ورود",
                    f"گذشت {self.exit_cfg['max_hold_hours']:.0f} ساعت بدون رسیدن به هدف",
                ]
            else:
                unknowns.append("قیمت لحظه‌ای — بدون آن هدف و حد ضرر قابل تعیین نیست")

        base.action = action
        base.conviction = conviction
        base.suggested_size_usd = size
        base.take_profit_price = tp
        base.stop_loss_price = sl
        base.max_hold_hours = max_hold
        base.reasons = _dedup(reasons, 8)
        base.risks = _dedup(risks, 8)
        base.unknowns = _dedup(unknowns, 8)
        base.invalidation = invalidation
        return base

    # --------------------------------------------------------------- HOLDINGS
    def advise_position(self, symbol: str, entry_price: float, current_price: float | None,
                        entry_ts: float, current_liquidity: float | None = None,
                        entry_liquidity: float | None = None,
                        security_alert: bool = False,
                        now: float | None = None) -> PositionAdvice:
        """Advice for an already-held position, using the locked PT-X1-v1 exit rules."""
        ts = time.time() if now is None else now
        cfg = self.exit_cfg
        reasons: list[str] = []
        risks: list[str] = []
        unknowns: list[str] = []

        if current_price is None:
            return PositionAdvice(
                symbol=symbol, action="HOLD", urgency="ROUTINE", sell_fraction=0.0,
                pnl_pct=None, current_price=None, entry_price=entry_price,
                reasons=["قیمت لحظه‌ای در دسترس نیست — بدون داده تصمیم نمی‌گیریم"],
                unknowns=["قیمت فعلی"], computed_ts=ts,
            )

        pnl_pct = ((current_price - entry_price) / entry_price) * 100.0 if entry_price else None

        # 1. SECURITY — always immediate, always full exit.
        if security_alert:
            return PositionAdvice(
                symbol=symbol, action="EXIT", urgency="IMMEDIATE", sell_fraction=1.0,
                pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
                reasons=["شواهد امنیتی بحرانی پس از ورود — خروج کامل و فوری"],
                risks=["ادامه نگهداری می‌تواند به از دست رفتن کامل سرمایه منجر شود"],
                computed_ts=ts,
            )

        # 2. LIQUIDITY COLLAPSE — the exit door is closing.
        if current_liquidity is not None:
            if current_liquidity < cfg["liq_collapse_floor_usd"]:
                return PositionAdvice(
                    symbol=symbol, action="EXIT", urgency="IMMEDIATE", sell_fraction=1.0,
                    pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
                    reasons=[f"نقدینگی به ${current_liquidity:,.0f} سقوط کرده — درِ خروج در حال بسته شدن است"],
                    risks=["تأخیر در خروج یعنی گیر افتادن سرمایه"], computed_ts=ts,
                )
            if entry_liquidity and current_liquidity < entry_liquidity * 0.5:
                risks.append(
                    f"نقدینگی از ${entry_liquidity:,.0f} به ${current_liquidity:,.0f} نصف شده است"
                )
        else:
            unknowns.append("نقدینگی فعلی")

        # 3. STOP LOSS — conservative, checked before take-profit.
        if pnl_pct is not None and pnl_pct <= -cfg["stop_loss_pct"] * 100:
            return PositionAdvice(
                symbol=symbol, action="EXIT", urgency="IMMEDIATE", sell_fraction=1.0,
                pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
                reasons=[f"حد ضرر فعال شد ({pnl_pct:.1f}٪) — خروج طبق قاعده از پیش تعیین‌شده"],
                risks=risks, unknowns=unknowns, computed_ts=ts,
            )

        # 4. TAKE PROFIT — scale out, never all-or-nothing.
        if pnl_pct is not None and pnl_pct >= cfg["take_profit_pct"] * 100:
            return PositionAdvice(
                symbol=symbol, action="REDUCE", urgency="SOON", sell_fraction=0.5,
                pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
                reasons=[
                    f"هدف سود محقق شد ({pnl_pct:+.1f}٪)",
                    "فروش ۵۰٪ پیشنهاد می‌شود: اصل سرمایه آزاد، مابقی برای ادامه روند",
                ],
                risks=risks + ["نگهداری کامل، سود محقق‌نشده را در معرض بازگشت قرار می‌دهد"],
                unknowns=unknowns, computed_ts=ts,
            )

        # 5. TIME EXIT.
        held_h = (ts - entry_ts) / 3600.0
        if held_h >= cfg["max_hold_hours"]:
            return PositionAdvice(
                symbol=symbol, action="EXIT", urgency="SOON", sell_fraction=1.0,
                pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
                reasons=[
                    f"افق زمانی {cfg['max_hold_hours']:.0f} ساعته تمام شد "
                    f"({held_h:.1f} ساعت نگهداری، بازده {pnl_pct:+.1f}٪)"
                ],
                risks=risks, unknowns=unknowns, computed_ts=ts,
            )

        # 6. HOLD.
        reasons.append(
            f"در محدوده برنامه: بازده {pnl_pct:+.1f}٪ پس از {held_h:.1f} ساعت"
        )
        reasons.append(
            f"هدف {entry_price * (1 + cfg['take_profit_pct']):.8g} | "
            f"حد ضرر {entry_price * (1 - cfg['stop_loss_pct']):.8g}"
        )
        return PositionAdvice(
            symbol=symbol, action="HOLD", urgency="ROUTINE", sell_fraction=0.0,
            pnl_pct=pnl_pct, current_price=current_price, entry_price=entry_price,
            reasons=reasons, risks=risks, unknowns=unknowns, computed_ts=ts,
        )


def _dedup(items: list[str], limit: int) -> list[str]:
    seen, out = set(), []
    for x in items:
        k = (x or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(x)
    return out[:limit]
