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
from ..security.gate import SecurityGate, SecurityDisposition
from ..canonical.contract import CanonicalDecision
from ..canonical.decision_store import CanonicalDecisionStore
from ..canonical.identity import canonical_token_id, canonical_chain, canonical_address
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
    # RAW highest-score candidate — NOT an authority. It may be a SECURITY_VETO or
    # PASS_WITH_UNKNOWN candidate. Never interpret this as a recommendation; use
    # `recommended_opportunity` for the security-cleared, authoritative opportunity.
    top_opportunity: OpportunityScoreReport | None = None
    # AUTHORITATIVE opportunity: the top security-cleared (PASS) candidate only.
    # None when no candidate passed the security gate. Safe for user-facing surfaces.
    recommended_opportunity: OpportunityScoreReport | None = None
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
                 score_ledger: ScoreLedger | None = None,
                 security_gate: SecurityGate | None = None,
                 decision_store: CanonicalDecisionStore | None = None):
        self.intelligence = intelligence or IntelligenceEngine()
        self.collector = collector or CollectorEngine()
        self.scorer = scorer or OpportunityScorer(intelligence=self.intelligence)
        self.alert_engine = alert_engine or AlertEngine(score_threshold=70.0)
        # P0 security authority: VETO / WATCH-cap / PASS is decided BEFORE ranking
        # and alerting. UNKNOWN security can never become a positive opportunity.
        self.security_gate = security_gate or SecurityGate()
        # Canonical decision store: when injected (production daemon), this
        # orchestrator is the SOLE writer of the cross-runtime canonical record
        # every adapter (web/Telegram/n8n) consumes. Not defaulted, so ad-hoc /
        # test constructions never write to the operator's real store.
        self.decision_store = decision_store
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

    @staticmethod
    def _canonical_decision(cand: NormalizedTokenCandidate,
                            rep: OpportunityScoreReport,
                            disposition: SecurityDisposition,
                            now: float) -> CanonicalDecision | None:
        """Build the canonical record from the ALREADY-computed disposition/score.

        Fail-closed: if a canonical identity cannot be formed, no record is
        produced (the token simply has no canonical decision → adapters treat it
        as not evaluated). No security/score is recomputed here.
        """
        cid = canonical_token_id(getattr(cand, "chain", None), getattr(cand, "address", None))
        if cid is None:
            return None
        chain = canonical_chain(getattr(cand, "chain", None)) or str(getattr(cand, "chain", "") or "")
        addr = canonical_address(getattr(cand, "chain", None), getattr(cand, "address", None)) \
            or str(getattr(cand, "address", "") or "")
        decision = CanonicalDecision(
            canonical_token_id=cid,
            chain=chain,
            normalized_contract_address=addr,
            security_disposition=disposition.verdict,
            recommendation_cap=disposition.recommendation_cap,
            # Authoritative eligibility == the security gate's PASS verdict.
            opportunity_eligible=disposition.allows_opportunity(),
            # Score is evidence only (never authority).
            opportunity_score=float(getattr(rep, "opportunity_score", 0.0) or 0.0),
            evidence_reference=str(getattr(rep, "provenance_sha256", "") or ""),
            decision_timestamp=now,
            # Non-authoritative display payload from the SAME report (no recompute).
            presentation={
                "symbol": str(getattr(rep, "token_symbol", "") or ""),
                "name": str(getattr(rep, "token_name", "") or ""),
                "chain": chain,
                "confidence_level": str(getattr(rep, "confidence_level", "") or ""),
                "risk_level": str(getattr(rep, "risk_level", "") or ""),
                "reasons_fa": list(getattr(rep, "positive_reasons", []) or [])[:5],
                "risks_fa": [getattr(r, "description", "") for r in (getattr(rep, "risk_deductions", []) or [])][:5],
                "unknowns_fa": list(getattr(rep, "missing_unknowns", []) or [])[:5],
            },
        )
        return decision if decision.validate() else None

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

        # 2. Evidence → Security Gate → Features → Risk → Score → Explanations
        #    (raw candidate data does not enter the intelligence calculations)
        #
        # SECURITY AUTHORITY PRECEDES RANKING (P0): the security disposition is
        # computed from the materialized Evidence BEFORE any ranking or alerting
        # decision. UNKNOWN security is capped at WATCH and a confirmed veto is
        # excluded from the positive-opportunity surface — a high numeric score can
        # never bypass the security gate.
        paired: list[tuple[NormalizedTokenCandidate, OpportunityScoreReport, SecurityDisposition]] = []
        for cand in candidates:
            bundle = materialize_evidence(cand, now=t0)
            bundle = OpportunityScorer.attach_virality(bundle, cand, t0)
            intel = self.intelligence.evaluate(bundle)
            disposition = self.security_gate.evaluate(intel.evidence, intel.security)
            rep = self.scorer.from_intelligence(intel)
            # Stamp the discovery provider on the report (calibration Q8
            # segmentation by provider); from_intelligence cannot see the
            # candidate, so the pipeline does it here.
            rep.source_provider = str(getattr(cand, "source_provider", "") or "")
            # Attach the security authority so every downstream consumer (alerts,
            # Telegram, ledger, web adapter) reads one canonical disposition.
            rep.security_disposition = disposition.verdict
            rep.recommendation_cap = disposition.recommendation_cap
            paired.append((cand, rep, disposition))

        ranked = sorted(paired, key=lambda item: item[1].opportunity_score, reverse=True)
        reports = [rep for _, rep, _ in ranked]
        top_opp = reports[0] if reports else None
        # The positive-opportunity surface (Telegram "special opportunity") may only
        # feature a security-cleared PASS candidate, regardless of numeric score.
        top_cleared = next(
            (rep for _, rep, disp in ranked if disp.allows_opportunity()), None)

        # 2b. Persist every prediction BEFORE any outcome is known.
        #     This is the `Prediction` node of the learning loop. Scoring after
        #     the fact from stored observations would leak hindsight, so the
        #     score is written down at the moment it is made. A ledger failure
        #     is counted and logged but never aborts a collection cycle.
        scores_persisted = 0
        if self.score_ledger is not None and reports:
            scores_persisted = self.score_ledger.record_many(
                reports, run_id=trace_ctx.run_id, now=t0)

        # 2c. Canonical decision store — the SINGLE cross-runtime authority.
        #     Python (this brain) is the sole writer; adapters read only. We reuse
        #     the disposition/score already computed above (no recomputation).
        if self.decision_store is not None and paired:
            decisions = [
                d for d in (
                    self._canonical_decision(cand, rep, disp, t0)
                    for cand, rep, disp in paired
                ) if d is not None
            ]
            if decisions:
                try:
                    self.decision_store.write_decisions(decisions, now=t0)
                except Exception:
                    # A store write failure must never abort a collection cycle;
                    # adapters fail closed on a missing/stale record.
                    pass

        # 3. Evaluate Alerts — keep candidate/report pairing (never zip after an independent sort)
        #    The security disposition is passed so a positive OPPORTUNITY alert can
        #    only fire for a security-cleared PASS candidate.
        emitted_alerts: list[Alert] = []
        for cand, rep, disposition in paired:
            alerts = self.alert_engine.evaluate_opportunity(
                rep, cand, now=t0, disposition=disposition)
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

                # If the top SECURITY-CLEARED opportunity is high quality, send summary.
                # Only a PASS candidate may surface as a positive "special opportunity";
                # UNKNOWN/vetoed tokens never reach this path even at a high score.
                if top_cleared and top_cleared.opportunity_score >= 75.0:
                    matching_cand = next((c for c in candidates if c.address == top_cleared.token_address), None)
                    card_text = format_opportunity_response(top_cleared, matching_cand)
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
            recommended_opportunity=top_cleared,
            alerts=emitted_alerts,
            trace=trace
        )
