#!/usr/bin/env python3
"""Sub-PR 2 (final reconciliation) — One-Brain authority matrix lock.

Adversarial governance tests that pin the *authority map*: the only production
positive-opportunity emitters are the two canonically-gated ones, no adapter can
independently promote a token, n8n cannot bypass the gate, and the research
broadcaster is evidence-only. Source-scanning mirrors the repo idiom
(`tests/test_zero_money_invariant.py`). Nothing is weakened or xfail'd.

NOTE: these tests lock the ELIGIBILITY-RULE invariant (UNKNOWN/VETO never become a
positive opportunity through any adapter). They do NOT — and cannot — assert that
the Python and TypeScript runtimes share a single per-token security disposition;
that cross-runtime bridge is the documented remaining blocker (see the mission
report), because the repository establishes no shared decision store / token
identity / co-execution guarantee.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _prod_sources():
    files = list(ROOT.glob("*.ts")) + list(ROOT.glob("*.tsx"))
    for sub in ("architecture", "telegram_ai", "engine", "app"):
        files += list((ROOT / sub).rglob("*.py"))
        files += list((ROOT / sub).rglob("*.ts"))
        files += list((ROOT / sub).rglob("*.tsx"))
    out = []
    for f in files:
        s = str(f)
        if "node_modules" in s or ".venv" in s or "/tests/" in s:
            continue
        out.append(f)
    return out


# ============================== single opportunity-alert authority (Python) ==
def test_python_opportunity_alert_construction_is_single_sourced():
    """The `cls="OPPORTUNITY"` alert is only built by the gated AlertEngine."""
    emitters = []
    for f in _prod_sources():
        if f.suffix != ".py":
            continue
        if re.search(r'cls\s*=\s*"OPPORTUNITY"', f.read_text(encoding="utf-8", errors="ignore")):
            emitters.append(str(f.relative_to(ROOT)))
    assert emitters == ["architecture/alerts/engine.py"], emitters
    # And that emitter is gated by the canonical security disposition.
    ae = (ROOT / "architecture" / "alerts" / "engine.py").read_text(encoding="utf-8")
    assert "security_cleared" in ae and 'verdict"' in ae or 'verdict\'' in ae or "disposition" in ae


def test_special_opportunity_card_is_single_sourced_and_pass_gated():
    """The Telegram 'special opportunity' card exists only in the orchestrator and
    is emitted only for a security-cleared (PASS) candidate."""
    hits = []
    for f in _prod_sources():
        if "فرصت ویژه" in f.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(f.relative_to(ROOT)))
    assert hits == ["architecture/pipeline/orchestrator.py"], hits
    orch = (ROOT / "architecture" / "pipeline" / "orchestrator.py").read_text(encoding="utf-8")
    assert "top_cleared" in orch and "allows_opportunity" in orch


# ============================== single opportunity-alert authority (TS) ======
def test_ts_opportunity_emission_is_single_sourced_and_canonical():
    """The web/Telegram opportunity emission lives only in alerts.ts and consumes
    the canonical eligibility authority."""
    banner_emitters = []
    for f in _prod_sources():
        if f.suffix != ".ts":
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "api.telegram.org" in txt and ("OPPORTUNITY" in txt or "pump" in txt.lower()):
            banner_emitters.append(str(f.relative_to(ROOT)))
    assert banner_emitters == ["alerts.ts"], banner_emitters
    alerts = (ROOT / "alerts.ts").read_text(encoding="utf-8")
    # Phase 4: emission is gated by the Python canonical decision store.
    assert "isCanonicalPositiveOpportunity" in alerts
    assert "canonical_store" in alerts


# ============================== n8n cannot bypass ============================
def test_n8n_has_no_enabled_live_execution_and_no_independent_scoring():
    wf_dir = ROOT / "n8n" / "workflows"
    if not wf_dir.exists():
        return
    for wf in wf_dir.glob("*.json"):
        raw = wf.read_text(encoding="utf-8", errors="ignore")
        data = json.loads(raw)
        for node in data.get("nodes", []):
            name = str(node.get("name", ""))
            if "LIVE" in name.upper() and "EXECUT" in name.upper():
                assert node.get("disabled") is True, f"{wf.name}: enabled LIVE execution node {name!r}"
        # n8n must not independently compute security/scoring/opportunity decisions.
        for token in ("opportunity_score", "scoreToken", "rankOpportunities", "honeypot", "securityStatus"):
            assert token not in raw, f"{wf.name}: n8n independently references {token!r}"


# ============================== research broadcaster is evidence-only ========
def test_research_report_bot_is_not_a_per_token_opportunity_emitter():
    p = ROOT / "engine" / "research_report_bot.py"
    if not p.exists():
        return
    txt = p.read_text(encoding="utf-8")
    assert "RESEARCH DIGEST" in txt
    # It broadcasts lab-registry research, not per-token opportunity eligibility.
    for token in ("cls=\"OPPORTUNITY\"", "isPositiveOpportunityEligible", "فرصت ویژه", "recommendation_cap"):
        assert token not in txt, f"research bot unexpectedly emits opportunity authority: {token!r}"


# ============================== dormant emitter stays gone ===================
def test_pump_alert_emitter_absent():
    assert not (ROOT / "telegram_ai" / "pump_alert.py").exists()
