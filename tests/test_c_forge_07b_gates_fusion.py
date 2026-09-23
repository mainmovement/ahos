"""C-FORGE-07b — gates/fusion refuse unminted VERIFIED (mint cookie required)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.decision.advisor import DecisionAdvisor  # noqa: E402
from architecture.decision.authority import (  # noqa: E402
    CanonicalDecisionAuthority,
    CanonicalOutcome,
)
from architecture.identity import __all__ as IDENTITY_ALL  # noqa: E402
from architecture.identity.fusion import (  # noqa: E402
    FUSION_VERSION,
    copy_canonical_token_id,
    is_canonical_verified,
)
from architecture.identity.gates import (  # noqa: E402
    identity_allows_alert,
    identity_allows_identity_mutation,
    identity_allows_paper_candidate,
    identity_allows_positive_decision,
    pool_liquidity_claims_allowed,
    token_monitoring_allowed,
)
from architecture.identity.resolution import _has_verified_mint  # noqa: E402
from architecture.identity.types import (  # noqa: E402
    ChainIdentity,
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from tests.helpers_identity import (  # noqa: E402
    SOL_CANON,
    verified_identity_fixture,
    verified_pool_identity_fixture,
)
from tests.helpers_security import OLD_POOL_TS, passing_security_signals  # noqa: E402

NOW = 1_800_000_000.0


def _unminted_verified(
    *,
    chain: str = "solana",
    address: str = SOL_CANON,
    token_id: str = "test-fixture-token-id",
    symbol: str = "TOK",
) -> IdentityResolution:
    """Hand-built VERIFIED IR WITHOUT resolver mint (copy helpers pattern, no mint)."""
    return IdentityResolution(
        chain=ChainIdentity(chain, chain, IdentityState.VERIFIED, "test_fixture"),
        token=TokenIdentity(
            chain=chain,
            address_canonical=address,
            address_input=address,
            token_id=token_id,
            symbol_alias=symbol,
            name_alias=f"{symbol} Token",
            state=IdentityState.VERIFIED,
            reason="test_fixture",
        ),
        pool=None,
        dex=None,
        policy_version="identity-resolution-v1",
        computed_ts=0.0,
    )


GATE_HELPERS = (
    identity_allows_positive_decision,
    identity_allows_alert,
    identity_allows_paper_candidate,
    identity_allows_identity_mutation,
    token_monitoring_allowed,
    pool_liquidity_claims_allowed,
)


def test_b1_unminted_verified_all_gates_false():
    unminted = _unminted_verified()
    assert unminted.token.state is IdentityState.VERIFIED
    assert _has_verified_mint(unminted) is False
    for fn in GATE_HELPERS:
        assert fn(unminted) is False, fn.__name__
    assert token_monitoring_allowed(unminted) is False
    assert pool_liquidity_claims_allowed(unminted) is False


def test_b2_unminted_fusion_not_canonical():
    unminted = _unminted_verified(token_id="abc123canonicalid")
    assert is_canonical_verified(unminted) is False
    assert copy_canonical_token_id(unminted) is None


def test_b3_minted_fixtures_gates_and_fusion():
    token_only = verified_identity_fixture()
    pool = verified_pool_identity_fixture()
    assert _has_verified_mint(token_only) is True
    assert _has_verified_mint(pool) is True

    assert identity_allows_positive_decision(token_only) is True
    assert identity_allows_alert(token_only) is True
    assert identity_allows_paper_candidate(token_only) is True
    assert identity_allows_identity_mutation(token_only) is True
    assert token_monitoring_allowed(token_only) is True
    assert pool_liquidity_claims_allowed(token_only) is False
    assert is_canonical_verified(token_only) is True
    assert copy_canonical_token_id(token_only) is not None

    assert identity_allows_positive_decision(pool) is True
    assert token_monitoring_allowed(pool) is True
    assert pool_liquidity_claims_allowed(pool) is True
    assert is_canonical_verified(pool) is True


def test_b4_unminted_cannot_open_authority_or_advisor_positive():
    unminted = _unminted_verified()
    cand = NormalizedTokenCandidate(
        chain="solana",
        address=SOL_CANON,
        symbol="TOK",
        name="TOK Token",
        metrics=MarketMetrics(
            price_usd=0.002,
            liquidity_usd=150_000,
            volume_5m=9_000,
            volume_1h=30_000,
            volume_24h=250_000,
            txns_5m_buys=90,
            txns_5m_sells=25,
            txns_1h_buys=400,
            txns_1h_sells=250,
            price_change_1h=12.0,
        ),
        security=passing_security_signals(),
        source_provider="dexscreener",
        retrieved_ts=NOW,
        pair_created_ts=NOW - 30 * 86400,
    )
    report = OpportunityScorer().evaluate(cand, now=NOW)
    decision = CanonicalDecisionAuthority().decide(
        cand,
        report,
        identity=unminted,
        now=NOW,
        exitability=ExitabilityAnalyzer().analyze(cand, 200),
    )
    assert decision.outcome != CanonicalOutcome.BUY
    assert decision.outcome in {
        CanonicalOutcome.INSUFFICIENT_EVIDENCE,
        CanonicalOutcome.NO_TRADE,
        CanonicalOutcome.REJECT,
        CanonicalOutcome.MONITOR_ONLY,
        CanonicalOutcome.WATCH,
        CanonicalOutcome.SKIP,
        CanonicalOutcome.HIGH_RISK,
    }
    # Unminted VERIFIED maps to INSUFFICIENT_EVIDENCE via identity gate failure.
    assert decision.outcome == CanonicalOutcome.INSUFFICIENT_EVIDENCE

    advice = DecisionAdvisor(bankroll_usd=1000.0).advise_entry(
        cand,
        report,
        exitability=ExitabilityAnalyzer().analyze(cand, 200),
        identity=unminted,
    )
    assert advice.action == "AVOID"
    assert advice.action != "ENTER"


def test_b6_mint_helpers_not_in_package_all():
    forbidden = {
        "_has_verified_mint",
        "_attach_verified_mint",
        "_VERIFIED_MINT",
        "_mint_verified_for_tests",
    }
    exported = set(IDENTITY_ALL)
    assert forbidden.isdisjoint(exported)
    for name in forbidden:
        assert name not in IDENTITY_ALL


def test_b9_paper_trading_identity_census_zero():
    """paper_trading/** must not reference Lane B identity surfaces."""
    patterns = (
        "IdentityResolution",
        "IdentityState",
        "identity_allows",
        "architecture.identity",
    )
    paper = ROOT / "paper_trading"
    hits: list[str] = []
    for path in sorted(paper.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in {".pyc", ".pyo"} or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pat in patterns:
            if pat in text:
                hits.append(f"{path.relative_to(ROOT)}:{pat}")
    assert hits == [], f"B9 census non-zero: {hits}"


def test_fusion_version_bumped_for_07b():
    assert FUSION_VERSION == "identity-fusion-foundation-v1.1"
    src = (ROOT / "architecture" / "identity" / "fusion.py").read_text(encoding="utf-8")
    assert "from discovery" not in src
    assert "resolve_identity" not in src


def test_b9_subprocess_rg_equivalent_zero():
    """Optional subprocess census; pathlib walk above is authoritative."""
    paper = ROOT / "paper_trading"
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                "root = Path(%r)\n"
                "pats = ('IdentityResolution','IdentityState','identity_allows','architecture.identity')\n"
                "hits = []\n"
                "for p in root.rglob('*'):\n"
                "    if not p.is_file() or p.suffix in {'.pyc','.pyo'} or '__pycache__' in p.parts:\n"
                "        continue\n"
                "    t = p.read_text(encoding='utf-8', errors='replace')\n"
                "    for pat in pats:\n"
                "        if pat in t:\n"
                "            hits.append(f'{p}:{pat}')\n"
                "print(len(hits))\n"
                "raise SystemExit(0 if not hits else 1)\n"
            )
            % str(paper),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "0"
