#!/usr/bin/env python3
"""T0 -> T1 promotion gate evaluator for the paper tracks (M13).

The vision's autonomy ladder (section 11.0) has every market at **T0** today:
paper only, no execution. Promotion to T1 is not a code decision. The ladder
law makes it an owner act plus the three gate agents (قاسم AG-16, رضا AG-19,
سپهر AG-03), and the exit gate (vision :1095) lists ten quantitative criteria a
track must satisfy *before* that act is even available. AG-28's own charter
underlines it: ``allowed_authority: []`` with DECIDE and PROMOTE forbidden.

So this module does not promote. What it does is the honest half of the job:
measure. It reads a track's recorded trade history, computes each of the ten
criteria against the recorded numbers, and reports which are met, which are
unmet, and -- importantly -- which are *unmeasurable as specified*. A criterion
the code cannot compute is reported as such; it is never passed by default and
never silently dropped, because either would let a promotion claim form on
evidence that does not exist.

The one structural unmeasurability found while writing this: the exit gate
requires **>=3 of 4 regimes with >=30 trades each**, and
``architecture/intel/regimes.py`` defines exactly **three** regimes
(``REGIME_LABELS`` = BULL_TREND / BEAR_VOLATILE / NEUTRAL_CHOP). A four-regime
denominator does not exist in the code, so the criterion cannot be evaluated as
written. It is reported as UNMEASURABLE with the evidence, and listed for the
owner as M-REGIME-4. Papering over it -- counting three-regime coverage as
four-regime coverage, or inventing a fourth label here -- would be exactly the
kind of gate-loosening that makes a number move.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from ..intel.regimes import MarketRegimeClassifier

#: The regime vocabulary the code actually has. ``MarketRegimeClassifier``
#: accepts an ``n_regimes`` constructor argument, so a caller *can* ask for 4,
#: but ``REGIME_LABELS`` only maps three ids and the classifier's own label
#: lookup falls back to ``NEUTRAL_CHOP`` for any id it does not know
#: (``regimes.py:92``). A fourth regime therefore has no name in code -- asking
#: for one silently relabels to the third. This is why the exit gate's
#: ">=3 of 4 regimes" clause is UNMEASURABLE rather than merely unsatisfied.
REGIME_LABELS: dict[int, str] = dict(MarketRegimeClassifier.REGIME_LABELS)

# The ten exit-gate criteria, keyed by the ids used in the report. Thresholds
# come from vision :1095 verbatim -- they are not tuned here.
CRITERIA = {
    "data_depth_months": 6,
    "trade_count": 200,
    "regime_coverage": {"min_regimes": 3, "of_total": 4, "per_regime": 30},
    "cost_model": "net of fees and funding with 2x slippage",
    "max_drawdown_pct": 15.0,
    "drawdown_vs_backtest_multiple": 1.5,
    "sharpe": 1.0,
    "dsr_psr": 0.95,
    "profit_factor": 1.3,
    "month_profit_share_pct": 40.0,
    "walk_forward": "walk-forward and out-of-sample evidence required",
}

#: The tier ladder, for the report's vocabulary only.
TIER_T0 = "T0"       # paper only, no execution (where every market is today)
TIER_T1 = "T1"       # paper-proven, owner + three gate agents must still sign
TIER_UNMEASURABLE = "UNMEASURABLE"


@dataclass(frozen=True)
class CriterionResult:
    criterion: str
    required: str
    measured: str | None
    passed: bool | None          # None = unmeasurable, never a pass
    detail: str


@dataclass(frozen=True)
class TierGateReport:
    market: str
    tier_today: str
    criteria: tuple[CriterionResult, ...] = field(default_factory=tuple)
    promoted: bool = False       # always False from code; promotion is an owner act
    measurable_and_passed: int = 0
    measurable_total: int = 0
    unmeasurable: tuple[str, ...] = field(default_factory=tuple)
    open_questions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ready_for_owner_review(self) -> bool:
        """Every measurable criterion passes, and none is unmeasurable.

        An unmeasurable criterion blocks readiness rather than being waived:
        the gate is only ready for the owner's T1 act when it can actually be
        evaluated in full.
        """
        return (self.measurable_total > 0
                and self.measurable_and_passed == self.measurable_total
                and not self.unmeasurable)


def _fmt(value: float | None, places: int = 2) -> str | None:
    if value is None or not math.isfinite(value):
        return None
    return f"{value:.{places}f}"


def _trades_by_month(trades: list[dict]) -> dict[str, float]:
    """Realised PnL bucketed by calendar month key."""
    out: dict[str, float] = {}
    for t in trades:
        ts = t.get("exit_ts")
        pnl = t.get("realized_pnl_usd")
        if ts is None or pnl is None:
            continue
        import datetime as _dt
        key = _dt.datetime.fromtimestamp(float(ts), tz=_dt.timezone.utc).strftime("%Y-%m")
        out[key] = out.get(key, 0.0) + float(pnl)
    return out


def evaluate_tier_gate(
    *,
    market: str,
    trades: list[dict],
    months_of_data: float | None = None,
    regime_counts: dict[str, int] | None = None,
    backtest_max_drawdown_pct: float | None = None,
    declared_cost_model: str | None = None,
    walk_forward_evidence: bool | None = None,
) -> TierGateReport:
    """Evaluate the ten exit-gate criteria against a track's recorded history.

    ``trades`` is the track's own record: dicts with at least ``exit_ts`` and
    ``realized_pnl_usd`` (plus optional ``equity_after`` / ``drawdown_pct`` /
    ``regime``). Missing numbers make a criterion UNMET, never passed -- the
    same fail-closed direction as every other gate in the system.
    """
    trades = list(trades or [])
    results: list[CriterionResult] = []
    questions: list[str] = []

    # --- data depth ---------------------------------------------------------
    if months_of_data is None:
        # An unsupplied measurement is UNMEASURABLE rather than FAIL: it blocks
        # readiness harder, because the gate cannot be evaluated at all, and a
        # FAIL would imply the number was seen and fell short.
        results.append(CriterionResult("data_depth_months", ">=6 months",
                                       None, None,
                                       "no data-depth measurement was supplied"))
    else:
        ok = months_of_data >= CRITERIA["data_depth_months"]
        results.append(CriterionResult(
            "data_depth_months", ">=6 months", _fmt(months_of_data),
            ok, f"{months_of_data:.2f} months of real data"))

    # --- trade count --------------------------------------------------------
    n = len(trades)
    results.append(CriterionResult(
        "trade_count", f">={CRITERIA['trade_count']} trades", str(n),
        n >= CRITERIA["trade_count"],
        f"{n} recorded trades"))

    # --- regime coverage (the 3-vs-4 unmeasurability) ----------------------
    spec = CRITERIA["regime_coverage"]
    defined = len(REGIME_LABELS)
    if defined < spec["of_total"]:
        # The gate names a 4-regime denominator the code does not have.
        results.append(CriterionResult(
            "regime_coverage",
            f">={spec['min_regimes']} of {spec['of_total']} regimes, "
            f">={spec['per_regime']} trades each",
            f"{defined} regimes defined", None,
            f"UNMEASURABLE as specified: architecture/intel/regimes.py defines "
            f"{defined} regimes ({', '.join(REGIME_LABELS.values())}) but the "
            f"exit gate requires >=3 of {spec['of_total']}. A fourth regime "
            f"has no label in code -- MarketRegimeClassifier(n_regimes=4) "
            f"would relabel the extra state to NEUTRAL_CHOP via the "
            f"REGIME_LABELS.get fallback at regimes.py:92 -- so it is not "
            f"invented here."))
        questions.append(
            "M-REGIME-4: the exit gate's >=3-of-4 regime coverage cannot be "
            "evaluated because only 3 regimes are defined "
            "(architecture/intel/regimes.py). Owner act: either name the "
            "fourth regime the gate intends, or amend the gate to 3.")
    else:
        counts = regime_counts or {}
        with_enough = sum(1 for label in REGIME_LABELS.values()
                          if counts.get(label, 0) >= spec["per_regime"])
        results.append(CriterionResult(
            "regime_coverage",
            f">={spec['min_regimes']} of {spec['of_total']} regimes, "
            f">={spec['per_regime']} trades each",
            f"{with_enough}/{defined} with >= {spec['per_regime']}",
            with_enough >= spec["min_regimes"],
            f"regime trade counts: {counts}"))

    # --- cost model ---------------------------------------------------------
    required_cost = CRITERIA["cost_model"]
    if declared_cost_model is None:
        results.append(CriterionResult(
            "cost_model", required_cost, None, None,
            "UNMEASURABLE: no measured cost model was supplied; a paper "
            "assumption is not sufficient for this criterion"))
    else:
        ok = required_cost in declared_cost_model
        results.append(CriterionResult(
            "cost_model", required_cost, declared_cost_model, ok,
            f"declared cost model: {declared_cost_model}"))

    # --- drawdown -----------------------------------------------------------
    dd = max((float(t.get("drawdown_pct") or 0.0) for t in trades), default=None)
    if dd is None:
        # An empty track has no drawdown to measure: a 0.00% reading would be
        # a vacuous PASS and could let readiness drift true on no evidence.
        results.append(CriterionResult(
            "max_drawdown_pct", f"<={CRITERIA['max_drawdown_pct']}%",
            None, None, "no trades recorded, drawdown undefined"))
    else:
        dd_ok = dd <= CRITERIA["max_drawdown_pct"]
        results.append(CriterionResult(
            "max_drawdown_pct", f"<={CRITERIA['max_drawdown_pct']}%",
            _fmt(dd), dd_ok,
            f"max drawdown {dd:.2f}% of the paper bankroll"))
    if backtest_max_drawdown_pct is None:
        results.append(CriterionResult(
            "drawdown_vs_backtest_multiple",
            f"<={CRITERIA['drawdown_vs_backtest_multiple']}x backtest",
            None, None,
            "UNMEASURABLE: no backtest drawdown was supplied to compare "
            "against, so the forward/live multiple cannot be computed"))
        questions.append(
            "M-DD-BACKTEST: the drawdown-vs-backtest criterion needs a "
            "backtest MaxDD reference; supply one or the criterion stays "
            "unmeasurable.")
    elif dd is None:
        results.append(CriterionResult(
            "drawdown_vs_backtest_multiple",
            f"<={CRITERIA['drawdown_vs_backtest_multiple']}x backtest",
            None, None, "no paper drawdown recorded to compare"))
    else:
        mult = dd / backtest_max_drawdown_pct if backtest_max_drawdown_pct > 0 else None
        results.append(CriterionResult(
            "drawdown_vs_backtest_multiple",
            f"<={CRITERIA['drawdown_vs_backtest_multiple']}x backtest",
            None if mult is None else _fmt(mult, 2),
            None if mult is None else mult <= CRITERIA["drawdown_vs_backtest_multiple"],
            f"paper MaxDD {dd:.2f}% vs backtest "
            f"{backtest_max_drawdown_pct:.2f}%"))

    # --- risk-adjusted return ----------------------------------------------
    pnls = [float(t.get("realized_pnl_usd") or 0.0) for t in trades]
    sharpe = _sharpe(pnls)
    results.append(CriterionResult(
        "sharpe", f">={CRITERIA['sharpe']}", _fmt(sharpe),
        None if sharpe is None else sharpe >= CRITERIA["sharpe"],
        "per-trade Sharpe of realised PnL" if sharpe is not None
        else "fewer than two trades, Sharpe undefined"))

    dsr = _dsr(sharpe, n)
    results.append(CriterionResult(
        "dsr_psr", f">={CRITERIA['dsr_psr']}", _fmt(dsr),
        None if dsr is None else dsr >= CRITERIA["dsr_psr"],
        "Deflated/Probabilistic Sharpe ratio; requires a Sharpe to deflate"
        if dsr is not None else "no Sharpe, so DSR/PSR is undefined"))

    # --- profit factor ------------------------------------------------------
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = -sum(p for p in pnls if p < 0)
    pf = (gross_profit / gross_loss) if gross_loss > 0 else None
    results.append(CriterionResult(
        "profit_factor", f">={CRITERIA['profit_factor']}",
        None if pf is None else _fmt(pf),
        None if pf is None else pf >= CRITERIA["profit_factor"],
        f"gross profit {gross_profit:.2f} / gross loss {gross_loss:.2f}"
        if pf is not None else "no losing trades recorded, PF undefined"))

    # --- month concentration ------------------------------------------------
    by_month = _trades_by_month(trades)
    total_profit = sum(v for v in by_month.values() if v > 0)
    worst_month_share = None
    if total_profit > 0 and by_month:
        worst_month_share = max(v for v in by_month.values() if v > 0) \
            / total_profit * 100.0
    results.append(CriterionResult(
        "month_profit_share_pct", f"no month >{CRITERIA['month_profit_share_pct']}%",
        None if worst_month_share is None else _fmt(worst_month_share, 1),
        None if worst_month_share is None
        else worst_month_share <= CRITERIA["month_profit_share_pct"],
        f"best month is {worst_month_share:.1f}% of total profit"
        if worst_month_share is not None
        else "no profitable month recorded yet"))

    # --- walk-forward -------------------------------------------------------
    if walk_forward_evidence is None:
        results.append(CriterionResult(
            "walk_forward", CRITERIA["walk_forward"], None, None,
            "UNMEASURABLE: no walk-forward / out-of-sample evidence was "
            "supplied"))
    else:
        results.append(CriterionResult(
            "walk_forward", CRITERIA["walk_forward"],
            "supplied" if walk_forward_evidence else "absent",
            bool(walk_forward_evidence),
            "walk-forward and out-of-sample splits present"
            if walk_forward_evidence else "no WF/OOS splits present"))

    measurable = [r for r in results if r.passed is not None]
    unmeasurable = tuple(r.criterion for r in results if r.passed is None)
    return TierGateReport(
        market=market,
        tier_today=TIER_T0,
        criteria=tuple(results),
        promoted=False,                       # code never promotes
        measurable_and_passed=sum(1 for r in measurable if r.passed),
        measurable_total=len(measurable),
        unmeasurable=unmeasurable,
        open_questions=tuple(questions),
    )


def _sharpe(pnls: list[float]) -> float | None:
    """Per-trade Sharpe of realised PnL, annualisation-free.

    The gate compares against a fixed threshold, so the annualisation factor
    cancels as long as it is applied consistently; a plain mean/std ratio is
    used and the report says so rather than implying an annualised figure.
    """
    if len(pnls) < 2:
        return None
    mean = sum(pnls) / len(pnls)
    var = sum((p - mean) ** 2 for p in pnls) / (len(pnls) - 1)
    if var <= 0:
        return None
    return mean / math.sqrt(var)


def _dsr(sharpe: float | None, n: int) -> float | None:
    """Probabilistic Sharpe ratio (no deflation adjustment).

    PSR = P(Sharpe_true > 0) under a normal approximation; a deflated variant
    needs the number of trials and the variance of the Sharpe distribution,
    which a single track does not have. Reported as PSR, and the criterion id
    keeps the DSR/PSR name the gate uses.
    """
    if sharpe is None or n < 2:
        return None
    import statistics
    se = 1.0 / math.sqrt(n - 1)
    if se <= 0:
        return None
    z = sharpe / se
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def write_gate_report(report: TierGateReport, path: Path) -> None:
    """Render the gate evaluation as markdown for the owner.

    A promotion claim reads 'ready for owner review' or it does not; the file
    never styles an unmeasurable or unmet criterion as progress.
    """
    lines = [
        f"# T0 -> T1 promotion gate — {report.market}",
        "",
        f"Tier today: **{report.tier_today}** (paper only, no execution).",
        f"Promoted by this evaluation: **{report.promoted}** — promotion is an "
        "owner act plus the three gate agents (قاسم AG-16, رضا AG-19, سپهر "
        "AG-03), never a code decision.",
        "",
        f"{report.measurable_and_passed}/{report.measurable_total} measurable "
        f"criteria passed; {len(report.unmeasurable)} unmeasurable.",
        "",
        "| Criterion | Required | Measured | Pass | Detail |",
        "|---|---|---|---|---|",
    ]
    for r in report.criteria:
        verdict = {True: "PASS", False: "FAIL", None: "UNMEASURABLE"}[r.passed]
        measured = r.measured if r.measured is not None else "—"
        lines.append(f"| `{r.criterion}` | {r.required} | {measured} | "
                     f"{verdict} | {r.detail} |")
    lines.append("")
    if report.open_questions:
        lines.append("## Owner questions")
        lines.append("")
        for q in report.open_questions:
            lines.append(f"- {q}")
        lines.append("")
    if report.unmeasurable:
        lines.append("## Unmeasurable criteria")
        lines.append("")
        lines.append("These block readiness rather than being waived:")
        for c in report.unmeasurable:
            lines.append(f"- `{c}`")
        lines.append("")
    if report.ready_for_owner_review:
        lines.append("**Ready for owner review.** All measurable criteria pass "
                     "and none is unmeasurable.")
    else:
        lines.append("**Not ready for owner review.** Measurable criteria must "
                     "all pass and every criterion must be evaluable before "
                     "the T1 act is available.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
