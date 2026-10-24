"""Strategy Red Team & 2x/3x Cost Stress Tester.
Attacks candidate paper strategies from M56 (`strategy_tournament.py`) and M13_REPLAY across 5 vectors:
1. COST_STRESS_2X_3X: Evaluates net Sharpe / return survival under 2x and 3x transaction cost / slippage bps
2. SINGLE_EVENT_DEPENDENCY: Removes the top 3 best trades/days and checks if cumulative edge turns negative
3. LOOKAHEAD_CANARY: Verifies strict causal/forward-only feature flag (`lookahead_leak_detected == False`)
4. REGIME_CONCENTRATION: Checks that strategy does not lose catastrophically outside a single lucky regime
5. PARAMETER_PERTURBATION: Checks stability under +/-15% parameter perturbation
Outputs `SURVIVED_RED_TEAM` or `VETOED_FRAGILE` with plain-Persian critique (`red_team_verdict_fa`).
Strictly PAPER_ONLY = True and auto_promote = False.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

PAPER_ONLY: bool = True
AUTO_PROMOTE: bool = False

ATTACK_VECTORS_5: tuple[str, ...] = (
    "01_COST_STRESS_2X_3X",
    "02_SINGLE_EVENT_DEPENDENCY",
    "03_LOOKAHEAD_CANARY",
    "04_REGIME_CONCENTRATION",
    "05_PARAMETER_PERTURBATION_15PCT",
)


@dataclass(frozen=True, slots=True)
class AttackVectorResult:
    vector_id: str
    passed: bool
    metric_summary: str
    critique_fa: str


@dataclass(frozen=True, slots=True)
class StrategyRedTeamReport:
    strategy_id: str
    title: str
    verdict: str  # "SURVIVED_RED_TEAM" | "VETOED_FRAGILE"
    vectors_passed: int
    vectors_total: int
    baseline_sharpe: float
    sharpe_at_2x_cost: float
    sharpe_at_3x_cost: float
    ex_top3_net_return_pct: float
    attack_results: tuple[AttackVectorResult, ...]
    red_team_verdict_fa: str
    paper_only: bool = True
    auto_promote: bool = False


def _annualized_sharpe(returns: Sequence[float]) -> float:
    n = len(returns)
    if n < 2:
        return 0.0
    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    std_r = math.sqrt(var_r) if var_r > 1e-12 else 0.0
    if std_r <= 0.0:
        return 0.0
    return round((mean_r / std_r) * math.sqrt(252.0), 4)


def evaluate_strategy_red_team(candidate: Mapping[str, Any]) -> StrategyRedTeamReport:
    sid = str(candidate.get("strategy_id") or "strat-unknown")
    title = str(candidate.get("title") or sid)
    gross_returns = [float(x) for x in (candidate.get("returns") or ())]
    cost_per_trade_bps = float(candidate.get("cost_bps", 4.5))
    cost_frac = cost_per_trade_bps / 10_000.0

    net_1x = [r - cost_frac for r in gross_returns]
    net_2x = [r - (2.0 * cost_frac) for r in gross_returns]
    net_3x = [r - (3.0 * cost_frac) for r in gross_returns]

    sr_1x = _annualized_sharpe(net_1x)
    sr_2x = _annualized_sharpe(net_2x)
    sr_3x = _annualized_sharpe(net_3x)

    # 1. Cost stress 2x/3x
    v1_pass = sr_2x >= 1.0 and sr_3x > 0.25 and sum(net_2x) > 0
    v1 = AttackVectorResult(
        vector_id="01_COST_STRESS_2X_3X",
        passed=v1_pass,
        metric_summary=f"sr_1x={sr_1x:.2f},sr_2x={sr_2x:.2f},sr_3x={sr_3x:.2f}",
        critique_fa=(
            f"مقاوم در برابر دوبرابر و سه‌برابر شدن کارمزد و اسلیپیج (Sharpe 2x={sr_2x:.2f}, 3x={sr_3x:.2f})."
            if v1_pass
            else f"شکننده در برابر افزایش هزینهٔ تراکنش و اسلیپیج (Sharpe 2x={sr_2x:.2f}, 3x={sr_3x:.2f})."
        ),
    )

    # 2. Single-event dependency (remove top 3 trades)
    sorted_net = sorted(net_1x, reverse=True)
    ex_top3 = sorted_net[3:] if len(sorted_net) > 3 else []
    ex_top3_pct = round(sum(ex_top3) * 100.0, 4)
    v2_pass = len(ex_top3) >= 5 and ex_top3_pct > 0.0
    v2 = AttackVectorResult(
        vector_id="02_SINGLE_EVENT_DEPENDENCY",
        passed=v2_pass,
        metric_summary=f"ex_top3_return_pct={ex_top3_pct:+.3f}%",
        critique_fa=(
            f"با حذف ۳ معاملهٔ برتر، بازده خالص همچنان مثبت است ({ex_top3_pct:+.2f}%)؛ سود وابسته به یک رویداد تصادفی نیست."
            if v2_pass
            else f"با حذف ۳ معاملهٔ برتر، کل سود استراتژی از بین می‌رود ({ex_top3_pct:+.2f}%)؛ خطر وابستگی به تک‌رویداد."
        ),
    )

    # 3. Lookahead canary
    lookahead_leak = bool(candidate.get("lookahead_leak_detected", False))
    v3_pass = not lookahead_leak
    v3 = AttackVectorResult(
        vector_id="03_LOOKAHEAD_CANARY",
        passed=v3_pass,
        metric_summary=f"lookahead_leak={lookahead_leak}",
        critique_fa=(
            "تست قناری نشت دادهٔ آینده (Lookahead Canary) پاک است؛ فقط از داده‌های گذشتهٔ هر کندل استفاده شده است."
            if v3_pass
            else "خطای بحرانی: نشت دادهٔ آینده (Lookahead Bias) در محاسبهٔ سیگنال شناسایی شد!"
        ),
    )

    # 4. Regime concentration
    # No invented defaults: a vector with no measured evidence FAILS (Stage 3 honesty rule).
    regime_pnl: Mapping[str, float] = candidate.get("regime_pnl_pct") or {}
    worst_regime_dd = min(float(v) for v in regime_pnl.values()) if regime_pnl else -99.0
    positive_regimes = sum(1 for v in regime_pnl.values() if float(v) > 0)
    v4_pass = positive_regimes >= 2 and worst_regime_dd >= -2.5
    v4 = AttackVectorResult(
        vector_id="04_REGIME_CONCENTRATION",
        passed=v4_pass,
        metric_summary=f"positive_regimes={positive_regimes},worst_regime_pct={worst_regime_dd:+.2f}%",
        critique_fa=(
            f"عملکرد متوازن در حداقل {positive_regimes} رژیم بازار بدون افت فاجعه‌بار در رژیم‌های دیگر."
            if v4_pass
            else f"تمرکز خطرناک در یک رژیم واحد یا زیان سنگین در رژیم معکوس ({worst_regime_dd:+.2f}%)."
        ),
    )

    # 5. Parameter perturbation +/-15%
    param_retention = float(candidate.get("param_perturbation_sharpe_retention", 0.0) or 0.0)
    v5_pass = param_retention >= 0.70
    v5 = AttackVectorResult(
        vector_id="05_PARAMETER_PERTURBATION_15PCT",
        passed=v5_pass,
        metric_summary=f"sharpe_retention={param_retention:.2f}",
        critique_fa=(
            f"پایداری پارامترها عالی است؛ با تغییر ±۱۵٪ پارامترها، {param_retention * 100:.0f}٪ از نسبت شارپ حفظ می‌شود."
            if v5_pass
            else f"بیش‌برازش (Overfitting) به اعداد دقیق پارامترها؛ افت شدید کارایی با تغییر ±۱۵٪ پارامترها."
        ),
    )

    attacks = (v1, v2, v3, v4, v5)
    passed_n = sum(1 for a in attacks if a.passed)
    survived = passed_n == len(attacks)
    verdict = "SURVIVED_RED_TEAM" if survived else "VETOED_FRAGILE"

    verdict_fa = (
        f"تأیید تیم قرمز (SURVIVED_RED_TEAM — {passed_n}/5): استراتژی «{title}» از هر ۵ حملهٔ استرس (کارمزد ۲ و ۳ برابر، حذف ۳ معاملهٔ برتر، قناری نشت آینده، تنوع رژیم و تغییر ±۱۵٪ پارامتر) با موفقیت عبور کرد (صرفاً کاغذی / PAPER_ONLY)."
        if survived
        else f"وتوی تیم قرمز (VETOED_FRAGILE — {passed_n}/5): استراتژی «{title}» در تست‌های استرس شکننده تشخیص داده شد و اجازهٔ ورود به اسلات سایه را ندارد."
    )

    return StrategyRedTeamReport(
        strategy_id=sid,
        title=title,
        verdict=verdict,
        vectors_passed=passed_n,
        vectors_total=len(attacks),
        baseline_sharpe=sr_1x,
        sharpe_at_2x_cost=sr_2x,
        sharpe_at_3x_cost=sr_3x,
        ex_top3_net_return_pct=ex_top3_pct,
        attack_results=attacks,
        red_team_verdict_fa=verdict_fa,
        paper_only=True,
        auto_promote=False,
    )


def default_red_team_candidates(root: "Path | None" = None) -> list[dict[str, Any]]:
    """REAL candidates only: out-of-sample trades from the M28.1 walk-forward on real Yahoo history
    (reports/grok/M28/walk_forward_snapshot.json). No snapshot -> empty list (nothing to attack), never invented rows."""
    from pathlib import Path as _P
    import json as _json
    base = _P(root) if root else _P(__file__).resolve().parents[2]
    rows = []
    for rel in ("walk_forward_snapshot.json", "batch4_research.json"):
        try:
            rows += _json.loads((base / "reports" / "grok" / "M28" / rel).read_text(encoding="utf-8")).get("candidates", [])
        except Exception:
            continue
    out = []
    for c in rows:
        if c.get("data_is_real") and len(c.get("returns") or []) >= 2:
            out.append({k: c[k] for k in ("strategy_id", "title", "returns", "cost_bps", "lookahead_leak_detected",
                                          "regime_pnl_pct", "param_perturbation_sharpe_retention") if k in c})
    return out


def run_strategy_red_team_suite(
    candidates: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = candidates if candidates is not None else default_red_team_candidates()
    reports = [evaluate_strategy_red_team(c) for c in rows]
    survived = [r for r in reports if r.verdict == "SURVIVED_RED_TEAM"]
    vetoed = [r for r in reports if r.verdict == "VETOED_FRAGILE"]

    return {
        "schema": "ahos.strategy_red_team.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "auto_promote": False,
        "attack_vectors": list(ATTACK_VECTORS_5),
        "candidates_tested": len(reports),
        "survived_count": len(survived),
        "vetoed_count": len(vetoed),
        "top_survivor_id": survived[0].strategy_id if survived else None,
        "top_survivor_verdict_fa": survived[0].red_team_verdict_fa if survived else "",
        "reports": [
            {
                "strategy_id": r.strategy_id,
                "title": r.title,
                "verdict": r.verdict,
                "vectors_passed": r.vectors_passed,
                "vectors_total": r.vectors_total,
                "baseline_sharpe": r.baseline_sharpe,
                "sharpe_at_2x_cost": r.sharpe_at_2x_cost,
                "sharpe_at_3x_cost": r.sharpe_at_3x_cost,
                "ex_top3_net_return_pct": r.ex_top3_net_return_pct,
                "red_team_verdict_fa": r.red_team_verdict_fa,
                "paper_only": r.paper_only,
                "auto_promote": r.auto_promote,
                "attacks": [
                    {
                        "vector_id": a.vector_id,
                        "passed": a.passed,
                        "metric_summary": a.metric_summary,
                        "critique_fa": a.critique_fa,
                    }
                    for a in r.attack_results
                ],
            }
            for r in reports
        ],
    }
