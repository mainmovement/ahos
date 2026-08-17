#!/usr/bin/env python3
"""AHOS Hindsight Engine (Wave-25) — "what would have happened if I had bought?"

The user's ask, verbatim in spirit: *"token X picked on date Y — what would have
happened if bought?"* This module answers that question honestly and turns the
answer into evidence the system can learn from.

Three laws govern this file, and they are the reason it is written the way it is:

1. HINDSIGHT MAY JUDGE A DECISION, NEVER JUSTIFY IT (§9).
   Every verdict is labelled OUT_OF_SAMPLE_REVIEW. Post-decision data is used to
   grade the decision rule, never retroactively to bless a call that happened to
   win. A lucky win on a broken rule is still a broken rule.

2. THE COUNTERFACTUAL IS PRICED AT REALIZABLE VALUE, NOT DISPLAYED VALUE.
   A naive backtest says "it went up 4x". The truthful question is: could $X have
   actually been sold at that price? We route the exit through
   paper_trading.realizable, so a 4x on a $900 pool is correctly reported as a
   trap, not a triumph. This distinction is the entire point of the exercise --
   a self-improvement loop trained on displayed value teaches itself to chase
   tokens it can never exit.

3. UNKNOWN IS A VERDICT.
   Thin or missing observation history yields INSUFFICIENT_DATA. It never
   silently becomes a zero, a neutral, or an average. Learning from fabricated
   outcomes is worse than not learning.

Read-only with respect to discovery data. Writes only its own lesson rows.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from typing import Any

HINDSIGHT_VERSION = "AHOS-HINDSIGHT-v1"

OUT_OF_SAMPLE_NOTE = (
    "OUT_OF_SAMPLE_REVIEW — این داده پس از تصمیم به دست آمده است؛ "
    "برای قضاوتِ قاعده مجاز است، برای توجیهِ تصمیمِ گذشته هرگز."
)

# Locked evaluation bands. Pre-registered here so results cannot be tuned after
# the fact by moving the goalposts.
WIN_MULTIPLE = 1.50            # >= +50% realizable  -> the pick would have paid
LOSS_MULTIPLE = 0.65           # <= -35% realizable  -> the pick would have hurt
DEAD_LIQUIDITY_USD = 500.0     # below this the position is effectively stranded
MIN_OBSERVATIONS = 3           # fewer points than this cannot describe a path
DEFAULT_HORIZON_HOURS = 48.0   # matches EXIT_V1 max_hold_hours
DEFAULT_POSITION_USD = 20.0    # matches BANKROLL_START_USD scale

VERDICTS = (
    "WOULD_HAVE_WON",        # realizable exit cleared the win band
    "WOULD_HAVE_LOST",       # realizable exit fell through the loss band
    "WOULD_HAVE_BEEN_FLAT",  # neither band touched
    "WOULD_HAVE_BEEN_TRAPPED",  # price may have risen, but exit was impossible
    "INSUFFICIENT_DATA",     # not enough honest observation history
)


@dataclass
class HindsightResult:
    """One counterfactual review of one pick."""
    token_id: str
    symbol: str
    decision_ts: float
    verdict: str
    horizon_hours: float
    position_usd: float

    entry_price: float | None = None
    peak_price: float | None = None
    trough_price: float | None = None
    final_price: float | None = None

    # Displayed (naive) vs realizable (honest) outcome. The gap between these
    # two numbers is the single most instructive figure this system produces.
    displayed_peak_multiple: float | None = None
    realizable_peak_usd: float | None = None
    realizable_final_usd: float | None = None
    realizable_peak_multiple: float | None = None

    max_favorable_pct: float | None = None
    max_adverse_pct: float | None = None
    time_to_peak_hours: float | None = None
    observation_count: int = 0
    min_liquidity_usd: float | None = None

    would_have_exited_by_rule: bool = False
    rule_exit_reason: str | None = None
    rule_exit_pnl_pct: float | None = None

    lesson: str = ""
    reasons: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    review_label: str = OUT_OF_SAMPLE_NOTE
    version: str = HINDSIGHT_VERSION
    computed_ts: float = 0.0

    @property
    def is_known(self) -> bool:
        return self.verdict != "INSUFFICIENT_DATA"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HindsightEngine:
    """Replays past picks against the observation history that followed them."""

    def __init__(self, discovery: sqlite3.Connection,
                 win_multiple: float = WIN_MULTIPLE,
                 loss_multiple: float = LOSS_MULTIPLE):
        self.discovery = discovery
        self.win_multiple = win_multiple
        self.loss_multiple = loss_multiple

    # ------------------------------------------------------------------ io --

    def _observations(self, token_id: str, since_ts: float,
                      until_ts: float) -> list[dict]:
        """Clean observations in (since, until]. Error rows are excluded, not zeroed."""
        try:
            rows = self.discovery.execute(
                """SELECT retrieved_ts, price_usd, liquidity_usd
                     FROM discovery_observations
                    WHERE token_id = ?
                      AND error_state IS NULL
                      AND price_usd IS NOT NULL AND price_usd > 0
                      AND retrieved_ts > ? AND retrieved_ts <= ?
                 ORDER BY retrieved_ts ASC""",
                (token_id, since_ts, until_ts)).fetchall()
        except Exception:
            return []
        return [{"ts": r[0], "price": r[1], "liq": r[2]} for r in rows]

    def _entry_reference(self, token_id: str, decision_ts: float) -> dict | None:
        """Price at (or just before) the decision. Never look forward for entry."""
        try:
            r = self.discovery.execute(
                """SELECT retrieved_ts, price_usd, liquidity_usd
                     FROM discovery_observations
                    WHERE token_id = ?
                      AND error_state IS NULL
                      AND price_usd IS NOT NULL AND price_usd > 0
                      AND retrieved_ts <= ?
                 ORDER BY retrieved_ts DESC LIMIT 1""",
                (token_id, decision_ts)).fetchone()
        except Exception:
            return None
        return {"ts": r[0], "price": r[1], "liq": r[2]} if r else None

    # ------------------------------------------------------------- pricing --

    def _realizable_usd(self, position_usd: float, entry_price: float,
                        price: float, liquidity_usd: float | None) -> float | None:
        """What the position could ACTUALLY be sold for at this point in time."""
        if not liquidity_usd or liquidity_usd <= 0 or entry_price <= 0:
            return None
        try:
            from paper_trading import realizable as rz
        except Exception:
            return None
        # qty is fixed at entry; only price and pool depth move afterwards.
        qty = position_usd / entry_price
        try:
            out = rz.assess(
                qty=qty,
                price_obs=float(price),
                liq_now=float(liquidity_usd),
                sell_tax_bps=0.0,
                chain="solana",
                classification="OK",
            )
            return out.get("realizable_value_usd")
        except Exception:
            return None

    # -------------------------------------------------------------- review --

    def review_pick(self, token_id: str, decision_ts: float,
                    symbol: str = "UNKNOWN",
                    horizon_hours: float = DEFAULT_HORIZON_HOURS,
                    position_usd: float = DEFAULT_POSITION_USD,
                    now: float | None = None) -> HindsightResult:
        """Answer: if we had bought `position_usd` of this at `decision_ts`, then what?"""
        now = time.time() if now is None else now
        res = HindsightResult(
            token_id=token_id, symbol=symbol, decision_ts=decision_ts,
            verdict="INSUFFICIENT_DATA", horizon_hours=horizon_hours,
            position_usd=position_usd, computed_ts=now,
        )

        entry = self._entry_reference(token_id, decision_ts)
        if entry is None:
            res.unknowns.append("قیمت مرجع در زمان تصمیم موجود نیست")
            res.lesson = "بدون قیمت ورودی، بازبینی این انتخاب ممکن نیست."
            return res

        res.entry_price = entry["price"]
        window_end = decision_ts + horizon_hours * 3600.0
        obs = self._observations(token_id, decision_ts, min(window_end, now))
        res.observation_count = len(obs)

        if len(obs) < MIN_OBSERVATIONS:
            res.unknowns.append(
                f"تنها {len(obs)} مشاهده پس از تصمیم ثبت شده "
                f"(حداقل لازم: {MIN_OBSERVATIONS})")
            res.lesson = ("پوشش رصد برای این توکن ناکافی بوده است — "
                          "این خودش یک نقص قابل رفع در سامانه است، نه نتیجه بازار.")
            return res

        prices = [o["price"] for o in obs]
        liqs = [o["liq"] for o in obs if o["liq"] is not None]
        peak = max(prices)
        trough = min(prices)
        res.peak_price = peak
        res.trough_price = trough
        res.final_price = prices[-1]
        res.min_liquidity_usd = min(liqs) if liqs else None

        e = res.entry_price
        res.displayed_peak_multiple = peak / e
        res.max_favorable_pct = (peak - e) / e * 100.0
        res.max_adverse_pct = (trough - e) / e * 100.0

        peak_obs = max(obs, key=lambda o: o["price"])
        res.time_to_peak_hours = (peak_obs["ts"] - decision_ts) / 3600.0

        # --- the honest half: could the money have come back out? ---
        res.realizable_peak_usd = self._realizable_usd(
            position_usd, e, peak, peak_obs["liq"])
        res.realizable_final_usd = self._realizable_usd(
            position_usd, e, prices[-1], obs[-1]["liq"])
        if res.realizable_peak_usd is not None and position_usd > 0:
            res.realizable_peak_multiple = res.realizable_peak_usd / position_usd

        self._apply_exit_rule(res, obs, e)
        self._classify(res)
        self._explain(res)
        return res

    def _apply_exit_rule(self, res: HindsightResult, obs: list[dict],
                         entry: float) -> None:
        """Replay the frozen EXIT_V1 card over the path -- would IT have fired?"""
        try:
            from paper_trading.exit_rules import EXIT_V1
            tp = EXIT_V1["take_profit_pct"]
            sl = EXIT_V1["stop_loss_pct"]
            floor_usd = EXIT_V1["liq_collapse_floor_usd"]
        except Exception:
            tp, sl, floor_usd = 0.50, 0.35, 2000.0

        for o in obs:
            change = (o["price"] - entry) / entry
            liq = o["liq"]
            # Priority order mirrors EXIT_V1: liquidity collapse, then SL, then TP.
            if liq is not None and liq < floor_usd:
                res.would_have_exited_by_rule = True
                res.rule_exit_reason = "LIQUIDITY_COLLAPSE"
                res.rule_exit_pnl_pct = change * 100.0
                return
            if change <= -sl:
                res.would_have_exited_by_rule = True
                res.rule_exit_reason = "STOP_LOSS"
                res.rule_exit_pnl_pct = change * 100.0
                return
            if change >= tp:
                res.would_have_exited_by_rule = True
                res.rule_exit_reason = "TAKE_PROFIT"
                res.rule_exit_pnl_pct = change * 100.0
                return
        res.rule_exit_reason = "TIME_EXIT"
        res.rule_exit_pnl_pct = (obs[-1]["price"] - entry) / entry * 100.0

    def _classify(self, res: HindsightResult) -> None:
        """Verdict reflects what the SYSTEM would actually have realized.

        Judging on the peak alone flatters every pick: a token that touched
        +10% on its way to -60% did not 'do fine'. So the outcome is taken from
        the exit the frozen rule would genuinely have produced, while the peak
        is reserved for detecting traps and missed upside.
        """
        stranded = (res.min_liquidity_usd is not None
                    and res.min_liquidity_usd < DEAD_LIQUIDITY_USD)

        # A pick whose pool died is trapped regardless of what the chart did.
        if stranded:
            res.verdict = "WOULD_HAVE_BEEN_TRAPPED"
            return

        peak_mult = res.realizable_peak_multiple
        if peak_mult is None:
            res.unknowns.append("محاسبه ارزش واقعی خروج ممکن نبود؛ "
                                "قضاوت بر پایه قیمت نمایشی است")
            peak_mult = res.displayed_peak_multiple or 0.0

        # Paper gains that evaporate once exit costs are applied are a trap:
        # the chart said win, the cash register said no.
        if (res.displayed_peak_multiple is not None
                and res.displayed_peak_multiple >= self.win_multiple
                and peak_mult < 1.0):
            res.verdict = "WOULD_HAVE_BEEN_TRAPPED"
            return

        # The realized outcome: where the frozen exit rule would have closed us.
        if res.rule_exit_pnl_pct is not None:
            exit_mult = 1.0 + (res.rule_exit_pnl_pct / 100.0)
        else:
            exit_mult = peak_mult

        if exit_mult >= self.win_multiple:
            res.verdict = "WOULD_HAVE_WON"
        elif exit_mult <= self.loss_multiple:
            res.verdict = "WOULD_HAVE_LOST"
        else:
            res.verdict = "WOULD_HAVE_BEEN_FLAT"

    def _explain(self, res: HindsightResult) -> None:
        """Persian, specific, and blunt. A lesson nobody reads teaches nothing."""
        d = res.displayed_peak_multiple
        r = res.realizable_peak_multiple

        if d is not None:
            res.reasons.append(f"اوج قیمت نمایشی: {d:.2f}× ورودی")
        if r is not None:
            res.reasons.append(f"اوج ارزش واقعیِ قابل برداشت: {r:.2f}× ورودی")
        if d is not None and r is not None and d - r > 0.15:
            res.reasons.append(
                f"شکاف نمایش/واقعیت: {(d - r):.2f}× از سود روی کاغذ در "
                f"لغزش، کارمزد و مالیات فروش از بین می‌رفت")
        if res.time_to_peak_hours is not None:
            res.reasons.append(f"زمان تا اوج: {res.time_to_peak_hours:.1f} ساعت")
        if res.rule_exit_reason:
            res.reasons.append(
                f"قاعده خروج EXIT_V1 با «{res.rule_exit_reason}» فعال می‌شد "
                f"({(res.rule_exit_pnl_pct or 0.0):+.1f}%)")

        if res.verdict == "WOULD_HAVE_WON":
            res.lesson = ("این انتخاب سودده می‌بود. باید بررسی شود چه ویژگی‌هایی "
                          "آن را متمایز می‌کرد و آیا آن ویژگی‌ها قابل تکرارند "
                          "یا صرفاً شانس بوده‌اند.")
        elif res.verdict == "WOULD_HAVE_LOST":
            res.lesson = ("این انتخاب زیان‌ده می‌بود. اگر قاعده خروج به‌موقع فعال "
                          "شده، سامانه درست عمل کرده است؛ زیانِ محدودشده یک موفقیت "
                          "است، نه یک شکست.")
        elif res.verdict == "WOULD_HAVE_BEEN_TRAPPED":
            res.lesson = ("مهم‌ترین درس: قیمت ممکن بود بالا برود اما پول بیرون "
                          "نمی‌آمد. سنجش «امکان خروج» باید بر «امتیاز فرصت» "
                          "مقدم باشد.")
        else:
            res.lesson = ("نه سود معنادار، نه زیان معنادار. هزینه فرصت و کارمزدها "
                          "را در برابر بی‌عملی بسنجید.")

    # ------------------------------------------------------------ batching --

    def review_recent_picks(self, limit: int = 20,
                            horizon_hours: float = DEFAULT_HORIZON_HOURS,
                            position_usd: float = DEFAULT_POSITION_USD,
                            now: float | None = None) -> list[HindsightResult]:
        """Review the most recent ranked opportunities that are old enough to judge."""
        now = time.time() if now is None else now
        cutoff = now - horizon_hours * 3600.0
        try:
            rows = self.discovery.execute(
                """SELECT r.token_id, r.as_of_ts, COALESCE(t.symbol, 'UNKNOWN')
                     FROM opportunity_rank r
                     LEFT JOIN tokens t ON t.token_id = r.token_id
                    WHERE r.as_of_ts <= ?
                 ORDER BY r.as_of_ts DESC LIMIT ?""", (cutoff, limit)).fetchall()
        except Exception:
            return []
        return [self.review_pick(tid, ts, symbol=sym,
                                 horizon_hours=horizon_hours,
                                 position_usd=position_usd, now=now)
                for tid, ts, sym in rows]

    def aggregate(self, results: list[HindsightResult]) -> dict[str, Any]:
        """Turn individual reviews into the numbers that should change behaviour."""
        known = [r for r in results if r.is_known]
        counts = {v: sum(1 for r in known if r.verdict == v) for v in VERDICTS}
        counts["INSUFFICIENT_DATA"] = len(results) - len(known)

        trapped = counts.get("WOULD_HAVE_BEEN_TRAPPED", 0)
        won = counts.get("WOULD_HAVE_WON", 0)

        gaps = [r.displayed_peak_multiple - r.realizable_peak_multiple
                for r in known
                if r.displayed_peak_multiple is not None
                and r.realizable_peak_multiple is not None]

        out: dict[str, Any] = {
            "reviewed": len(results),
            "judgeable": len(known),
            "counts": counts,
            "hit_rate": (won / len(known)) if known else None,
            "trap_rate": (trapped / len(known)) if known else None,
            "avg_display_reality_gap": (sum(gaps) / len(gaps)) if gaps else None,
            "review_label": OUT_OF_SAMPLE_NOTE,
            "version": HINDSIGHT_VERSION,
        }

        # Coverage is itself a finding: if most picks cannot be judged, the
        # bottleneck is observation, not strategy.
        if results and len(known) / len(results) < 0.5:
            out["priority_finding"] = (
                "بیش از نیمی از انتخاب‌ها قابل ارزیابی نیستند — "
                "اولویت اصلاح، پوشش رصد است نه منطق امتیازدهی.")
        elif known and trapped / len(known) > 0.25:
            out["priority_finding"] = (
                "نرخ بالای «قابل خروج نبودن» — آستانه نقدینگی باید سخت‌گیرانه‌تر شود.")
        return out

    def report_persian(self, results: list[HindsightResult]) -> str:
        """Human-facing digest for Telegram."""
        agg = self.aggregate(results)
        lines = ["🔁 بازبینی انتخاب‌های گذشته (یادگیری از خطا)", ""]
        if not results:
            lines.append("هنوز انتخاب قدیمیِ قابل بازبینی وجود ندارد.")
            lines.append("")
            lines.append(OUT_OF_SAMPLE_NOTE)
            return "\n".join(lines)

        lines.append(f"بررسی‌شده: {agg['reviewed']} | قابل قضاوت: {agg['judgeable']}")
        if agg["hit_rate"] is not None:
            lines.append(f"نرخ موفقیت: {agg['hit_rate']:.0%} | "
                         f"نرخ تله (غیرقابل خروج): {agg['trap_rate']:.0%}")
        if agg["avg_display_reality_gap"] is not None:
            lines.append(f"میانگین شکاف نمایش/واقعیت: "
                         f"{agg['avg_display_reality_gap']:.2f}×")
        if agg.get("priority_finding"):
            lines += ["", f"⚠️ {agg['priority_finding']}"]

        judged = [r for r in results if r.is_known][:5]
        if judged:
            lines += ["", "نمونه‌ها:"]
            icon = {"WOULD_HAVE_WON": "🟢", "WOULD_HAVE_LOST": "🔴",
                    "WOULD_HAVE_BEEN_TRAPPED": "🪤", "WOULD_HAVE_BEEN_FLAT": "⚪"}
            for r in judged:
                lines.append(f" {icon.get(r.verdict, '•')} {r.symbol}: {r.verdict}")
                if r.reasons:
                    lines.append(f"    {r.reasons[0]}")
        lines += ["", OUT_OF_SAMPLE_NOTE]
        return "\n".join(lines)
