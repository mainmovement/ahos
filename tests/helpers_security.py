"""Lane B security fixtures. Not production evidence."""
from __future__ import annotations

from architecture.providers.contracts import SecuritySignals

NOW = 1_800_000_000.0
OLD_POOL_TS = NOW - 30 * 86400


def passing_security_signals(**over) -> SecuritySignals:
    """All overlay-critical fields resolved FALSE so GATE 1 can PASS."""
    d = dict(
        is_honeypot=False,
        sell_tax_pct=1.0,
        buy_tax_pct=1.0,
        liquidity_locked_pct=95.0,
        has_mint_authority=False,
        has_freeze_authority=False,
        is_contract_verified=True,
        is_ownership_renounced=True,
        top10_holder_concentration_pct=20.0,
        deployer_past_rug_count=0,
        is_blacklisted=False,
        cannot_sell_all=False,
        is_proxy=False,
    )
    d.update(over)
    return SecuritySignals(**d)
