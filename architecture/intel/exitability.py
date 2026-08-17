#!/usr/bin/env python3
"""AHOS Exitability Analyzer — "if I buy, can I actually get my money OUT?"

This is the single most important question in early-token trading and the one
most systems ignore. A token can show +400% on the chart and still be a total
loss, because:

  - it is a HONEYPOT (buys succeed, sells revert by design)
  - the SELL TAX is 40% (you keep 60 cents on the dollar, before slippage)
  - the pool is $3,000 deep, so your $500 exit moves price -16% against you
  - liquidity is UNLOCKED, so the deployer can withdraw it before you sell
  - the mint authority is live, so supply can be inflated under you

WHAT THIS MODULE DOES
---------------------
Computes, for a concrete position size, the REALIZABLE fraction: the share of
displayed value you would actually recover by exiting right now, after slippage,
fees, tax and gas. Then it applies HARD VETOES that no upside can override.

LAW: DISPLAYED VALUE IS NOT MONEY. Only realizable value is money.

This reuses the locked, pre-registered constants from `paper_trading.cost_model`
and `paper_trading.realizable` — the same maths the paper ledger books trades
with, so advice and accounting can never diverge.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from paper_trading import cost_model as cm
from paper_trading import realizable as rz

EXITABILITY_VERSION = "AHOS-EXIT-v1"

# Locked decision bands for the realizable fraction.
EXIT_EXCELLENT = 0.90      # keep >=90% of displayed value
EXIT_ACCEPTABLE = 0.75
EXIT_POOR = 0.50           # below this, the position is a trap in slow motion

# A sell tax above this is treated as a soft honeypot.
SELL_TAX_VETO_PCT = 25.0
# Position must not exceed this share of pool liquidity.
MAX_POOL_SHARE_PCT = 2.0


@dataclass
class ExitabilityReport:
    symbol: str
    verdict: str                       # EXITABLE | DEGRADED | TRAPPED | UNKNOWN
    realizable_fraction: float | None  # [0,1]; None = UNKNOWN
    realizable_usd: float | None
    displayed_usd: float | None
    slippage_bps: float | None
    fee_usd: float | None
    tax_usd: float | None
    gas_usd: float | None
    pool_share_pct: float | None
    max_safe_position_usd: float | None
    hard_vetoes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)
    version: str = EXITABILITY_VERSION

    @property
    def is_safe(self) -> bool:
        return self.verdict == "EXITABLE" and not self.hard_vetoes

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol, "verdict": self.verdict,
            "realizable_fraction": self.realizable_fraction,
            "realizable_usd": self.realizable_usd,
            "displayed_usd": self.displayed_usd,
            "slippage_bps": self.slippage_bps,
            "fee_usd": self.fee_usd, "tax_usd": self.tax_usd, "gas_usd": self.gas_usd,
            "pool_share_pct": self.pool_share_pct,
            "max_safe_position_usd": self.max_safe_position_usd,
            "hard_vetoes": self.hard_vetoes, "warnings": self.warnings,
            "unknowns": self.unknowns, "reasons": self.reasons,
            "computed_ts": self.computed_ts, "version": self.version,
        }


class ExitabilityAnalyzer:
    """Position-size-aware exit feasibility, using the locked cost model."""

    def analyze(self,
                candidate,
                position_usd: float = 100.0,
                now: float | None = None) -> ExitabilityReport:
        ts = time.time() if now is None else now
        m = candidate.metrics
        sec = candidate.security
        symbol = getattr(candidate, "symbol", "?")
        chain = getattr(candidate, "chain", "solana")

        vetoes: list[str] = []
        warnings: list[str] = []
        unknowns: list[str] = []
        reasons: list[str] = []

        # ================= HARD VETOES — no upside overrides these ============
        if sec.is_honeypot is True:
            vetoes.append("قرارداد HONEYPOT است: خرید ممکن، فروش مسدود — ورود ممنوع")

        if sec.sell_tax_pct is not None and sec.sell_tax_pct >= SELL_TAX_VETO_PCT:
            vetoes.append(
                f"مالیات فروش {sec.sell_tax_pct:.1f}٪ — عملاً هانی‌پات نرم است"
            )

        if sec.has_mint_authority is True:
            vetoes.append(
                "اختیار ضرب سکه (mint authority) هنوز فعال است — عرضه می‌تواند "
                "زیر پای شما بی‌نهایت شود"
            )

        if sec.has_freeze_authority is True:
            vetoes.append(
                "اختیار انجماد (freeze authority) فعال است — کیف‌پول شما قابل قفل شدن است"
            )

        # ================= LIQUIDITY ANALYSIS =================================
        liq = m.liquidity_usd
        price = m.price_usd

        if liq is None:
            unknowns.append("عمق نقدینگی استخر")
        if price is None:
            unknowns.append("قیمت لحظه‌ای")

        # Liquidity lock status: unlocked liquidity = the exit can vanish.
        locked = sec.liquidity_locked_pct
        burned = sec.liquidity_burned_pct
        secured = None
        if locked is not None or burned is not None:
            secured = (locked or 0.0) + (burned or 0.0)
            if secured < 50.0:
                warnings.append(
                    f"فقط {secured:.0f}٪ نقدینگی قفل/سوزانده شده — سازنده می‌تواند "
                    "استخر را قبل از فروش شما خالی کند"
                )
            else:
                reasons.append(f"{secured:.0f}٪ نقدینگی قفل یا سوزانده شده است")
        else:
            unknowns.append("وضعیت قفل نقدینگی")

        # If we cannot price the exit, we say UNKNOWN. We do not guess.
        if liq is None or liq <= 0 or price is None or price <= 0:
            return ExitabilityReport(
                symbol=symbol,
                verdict="TRAPPED" if vetoes else "UNKNOWN",
                realizable_fraction=None, realizable_usd=None, displayed_usd=None,
                slippage_bps=None, fee_usd=None, tax_usd=None, gas_usd=None,
                pool_share_pct=None, max_safe_position_usd=None,
                hard_vetoes=vetoes, warnings=warnings,
                unknowns=unknowns + ["امکان محاسبه خروج بدون قیمت و نقدینگی وجود ندارد"],
                reasons=reasons, computed_ts=ts,
            )

        # ================= REALIZABLE VALUE ===================================
        pool_share = (position_usd / liq) * 100.0
        if pool_share > MAX_POOL_SHARE_PCT:
            warnings.append(
                f"حجم پیشنهادی {pool_share:.1f}٪ از کل استخر است — خروج شما خودش "
                f"قیمت را می‌شکند (حد امن: {MAX_POOL_SHARE_PCT}٪)"
            )

        # Largest position that still exits inside the locked impact cap.
        max_exec = rz.max_executable_notional(liq)
        max_safe = min(max_exec, liq * MAX_POOL_SHARE_PCT / 100.0)

        qty = position_usd / price
        sell_tax_bps = (sec.sell_tax_pct * 100.0) if sec.sell_tax_pct is not None else None
        if sell_tax_bps is None:
            unknowns.append("مالیات فروش توکن")

        assessment = rz.assess(
            qty=qty, price_obs=price, liq_now=liq,
            sell_tax_bps=sell_tax_bps, chain=chain,
            classification="EXITABILITY_PROBE",
        )

        displayed = assessment.get("displayed_value_usd", qty * price)
        net = assessment.get("realizable_value_usd")
        route_status = assessment.get("route_status")

        slip = assessment.get("exit_slippage_bps")
        if slip is None:
            slip = cm.slippage_bps(position_usd, liq)
        gas = assessment.get("gas_cost_usd", rz.gas_usd(chain))
        fee_usd = assessment.get("exit_fee_usd")
        tax_usd = assessment.get("sell_tax_usd")

        if net is None:
            fraction = None
            unknowns.append("ارزش قابل تحقق (مدل خروج نتیجه‌ای برنگرداند)")
        else:
            fraction = max(0.0, net / displayed) if displayed > 0 else 0.0

        # The locked model can itself declare the position unexitable.
        if route_status and str(route_status).startswith("UNEXITABLE"):
            vetoes.append(f"مدل خروج وضعیت «{route_status}» را اعلام کرد — خروج ممکن نیست")
        elif route_status == "EXECUTABLE_PARTIAL":
            stuck = assessment.get("unexited_displayed_usd") or 0.0
            warnings.append(
                f"تنها بخشی از موقعیت قابل خروج است؛ حدود ${stuck:,.2f} در استخر گیر می‌کند"
            )

        # ================= VERDICT ============================================
        if vetoes:
            verdict = "TRAPPED"
        elif fraction is None:
            verdict = "UNKNOWN"
        elif fraction >= EXIT_EXCELLENT:
            verdict = "EXITABLE"
            reasons.append(f"خروج روان: حدود {fraction * 100:.1f}٪ ارزش قابل بازیابی است")
        elif fraction >= EXIT_ACCEPTABLE:
            verdict = "EXITABLE"
            warnings.append(f"هزینه خروج محسوس: تنها {fraction * 100:.1f}٪ بازیابی می‌شود")
        elif fraction >= EXIT_POOR:
            verdict = "DEGRADED"
            warnings.append(
                f"خروج گران: فقط {fraction * 100:.1f}٪ ارزش نمایشی بازیابی می‌شود"
            )
        else:
            verdict = "TRAPPED"
            warnings.append(
                f"عملاً به دام افتاده: تنها {fraction * 100:.1f}٪ سرمایه قابل خروج است"
            )

        return ExitabilityReport(
            symbol=symbol, verdict=verdict,
            realizable_fraction=round(fraction, 4) if fraction is not None else None,
            realizable_usd=round(net, 4) if net is not None else None,
            displayed_usd=round(displayed, 4),
            slippage_bps=round(slip, 2) if slip is not None else None,
            fee_usd=round(fee_usd, 4) if fee_usd is not None else None,
            tax_usd=round(tax_usd, 4) if tax_usd is not None else None,
            gas_usd=gas,
            pool_share_pct=round(pool_share, 3),
            max_safe_position_usd=round(max_safe, 2),
            hard_vetoes=vetoes, warnings=warnings, unknowns=unknowns,
            reasons=reasons, computed_ts=ts,
        )
