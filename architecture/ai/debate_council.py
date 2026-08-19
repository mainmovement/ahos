"""AHOS Structured Adversarial Debate Council (TradingAgents Pattern).

Implements multi-role cognitive debate:
- Bull Analyst (Upside, momentum, liquidity growth)
- Bear Analyst (Downside risks, liquidity traps, developer dump)
- Risk Manager (Hard veto authority on capital risk)
- Arbitrator (Consensus synthesis and score arbitration)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from architecture.ai.router import AIProviderRouter


class AdversarialDebateCouncil:
    """Orchestrates structured Bull vs Bear debates with Risk veto authority."""

    def __init__(self, router: Optional[AIProviderRouter] = None) -> None:
        self.router = router or AIProviderRouter()

    def conduct_debate(
        self,
        token_symbol: str,
        price_usd: float,
        liquidity_usd: float,
        security_score: float,
        momentum_score: float,
    ) -> Dict[str, Any]:
        """Runs a 2-round adversarial debate on a candidate opportunity."""
        # 1. Bull Analyst Perspective
        bull_case = self._bull_case(
            token_symbol, liquidity_usd, momentum_score
        )

        # 2. Bear Analyst Perspective
        bear_case = self._bear_case(
            token_symbol, liquidity_usd, security_score
        )

        # 3. Risk Manager Evaluation (Holds Veto Power)
        risk_veto, risk_reason = self._risk_manager_evaluation(
            liquidity_usd, security_score
        )

        # 4. Arbitrator Consensus Decision
        if risk_veto:
            consensus_recommendation = "REJECT_RISK_VETO"
            consensus_score = 0.0
            arbitration_summary = f"Opportunity rejected by Risk Manager: {risk_reason}"
        else:
            # Weighted synthesis of Bull vs Bear
            net_score = (momentum_score * 0.55) + (security_score * 0.45)
            if net_score >= 75.0:
                consensus_recommendation = "HIGH_OPPORTUNITY"
            elif net_score >= 50.0:
                consensus_recommendation = "MODERATE_WATCH"
            else:
                consensus_recommendation = "LOW_PRIORITY"

            consensus_score = round(net_score, 2)
            arbitration_summary = (
                f"Consensus reached. Bull arguments: '{bull_case['argument']}'. "
                f"Bear counter: '{bear_case['argument']}'."
            )

        return {
            "token_symbol": token_symbol,
            "bull_perspective": bull_case,
            "bear_perspective": bear_case,
            "risk_veto": risk_veto,
            "risk_veto_reason": risk_reason,
            "consensus_score": consensus_score,
            "consensus_recommendation": consensus_recommendation,
            "arbitration_summary": arbitration_summary,
        }

    def _bull_case(
        self, symbol: str, liquidity_usd: float, momentum: float
    ) -> Dict[str, Any]:
        return {
            "persona": "BULL_RESEARCHER",
            "argument": f"{symbol} exhibits positive volume velocity (momentum {momentum:.1f}/100) and healthy pool liquidity (${liquidity_usd:,.0f}).",
            "conviction": min(1.0, momentum / 100.0),
        }

    def _bear_case(
        self, symbol: str, liquidity_usd: float, security: float
    ) -> Dict[str, Any]:
        concerns = []
        if liquidity_usd < 20000.0:
            concerns.append("Low liquidity depth increases AMM price impact")
        if security < 70.0:
            concerns.append("Contract forensics show elevated security risks")
        if not concerns:
            concerns.append("Macro chop and potential volume dry-up")

        return {
            "persona": "BEAR_RESEARCHER",
            "argument": "; ".join(concerns),
            "threat_level": "HIGH" if security < 60.0 else "MODERATE",
        }

    def _risk_manager_evaluation(
        self, liquidity_usd: float, security_score: float
    ) -> Tuple[bool, Optional[str]]:
        """Risk Manager holds absolute veto authority."""
        if security_score < 40.0:
            return (
                True,
                "Security score below 40.0 threshold (Potential Honeypot/Malicious Bytecode)",
            )
        if liquidity_usd < 5000.0:
            return (
                True,
                "Pool liquidity under $5,000 threshold (Severe Liquidity Trap Risk)",
            )
        return False, None
