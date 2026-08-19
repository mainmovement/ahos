#!/usr/bin/env python3
"""Canonical AHOS opportunity-pipeline orchestrator.

The unattended path is intentionally the most conservative path in AHOS:

    Provider collection -> normalized candidate -> Evidence materialization
    -> deterministic intelligence/score -> specialist vetting -> ranking
    -> alerts / paper-position review / optional Telegram notification

A score is an ordinal research signal, not permission to recommend an entry.
Exitability, deterministic council and advisor checks must run before an
OPPORTUNITY alert or proactive Telegram announcement is allowed. The module has
no live-execution surface and can only emit advice, paper-state reviews and
notifications.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ..alerts.engine import AlertEngine
from ..collector.engine import CollectorEngine
from ..decision.advisor import DecisionAdvisor
from ..intel.exitability import ExitabilityAnalyzer
from ..intel.viral import ViralityTracker
from ..intel.whales import WhaleTracker
from ..intelligence.engine import IntelligenceEngine
from ..intelligence.evidence import materialize_evidence
from ..knowledge.panel import CognitivePanel
from ..learning.calibration import CalibrationHarness
from ..learning.score_ledger import ScoreLedger
from ..observability import OperationTrace, Tracer
from ..providers.contracts import NormalizedTokenCandidate
from ..scoring.engine import OpportunityScoreReport, OpportunityScorer
from telegram_ai.adapter import TelegramBotAdapterInterface
from telegram_ai.alerts import Alert, render_fa as render_alert_fa
from telegram_ai.announced import record_announcement
from telegram_ai.response_contract import esc, format_opportunity_response


@dataclass
class PipelineExecutionReport:
    run_id: str
    started_ts: float
    duration_ms: float
    candidates_collected: int
    scores_generated: int
    alerts_emitted: int
    telegram_messages_sent: int
    scores_persisted: int = 0
    top_opportunity: OpportunityScoreReport | None = None
    alerts: list[Alert] = field(default_factory=list)
    trace: OperationTrace | None = None
    vetted_advice: Any | None = None
    suppressed_by_veto: list[str] = field(default_factory=list)
    position_reviews: list[Any] = field(default_factory=list)


class OpportunityPipelineOrchestrator:
    def __init__(
        self,
        collector: CollectorEngine | None = None,
        scorer: OpportunityScorer | None = None,
        alert_engine: AlertEngine | None = None,
        telegram_adapter: TelegramBotAdapterInterface | None = None,
        target_chat_id: int | str | None = None,
        intelligence: IntelligenceEngine | None = None,
        score_ledger: ScoreLedger | None = None,
        position_monitor: Any | None = None,
    ):
        self.intelligence = intelligence or IntelligenceEngine()
        self.collector = collector or CollectorEngine()
        self.scorer = scorer or OpportunityScorer(intelligence=self.intelligence)
        self.alert_engine = alert_engine or AlertEngine(score_threshold=70.0)

        # Specialist chain. These checks are deterministic and local. Optional
        # AI council output may be queried elsewhere but never grants entry here.
        self.exitability = ExitabilityAnalyzer()
        self.virality = ViralityTracker()
        self.whales = WhaleTracker()
        self.panel = CognitivePanel()
        self.advisor = DecisionAdvisor()

        self.telegram_adapter = telegram_adapter
        self.target_chat_id = target_chat_id
        self.position_monitor = position_monitor

        # Prediction persistence is explicitly injected. Defaulting to a live
        # ledger would let tests/ad-hoc callers contaminate calibration evidence.
        self.score_ledger = score_ledger
        self.tracer = Tracer("opportunity_pipeline", version="2.0.0")

    def run_pipeline(
        self, chain: str = "solana", limit: int = 10, now: float | None = None
    ) -> PipelineExecutionReport:
        started = time.time()
        reference_ts = started if now is None else now
        trace_ctx = self.tracer.trace_operation(
            "run_pipeline", {"chain": chain, "limit": limit}
        )

        # 1. Collect and rehydrate normalized candidate contracts.
        observations = self.collector.collect_candidates(
            chain=chain, limit=limit, now=reference_ts
        )
        candidates: list[NormalizedTokenCandidate] = []
        for record in observations:
            candidate = NormalizedTokenCandidate(
                chain=record.chain,
                address=record.token_address,
                symbol=record.symbol,
                name=record.name,
                source_provider=record.provider_source,
                retrieved_ts=record.retrieved_ts,
                raw_payload_sha256=record.raw_evidence_hash,
            )
            for key, value in record.metrics.items():
                if hasattr(candidate.metrics, key):
                    setattr(candidate.metrics, key, value)
            for key, value in record.security.items():
                if hasattr(candidate.security, key):
                    setattr(candidate.security, key, value)
            candidate.identify_unknowns()
            candidates.append(candidate)

        # 2. Evidence -> intelligence -> deterministic score. Candidate/report
        # pairs stay adjacent so sorting can never cross-wire two tokens.
        paired: list[tuple[NormalizedTokenCandidate, OpportunityScoreReport]] = []
        for candidate in candidates:
            evidence = materialize_evidence(candidate, now=reference_ts)
            intelligence = self.intelligence.evaluate(evidence)
            paired.append((candidate, self.scorer.from_intelligence(intelligence)))
        ranked = sorted(
            paired, key=lambda item: item[1].opportunity_score, reverse=True
        )
        reports = [report for _, report in ranked]
        top_opportunity = reports[0] if reports else None

        # 3. Freeze predictions before any outcome can be known. Best effort,
        # visible in the report, and never allowed to stop collection.
        scores_persisted = 0
        if self.score_ledger is not None and reports:
            scores_persisted = self.score_ledger.record_many(
                reports, run_id=trace_ctx.run_id, now=reference_ts
            )

        # 4. Vet every scored candidate. A proactive OPPORTUNITY alert is
        # allowed only when the complete deterministic chain says ENTER.
        vetted: list[
            tuple[NormalizedTokenCandidate, OpportunityScoreReport, Any | None, list[str]]
        ] = []
        emitted_alerts: list[Alert] = []
        for candidate, report in ranked:
            advice, suppression = self._vet(candidate, report, reference_ts)
            vetted.append((candidate, report, advice, suppression))
            for alert in self.alert_engine.evaluate_opportunity(
                report, candidate, now=reference_ts
            ):
                if alert.cls == "OPPORTUNITY" and (
                    advice is None
                    or getattr(advice, "action", None) != "ENTER"
                    or suppression
                ):
                    continue
                emitted_alerts.append(alert)

        top_advice = vetted[0][2] if vetted else None
        top_suppression = list(vetted[0][3]) if vetted else []

        # 5. Notify. High-priority security alerts can always pass; a special
        # opportunity announcement additionally needs vetted ENTER and no
        # analyser failure/suppression reason.
        messages_sent = 0
        if self.telegram_adapter and self.target_chat_id:
            for alert in emitted_alerts:
                if alert.severity not in ("HIGH", "CRITICAL"):
                    continue
                try:
                    self.telegram_adapter.send_message(
                        self.target_chat_id, render_alert_fa(alert)
                    )
                    messages_sent += 1
                except Exception as exc:  # notification failure is observable
                    self.tracer.trace_operation(
                        "alert_send", {"symbol": alert.symbol, "cls": alert.cls}
                    ).failure(exc, error_class="TELEGRAM_SEND")

            if vetted:
                top_candidate, top_report, vetted_advice, suppressed = vetted[0]
                if (
                    getattr(vetted_advice, "action", None) == "ENTER"
                    and not suppressed
                    and top_report.opportunity_score >= 75.0
                ):
                    try:
                        message = (
                            "🚨 <b>فرصت ویژه شناسایی شد</b>\n\n"
                            + format_opportunity_response(top_report, top_candidate)
                            + "\n\n"
                            + self._render_verdict_fa(vetted_advice, top_candidate)
                        )
                        self.telegram_adapter.send_message(self.target_chat_id, message)
                        messages_sent += 1
                        record_announcement(
                            address=top_candidate.address,
                            chain=top_candidate.chain,
                            symbol=top_candidate.symbol or "",
                            name=top_candidate.name or "",
                            score=top_report.opportunity_score,
                            now=reference_ts,
                        )
                    except Exception as exc:
                        self.tracer.trace_operation(
                            "opportunity_send", {"symbol": top_candidate.symbol}
                        ).failure(exc, error_class="TELEGRAM_SEND")

        # 6. Review existing paper positions independently of discovery.
        position_reviews = self._review_positions(reference_ts)
        for review in position_reviews:
            for alert in review.alerts:
                emitted_alerts.append(alert)
                if not (self.telegram_adapter and self.target_chat_id):
                    continue
                if alert.severity not in ("MED", "HIGH", "CRITICAL"):
                    continue
                try:
                    self.telegram_adapter.send_message(
                        self.target_chat_id, render_alert_fa(alert)
                    )
                    messages_sent += 1
                except Exception as exc:
                    self.tracer.trace_operation(
                        "position_alert_send",
                        {"symbol": alert.symbol, "cls": alert.cls},
                    ).failure(exc, error_class="TELEGRAM_SEND")

        duration_ms = (time.time() - started) * 1000.0
        trace = trace_ctx.success(
            {
                "candidates": len(candidates),
                "scores": len(reports),
                "scores_persisted": scores_persisted,
                "alerts": len(emitted_alerts),
                "messages_sent": messages_sent,
                "vetted_action": getattr(top_advice, "action", None),
                "suppressed_by_veto": len(top_suppression),
                "position_reviews": len(position_reviews),
            }
        )
        return PipelineExecutionReport(
            run_id=trace_ctx.run_id,
            started_ts=reference_ts,
            duration_ms=round(duration_ms, 2),
            candidates_collected=len(candidates),
            scores_generated=len(reports),
            alerts_emitted=len(emitted_alerts),
            telegram_messages_sent=messages_sent,
            scores_persisted=scores_persisted,
            top_opportunity=top_opportunity,
            alerts=emitted_alerts,
            trace=trace,
            vetted_advice=top_advice,
            suppressed_by_veto=top_suppression,
            position_reviews=position_reviews,
        )

    def _review_positions(self, now: float) -> list[Any]:
        """Review every open paper position; isolate failures from discovery."""
        if self.position_monitor is None:
            return []
        try:
            return self.position_monitor.review_all(now=now)
        except Exception as exc:
            self.tracer.trace_operation(
                "position_review", {"scope": "all_open"}
            ).failure(exc, error_class="POSITION_REVIEW")
            return []

    def _calibration(self):
        """Return an earned canonical calibration report, otherwise ``None``."""
        if self.score_ledger is None:
            return None
        try:
            report = CalibrationHarness(ledger_db=self.score_ledger.db_path).run()
        except Exception:
            return None
        return report if report.is_usable else None

    def _vet(
        self,
        candidate: NormalizedTokenCandidate,
        report: OpportunityScoreReport,
        now: float,
    ) -> tuple[Any | None, list[str]]:
        """Run the complete specialist chain without treating failure as PASS."""
        suppressed: list[str] = []

        def safe(label: str, operation):
            try:
                return operation()
            except Exception as exc:
                suppressed.append(f"{label}: {type(exc).__name__}")
                return None

        exitability = safe(
            "exitability",
            lambda: self.exitability.analyze(candidate, position_usd=100.0, now=now),
        )
        virality = safe("virality", lambda: self.virality.analyze(candidate, now=now))
        whale = safe(
            "whales",
            lambda: self.whales.analyze(
                candidate.symbol,
                top10_share_pct=(
                    candidate.security.top10_holder_concentration_pct
                ),
                price_change_pct=candidate.metrics.price_change_1h,
                now=now,
            ),
        )
        calibration = safe("calibration", self._calibration)
        panel = safe(
            "panel",
            lambda: self.panel.deliberate(
                candidate,
                score_report=report,
                exitability=exitability,
                virality=virality,
                whale=whale,
                calibration=calibration,
                now=now,
            ),
        )
        advice = safe(
            "advisor",
            lambda: self.advisor.advise_entry(
                candidate,
                score_report=report,
                exitability=exitability,
                virality=virality,
                whale=whale,
                panel=panel,
                now=now,
            ),
        )

        # Exitability is a mandatory gate for proactive announcements. A failed
        # probe remains UNKNOWN even if the score itself is high.
        if exitability is None and not any(s.startswith("exitability:") for s in suppressed):
            suppressed.append("exitability: UNKNOWN")
        if advice is not None and getattr(advice, "action", None) != "ENTER":
            reasons = list(getattr(advice, "hard_vetoes", None) or [])
            reasons += list(getattr(advice, "reasons", None) or [])
            suppressed.extend(reasons[:5])
        return advice, _deduplicate(suppressed)

    @staticmethod
    def _render_verdict_fa(advice, candidate=None) -> str:
        """Render a short accountable verdict rather than a raw council dump."""
        lines = ["🧠 حکم زنجیره تخصصی", ""]
        if candidate is not None:
            symbol = esc(getattr(candidate, "symbol", "") or "?")
            name = getattr(candidate, "name", None)
            chain = esc((getattr(candidate, "chain", "") or "?").upper())
            address = getattr(candidate, "address", None)
            title = f"• توکن: <b>{symbol}</b>"
            if name and str(name) != str(getattr(candidate, "symbol", "")):
                title += f" — {esc(name)}"
            lines.extend([title, f"• شبکه: {chain}"])
            if address:
                lines.extend(
                    ["• آدرس قرارداد (برای ثبت معامله):", f"<code>{esc(address)}</code>"]
                )
            lines.append("")

        action = esc(getattr(advice, "action", "?"))
        conviction = getattr(advice, "conviction", None)
        lines.append(
            f"• تصمیم: <b>{action}</b>"
            + (f" (اطمینان {esc(conviction)})" if conviction else "")
        )
        size = getattr(advice, "suggested_size_usd", None)
        if size:
            lines.append(f"• اندازه پیشنهادی: ${size:,.2f}")
        exit_verdict = getattr(advice, "exit_verdict", None)
        if exit_verdict:
            lines.append(f"• امکان خروج: {esc(exit_verdict)}")

        panel_payload = getattr(advice, "panel", None)
        if isinstance(panel_payload, dict) and panel_payload.get("verdict"):
            detail = (
                f"{len(panel_payload.get('approvals') or [])} موافق / "
                f"{len(panel_payload.get('vetoes') or [])} مخالف"
            )
            coverage = panel_payload.get("coverage")
            if isinstance(coverage, (int, float)):
                detail += f" — پوشش {coverage:.0%}"
            lines.append(
                f"• شورای تحلیلی: {esc(panel_payload['verdict'])} ({detail})"
            )

        reasons = list(getattr(advice, "reasons", None) or [])[:4]
        if reasons:
            lines.extend(["", "دلیل انتخاب:"])
            lines.extend(f"  • {esc(reason)}" for reason in reasons)
        unknowns = list(getattr(advice, "unknowns", None) or [])[:3]
        if unknowns:
            lines.extend(["", "نامعلوم‌ها: " + "، ".join(esc(x) for x in unknowns)])
        return "\n".join(lines)


def _deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))
