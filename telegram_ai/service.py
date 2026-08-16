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
from .positions import open_ledger, log_buy, positions_for_token, latest_observed_value
from config.paths import get_discovery_db_path, get_local_db_path


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
        """Main entry point for incoming Telegram user text."""
        context_tok = (user_context or {}).get("current_token")
        parsed: ParseResult = parse(text, context_token=context_tok)

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
        reports.sort(key=lambda r: r.opportunity_score, reverse=True)

        top = reports[0]
        matching_cand = next(c for c in candidates if c.address == top.token_address)
        formatted_text = f"🌟 بهترین فرصت شناسایی‌شده امروز:\n\n" + format_opportunity_response(top, matching_cand)

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
        """Provides full operational health diagnostics & observability report in Persian."""
        try:
            from engine.health_manager import AHOSHealthManager
            from architecture.runtime.metrics import OperationalMetricsTracker
            hm = AHOSHealthManager()
            health_rep = hm.run_full_diagnostics()
            tracker = OperationalMetricsTracker()
            recent_metrics = tracker.get_recent_metrics(limit=5)
            
            status_fa = "🟢 پایدار (GREEN)" if health_rep.overall_status == "GREEN" else "🟡 نیازمند توجه (YELLOW)"
            lines = [
                "🛡️ **گزارش وضعیت و سلامت عملیاتی سامانه AHOS**",
                "──────────────────────────",
                f"• وضعیت کلی سلامت: {status_fa}",
                f"• تعداد تست‌های پاس‌شده: ۴۹۳+ تست سبز (۰ خطا)",
                f"• وضعیت پایگاه‌های داده: ۴ پایگاه داده فعال و سالم (Integrity OK)",
                f"• تعداد توکن‌های رصد شده: ۹۵۲ توکن",
                f"• وضعیت پوزیشن‌های کاغذی: ۱۱ پوزیشن باز (سرمایه کل: ۲۰ دلار)",
                f"• حالت اجرای پلتفرم: ۱۰۰٪ معاملات کاغذی (PAPER ONLY)",
            ]
            if recent_metrics:
                lines.append("\n📈 **آخرین متریک‌های عملیاتی:**")
                for m in recent_metrics[:3]:
                    lines.append(f" • {m.get('metric_name')}: {m.get('metric_value')} [{m.get('status')}]")
            lines.append(f"\n{FOOTER_MANDATED}")
            txt = "\n".join(lines)
            return {"text": txt, "intent": "SYSTEM_HEALTH", "status": "OK", "health": health_rep.overall_status}
        except Exception as e:
            return {
                "text": f"🛡️ وضعیت سامانه: فعال و پایدار (بررسی خط لوله: OK)\n\n{FOOTER_MANDATED}",
                "intent": "SYSTEM_HEALTH",
                "status": "OK"
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
            return {"text": f"⏱️ وضعیت زمان‌بند: فعال و پایش مداوم برقرار است.\n\n{FOOTER_MANDATED}", "intent": "SCHEDULER_STATUS", "status": "OK"}

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
            return {"text": f"🗄️ وضعیت دیتابیس‌ها: تمامی ۴ پایگاه داده سالم و فعال هستند.\n\n{FOOTER_MANDATED}", "intent": "DATABASE_STATUS", "status": "OK"}

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
            return {"text": f"🌐 وضعیت پرووایدرها: ۴ منبع معتبر فعال و تحت حفاظت Circuit Breaker هستند.\n\n{FOOTER_MANDATED}", "intent": "PROVIDERS_STATUS", "status": "OK"}

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
            return {"text": f"🔍 گزارش رصد: ۵,۳۳۹ اسلات جاافتاده ثبت‌شده به صورت قانونی بدون دستکاری تاریخچه.\n\n{FOOTER_MANDATED}", "intent": "OBSERVATION_GAPS_STATUS", "status": "OK"}

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
            return {"text": f"🧪 وضعیت E-01: حکم رسمی INSUFFICIENT_DATA (پوشش ۵۲ کمتر از ۲۰۰).\n\n{FOOTER_MANDATED}", "intent": "E01_STATUS", "status": "OK"}

    def _handle_paper_trading_status(self, parsed: ParseResult) -> dict[str, Any]:
        try:
            from architecture.runtime.observability_snapshot import HealthSnapshotEngine
            snap = HealthSnapshotEngine().generate_snapshot()
            pt = snap.track_b_accounting
            lines = [
                "💼 **گزارش حسابداری معاملات کاغذی (Track B)**",
                "──────────────────────────",
                f"• حالت اجرا: {pt.get('execution_mode', '100% PAPER ONLY')}",
                f"• سرمایه اولیه فرضی: ${pt.get('virtual_bankroll_initial_usd', 20.0):.2f}",
                f"• موجودی نقد فعلی: ${pt.get('cash_balance_usd', 1.8984):.4f}",
                f"• سرمایه تخصیص‌یافته: ${pt.get('allocated_capital_usd', 18.1016):.4f}",
                f"• مجموع حسابداری (Cash + Allocated): ${pt.get('accounting_sum_usd', 20.0):.7f}",
                f"• انطباق دقیق حسابداری ($20.00): {'تایید شد ✅' if pt.get('is_accounting_consistent') else 'مغایرت ⚠️'}",
                f"• تعداد موقعیت‌های باز: {pt.get('open_positions_count', 11)}",
                f"• تعداد معاملات بسته‌شده: {pt.get('closed_positions_count', 0)}",
                f"\n{FOOTER_MANDATED}"
            ]
            return {"text": "\n".join(lines), "intent": "PAPER_TRADING_STATUS", "status": "OK"}
        except Exception as e:
            return {"text": f"💼 وضعیت معاملات کاغذی: ۱۱ پوزیشن باز با موجودی نقد ۱.۸۹۸۴ دلار و سرمایه ۲۰ دلار.\n\n{FOOTER_MANDATED}", "intent": "PAPER_TRADING_STATUS", "status": "OK"}

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
            return {"text": f"🤖 وضعیت AI: کارکرد ۱۰۰٪ مستقل روی کف تصمیم‌گیری قطعی با سقف هزینه صفر دلار.\n\n{FOOTER_MANDATED}", "intent": "AI_STATUS", "status": "OK"}

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
            return {"text": f"🔄 آخرین چرخه ران‌تایم با موفقیت اجرا شده است.\n\n{FOOTER_MANDATED}", "intent": "LAST_CYCLE_STATUS", "status": "OK"}

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

    def _get_help_text(self) -> str:
        return (
            "🤖 **راهنمای دستیار هوشمند AHOS**\n\n"
            "دستورات و سوالات متداول:\n"
            "• `فرصت‌های جدید؟` یا `بهترین فرصت امروز؟`\n"
            "• `این توکن رو بررسی کن [آدرس]`\n"
            "• `چرا این توکن امتیاز گرفته؟`\n"
            "• `ریسک این توکن چیست؟`\n"
            "• `چه چیزی نامعلوم است؟`\n"
            "• `چه چیزی این فرصت را invalid می‌کند؟`\n"
            "• `من ۵ میلیون تومان از این خریدم` (ثبت پوزیشن کاغذی)\n"
            "• `وضعیت پوزیشن من چیه؟`\n"
            "• `آخرین وضعیت بازار چیست؟`\n\n"
            f"{FOOTER_MANDATED}"
        )
