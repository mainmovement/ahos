"""M31 / M35.4 nightly paper report. A short sample is not a profit claim."""
from __future__ import annotations

from typing import Any, Mapping


def render(*, day: str, trades: int, pnl_usd: float) -> str:
    verdict = "NO_PROVEN_EDGE" if trades < 30 else "SAMPLE_ONLY"
    return (
        f"# Nightly {day}\n"
        f"trades: {trades}\n"
        f"paper_pnl_usd: {pnl_usd}\n"
        f"verdict: {verdict}\n"
        "live: false\n"
    )


def render_fa(*, day: str, trades: int, pnl_usd: float) -> str:
    body = render(day=day, trades=trades, pnl_usd=pnl_usd)
    return body + "یادداشت: این عدد کاغذی است و سود ثابت‌شده نیست.\n"


def _witness_verified_count(multi_market: Mapping[str, Any]) -> int:
    if "verified_instruments" in multi_market:
        return int(multi_market["verified_instruments"])
    instruments = multi_market.get("instruments") or ()
    return sum(1 for row in instruments if row.get("witness_state") == "VERIFIED")


def build_comprehensive_nightly_digest_fa(
    *,
    day: str,
    trades: int,
    pnl_usd: float,
    gold_soak: Mapping[str, Any] | None = None,
    oil_soak: Mapping[str, Any] | None = None,
    multi_market: Mapping[str, Any] | None = None,
    tournament: Mapping[str, Any] | None = None,
    astra: Mapping[str, Any] | None = None,
    macro_overlays: Mapping[str, Any] | None = None,
    strategy_red_team: Mapping[str, Any] | None = None,
    teaching_journal: Mapping[str, Any] | None = None,
    crypto_universe: Mapping[str, Any] | None = None,
    pilot_gateway: Mapping[str, Any] | None = None,
    science_pipeline: Mapping[str, Any] | None = None,
    aci_agi_si_brain: Mapping[str, Any] | None = None,
    whole_ahos_organs: Mapping[str, Any] | None = None,
    autonomous_coder: Mapping[str, Any] | None = None,
    hundred_dollar_compounding: Mapping[str, Any] | None = None,
    self_evolution_cycle: Mapping[str, Any] | None = None,
    cross_asset_fusion: Mapping[str, Any] | None = None,
    owner_live_switch_readiness: Mapping[str, Any] | None = None,
) -> str:
    """Persian executive digest for M31/M35.4 (backward-compatible; optional snapshot inputs)."""
    base = render_fa(day=day, trades=trades, pnl_usd=pnl_usd)

    if multi_market is None:
        from architecture.markets.multi_market_desks import DESK_SPECS, evaluate_all_desks

        cycles = evaluate_all_desks()
        multi_market = {
            "desks_count": len(DESK_SPECS),
            "verified_instruments": sum(1 for c in cycles if c.witness.state == "VERIFIED"),
        }
    if tournament is None:
        from architecture.learning.strategy_tournament import run_strategy_tournament

        tournament = run_strategy_tournament()
    if astra is None:
        from pathlib import Path

        from architecture.learning.astra_engine import run_astra_evolution_cycle

        astra = run_astra_evolution_cycle(root=Path(__file__).resolve().parents[2])

    gold_status = str((gold_soak or {}).get("status") or (gold_soak or {}).get("overall_status") or "UNKNOWN")
    oil_status = str((oil_soak or {}).get("status") or (oil_soak or {}).get("overall_status") or "UNKNOWN")
    desks_n = int(multi_market.get("desks_count") or 7)
    verified_n = _witness_verified_count(multi_market)
    leader = tournament.get("leader_title") or tournament.get("leader_id") or "—"
    leader_dsr = tournament.get("leader_dsr")
    astra_status = str(astra.get("overall_status") or astra.get("shadow_status") or "UNKNOWN")

    lines = [
        "",
        "## خلاصهٔ اجرایی شبانه (M31 · M35.4)",
        f"- طلا (M13): وضعیت ساک {gold_status} — فقط کاغذی.",
        f"- نفت (M13.1): وضعیت ساک {oil_status} — فقط کاغذی.",
        f"- میزهای M19: {verified_n} نماد با شاهد VERIFIED از {desks_n} میز (قانون دو منبع).",
        f"- تورنمنت M56: پیشتاز «{leader}»" + (f" (DSR={leader_dsr})" if leader_dsr is not None else "") + ".",
        f"- آسترا M60: وضعیت سایه {astra_status} — بدون ارتقای زنده.",
        "- یادآوری: نمونهٔ کوتاه ≠ لبهٔ ثابت‌شده؛ live=false.",
    ]

    if macro_overlays:
        gold_bias = macro_overlays.get("gold_macro_bias", "UNKNOWN")
        oil_bias = macro_overlays.get("oil_macro_bias", "UNKNOWN")
        summary_fa = str(macro_overlays.get("macro_summary_fa") or "").strip()
        lines.extend(
            [
                "",
                "## قطب‌نمای کلان طلا و نفت (Macro Overlays)",
                f"- طلا: {gold_bias} | نفت WTI: {oil_bias}",
            ]
        )
        if summary_fa:
            lines.append(f"- {summary_fa}")

    if strategy_red_team:
        survived = strategy_red_team.get("survived_count", "—")
        vetoed = strategy_red_team.get("vetoed_count", "—")
        verdict_fa = str(strategy_red_team.get("top_survivor_verdict_fa") or "").strip()
        lines.extend(
            [
                "",
                "## گزارش تیم قرمز استراتژی‌ها (۲×/۳× استرس هزینه)",
                f"- نتیجه: {survived} SURVIVED / {vetoed} VETO (PAPER_ONLY، بدون auto_promote).",
            ]
        )
        if verdict_fa:
            lines.append(f"- {verdict_fa}")

    if teaching_journal:
        title_fa = str(teaching_journal.get("latest_lesson_title_fa") or "").strip()
        takeaway_fa = str(teaching_journal.get("latest_key_takeaway_fa") or "").strip()
        lessons_n = teaching_journal.get("lessons_count", "—")
        journal_n = teaching_journal.get("journal_entries_count", "—")
        lines.extend(
            [
                "",
                "## درس روز و ژورنال تصمیم هومن (M65 Teaching Mode)",
                f"- درس‌های ثبت‌شده: {lessons_n} · ورودی ژورنال: {journal_n}",
            ]
        )
        if title_fa:
            lines.append(f"- عنوان: {title_fa}")
        if takeaway_fa:
            lines.append(f"- نکتهٔ کلیدی: {takeaway_fa}")

    if pilot_gateway:
        acct = pilot_gateway.get("pilot_account") or {}
        gw = pilot_gateway.get("gateway") or {}
        fut = pilot_gateway.get("high_leverage_futures") or {}
        lines.extend(
            [
                "",
                "## پایلوت ۱۰۰ دلاری و درگاه آمادهٔ زنده (قفل HOLD · M43)",
                f"- سرمایهٔ اولیه: ${acct.get('initial_capital_usd', 100)} · ارزش فعلی: ${acct.get('current_equity_usd', '—')} · ROI: {acct.get('roi_pct', '—')}%",
                f"- وضعیت لوله‌کشی: {gw.get('plumbing_status', 'READY_LOCKED_BY_HOLD_FLAG')} · live_orders_blocked={gw.get('live_orders_blocked_until_owner_unlock', True)}",
                f"- اهرم ایزوله LONG/SHORT (حداقل {fut.get('min_leverage_enforced', 10)}×): {len(fut.get('positions') or [])} موقعیت آموزشی کاغذی.",
            ]
        )

    if crypto_universe:
        lines.extend(
            [
                "",
                "## رادار جهانی کریپتو (M33 Full Universe)",
                f"- شاخص‌شده: {crypto_universe.get('total_indexed_universe', '—')} · ELIGIBLE_GEM: {crypto_universe.get('eligible_gems_count', '—')}",
            ]
        )
        top = crypto_universe.get("top_eligible_gems") or []
        for row in top[:3]:
            if isinstance(row, dict):
                lines.append(
                    f"- {row.get('symbol', '—')}: جهش حجم {row.get('volume_surge_multiple', '—')}× · {row.get('discovery_reason_fa', '')}"
                )

    if science_pipeline:
        stages = science_pipeline.get("stages") or {}
        lines.extend(
            [
                "",
                "## خط لولهٔ علم → پژوهشکده → AHOS → دانشگاه (M57)",
                f"- منابع جهانی: {science_pipeline.get('sources_count', '—')} · میزهای آموزش‌دیده: {science_pipeline.get('desks_trained', '—')}",
                f"- مراحل: scouts={len(stages.get('scouts') or [])} · research={len(stages.get('research_institute') or [])} · applied={len(stages.get('ahos_applied') or [])}",
            ]
        )

    if autonomous_coder:
        eng = autonomous_coder.get("four_brain_engine") or {}
        lines.extend(
            [
                "",
                "## معماری ۴ مغز کدنویس، خوددیباگ‌کن و نویسنده داخلی (M60.C)",
                f"- مغز ۱ (پل :8787): {autonomous_coder.get('bridge_port_8787_status', '—')} · "
                f"مغز ۲ (OSS): {eng.get('brain_2_local_oss_tier', '—')} · "
                f"مغز ۳ (سندباکس): {eng.get('brain_3_sandbox_verifier', '—')}.",
                f"- مغز ۴ (حافظه/علم): {eng.get('brain_4_memory_science_context', '—')} بلوک زمینه.",
                f"- پچ‌های تأییدشده: {eng.get('synthesized_patches_verified', '—')} · "
                f"خلاصهٔ فارسی: {eng.get('persian_briefs_generated', '—')} · "
                f"قفل M70.6: {autonomous_coder.get('m70_6_safety_lock_status', '—')}.",
            ]
        )

    if cross_asset_fusion or owner_live_switch_readiness:
        opps = cross_asset_fusion.get("confluence_opportunities") or [] if cross_asset_fusion else []
        top = opps[0] if opps and isinstance(opps[0], dict) else {}
        gates = owner_live_switch_readiness or {}
        lines.extend(
            [
                "",
                "## ماتریس همگرایی سیگنال‌های ۷ بازار و ۶ قفل آمادگی حساب ۱۰۰ دلاری (M60.F / M60.G)",
                f"- همگرایی: {len(opps)} فرصت رتبه‌بندی‌شده · برترین {top.get('symbol', '—')} {top.get('side', '—')} "
                f"({top.get('leverage', '—')}×) — PAPER_ONLY.",
                f"- ۶ قفل: {gates.get('gates_green_count', '—')}/{gates.get('gates_total', 6)} سبز · "
                f"unlock={gates.get('owner_unlock_allowed', False)} · {gates.get('live_gateway_status', 'READY_LOCKED_BY_HOLD_FLAG')}.",
            ]
        )
        guide = str(gates.get("persian_owner_guide_fa") or "").strip()
        if guide:
            lines.append(f"- {guide}")

    if hundred_dollar_compounding or self_evolution_cycle:
        comp = hundred_dollar_compounding or {}
        ledger = comp.get("paper_compounding_ledger") or {}
        evo = self_evolution_cycle or {}
        stages = evo.get("stages") or []
        target = (stages[0].get("selected_target") if stages and isinstance(stages[0], dict) else {}) or {}
        lines.extend(
            [
                "",
                "## پله‌های رشد مرکب ۱۰۰ دلاری و چرخه خودتکاملی بسته (M60.P / M60.E)",
                f"- مرکب: ${ledger.get('initial_capital_usd', 100)} → ${ledger.get('current_equity_usd', '—')} · "
                f"قفل سود ${ledger.get('active_profit_lock_floor_usd', '—')} · پله {comp.get('active_ladder_step_id', '—')}.",
                f"- پایلوت زنده: {(comp.get('live_pilot_ledger') or {}).get('status', 'READY_LOCKED_BY_HOLD_FLAG')} · "
                f"LONG/SHORT · {(comp.get('live_pilot_ledger') or {}).get('leverage_range', '10x-25x')}.",
                f"- چرخهٔ M60.E: اندام هدف «{target.get('organ_title_fa', '—')}» · "
                f"day_1_agi_claimed={evo.get('day_1_agi_claimed', False)}.",
            ]
        )
        summary_evo = str(evo.get("persian_cycle_summary_fa") or "").strip()
        if summary_evo:
            lines.append(f"- {summary_evo}")

    if aci_agi_si_brain or whole_ahos_organs:
        brain = aci_agi_si_brain or {}
        organs = whole_ahos_organs or {}
        stage_fa = brain.get("current_stage_title_fa", "—")
        index = brain.get("compounding_capability_index", "—")
        loops = brain.get("loops") or {}
        loop_names = ("self_deciding", "self_fault_finding", "self_debugging", "self_updating")
        active_loops = sum(1 for k in loop_names if loops.get(k))
        avg_exam = organs.get("average_university_exam_score_pct", "—")
        organs_n = organs.get("organs_covered_count", "—")
        lines.extend(
            [
                "",
                "## تکامل تدریجی مغز (ACI -> AGI -> SI) و ارتقای ۸ اندام AHOS",
                f"- مرحلهٔ فعلی: {stage_fa} · شاخص توانمندی: {index}/100 (day_1_agi_claimed=false).",
                f"- حلقه‌های خودمختار فعال: {active_loops}/4 (خودتصمیم‌گیر · خودعیب‌پیداکن · خوددیباگ‌کن · خودآپدیت‌کن با قفل M70.6).",
                f"- پژوهش و دانشگاه: {organs_n}/8 اندام · میانگین آزمون: {avg_exam}% · trading_only=false.",
            ]
        )

    return base + "\n".join(lines) + "\n"
