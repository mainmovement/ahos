#!/usr/bin/env python3
"""AHOS Telegram Domain Service Controller.

Decouples Telegram edge handlers from core intelligence services:
  - Dispatches parsed natural-language intents to domain engines.
  - Queries real stored evidence (SQLite tables & memory cache).
  - Emits formatted Persian response cards.
  - Never mutates scientific validation or live funds.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from .intent import parse, ParseResult, INFO_ONLY_INTENTS, LEDGER_MUTATING_INTENTS
from .response_contract import format_opportunity_response, format_market_overview, FOOTER_MANDATED
from architecture.scoring.engine import OpportunityScorer, OpportunityScoreReport
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
from .positions import open_ledger, log_buy, log_watch, positions_for_token, latest_observed_value
from config.paths import get_discovery_db_path, get_local_db_path

# Intents that are meaningless without a specific token, and may therefore
# inherit the token currently under discussion in the conversation.
TOKEN_SCOPED_INTENTS = {
    "EXITABILITY_QUERY", "WHALE_QUERY", "VIRALITY_QUERY", "COUNCIL_OPINION",
    "PANEL_ANALYSIS", "WATCH_TOKEN", "ALERT_SET", "WHY_REJECTED",
    "SELL_ADVICE_QUERY", "TAKE_PROFIT_QUERY", "WHY_ALERTED",
}


class TelegramDomainService:
    def __init__(self, discovery_db_path: str | None = None,
                 ledger_db_path: str | None = None):
        self.discovery_db_path = discovery_db_path or get_discovery_db_path()
        self.ledger_db_path = ledger_db_path or get_local_db_path()
        self.scorer = OpportunityScorer()

    def _open_discovery(self) -> sqlite3.Connection:
        c = sqlite3.connect(f"file:{self.discovery_db_path}?mode=ro", uri=True)
        c.row_factory = sqlite3.Row
        return c

    def _open_ledger(self) -> sqlite3.Connection:
        Path(self.ledger_db_path).parent.mkdir(parents=True, exist_ok=True)
        return open_ledger(self.ledger_db_path)

    def handle_message(self, text: str, user_context: dict | None = None) -> dict[str, Any]:
        """Main entry point for incoming Telegram user text.

        Wraps the router so the footer law is enforced STRUCTURALLY. Previously
        every handler appended the footer by hand, which meant compliance was a
        convention -- one new handler forgetting it would ship a bare
        recommendation. Now no reply can leave this method without it.
        """
        result = self._route(text, user_context)
        text_out = result.get("text", "")
        if text_out and FOOTER_MANDATED not in text_out:
            result["text"] = f"{text_out}\n\n{FOOTER_MANDATED}"
            result["footer_injected"] = True
        return result

    def _route(self, text: str, user_context: dict | None = None) -> dict[str, Any]:
        context_tok = (user_context or {}).get("current_token")
        parsed: ParseResult = parse(text, context_token=context_tok)

        # Conversational continuity: token-scoped questions asked without any
        # pointing word («نهنگ‌ها چیکار می‌کنن؟») still mean "the token we are
        # discussing". Inherit the session token when the parser found none.
        # This never invents a token — it only reuses one the user already raised.
        if (context_tok and parsed.intent in TOKEN_SCOPED_INTENTS
                and not parsed.slots.get("token")):
            parsed.slots["token"] = context_tok

        if parsed.intent == "UNKNOWN":
            return {
                "text": f"متوجه منظور شما نشدم. می‌توانید از راهنما یا سوالاتی مثل «بهترین فرصت‌های امروز؟» یا «بررسی توکن [آدرس]» استفاده کنید.\n\n{FOOTER_MANDATED}",
                "intent": "UNKNOWN",
                "status": "UNRECOGNIZED"
            }

        # Route to specific handlers
        if parsed.intent in ("NEW_OPPORTUNITIES", "TOP_OPPORTUNITIES"):
            return self._handle_top_opportunities(parsed)
        elif parsed.intent in ("CHECK_TOKEN", "TOKEN_STATUS", "WHY_SCORED", "RISK_ANALYSIS", "WHAT_IS_UNKNOWN", "INVALIDATION_CONDITIONS"):
            return self._handle_token_query(parsed)
        elif parsed.intent == "BUY_LOG":
            return self._handle_buy_log(parsed)
        elif parsed.intent in ("PNL_QUERY", "POSITION_STATUS"):
            return self._handle_position_status(parsed)
        elif parsed.intent == "MARKET_OVERVIEW":
            return self._handle_market_overview(parsed)
        elif parsed.intent == "SYSTEM_HEALTH":
            return self._handle_system_health(parsed)
        elif parsed.intent == "SCHEDULER_STATUS":
            return self._handle_scheduler_status(parsed)
        elif parsed.intent == "DATABASE_STATUS":
            return self._handle_database_status(parsed)
        elif parsed.intent == "PROVIDERS_STATUS":
            return self._handle_providers_status(parsed)
        elif parsed.intent == "OBSERVATION_GAPS_STATUS":
            return self._handle_observation_gaps_status(parsed)
        elif parsed.intent == "E01_STATUS":
            return self._handle_e01_status(parsed)
        elif parsed.intent == "PAPER_TRADING_STATUS":
            return self._handle_paper_trading_status(parsed)
        elif parsed.intent == "AI_STATUS":
            return self._handle_ai_status(parsed)
        elif parsed.intent == "LAST_CYCLE_STATUS":
            return self._handle_last_cycle_status(parsed)
        elif parsed.intent == "GREETING":
            return self._handle_greeting(parsed)
        elif parsed.intent == "NEWS_DIGEST":
            return self._handle_news_digest(parsed)
        elif parsed.intent in ("WHAT_TO_BUY", "ENTRY_TIMING"):
            return self._handle_what_to_buy(parsed)
        elif parsed.intent == "EXITABILITY_QUERY":
            return self._handle_exitability(parsed)
        elif parsed.intent == "WHALE_QUERY":
            return self._handle_whales(parsed)
        elif parsed.intent == "VIRALITY_QUERY":
            return self._handle_virality(parsed)
        elif parsed.intent == "COUNCIL_OPINION":
            return self._handle_council(parsed)
        elif parsed.intent == "PANEL_ANALYSIS":
            return self._handle_panel(parsed)
        elif parsed.intent == "SELF_REVIEW":
            return self._handle_self_review(parsed)
        elif parsed.intent in ("WATCH_TOKEN", "ALERT_SET"):
            return self._handle_watch(parsed)
        elif parsed.intent == "WHY_REJECTED":
            return self._handle_why_rejected(parsed)
        elif parsed.intent in ("SELL_ADVICE_QUERY", "TAKE_PROFIT_QUERY"):
            return self._handle_sell_advice(parsed)
        elif parsed.intent == "HELP":
            return {
                "text": self._get_help_text(),
                "intent": "HELP",
                "status": "OK"
            }
        else:
            return {
                "text": f"درخواست «{parsed.intent}» دریافت شد.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "OK"
            }

    def _handle_token_query(self, parsed: ParseResult) -> dict[str, Any]:
        token_info = parsed.slots.get("token")
        if not token_info or not token_info.get("address"):
            return {
                "text": f"لطفاً آدرس توکن مورد نظر یا عبارتی مانند «این توکن» در ادامه پیام قبلی را مشخص کنید.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "NEEDS_CONTEXT"
            }

        addr = token_info["address"]
        chain = token_info.get("chain", "solana")

        # Build candidate from discovery DB or synthetic query
        cand = self._get_candidate_from_store(addr, chain)
        report = self.scorer.evaluate(cand)
        formatted_text = format_opportunity_response(report, cand)

        return {
            "text": formatted_text,
            "intent": parsed.intent,
            "report": report,
            "candidate": cand,
            "status": "OK"
        }

    def _handle_top_opportunities(self, parsed: ParseResult) -> dict[str, Any]:
        candidates = self._load_recent_active_candidates(limit=5)
        if not candidates:
            return {
                "text": f"در حال حاضر هیچ توکن جدیدی با داده‌های کافی در پایگاه داده ثبت نشده است.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "EMPTY"
            }
        reports = [self.scorer.evaluate(c) for c in candidates]
        from architecture.scoring.ranker import rank_reports
        ranked = rank_reports(reports)
        pick = next((row for row in ranked if row.disposition in ("SELECT", "INVESTIGATE")), None)
        if pick is None:
            pick = next((row for row in ranked if row.disposition != "REJECT"), None)
        if pick is None:
            return {
                "text": f"از {len(reports)} توکن بررسی‌شده هیچ‌کدام از فیلتر امنیت/خروج عبور نکرد.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "EMPTY",
            }
        top = next(r for r in reports if r.token_address == pick.token_address)
        matching_cand = next(c for c in candidates if c.address == top.token_address)
        formatted_text = (
            f"🌟 بالاترین رتبه چندعاملی ({pick.disposition}) — نه صرفاً بالاترین امتیاز:\n\n"
            + format_opportunity_response(top, matching_cand)
        )

        return {
            "text": formatted_text,
            "intent": parsed.intent,
            "top_report": top,
            "status": "OK"
        }

    def _handle_buy_log(self, parsed: ParseResult) -> dict[str, Any]:
        token_info = parsed.slots.get("token")
        amt = parsed.slots.get("amount")
        cur = parsed.slots.get("currency") or "IRT"
        if not token_info or not token_info.get("address") or not amt:
            return {
                "text": f"ثبت خرید کاغذی ناموفق بود: اطلاعات توکن یا مبلغ مشخص نیست.\n\n{FOOTER_MANDATED}",
                "intent": "BUY_LOG",
                "status": "REFUSED"
            }
        conn = self._open_ledger()
        eid = log_buy(
            conn,
            token=token_info,
            amount_value=amt,
            amount_currency=cur,
            intent_rule=parsed.rule_id,
            raw_text=parsed.normalized,
            now=time.time()
        )
        conn.close()
        if eid:
            return {
                "text": f"✅ پوزیشن خرید کاغذی با موفقیت ثبت شد.\n• شناسه: {eid}\n• مبلغ: {amt:,.0f} {cur}\n• توکن: {token_info['address']}\n\n{FOOTER_MANDATED}",
                "intent": "BUY_LOG",
                "entry_id": eid,
                "status": "RECORDED"
            }
        return {
            "text": f"ثبت پوزیشن توسط دفتر کل رد شد.\n\n{FOOTER_MANDATED}",
            "intent": "BUY_LOG",
            "status": "REFUSED"
        }

    def _handle_position_status(self, parsed: ParseResult) -> dict[str, Any]:
        token_info = parsed.slots.get("token")
        if not token_info or not token_info.get("address"):
            return {
                "text": f"برای مشاهده سود/زیان یا وضعیت پوزیشن، آدرس توکن را مشخص کنید.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "NEEDS_CONTEXT"
            }
        conn = self._open_ledger()
        positions = positions_for_token(conn, token_info.get("chain", "solana"), token_info["address"])
        conn.close()
        if not positions:
            return {
                "text": f"هیچ پوزیشن کاغذی برای توکن {token_info['address']} ثبت نشده است.\n\n{FOOTER_MANDATED}",
                "intent": parsed.intent,
                "status": "NOT_FOUND"
            }
        tot_invested = sum(p["amount_value"] for p in positions)
        return {
            "text": f"📊 وضعیت پوزیشن کاغذی:\n• کل مبلغ ثبت‌شده: {tot_invested:,.0f} {positions[0]['amount_currency']}\n• تعداد ورودی‌ها: {len(positions)}\n• وضعیت: ACTIVE (PAPER)\n\n{FOOTER_MANDATED}",
            "intent": parsed.intent,
            "status": "OK"
        }

    def _handle_market_overview(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            conn = self._open_discovery()
            cur = conn.cursor()
            tok_count = cur.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
            st = dict(cur.execute("SELECT state, COUNT(*) FROM observation_state GROUP BY state").fetchall())
            resolved = st.get("RESOLVED", 0)
            dead = st.get("DEAD", 0)
            conn.close()
        except Exception:
            tok_count, resolved, dead = 0, 0, 0

        candidates = self._load_recent_active_candidates(limit=5)
        reports = [self.scorer.evaluate(c) for c in candidates]
        reports.sort(key=lambda r: r.opportunity_score, reverse=True)

        txt = format_market_overview(tok_count, resolved, dead, reports)
        return {
            "text": txt,
            "intent": "MARKET_OVERVIEW",
            "status": "OK"
        }

    def _handle_system_health(self, parsed: ParseResult) -> dict[str, Any]:
        """Live health diagnostics. Hardcoded census numbers are forbidden."""
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            e01 = snap.e01_experiment_state or {}
            tb = snap.track_b_accounting or {}
            so = snap.self_observation or {}
            test = (so.get("test_health") or {}).get("pytest") or {}
            tokens = e01.get("total_tokens_observed")
            pytest_passed = test.get("passed")
            pytest_exit = test.get("exit_code")
            open_pos = tb.get("open_positions_count")
            bankroll = tb.get("virtual_bankroll_initial_usd")
            db_ok = sum(1 for v in (snap.database_integrity or {}).values()
                        if isinstance(v, dict) and v.get("integrity") == "OK")
            db_n = len(snap.database_integrity or {})
            verdict = snap.overall_verdict or "UNKNOWN"
            status_fa = {
                "GREEN": "🟢 پایدار (GREEN)",
                "DEGRADED": "🟡 تنزل‌یافته (DEGRADED)",
                "WARNING": "🟡 هشدار (WARNING)",
                "CRITICAL": "🔴 بحرانی (CRITICAL)",
            }.get(verdict, "⚪ نامعلوم (UNKNOWN)")
            def _n(v):
                return str(v) if v is not None else "نامعلوم"
            extra = ""
            if pytest_exit is not None:
                extra = f" (exit {pytest_exit})"
            elif pytest_passed is None:
                extra = " (artifact نیست)"
            bank = f" (بانکرول ${bankroll})" if bankroll is not None else ""
            lines = [
                "🛡️ **گزارش وضعیت و سلامت عملیاتی سامانه AHOS**",
                "──────────────────────────",
                f"• وضعیت کلی سلامت: {status_fa}",
                f"• تست‌های پاس‌شده (artifact): {_n(pytest_passed)}{extra}",
                f"• پایگاه‌های داده با integrity=OK: {db_ok} از {_n(db_n or None)}",
                f"• تعداد توکن‌های رصد شده: {_n(tokens)}",
                f"• پوزیشن‌های کاغذی باز: {_n(open_pos)}{bank}",
                "• حالت اجرا: PAPER ONLY (هیچ معامله واقعی)",
            ]
            if snap.summary_reasons:
                lines.append("• دلایل: " + "; ".join(snap.summary_reasons[:3]))
            lines.append(f"\n{FOOTER_MANDATED}")
            return {"text": "\n".join(lines), "intent": "SYSTEM_HEALTH",
                    "status": "OK", "health": verdict}
        except Exception as e:
            return {
                "text": f"🛡️ وضعیت سامانه: نامعلوم ({type(e).__name__}) — عدد جعل نمی‌شود.\n\n{FOOTER_MANDATED}",
                "intent": "SYSTEM_HEALTH",
                "status": "UNKNOWN"
            }

    def _handle_scheduler_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            sch = snap.scheduler_status
            lines = [
                "⏱️ **گزارش وضعیت زمان‌بند تولیدی (Production Scheduler)**",
                "──────────────────────────",
                f"• قفل‌های اجاره‌ای فعال: {sch.get('active_locks_count', 0)}",
                f"• شناسه آخرین اجرا: <code>{sch.get('last_run_id', 'N/A')}</code>",
                f"• وضعیت آخرین اجرا: {sch.get('last_run_status', 'N/A')}",
                f"• آخرین ضربان قلب (Heartbeat): {sch.get('last_heartbeat_utc', 'N/A')}",
                f"• عمر ضربان قلب: {sch.get('heartbeat_age_seconds', 'N/A')} ثانیه",
                f"• اسلات‌های جاافتاده ثبت‌شده: {snap.observation_metrics.get('total_gaps', 0):,} اسلات",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "SCHEDULER_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"⏱️ وضعیت زمان‌بند: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "SCHEDULER_STATUS", "status": "OK"}

    def _handle_database_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            dbs = snap.database_integrity
            lines = [
                "🗄️ **گزارش وضعیت پایگاه‌های داده SQLite**",
                "──────────────────────────"
            ]
            for name, info in dbs.items():
                integ = info.get("integrity", "UNKNOWN")
                rows = info.get("total_rows", 0)
                status_emoji = "✅" if integ == "OK" else "⚠️"
                lines.append(f"{status_emoji} **{name}**: {integ} | سطرها: {rows:,}")
            lines.append(f"\n{FOOTER_MANDATED}")
            return {"text": "\n".join(lines), "intent": "DATABASE_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🗄️ وضعیت دیتابیس: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "DATABASE_STATUS", "status": "OK"}

    def _handle_providers_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            provs = snap.provider_health
            lines = [
                "🌐 **گزارش وضعیت پرووایدرها و Circuit Breakers**",
                "──────────────────────────"
            ]
            for name, info in provs.items():
                st = info.get("state", "UNKNOWN")
                fails = info.get("failure_count", 0)
                emoji = "🟢" if st == "CLOSED" else ("🟡" if st == "HALF_OPEN" else "🔴")
                lines.append(f"{emoji} **{name}**: وضعیت {st} | شکست‌ها: {fails}")
            lines.append(f"\n{FOOTER_MANDATED}")
            return {"text": "\n".join(lines), "intent": "PROVIDERS_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🌐 وضعیت پرووایدرها: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "PROVIDERS_STATUS", "status": "OK"}

    def _handle_observation_gaps_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            e01 = snap.e01_experiment_state
            lines = [
                "🔍 **گزارش شکاف‌های رصدی و وضعیت مشاهدات**",
                "──────────────────────────",
                f"• کل توکن‌های تحت رصد: {e01.get('total_tokens_observed', 0):,}",
                f"• کل مشاهدات ثبت‌شده: {e01.get('total_observations_recorded', 0):,}",
                f"• کل اسلات‌های جاافتاده (Gap Register): {e01.get('total_gaps_registered', 0):,}",
                f"• توکن‌های تکمیل‌شده (RESOLVED): {e01.get('tokens_resolved', 0):,}",
                f"• توکن‌های غیرفعال (DEAD): {e01.get('tokens_dead', 0):,}",
                f"• پوشش افق ۷۲ ساعته: {e01.get('covered_72h_outcomes', 0)} از ۲۰۰ مورد نصاب",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "OBSERVATION_GAPS_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🔍 گزارش رصد: نامعلوم ({type(e).__name__}) — عدد تاریخی جعل نمی‌شود.\n\n{FOOTER_MANDATED}", "intent": "OBSERVATION_GAPS_STATUS", "status": "OK"}

    def _handle_e01_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            e01 = snap.e01_experiment_state
            lines = [
                "🧪 **گزارش وضعیت گیت اعتبارسنجی E-01**",
                "──────────────────────────",
                f"• حکم رسمی گیت: {e01.get('official_verdict', 'INSUFFICIENT_DATA')}",
                f"• وضعیت اعتبارسنجی: {e01.get('validation_status', 'NOT YET VALIDATED')}",
                f"• پوشش واقعی ۷۲ ساعته: {e01.get('covered_72h_outcomes', 0)} / {e01.get('required_threshold', 200)}",
                f"• اصل حاکمیتی: عدم ارتقا به Validated به دلیل صداقت علمی و آماری",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "E01_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🧪 وضعیت E-01: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "E01_STATUS", "status": "OK"}

    def _handle_paper_trading_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            pt = snap.track_b_accounting
            lines = [
                "💼 **گزارش حسابداری معاملات کاغذی (Track B)**",
                "──────────────────────────",
                f"• حالت اجرا: {pt.get('execution_mode', '100% PAPER ONLY')}",
                f"• سرمایه اولیه فرضی: {('$' + format(pt.get('virtual_bankroll_initial_usd'), '.2f')) if pt.get('virtual_bankroll_initial_usd') is not None else 'نامعلوم'}",
                f"• موجودی نقد فعلی: {('$' + format(pt.get('cash_balance_usd'), '.4f')) if pt.get('cash_balance_usd') is not None else 'نامعلوم'}",
                f"• سرمایه تخصیص‌یافته: {('$' + format(pt.get('allocated_capital_usd'), '.4f')) if pt.get('allocated_capital_usd') is not None else 'نامعلوم'}",
                f"• مجموع حسابداری (Cash + Allocated): {('$' + format(pt.get('accounting_sum_usd'), '.7f')) if pt.get('accounting_sum_usd') is not None else 'نامعلوم'}",
                f"• انطباق دقیق حسابداری ($20.00): {'تایید شد ✅' if pt.get('is_accounting_consistent') else 'مغایرت ⚠️'}",
                f"• تعداد موقعیت‌های باز: {pt.get('open_positions_count')}",
                f"• تعداد معاملات بسته‌شده: {pt.get('closed_positions_count', 0)}",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "PAPER_TRADING_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"💼 وضعیت معاملات کاغذی: نامعلوم ({type(e).__name__}) — موجودی جعل نمی‌شود.\n\n{FOOTER_MANDATED}", "intent": "PAPER_TRADING_STATUS", "status": "OK"}

    def _handle_ai_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            ai = snap.ai_router_status
            lines = [
                "🤖 **گزارش وضعیت روتر هوش مصنوعی و مدل‌ها**",
                "──────────────────────────",
                f"• کف تصمیم‌گیری قطعی ($0): {'فعال و خودکفا ✅' if ai.get('deterministic_floor_active') else 'غیرفعال'}",
                f"• سقف هزینه ماهانه: ${ai.get('cost_ceiling_usd_month', 0.0):.2f}",
                f"• تعداد ارائه‌دهندگان ثبت‌شده: {ai.get('registered_providers_count', 0)}",
                f"• قرارداد NVIDIA NIM: {'پیکربندی‌شده ✅' if ai.get('nvidia_nim_configured') else 'عدم پیکربندی'}",
                f"• کلید NVIDIA NIM: {'موجود ✅' if ai.get('nvidia_key_present') else 'عدم تزریق (کارکرد روی کف قطعی)'}",
                f"• اختیار تصمیم‌گیری AI: {ai.get('ai_decision_authority', 'ZERO (Advisory Only)')}",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "AI_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🤖 وضعیت AI: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "AI_STATUS", "status": "OK"}

    def _handle_last_cycle_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.metrics import OperationalMetricsTracker
            tracker = OperationalMetricsTracker()
            metrics = tracker.get_recent_metrics(limit=10)
            dur = next((m["metric_value"] for m in metrics if m["metric_name"] == "cycle_duration_ms"), None)
            scores = next((m["metric_value"] for m in metrics if m["metric_name"] == "scores_generated"), None)
            alerts = next((m["metric_value"] for m in metrics if m["metric_name"] == "alerts_emitted"), None)
            lines = [
                "🔄 **گزارش آخرین چرخه اجرای ران‌تایم**",
                "──────────────────────────",
                f"• مدت‌زمان چرخه: {dur:.2f} میلی‌ثانیه" if dur else "• مدت‌زمان: در دسترس نیست",
                f"• تعداد توکن‌های امتیازدهی‌شده: {scores:.0f}" if scores else "• امتیازها: در دسترس نیست",
                f"• تعداد اخطارهای صادره: {alerts:.0f}" if alerts else "• اخطارها: ۰",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "LAST_CYCLE_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"🔄 آخرین چرخه: نامعلوم ({type(e).__name__}).\n\n{FOOTER_MANDATED}", "intent": "LAST_CYCLE_STATUS", "status": "OK"}

    def _get_candidate_from_store(self, address: str, chain: str) -> NormalizedTokenCandidate:
        try:
            conn = self._open_discovery()
            r = conn.execute(
                """SELECT t.token_id, t.symbol, t.name, t.address, t.chain, p.pair_address, p.dex, p.pair_created_ts
                   FROM tokens t LEFT JOIN pairs p ON p.token_id=t.token_id
                   WHERE (t.address=? OR t.token_id=?) LIMIT 1""",
                (address, address)).fetchone()
            if r:
                # Get last observation
                obs_row = conn.execute(
                    """SELECT * FROM discovery_observations WHERE token_id=?
                       ORDER BY retrieved_ts DESC LIMIT 1""", (r["token_id"],)).fetchone()
                m = MarketMetrics()
                if obs_row:
                    m.price_usd = obs_row["price_usd"]
                    m.liquidity_usd = obs_row["liquidity_usd"]
                    m.volume_1h = obs_row["volume_1h"]
                    m.volume_24h = obs_row["volume_24h"]
                    m.txns_1h_buys = obs_row["txns_1h_buys"]
                    m.txns_1h_sells = obs_row["txns_1h_sells"]
                cand = NormalizedTokenCandidate(
                    chain=r["chain"],
                    address=r["address"],
                    symbol=r["symbol"] or "TOK",
                    name=r["name"] or "Token",
                    pair_address=r["pair_address"],
                    dex_id=r["dex"],
                    pair_created_ts=r["pair_created_ts"],
                    metrics=m,
                    source_provider="e01_discovery_db",
                    retrieved_ts=obs_row["retrieved_ts"] if obs_row else time.time()
                )
                cand.identify_unknowns()
                conn.close()
                return cand
            conn.close()
        except Exception:
            pass

        # Fallback candidate
        cand = NormalizedTokenCandidate(
            chain=chain,
            address=address,
            symbol="UNKNOWN",
            name="Unknown Token",
            source_provider="ad_hoc_query"
        )
        cand.identify_unknowns()
        return cand

    def _load_recent_active_candidates(self, limit: int = 5) -> list[NormalizedTokenCandidate]:
        candidates = []
        try:
            conn = self._open_discovery()
            rows = conn.execute(
                """SELECT t.token_id, t.symbol, t.name, t.address, t.chain, p.pair_address, p.dex, p.pair_created_ts
                   FROM tokens t
                   JOIN observation_state s ON s.token_id=t.token_id
                   LEFT JOIN pairs p ON p.token_id=t.token_id
                   ORDER BY s.last_obs_ts DESC LIMIT ?""", (limit,)).fetchall()
            for r in rows:
                obs_row = conn.execute(
                    """SELECT * FROM discovery_observations WHERE token_id=?
                       ORDER BY retrieved_ts DESC LIMIT 1""", (r["token_id"],)).fetchone()
                m = MarketMetrics()
                if obs_row:
                    m.price_usd = obs_row["price_usd"]
                    m.liquidity_usd = obs_row["liquidity_usd"]
                    m.volume_1h = obs_row["volume_1h"]
                    m.volume_24h = obs_row["volume_24h"]
                    m.txns_1h_buys = obs_row["txns_1h_buys"]
                    m.txns_1h_sells = obs_row["txns_1h_sells"]
                c = NormalizedTokenCandidate(
                    chain=r["chain"],
                    address=r["address"],
                    symbol=r["symbol"] or "TOK",
                    name=r["name"] or "Token",
                    pair_address=r["pair_address"],
                    dex_id=r["dex"],
                    pair_created_ts=r["pair_created_ts"],
                    metrics=m,
                    source_provider="e01_discovery_db",
                    retrieved_ts=obs_row["retrieved_ts"] if obs_row else time.time()
                )
                c.identify_unknowns()
                candidates.append(c)
            conn.close()
        except Exception:
            pass
        return candidates

    # ==================================================================
    # Conversational advisory handlers (Wave-25)
    # Every one of these is INFORMATIONAL: it explains measured evidence and
    # the options it implies. None of them can place an order — no order path
    # exists in this system. All end with the mandated footer.
    # ==================================================================

    def _handle_greeting(self, parsed: ParseResult) -> dict[str, Any]:
        return {
            "text": (
                "سلام! 👋 من دستیار تحلیل فرصت‌های کریپتو هستم.\n\n"
                "می‌توانید راحت با من حرف بزنید، مثلاً:\n"
                "• «امروز چه خبر از بازار کریپتو؟»\n"
                "• «بهترین فرصت‌های امروز چیه؟»\n"
                "• «این توکن رو بررسی کن [آدرس]»\n"
                "• «۵ میلیون تومان خریدم» (ثبت در دفتر کاغذی)\n"
                "• «کی بفروشم؟»\n\n"
                "یادآوری مهم: من ابزار تحلیل و پشتیبانی تصمیم هستم، نه ربات معامله‌گر. "
                "هیچ خرید و فروش واقعی انجام نمی‌دهم.\n\n"
                f"{FOOTER_MANDATED}"
            ),
            "intent": "GREETING",
            "status": "OK",
        }

    def _handle_news_digest(self, parsed: ParseResult) -> dict[str, Any]:
        """Crypto news digest. Honest about unreachable feeds (filtering/sanctions)."""
        from architecture.intel.news import NewsCollector

        token_info = parsed.slots.get("token") or {}
        keywords = None
        subject = "MARKET"
        if token_info.get("address"):
            cand = self._get_candidate_from_store(
                token_info["address"], token_info.get("chain", "solana"))
            subject = cand.symbol
            keywords = [cand.symbol, cand.name]

        signal = NewsCollector().analyze(subject=subject, keywords=keywords)

        lines = [f"📰 خلاصه اخبار — {'بازار کلی' if subject == 'MARKET' else subject}", ""]
        if not signal.is_known:
            reason = (signal.error_state or {}).get("kind", "unknown")
            if reason == "all_feeds_unreachable":
                lines += [
                    "⚠️ هیچ‌کدام از منابع خبری در دسترس نبودند.",
                    "این معمولاً یعنی فیلترینگ یا قطعی شبکه — نه اینکه خبری نیست.",
                    "",
                    "راهکار: یک تونل/پروکسی محلی روشن کنید و متغیر زیر را تنظیم کنید:",
                    "`ALL_PROXY=socks5://127.0.0.1:10808`",
                ]
            else:
                lines.append("در بازه اخیر خبری مرتبط با این موضوع پیدا نشد.")
            if signal.feeds_failed:
                lines += ["", "منابع ناموفق:"]
                lines += [f" • {f['feed']}" for f in signal.feeds_failed[:5]]
        else:
            mood = {"BULLISH": "مثبت 🟢", "BEARISH": "منفی 🔴", "NEUTRAL": "خنثی ⚪"}
            lines += [
                f"فضای کلی: {mood.get(signal.label, signal.label)} "
                f"(امتیاز {signal.sentiment:+.2f})",
                f"تعداد تیترهای بررسی‌شده: {signal.mention_count}",
            ]
            if signal.high_impact_count:
                lines.append(f"تیترهای پرتأثیر: {signal.high_impact_count}")
            if signal.evidence:
                lines += ["", "مهم‌ترین تیترها:"]
                for ev in signal.evidence[:5]:
                    arrow = "🟢" if ev["score"] > 0 else ("🔴" if ev["score"] < 0 else "⚪")
                    lines.append(f" {arrow} {ev['title']}  [{ev['source']}]")
            lines += ["", "⚠️ خبر «شاهد» است، نه «دلیل». تصمیم بر پایه داده‌های اندازه‌گیری‌شده گرفته می‌شود."]

        lines += ["", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "NEWS_DIGEST",
                "status": "OK" if signal.is_known else "UNKNOWN", "signal": signal}

    def _handle_what_to_buy(self, parsed: ParseResult) -> dict[str, Any]:
        """Ranked, fully-justified advice across currently observed candidates."""
        from architecture.decision.advisor import DecisionAdvisor
        from architecture.intel.exitability import ExitabilityAnalyzer
        from architecture.intel.viral import ViralityTracker

        candidates = self._load_recent_active_candidates(limit=12)
        if not candidates:
            return {
                "text": (
                    "هنوز هیچ توکنی با داده کافی در پایگاه داده ثبت نشده است.\n\n"
                    "برای شروع جمع‌آوری داده، یک چرخه اجرا کنید:\n"
                    "`python -m architecture.runtime --single-cycle`\n\n"
                    f"{FOOTER_MANDATED}"
                ),
                "intent": parsed.intent, "status": "EMPTY",
            }

        advisor = DecisionAdvisor()
        exiter = ExitabilityAnalyzer()
        viral = ViralityTracker()

        scored = []
        for c in candidates:
            report = self.scorer.evaluate(c)
            advice = advisor.advise_entry(
                c, report,
                exitability=exiter.analyze(c, position_usd=100.0),
                virality=viral.analyze(c),
            )
            scored.append(advice)

        actionable = [a for a in scored if a.action == "ENTER"]
        actionable.sort(key=lambda a: a.deterministic_score or 0, reverse=True)

        lines = ["🎯 تحلیل فرصت‌های فعلی", ""]
        if not actionable:
            avoided = sum(1 for a in scored if a.action == "AVOID")
            lines += [
                f"از {len(scored)} توکن بررسی‌شده، هیچ‌کدام شرایط ورود را ندارند.",
                f"({avoided} مورد رد شد، {len(scored) - avoided} مورد در حالت انتظار)",
                "",
                "«فرصت مناسبی نیست» هم یک پاسخ معتبر است — نه یک خطا.",
            ]
            worst = [a for a in scored if a.hard_vetoes][:3]
            if worst:
                lines += ["", "نمونه دلایل رد:"]
                for a in worst:
                    lines.append(f" • {a.symbol}: {a.hard_vetoes[0]}")
        else:
            lines.append(f"از {len(scored)} توکن بررسی‌شده، {len(actionable)} مورد شرایط ورود دارند:")
            lines.append("")
            for a in actionable[:3]:
                lines += self._render_advice_block(a)
                lines.append("")
        lines += [FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": parsed.intent,
                "status": "OK", "advice": actionable}

    def _render_advice_block(self, a: Any) -> list[str]:
        """Renders one Advice with its full WHY — reasons, risks, unknowns, exit plan."""
        out = [f"▸ **{a.symbol}** — امتیاز {(a.deterministic_score or 0):.0f}/100 "
               f"(اطمینان: {a.conviction})"]
        if a.suggested_size_usd:
            out.append(f"   حجم پیشنهادی: ${a.suggested_size_usd:,.2f}")
        if a.take_profit_price and a.stop_loss_price:
            out.append(f"   برنامه خروج: هدف سود ${a.take_profit_price:.8g} / "
                       f"حد ضرر ${a.stop_loss_price:.8g} / حداکثر {a.max_hold_hours:.0f} ساعت")
        for r in a.reasons[:3]:
            out.append(f"   ✅ {r}")
        for r in a.risks[:3]:
            out.append(f"   ⚠️ {r}")
        for u in a.unknowns[:2]:
            out.append(f"   ❓ {u}")
        if a.council and getattr(a.council, "council_status", "") not in ("", "OFFLINE"):
            out.append(f"   🧠 شورای هوش مصنوعی: {a.council.final_stance} "
                       f"({a.council.agreement})")
        return out

    def _require_token(self, parsed: ParseResult):
        """Returns (candidate, None) or (None, error_response) for token-scoped queries."""
        token_info = parsed.slots.get("token")
        if not token_info or not token_info.get("address"):
            return None, {
                "text": ("لطفاً آدرس توکن را مشخص کنید یا ابتدا یک توکن را "
                         f"بررسی کنید تا «این» به آن اشاره کند.\n\n{FOOTER_MANDATED}"),
                "intent": parsed.intent, "status": "NEEDS_CONTEXT",
            }
        return self._get_candidate_from_store(
            token_info["address"], token_info.get("chain", "solana")), None

    def _handle_exitability(self, parsed: ParseResult) -> dict[str, Any]:
        """THE question that matters: can the money actually come back out?"""
        from architecture.intel.exitability import ExitabilityAnalyzer

        cand, err = self._require_token(parsed)
        if err:
            return err

        amount = parsed.slots.get("amount_usd") or 100.0
        rep = ExitabilityAnalyzer().analyze(cand, position_usd=float(amount))

        icon = {"EXITABLE": "🟢", "DEGRADED": "🟡",
                "TRAPPED": "🔴", "UNKNOWN": "⚪"}.get(rep.verdict, "⚪")
        lines = [
            f"{icon} بررسی امکان خروج — {cand.symbol}",
            "",
            f"حکم: **{rep.verdict}** (کسر قابل‌بازیافت: {rep.realizable_fraction:.1%})"
            if rep.realizable_fraction is not None else f"حکم: **{rep.verdict}**",
            f"مبلغ بررسی‌شده: ${float(amount):,.2f}",
        ]
        if rep.realizable_usd is not None:
            lines.append(f"ارزش نمایشی: ${rep.displayed_usd:,.2f}  →  "
                         f"واقعاً قابل برداشت: ${rep.realizable_usd:,.2f}")
        if rep.slippage_bps is not None:
            lines.append(f"لغزش خروج: {rep.slippage_bps:.0f} bps | "
                         f"کارمزد: ${(rep.fee_usd or 0):,.2f} | "
                         f"مالیات فروش: ${(rep.tax_usd or 0):,.2f}")
        if rep.max_safe_position_usd is not None:
            lines.append(f"حداکثر حجم امن: ${rep.max_safe_position_usd:,.2f}")
        if rep.hard_vetoes:
            lines += ["", "🚫 وتوی قطعی:"]
            lines += [f" • {v}" for v in rep.hard_vetoes]
        if rep.warnings:
            lines += ["", "⚠️ هشدارها:"]
            lines += [f" • {w}" for w in rep.warnings]
        if rep.unknowns:
            lines += ["", "❓ نامعلوم‌ها:"]
            lines += [f" • {u}" for u in rep.unknowns]
        lines += ["", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "EXITABILITY_QUERY",
                "status": "OK", "exitability": rep}

    def _handle_whales(self, parsed: ParseResult) -> dict[str, Any]:
        from architecture.intel.whales import WhaleTracker

        cand, err = self._require_token(parsed)
        if err:
            return err

        sec = cand.security
        rep = WhaleTracker().analyze(
            symbol=cand.symbol,
            top10_share_pct=getattr(sec, "top10_holder_concentration_pct", None),
            top1_share_pct=None,
            holder_count=None,
            price_change_pct=getattr(cand.metrics, "price_change_1h", None),
        )
        # Distribution forensics (Gini / coordination) from the holder store.
        forensic = None
        try:
            from architecture.intel.forensics import ForensicsAnalyzer
            conn = self._open_discovery()
            row = conn.execute(
                "SELECT token_id FROM tokens WHERE address=? LIMIT 1",
                (cand.address,)).fetchone()
            if row:
                forensic = ForensicsAnalyzer().analyze_from_store(
                    conn, row[0], symbol=cand.symbol)
            conn.close()
        except Exception:
            forensic = None

        lines = [f"🐋 توزیع مالکیت — {cand.symbol}", "",
                 f"وضعیت: **{rep.label}**"]
        if rep.top10_share_pct is not None:
            lines.append(f"سهم ۱۰ کیف‌پول برتر: {rep.top10_share_pct:.1f}%")
        if rep.holder_count is not None:
            lines.append(f"تعداد دارندگان: {rep.holder_count:,}")
        if rep.delta_pct_points:
            lines.append(f"تغییر تمرکز: {rep.delta_pct_points:+.1f} واحد درصد")
        if rep.risk_penalty:
            lines.append(f"جریمه ریسک: −{rep.risk_penalty:.0f}")
        for r in rep.reasons[:3]:
            lines.append(f" • {r}")
        for w in rep.warnings:
            lines.append(f" ⚠️ {w}")
        for u in rep.unknowns:
            lines.append(f" ❓ {u}")
        if forensic is not None and forensic.is_known:
            lines += ["", f"🔬 تحلیل توزیع: **{forensic.label}**"]
            if forensic.gini is not None:
                lines.append(f"ضریب جینی: {forensic.gini:.2f} ({forensic.gini_label})")
            for w in forensic.warnings[:3]:
                lines.append(f" ⚠️ {w}")

        if rep.label == "UNKNOWN" and (forensic is None or not forensic.is_known):
            lines += ["", "توضیح صادقانه: نقاط پایانی رایگان RPC فهرست دارندگان را "
                          "ارائه نمی‌دهند. نبود داده را «امن» تفسیر نمی‌کنیم."]
        lines += ["", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "WHALE_QUERY",
                "status": "OK", "whales": rep, "forensics": forensic}

    def _handle_virality(self, parsed: ParseResult) -> dict[str, Any]:
        from architecture.intel.viral import ViralityTracker

        cand, err = self._require_token(parsed)
        if err:
            return err

        rep = ViralityTracker().analyze(cand)
        icon = {"VIRAL": "🔥", "BUILDING": "📈", "COOLING": "📉",
                "FLAT": "➖", "UNKNOWN": "⚪"}.get(rep.label, "⚪")
        lines = [f"{icon} سنجش توجه بازار — {cand.symbol}", "",
                 f"وضعیت: **{rep.label}** (امتیاز: {rep.score:.0f}/100)"]
        if rep.txn_acceleration is not None:
            lines.append(f"شتاب تراکنش (۵د نسبت به میانگین ساعتی): {rep.txn_acceleration:.2f}×")
        if rep.volume_acceleration is not None:
            lines.append(f"شتاب حجم: {rep.volume_acceleration:.2f}×")
        if rep.buy_pressure is not None:
            lines.append(f"فشار خرید: {rep.buy_pressure:.2f}")
        if rep.is_paid_promotion:
            lines.append("💰 نشانه تبلیغ پولی (paid boost) شناسایی شد.")
        if rep.wash_suspected:
            lines += ["", "🚨 الگوی مشکوک به معامله صوری (wash trading) شناسایی شد — "
                          "حجم بالا بدون تغییر معنادار قیمت."]
        for w in rep.warnings:
            lines.append(f" ⚠️ {w}")
        for u in rep.unknowns:
            lines.append(f" ❓ {u}")
        lines += ["", "توضیح: «وایرال بودن» را از ردپای واقعی روی زنجیره می‌سنجیم، "
                      "نه از شبکه‌های اجتماعی.", "", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "VIRALITY_QUERY",
                "status": "OK", "virality": rep}

    def _handle_council(self, parsed: ParseResult) -> dict[str, Any]:
        """Live multi-AI deliberation. Advisory only — can never overrule the math."""
        from architecture.ai.council_live import LiveCouncil, build_evidence_packet
        from architecture.intel.exitability import ExitabilityAnalyzer

        cand, err = self._require_token(parsed)
        if err:
            return err

        report = self.scorer.evaluate(cand)
        exitability = ExitabilityAnalyzer().analyze(cand, position_usd=100.0)
        packet = build_evidence_packet(score_report=report, exitability=exitability)

        verdict = LiveCouncil().deliberate(
            packet, question="آیا ورود به این توکن منطقی است؟", allow_paid=False)

        lines = [f"🧠 شورای هوش مصنوعی — {cand.symbol}", "",
                 f"جمع‌بندی: **{verdict.final_stance}** (توافق: {verdict.agreement})",
                 f"وضعیت شورا: {verdict.council_status}"]
        if verdict.providers_ok:
            lines.append(f"پاسخ‌دهندگان ({verdict.responded}): "
                         f"{', '.join(verdict.providers_ok)}")
        if verdict.providers_failed:
            names = [f.get("provider", "?") for f in verdict.providers_failed]
            lines.append(f"در دسترس نبودند: {', '.join(names)}")
        if verdict.council_status in ("OFFLINE", "DETERMINISTIC_ONLY"):
            lines += ["", "هیچ مدل هوش مصنوعی در دسترس نبود — احتمالاً فیلترینگ یا "
                          "نبود کلید API. سامانه روی موتور قطعی (ریاضی) کار می‌کند "
                          "و همچنان معتبر است."]
        if verdict.reasons:
            lines += ["", "دلایل مطرح‌شده:"]
            lines += [f" • {r}" for r in verdict.reasons[:6]]
        for w in verdict.warnings:
            lines.append(f" ⚠️ {w}")
        if verdict.echo_suspected:
            lines += ["", "⚠️ اتفاق‌نظر کامل روی شواهد ضعیف — احتمال هم‌صدایی "
                          "(echo) مدل‌ها. به این اجماع وزن کمتری بدهید."]
        lines += ["", "⚠️ نظر مدل‌ها فقط مشورتی است و هرگز نمی‌تواند وتوهای "
                      "قطعی موتور ریاضی را لغو کند.", "", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "COUNCIL_OPINION",
                "status": "OK", "council": verdict}

    def _handle_panel(self, parsed: ParseResult) -> dict[str, Any]:
        """The 100-mind panel, run as deterministic checks over real evidence."""
        from architecture.knowledge.panel import CognitivePanel
        from architecture.intel.exitability import ExitabilityAnalyzer
        from architecture.intel.viral import ViralityTracker

        cand, err = self._require_token(parsed)
        if err:
            return err

        report = self.scorer.evaluate(cand)
        verdict = CognitivePanel().deliberate(
            cand, score_report=report,
            exitability=ExitabilityAnalyzer().analyze(cand),
            virality=ViralityTracker().analyze(cand),
        )
        return {"text": f"{verdict.summary_persian()}\n\n{FOOTER_MANDATED}",
                "intent": "PANEL_ANALYSIS", "status": "OK", "panel": verdict}

    def _handle_self_review(self, parsed: ParseResult) -> dict[str, Any]:
        """The learning loop, on demand: how good were our past calls, really?"""
        from architecture.evolution.hindsight import HindsightEngine
        try:
            conn = self._open_discovery()
            engine = HindsightEngine(conn)
            results = engine.review_recent_picks(limit=20)
            text = engine.report_persian(results)
            agg = engine.aggregate(results)
            conn.close()
        except Exception as e:
            return {
                "text": (f"بازبینی گذشته ممکن نشد: {type(e).__name__}\n\n"
                         f"{FOOTER_MANDATED}"),
                "intent": "SELF_REVIEW", "status": "ERROR",
            }
        return {"text": f"{text}\n\n{FOOTER_MANDATED}",
                "intent": "SELF_REVIEW", "status": "OK", "aggregate": agg}


    def _handle_watch(self, parsed: ParseResult) -> dict[str, Any]:
        """Paper watchlist / alert-condition log. Never fires a live trade."""
        cand, err = self._require_token(parsed)
        if err:
            return err
        cond = parsed.slots.get("condition") or (
            "CONDITIONS_DETERIORATE" if parsed.intent == "ALERT_SET" else "WATCH"
        )
        conn = self._open_ledger()
        wid = log_watch(conn, token={"address": cand.address, "chain": cand.chain},
                        condition=cond, raw_text=parsed.normalized, now=time.time())
        conn.close()
        if not wid:
            return {"text": f"ثبت دیده‌بانی رد شد (توکن نامشخص).\n\n{FOOTER_MANDATED}",
                    "intent": parsed.intent, "status": "REFUSED"}
        kind = "هشدار کاغذی" if parsed.intent == "ALERT_SET" else "دیده‌بانی کاغذی"
        return {
            "text": (f"✅ {kind} ثبت شد.\n• شناسه: {wid}\n"
                     f"• توکن: {cand.symbol} ({cand.address})\n"
                     f"• شرط: {cond}\n"
                     "این فقط دفتر محلی است — هیچ معامله‌ای اجرا نمی‌شود.\n\n"
                     f"{FOOTER_MANDATED}"),
            "intent": parsed.intent, "watch_id": wid, "status": "RECORDED",
        }

    def _handle_why_rejected(self, parsed: ParseResult) -> dict[str, Any]:
        from architecture.scoring.ranker import classify
        cand, err = self._require_token(parsed)
        if err:
            return err
        report = self.scorer.evaluate(cand)
        row = classify(report)
        lines = [f"🚫 چرا انتخاب نشد — {cand.symbol}", "",
                 f"حکم رتبه: **{row.disposition}** (امتیاز {row.opportunity_score})"]
        for r in (row.why_not_selected or row.reasons)[:6]:
            lines.append(f" • {r}")
        for r in row.risk_factors[:4]:
            lines.append(f" ⚠️ {r}")
        for u in row.unknown_factors[:4]:
            lines.append(f" ❓ {u}")
        if not row.why_not_selected and row.disposition in ("SELECT", "INVESTIGATE"):
            lines.append("این توکن رد نشده — برای رد شدن، وتوی امنیت/خروج لازم است.")
        lines += ["", FOOTER_MANDATED]
        return {"text": "\n".join(lines), "intent": "WHY_REJECTED",
                "status": "OK", "ranking": row.as_dict()}

    def _handle_sell_advice(self, parsed: ParseResult) -> dict[str, Any]:
        """INFO-ONLY. Uses paper ledger + observed price. UNKNOWN price → no advice."""
        cand, err = self._require_token(parsed)
        if err:
            return err
        conn = self._open_ledger()
        positions = positions_for_token(conn, cand.chain, cand.address)
        conn.close()
        if not positions:
            return {
                "text": (f"پوزیشن کاغذی برای {cand.symbol} ثبت نشده. "
                         "ابتدا «خریدم» را ثبت کنید؛ بدون ورود، خروج معنی ندارد."
                         f"\n\n{FOOTER_MANDATED}"),
                "intent": parsed.intent, "status": "NOT_FOUND",
            }
        price = cand.metrics.price_usd
        if price is None:
            return {
                "text": (f"قیمت فعلی {cand.symbol} نامعلوم است — "
                         "بدون قیمت، توصیه خروج جعل نمی‌شود."
                         f"\n\n{FOOTER_MANDATED}"),
                "intent": parsed.intent, "status": "UNKNOWN",
            }
        return {
            "text": (f"پوزیشن کاغذی وجود دارد ({len(positions)} ورود) و قیمت مشاهده‌شده "
                     f"${price} است، اما قیمت ورود در دفتر تلگرام ذخیره نشده. "
                     "توصیه حدسود/حدضرر بدون entry price ساخته نمی‌شود."
                     f"\n\n{FOOTER_MANDATED}"),
            "intent": parsed.intent, "status": "INSUFFICIENT_EVIDENCE",
        }

    def _get_help_text(self) -> str:
        return (
            "🤖 **راهنمای دستیار هوشمند AHOS**\n\n"
            "می‌توانید طبیعی حرف بزنید. نمونه‌ها:\n\n"
            "📰 اخبار و بازار\n"
            "• `امروز چه خبر؟` / `اخبار کریپتو`\n"
            "• `آخرین وضعیت بازار چیست؟`\n\n"
            "🎯 فرصت‌ها\n"
            "• `فرصت‌های جدید؟` / `بهترین فرصت امروز؟`\n"
            "• `چی بخرم؟` / `کی وارد بشم؟`\n"
            "• `این توکن رو بررسی کن [آدرس]`\n\n"
            "🔍 تحلیل عمیق\n"
            "• `چرا این توکن امتیاز گرفته؟`\n"
            "• `ریسک این توکن چیست؟`\n"
            "• `میتونم بفروشمش؟` (بررسی نقدشوندگی خروج)\n"
            "• `نهنگ‌ها چیکار می‌کنن؟`\n"
            "• `این وایرال شده؟`\n"
            "• `نظر هوش مصنوعی‌ها چیه؟`\n"
            "• `شورای تحلیلی چی میگه؟` (۱۰ دیدگاه تخصصی)\n"
            "• `چه چیزی نامعلوم است؟`\n"
            "• `چه چیزی این فرصت را invalid می‌کند؟`\n\n"
            "💼 پوزیشن‌های من\n"
            "• `۵ میلیون تومان خریدم` (ثبت پوزیشن کاغذی)\n"
            "• `چند درصد سود دارم؟`\n"
            "• `کی بفروشم؟` / `وضعیت پوزیشن من چیه؟`\n\n"
            "⚙️ سیستم و یادگیری\n"
            "• `وضعیت سیستم چطوره؟`\n"
            "• `اشتباهاتت رو مرور کن` (بازبینی انتخاب‌های گذشته)\n\n"
            "⚠️ این سامانه ابزار تحلیل است، نه ربات معامله‌گر. "
            "هیچ خرید و فروش واقعی انجام نمی‌شود.\n\n"
            f"{FOOTER_MANDATED}"
        )
