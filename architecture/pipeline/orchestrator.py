#!/usr/bin/env python3
"""AHOS End-to-End Opportunity Pipeline Orchestrator (Phase XX).

Connects the full scientific and intelligence flow:
  Providers
      ↓
  Normalization
      ↓
  Evidence materialization (architecture/intelligence)
      ↓
  Features → Risk → Scoring → Explanations  (Phase 4 intelligence engine)
      ↓
  Alert Engine
      ↓
  Telegram Intelligence Surface
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ..providers.contracts import NormalizedTokenCandidate
from ..providers.registry import ProviderRouter
from ..collector.engine import CollectorEngine, CollectedObservationRecord
from ..scoring.engine import OpportunityScorer, OpportunityScoreReport
from ..intelligence.engine import IntelligenceEngine
from ..intelligence.evidence import materialize_evidence
from ..learning.score_ledger import ScoreLedger
from ..alerts.engine import AlertEngine
from ..observability import Tracer, OperationTrace
from telegram_ai.adapter import TelegramBotAdapterInterface
from telegram_ai.alerts import Alert, render_fa as render_alert_fa
from telegram_ai.response_contract import format_opportunity_response


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


class OpportunityPipelineOrchestrator:
    def __init__(self,
                 collector: CollectorEngine | None = None,
                 scorer: OpportunityScorer | None = None,
                 alert_engine: AlertEngine | None = None,
                 telegram_adapter: TelegramBotAdapterInterface | None = None,
                 target_chat_id: int | str | None = None,
                 intelligence: IntelligenceEngine | None = None,
                 score_ledger: ScoreLedger | None = None):
        self.intelligence = intelligence or IntelligenceEngine()
        self.collector = collector or CollectorEngine()
        self.scorer = scorer or OpportunityScorer(intelligence=self.intelligence)
        self.alert_engine = alert_engine or AlertEngine(score_threshold=70.0)
        self.telegram_adapter = telegram_adapter
        self.target_chat_id = target_chat_id
        # Prediction persistence is EXPLICITLY INJECTED, never defaulted.
        #
        # Defaulting to a live ScoreLedger() here would mean every ad-hoc or
        # test construction of this orchestrator silently appends rows to the
        # operator's real prediction store. Those fixture rows would later be
        # joined to outcome labels and reported as calibration evidence -- a
        # measurement corrupted by its own test suite. The production daemon
        # (architecture/runtime/__main__.py) injects the real ledger; anything
        # that does not ask for persistence does not get it.
        self.score_ledger = score_ledger
        self.tracer = Tracer("opportunity_pipeline", version="1.0.0")

    def run_pipeline(self, chain: str = "solana", limit: int = 10,
                     now: float | None = None) -> PipelineExecutionReport:
        t0 = time.time() if now is None else now
        trace_ctx = self.tracer.trace_operation("run_pipeline", {"chain": chain, "limit": limit})

        # 1. Collect & Normalize Candidate Tokens
        obs_records = self.collector.collect_candidates(chain=chain, limit=limit, now=t0)

        # Convert records to candidates for scoring
        candidates: list[NormalizedTokenCandidate] = []
        for r in obs_records:
            cand = self.collector.router.get_provider("dexscreener")  # router lookup
            # Build normalized candidate from observation record
            cand_obj = NormalizedTokenCandidate(
                chain=r.chain,
                address=r.token_address,
                symbol=r.symbol,
                name=r.name,
                source_provider=r.provider_source,
                retrieved_ts=r.retrieved_ts,
                raw_payload_sha256=r.raw_evidence_hash
            )
            # Rehydrate metrics
            for k, v in r.metrics.items():
                if hasattr(cand_obj.metrics, k):
                    setattr(cand_obj.metrics, k, v)
            for k, v in r.security.items():
                if hasattr(cand_obj.security, k):
                    setattr(cand_obj.security, k, v)
            cand_obj.identify_unknowns()
            candidates.append(cand_obj)

        # 2. Evidence → Features → Risk → Score → Explanations
        #    (raw candidate data does not enter the intelligence calculations)
        paired: list[tuple[NormalizedTokenCandidate, OpportunityScoreReport]] = []
        for cand in candidates:
            bundle = materialize_evidence(cand, now=t0)
            intel = self.intelligence.evaluate(bundle)
            paired.append((cand, self.scorer.from_intelligence(intel)))

        ranked = sorted(paired, key=lambda item: item[1].opportunity_score, reverse=True)
        reports = [rep for _, rep in ranked]
        top_opp = reports[0] if reports else None

        # 2b. Persist every prediction BEFORE any outcome is known.
        #     This is the `Prediction` node of the learning loop. Scoring after
        #     the fact from stored observations would leak hindsight, so the
        #     score is written down at the moment it is made. A ledger failure
        #     is counted and logged but never aborts a collection cycle.
        scores_persisted = 0
        if self.score_ledger is not None and reports:
            scores_persisted = self.score_ledger.record_many(
                reports, run_id=trace_ctx.run_id, now=t0)

        # 3. Evaluate Alerts — keep candidate/report pairing (never zip after an independent sort)
        emitted_alerts: list[Alert] = []
        for cand, rep in paired:
            alerts = self.alert_engine.evaluate_opportunity(rep, cand, now=t0)
            emitted_alerts.extend(alerts)

        # 4. Notify Telegram Surface
        messages_sent = 0
        if self.telegram_adapter and self.target_chat_id:
            try:
                # Send high priority alerts
                for alert in emitted_alerts:
                    if alert.severity in ("HIGH", "CRITICAL"):
                        msg_text = render_alert_fa(alert)
                        self.telegram_adapter.send_message(self.target_chat_id, msg_text)
                        messages_sent += 1

                # If top opportunity is high quality, send summary
                if top_opp and top_opp.opportunity_score >= 75.0:
                    matching_cand = next((c for c in candidates if c.address == top_opp.token_address), None)
                    card_text = format_opportunity_response(top_opp, matching_cand)
                    self.telegram_adapter.send_message(self.target_chat_id, f"🚨 **فرصت ویژه شناسایی شد**\n\n" + card_text)
                    messages_sent += 1
            except Exception:
                pass

        dt = (time.time() - t0) * 1000.0
        trace = trace_ctx.success({
            "candidates": len(candidates),
            "scores": len(reports),
            "scores_persisted": scores_persisted,
            "alerts": len(emitted_alerts),
            "messages_sent": messages_sent
        })

        return PipelineExecutionReport(
            run_id=trace_ctx.run_id,
            started_ts=t0,
            duration_ms=round(dt, 2),
            candidates_collected=len(candidates),
            scores_generated=len(reports),
            alerts_emitted=len(emitted_alerts),
            telegram_messages_sent=messages_sent,
            scores_persisted=scores_persisted,
            top_opportunity=top_opp,
            alerts=emitted_alerts,
            trace=trace
        )
