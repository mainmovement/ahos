#!/usr/bin/env python3
"""AHOS Whale & Holder-Concentration Tracker.

Answers: "who actually owns this, and are the big holders accumulating or leaving?"

DATA REALITY (documented, not assumed)
--------------------------------------
Free Solana RPC endpoints rate-limit or forbid `getTokenLargestAccounts`, and free
EVM endpoints do not expose holder lists at all. The project already proved this
(discovery/holders.py, wave-6 probes). Therefore:

  - When holder data IS available, we analyse concentration and its DELTA.
  - When it is NOT, we return UNKNOWN with an explicit reason. We never estimate
    concentration from price action — that is astrology, not evidence.

WHY CONCENTRATION IS A RISK, NOT AN OPPORTUNITY
-----------------------------------------------
A token where the top 10 wallets hold 80% is one Telegram message away from a
-90% candle. Concentration is scored as a DEDUCTION. A falling top-10 share
across snapshots (distribution) is mildly positive; a rising share while price
rises (accumulation into a thin float) is a TRAP warning.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

WHALE_VERSION = "AHOS-WHALE-v1"

# Locked concentration bands (top-10 holder share of supply).
CONCENTRATION_CRITICAL = 80.0
CONCENTRATION_HIGH = 60.0
CONCENTRATION_MODERATE = 40.0

# A single wallet above this share can single-handedly break the pool.
SINGLE_WALLET_CRITICAL = 25.0

# Minimum change (percentage points) before we call it a real move, not noise.
DELTA_SIGNIFICANT = 3.0


@dataclass
class WhaleSignal:
    subject: str
    label: str                        # DISTRIBUTING | ACCUMULATING | STABLE | DANGEROUS | UNKNOWN
    top10_share_pct: float | None
    top1_share_pct: float | None
    delta_pct_points: float | None    # change in top-10 share vs previous snapshot
    holder_count: int | None
    risk_penalty: float               # points to subtract from an opportunity score
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    # Role is UNKNOWN unless identity evidence is supplied. Concentration
    # alone never proves whale vs smart-money vs insider vs deployer vs LP vs MM.
    wallet_role: str = "UNKNOWN"   # WHALE|SMART_MONEY|INSIDER|DEPLOYER|LP|MARKET_MAKER|UNKNOWN
    computed_ts: float = field(default_factory=time.time)
    version: str = WHALE_VERSION

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject, "label": self.label,
            "top10_share_pct": self.top10_share_pct,
            "top1_share_pct": self.top1_share_pct,
            "delta_pct_points": self.delta_pct_points,
            "holder_count": self.holder_count,
            "risk_penalty": self.risk_penalty,
            "reasons": self.reasons, "warnings": self.warnings,
            "unknowns": self.unknowns, "evidence": self.evidence,
            "computed_ts": self.computed_ts, "version": self.version,
        }


class WhaleTracker:
    """Analyses holder concentration and its movement across snapshots."""

    def analyze(self,
                symbol: str,
                top10_share_pct: float | None,
                top1_share_pct: float | None = None,
                previous_top10_share_pct: float | None = None,
                holder_count: int | None = None,
                price_change_pct: float | None = None,
                evidence_refs: list[str] | None = None,
                wallet_role: str | None = None,
                role_evidence: str | None = None,
                now: float | None = None) -> WhaleSignal:
        ts = time.time() if now is None else now
        reasons: list[str] = []
        warnings: list[str] = []
        unknowns: list[str] = []
        penalty = 0.0

        # ---- HONESTY GATE ---------------------------------------------------
        if top10_share_pct is None:
            return WhaleSignal(
                subject=symbol, label="UNKNOWN",
                top10_share_pct=None, top1_share_pct=top1_share_pct,
                delta_pct_points=None, holder_count=holder_count,
                risk_penalty=0.0, reasons=[], warnings=[],
                unknowns=["توزیع هولدرها (رایگان در دسترس نیست — RPC عمومی محدود است)",
                          "wallet_role"],
                evidence=evidence_refs or [], wallet_role="UNKNOWN", computed_ts=ts,
            )

        # ---- 1. Absolute concentration --------------------------------------
        if top10_share_pct >= CONCENTRATION_CRITICAL:
            penalty += 30.0
            warnings.append(
                f"تمرکز بحرانی: ۱۰ کیف‌پول برتر {top10_share_pct:.1f}٪ از عرضه را دارند — "
                "یک تصمیم جمعی می‌تواند قیمت را نابود کند"
            )
        elif top10_share_pct >= CONCENTRATION_HIGH:
            penalty += 18.0
            warnings.append(f"تمرکز بالا: ۱۰ کیف‌پول برتر {top10_share_pct:.1f}٪ از عرضه")
        elif top10_share_pct >= CONCENTRATION_MODERATE:
            penalty += 8.0
            warnings.append(f"تمرکز متوسط: ۱۰ کیف‌پول برتر {top10_share_pct:.1f}٪ از عرضه")
        else:
            reasons.append(f"توزیع نسبتاً سالم (۱۰ کیف‌پول برتر فقط {top10_share_pct:.1f}٪)")

        # ---- 2. Single-wallet dominance -------------------------------------
        if top1_share_pct is not None:
            if top1_share_pct >= SINGLE_WALLET_CRITICAL:
                penalty += 20.0
                warnings.append(
                    f"یک کیف‌پول به‌تنهایی {top1_share_pct:.1f}٪ از عرضه را دارد — ریسک تک‌نقطه‌ای"
                )
        else:
            unknowns.append("سهم بزرگ‌ترین کیف‌پول منفرد")

        # ---- 3. Movement between snapshots ----------------------------------
        delta: float | None = None
        if previous_top10_share_pct is not None:
            delta = top10_share_pct - previous_top10_share_pct

            if delta <= -DELTA_SIGNIFICANT:
                reasons.append(
                    f"نهنگ‌ها در حال توزیع: سهم ۱۰ کیف‌پول برتر {abs(delta):.1f} واحد کاهش یافته"
                )
            elif delta >= DELTA_SIGNIFICANT:
                # Accumulation into a thin float, while price pumps == classic trap.
                if price_change_pct is not None and price_change_pct > 20.0:
                    penalty += 15.0
                    warnings.append(
                        f"الگوی تله: قیمت {price_change_pct:.0f}٪ بالا رفته و همزمان تمرکز "
                        f"{delta:.1f} واحد بیشتر شده — شناوری در حال نازک شدن است"
                    )
                else:
                    warnings.append(
                        f"تمرکز در حال افزایش: سهم ۱۰ کیف‌پول برتر {delta:.1f} واحد بیشتر شده"
                    )
        else:
            unknowns.append("اسنپ‌شات قبلی هولدرها (برای سنجش روند)")

        # ---- 4. Holder breadth ----------------------------------------------
        if holder_count is not None:
            if holder_count < 50:
                penalty += 12.0
                warnings.append(f"تعداد هولدر بسیار کم ({holder_count}) — بازار واقعی وجود ندارد")
            elif holder_count > 1000:
                reasons.append(f"پایه هولدر گسترده ({holder_count} کیف‌پول)")
        else:
            unknowns.append("تعداد کل هولدرها")

        # ---- 5. Wallet role (identity evidence required) ---------------------
        allowed_roles = {
            "WHALE", "SMART_MONEY", "INSIDER", "DEPLOYER", "LP", "MARKET_MAKER",
        }
        role = "UNKNOWN"
        if wallet_role and role_evidence:
            cand = str(wallet_role).upper()
            if cand in allowed_roles:
                role = cand
                reasons.append(f"wallet_role={role} (evidence: {role_evidence})")
            else:
                unknowns.append("wallet_role (unrecognised label refused)")
        else:
            unknowns.append(
                "wallet_role — concentration is not identity; "
                "whale/smart-money/insider/deployer/LP/MM stay UNKNOWN without evidence"
            )

        # ---- 6. Verdict -------------------------------------------------------
        if top10_share_pct >= CONCENTRATION_CRITICAL or (
            top1_share_pct is not None and top1_share_pct >= SINGLE_WALLET_CRITICAL
        ):
            label = "DANGEROUS"
        elif delta is not None and delta <= -DELTA_SIGNIFICANT:
            label = "DISTRIBUTING"
        elif delta is not None and delta >= DELTA_SIGNIFICANT:
            label = "ACCUMULATING"
        else:
            label = "STABLE"

        return WhaleSignal(
            subject=symbol, label=label,
            top10_share_pct=round(top10_share_pct, 2),
            top1_share_pct=round(top1_share_pct, 2) if top1_share_pct is not None else None,
            delta_pct_points=round(delta, 2) if delta is not None else None,
            holder_count=holder_count,
            risk_penalty=round(min(penalty, 50.0), 2),
            reasons=reasons, warnings=warnings, unknowns=unknowns,
            evidence=evidence_refs or [], wallet_role=role, computed_ts=ts,
        )
