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
    lane_a_registered: int = 0
    lane_a_observations_written: int = 0
    top_opportunity: OpportunityScoreReport | None = None
    alerts: list[Alert] = field(default_factory=list)
    trace: OperationTrace | None = None
    lifecycle_bridge: dict | None = None


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

        # 1b. Seed Lane-A observation lifecycle (prediction→outcome bridge).
        #     Without this, ScoreLedger rows never join outcome_label.
        #     Uses frozen discovery APIs only — no Lane-A source edits.
        lifecycle_reg = None
        try:
            from ..learning.prediction_lifecycle import register_for_observation
            lifecycle_reg = register_for_observation(obs_records, now=t0)
        except Exception as e:  # noqa: BLE001 — scoring must not abort
            lifecycle_reg = {"error": type(e).__name__, "detail": str(e)[:160]}

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
                raw_payload_sha256=r.raw_evidence_hash,
                # Paid-promotion spend, when the observation carried it
                # (boost feed); None stays None -> virality evidence reports
                # promotion status UNKNOWN, never a fabricated False.
                boost_amount=r.metrics.get("boost_amount"),
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
        #
        # Narrative prefetch (P0-3 / R-69): one RSS pull per pipeline cycle.
        # Disable with AHOS_NARRATIVE_FETCH=0. Failures degrade to UNKNOWN.
        import os
        narrative_items = None
        narrative_feeds_ok: list[str] = []
        narrative_feeds_failed: list[dict] = []
        narrative_fetch_enabled = os.environ.get("AHOS_NARRATIVE_FETCH", "1").strip() != "0"
        if narrative_fetch_enabled:
            try:
                from ..intel.news import NewsCollector
                narrative_items, narrative_feeds_ok, narrative_feeds_failed = (
                    NewsCollector().fetch_all())
            except Exception as e:  # noqa: BLE001 — never abort scoring for news
                narrative_items = []
                narrative_feeds_failed = [
                    {"feed": "*", "error": f"{type(e).__name__}: {str(e)[:120]}"}]

        paired: list[tuple[NormalizedTokenCandidate, OpportunityScoreReport]] = []
        for cand in candidates:
            bundle = materialize_evidence(cand, now=t0)
            bundle = OpportunityScorer.attach_virality(bundle, cand, t0)
            if narrative_items is not None:
                bundle = OpportunityScorer.attach_narrative(
                    bundle, cand, t0,
                    items=narrative_items,
                    feeds_ok=narrative_feeds_ok,
                    feeds_failed=narrative_feeds_failed,
                )
            else:
                bundle = OpportunityScorer.attach_narrative(
                    bundle, cand, t0, fetch=False)
            bundle = OpportunityScorer.attach_market_structure(bundle, cand, t0)
            bundle = OpportunityScorer.attach_tokenomics(bundle, cand, t0)
            bundle = OpportunityScorer.attach_catalysts(
                bundle, cand, t0,
                news_items=narrative_items if narrative_items is not None else [])
            intel = self.intelligence.evaluate(bundle)
            rep = self.scorer.from_intelligence(intel)
            # Stamp the discovery provider on the report (calibration Q8
            # segmentation by provider); from_intelligence cannot see the
            # candidate, so the pipeline does it here.
            rep.source_provider = str(getattr(cand, "source_provider", "") or "")
            paired.append((cand, rep))

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
        bridge_dict = None
        lane_a_reg = 0
        lane_a_obs = 0
        if lifecycle_reg is not None:
            if hasattr(lifecycle_reg, "as_dict"):
                bridge_dict = lifecycle_reg.as_dict()
                lane_a_reg = int(lifecycle_reg.registered)
                lane_a_obs = int(lifecycle_reg.observations_written)
            elif isinstance(lifecycle_reg, dict):
                bridge_dict = lifecycle_reg

        trace = trace_ctx.success({
            "candidates": len(candidates),
            "scores": len(reports),
            "scores_persisted": scores_persisted,
            "alerts": len(emitted_alerts),
            "messages_sent": messages_sent,
            "lane_a_registered": lane_a_reg,
            "lane_a_observations_written": lane_a_obs,
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
            lane_a_registered=lane_a_reg,
            lane_a_observations_written=lane_a_obs,
            top_opportunity=top_opp,
            alerts=emitted_alerts,
            trace=trace,
            lifecycle_bridge=bridge_dict,
        )
