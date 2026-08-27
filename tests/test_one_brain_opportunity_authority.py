#!/usr/bin/env python3
"""Sub-PR 2 — Canonical One-Brain opportunity authority.

Proves that every production-reachable positive-opportunity emitter consumes the
SINGLE canonical eligibility authority and that UNKNOWN / vetoed security can
never be promoted into a positive opportunity through any adapter:

  * TypeScript web/Telegram adapter (`alerts.ts`) consumes `opportunity_authority.ts`
    and no longer contains the removed score-based UNKNOWN promotion.
  * The dormant Python emitter `telegram_ai/pump_alert.py` is removed.
  * `PipelineExecutionReport.recommended_opportunity` (authoritative) never exposes
    a non-cleared candidate; `top_opportunity` remains raw/non-authoritative.

Source-scanning mirrors the repository's existing governance-test idiom
(`tests/test_zero_money_invariant.py`). No tests are weakened; nothing is xfail'd.
"""
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.collector.engine import CollectorEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals, ProviderResponse,
)
from architecture.providers.registry import ProviderRouter
from telegram_ai.adapter import MockTelegramAdapter


# ------------------------------------------------------------- helpers ------
class _MockDiscoveryProvider:
    def __init__(self, name, candidates):
        self.provider_id = name
        self.capabilities = ["discovery"]
        self.candidates = candidates

    def fetch_candidate_tokens(self, chain, limit=10):
        return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

    def fetch_token_metrics(self, chain, address):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def _strong_metrics():
    return MarketMetrics(price_usd=0.10, liquidity_usd=90000.0, volume_1h=45000.0,
                         txns_1h_buys=95, txns_1h_sells=15)


def _run(cand, tmp_path, db_name):
    router = ProviderRouter()
    router.providers["dexscreener"] = _MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = _MockDiscoveryProvider("geckoterminal", [])
    collector = CollectorEngine(db_path=str(tmp_path / db_name), router=router)
    orch = OpportunityPipelineOrchestrator(
        collector=collector, scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
        telegram_adapter=MockTelegramAdapter(), target_chat_id=1,
    )
    return orch.run_pipeline(chain="solana", limit=5)


# ============================================================ TS adapter ====
def test_ts_alerts_consume_canonical_authority_and_have_no_unknown_promotion():
    alerts_ts = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    # Phase 4: alerts.ts now consumes the Python CANONICAL decision store as the
    # sole authority (stricter than the Sub-PR2 in-runtime eligibility mapping).
    assert "canonical_store" in alerts_ts
    assert "isCanonicalPositiveOpportunity" in alerts_ts
    assert "canonical_identity" in alerts_ts
    # The removed P0 bypass (score-based UNKNOWN promotion) must stay gone.
    assert 'rankScore >= 0.8' not in alerts_ts
    assert 's === "UNKNOWN"' not in alerts_ts
    # No independent local security-eligibility function remains.
    assert "function securityOk" not in alerts_ts


def test_canonical_authority_module_is_pass_only():
    mod = (ROOT / "opportunity_authority.ts").read_text(encoding="utf-8")
    # UNKNOWN maps to PASS_WITH_UNKNOWN (never a positive opportunity).
    assert "PASS_WITH_UNKNOWN" in mod
    assert "SECURITY_VETO" in mod
    # The single eligibility rule is PASS-only (mirrors Python allows_opportunity()).
    assert re.search(r"isPositiveOpportunityEligible[\s\S]{0,120}===\s*PASS", mod)


def test_ts_telegram_opportunity_only_reachable_through_gated_path():
    alerts_ts = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    # The only Telegram send site is pushTelegram, and it is invoked solely inside
    # processOpportunityAlerts, after the canonical shouldAlertOpportunity gate.
    assert alerts_ts.count("api.telegram.org") == 1
    assert alerts_ts.count("pushTelegram(") == 2  # definition + single call site
    proc = alerts_ts[alerts_ts.index("export async function processOpportunityAlerts"):]
    # Phase 4: the gate call now carries the canonical snapshot.
    assert "shouldAlertOpportunity(opp, state, snapshot" in proc
    guard = proc.index("if (!shouldAlertOpportunity")
    push = proc.index("pushTelegram(")
    assert guard < push, "Telegram push must occur only after the canonical eligibility gate"


# ==================================================== pump_alert removal ====
def test_dormant_pump_alert_emitter_removed():
    assert not (ROOT / "telegram_ai" / "pump_alert.py").exists(), (
        "dormant UNKNOWN-permissive Python opportunity emitter must not remain")


def test_no_production_emitter_promotes_unknown_to_positive():
    """Repo-wide: no production source encodes 'UNKNOWN security + high score => alert'."""
    offenders = []
    for path in list(ROOT.glob("*.ts")) + list((ROOT / "telegram_ai").glob("*.py")) \
            + list((ROOT / "architecture").rglob("*.py")):
        if "node_modules" in str(path) or ".venv" in str(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # dangerous idiom: UNKNOWN branch that returns/permits on a score threshold
        if re.search(r'UNKNOWN"?\s*(&&|and)\s*[^\n]*score', text) and re.search(r'>=\s*(0\.8|80)\b', text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"UNKNOWN-permissive opportunity promotion still present: {offenders}"


# ================================================= top_opportunity safety ===
def test_recommended_opportunity_is_none_for_unknown_top(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana", address="SolUnkTop1111111111111111111111111111111",
        symbol="UNK", name="Unknown", source_provider="dexscreener",
        retrieved_ts=time.time(), metrics=_strong_metrics(), security=SecuritySignals())
    rep = _run(cand, tmp_path, "ob_unknown.sqlite")
    assert rep.top_opportunity is not None                     # raw field still populated
    assert rep.top_opportunity.security_disposition == "PASS_WITH_UNKNOWN"
    assert rep.recommended_opportunity is None                 # authoritative field is safe


def test_recommended_opportunity_is_none_for_veto_top(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana", address="SolVetoTop111111111111111111111111111111",
        symbol="MINT", name="Mint Veto", source_provider="dexscreener",
        retrieved_ts=time.time(), metrics=_strong_metrics(),
        security=SecuritySignals(is_honeypot=False, has_mint_authority=True))
    rep = _run(cand, tmp_path, "ob_veto.sqlite")
    assert rep.top_opportunity is not None
    assert rep.top_opportunity.security_disposition == "SECURITY_VETO"
    assert rep.recommended_opportunity is None


def test_recommended_opportunity_equals_top_for_pass(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana", address="SolPassTop111111111111111111111111111111",
        symbol="PASS", name="Clean Pass", source_provider="dexscreener",
        retrieved_ts=time.time(), metrics=_strong_metrics(),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 is_ownership_renounced=True,
                                 top10_holder_concentration_pct=20.0))
    rep = _run(cand, tmp_path, "ob_pass.sqlite")
    assert rep.recommended_opportunity is not None
    assert rep.recommended_opportunity.security_disposition == "PASS"
    assert rep.recommended_opportunity.token_address == rep.top_opportunity.token_address
