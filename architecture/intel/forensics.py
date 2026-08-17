#!/usr/bin/env python3
"""AHOS On-Chain Forensics (Wave-26) — distribution & coordination analysis.

TECHNIQUES HARVESTED FROM OPEN SOURCE
-------------------------------------
The user asked to study OSS projects and reuse what works. We surveyed the
Solana rug-detection ecosystem (rugcheck wrappers, solana-bundler-detector,
solana-rugchecker, assorted holder analyzers). Almost none of that CODE is
reusable here: it is mostly TypeScript, and the Python entries are thin
wrappers around paid APIs (Solsniffer, Helius, gmgn.ai) that violate both the
$0 cost floor and the "works under sanctions" constraint.

What IS reusable is the MATHEMATICS, which is public and unencumbered:

  * Gini coefficient over holder balances
        -- seen in nothingdao/solana-bundler-detector as a concentration metric.
        The formula is standard welfare economics (Gini 1912), not anyone's IP.

  * Coefficient of variation across wallet behaviour to expose coordination
        -- same project's "wallet similarity" heuristic. Bots produce
        suspiciously UNIFORM transaction sizes; humans produce ragged ones.
        Low variance across many wallets is evidence of one actor wearing
        many hats.

  * Round-number clustering as a bot signature
        -- a widely used heuristic: automated buyers submit 1.0 / 0.5 / 0.1
        SOL, while organic buyers submit 0.3271...

So this module reimplements the techniques from first principles, in our own
style, against our own schema, with our own UNKNOWN discipline. No code was
copied, so no license obligation is inherited -- and, more importantly, we
understand every line well enough to debug it.

DISCIPLINE
----------
Free Solana RPC will not serve holder lists, so most of the time these inputs
are simply absent. Every function here returns UNKNOWN rather than a
comfortable default when that happens. A concentration score of 0 for a token
we could not measure would be a lie that reads as safety.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Sequence

FORENSICS_VERSION = "AHOS-FORENSICS-v1"

# --- locked thresholds (pre-registered so results cannot be tuned later) ----
GINI_EXTREME = 0.90        # near-total concentration in a few wallets
GINI_HIGH = 0.80
GINI_MODERATE = 0.65
MIN_HOLDERS_FOR_GINI = 5   # below this, inequality metrics are meaningless

CV_COORDINATED = 0.25      # coefficient of variation below this => uniform => bot-like
MIN_WALLETS_FOR_CV = 6
ROUND_NUMBER_SHARE = 0.60  # share of round-value buys that implies automation
MIN_TXNS_FOR_ROUND = 8


@dataclass
class ForensicsReport:
    subject: str
    label: str                       # CLEAN | SUSPICIOUS | MANIPULATED | UNKNOWN
    gini: float | None = None
    gini_label: str = "UNKNOWN"
    holder_count: int | None = None
    top1_share_pct: float | None = None
    top10_share_pct: float | None = None
    coordination_cv: float | None = None
    coordination_suspected: bool = False
    round_number_share: float | None = None
    bot_pattern_suspected: bool = False
    risk_penalty: float = 0.0        # 0..50, mirrors WhaleTracker's scale
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    version: str = FORENSICS_VERSION
    computed_ts: float = 0.0

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------- primitives --

def gini_coefficient(values: Sequence[float]) -> float | None:
    """Gini over non-negative balances. 0 = perfect equality, 1 = one owner.

    Returns None when the input cannot support the statistic, rather than 0.0 --
    an empty holder list is 'unmeasured', which is the opposite of 'equal'.
    """
    vals = [float(v) for v in values if v is not None and float(v) >= 0.0]
    n = len(vals)
    if n < MIN_HOLDERS_FOR_GINI:
        return None
    total = sum(vals)
    if total <= 0:
        return None
    vals.sort()
    # Standard relative mean absolute difference formulation.
    cumulative = sum((i + 1) * v for i, v in enumerate(vals))
    return (2.0 * cumulative) / (n * total) - (n + 1.0) / n


def coefficient_of_variation(values: Sequence[float]) -> float | None:
    """CV = stdev / mean. Low CV across many wallets suggests one operator."""
    vals = [float(v) for v in values if v is not None]
    n = len(vals)
    if n < MIN_WALLETS_FOR_CV:
        return None
    mean = sum(vals) / n
    if mean == 0:
        return None
    var = sum((v - mean) ** 2 for v in vals) / n
    return math.sqrt(var) / abs(mean)


def round_number_share(values: Sequence[float], tolerance: float = 1e-9) -> float | None:
    """Share of values that land on suspiciously round amounts.

    Humans buy 0.3271 SOL. Bots buy 0.5, 1.0, 2.0. A high share is a signature
    of scripted participation rather than organic demand.
    """
    vals = [float(v) for v in values if v is not None and float(v) > 0]
    if len(vals) < MIN_TXNS_FOR_ROUND:
        return None
    round_hits = 0
    for v in vals:
        for step in (1.0, 0.5, 0.1):
            if abs(v / step - round(v / step)) < tolerance or \
                    abs((v % step)) < step * 1e-6:
                round_hits += 1
                break
    return round_hits / len(vals)


def parse_top_accounts(raw: Any) -> list[float]:
    """Extract balances from holder_snapshot.top_accounts_json, tolerantly.

    The stored shape has varied across collectors, so accept the plausible
    encodings and ignore what cannot be understood -- never guess a balance.
    """
    if raw is None:
        return []
    data = raw
    if isinstance(raw, (str, bytes)):
        try:
            data = json.loads(raw)
        except Exception:
            return []
    out: list[float] = []
    if isinstance(data, dict):
        data = data.get("accounts") or data.get("value") or list(data.values())
    if not isinstance(data, (list, tuple)):
        return []
    for item in data:
        if isinstance(item, (int, float)):
            out.append(float(item))
            continue
        if isinstance(item, dict):
            for key in ("amount", "uiAmount", "balance", "share", "uiAmountString"):
                v = item.get(key)
                if isinstance(v, dict):           # RPC nests uiAmount sometimes
                    v = v.get("uiAmount", v.get("amount"))
                try:
                    if v is not None:
                        out.append(float(v))
                        break
                except (TypeError, ValueError):
                    continue
    return [v for v in out if v >= 0]


# ----------------------------------------------------------------- analyzer --

class ForensicsAnalyzer:
    """Distribution and coordination forensics over whatever evidence exists."""

    def analyze(self, subject: str,
                holder_balances: Sequence[float] | None = None,
                buy_amounts: Sequence[float] | None = None,
                wallet_txn_counts: Sequence[float] | None = None,
                now: float | None = None) -> ForensicsReport:
        rep = ForensicsReport(subject=subject, label="UNKNOWN",
                              computed_ts=time.time() if now is None else now)

        balances = list(holder_balances or [])
        # --- concentration ---------------------------------------------------
        if balances:
            rep.holder_count = len(balances)
            g = gini_coefficient(balances)
            rep.gini = g
            if g is None:
                rep.unknowns.append(
                    f"تعداد دارندگان ({len(balances)}) برای محاسبه ضریب جینی کافی نیست")
            else:
                total = sum(balances)
                ordered = sorted(balances, reverse=True)
                if total > 0:
                    rep.top1_share_pct = ordered[0] / total * 100.0
                    rep.top10_share_pct = sum(ordered[:10]) / total * 100.0
                if g >= GINI_EXTREME:
                    rep.gini_label = "EXTREME"
                    rep.risk_penalty += 35.0
                    rep.warnings.append(
                        f"ضریب جینی {g:.2f} — مالکیت تقریباً کامل در دست چند کیف‌پول")
                elif g >= GINI_HIGH:
                    rep.gini_label = "HIGH"
                    rep.risk_penalty += 22.0
                    rep.warnings.append(f"ضریب جینی {g:.2f} — تمرکز مالکیت بالا")
                elif g >= GINI_MODERATE:
                    rep.gini_label = "MODERATE"
                    rep.risk_penalty += 10.0
                    rep.reasons.append(f"ضریب جینی {g:.2f} — تمرکز متوسط")
                else:
                    rep.gini_label = "DISTRIBUTED"
                    rep.reasons.append(f"ضریب جینی {g:.2f} — توزیع نسبتاً سالم")
        else:
            rep.unknowns.append(
                "فهرست دارندگان در دسترس نیست (RPC رایگان آن را ارائه نمی‌دهد)")

        # --- coordination among wallets --------------------------------------
        cv = coefficient_of_variation(wallet_txn_counts or [])
        rep.coordination_cv = cv
        if cv is None:
            if wallet_txn_counts:
                rep.unknowns.append("تعداد کیف‌پول‌ها برای سنجش هماهنگی کافی نیست")
        elif cv < CV_COORDINATED:
            rep.coordination_suspected = True
            rep.risk_penalty += 20.0
            rep.warnings.append(
                f"رفتار کیف‌پول‌ها بیش از حد یکنواخت است (CV={cv:.2f}) — "
                f"نشانه هماهنگی یا یک اپراتور با چند کیف‌پول")
        else:
            rep.reasons.append(f"پراکندگی رفتار کیف‌پول‌ها طبیعی است (CV={cv:.2f})")

        # --- automation signature --------------------------------------------
        rn = round_number_share(buy_amounts or [])
        rep.round_number_share = rn
        if rn is None:
            if buy_amounts:
                rep.unknowns.append("تعداد تراکنش‌ها برای تحلیل الگوی رُند کافی نیست")
        elif rn >= ROUND_NUMBER_SHARE:
            rep.bot_pattern_suspected = True
            rep.risk_penalty += 15.0
            rep.warnings.append(
                f"{rn:.0%} خریدها با مبالغ رُند انجام شده — الگوی ربات، نه تقاضای ارگانیک")
        else:
            rep.reasons.append(f"مبالغ خرید الگوی انسانی دارند ({rn:.0%} رُند)")

        rep.risk_penalty = min(rep.risk_penalty, 50.0)

        # --- verdict ----------------------------------------------------------
        measured = sum(x is not None for x in (rep.gini, cv, rn))
        if measured == 0:
            rep.label = "UNKNOWN"
            rep.unknowns.append("هیچ سنجه‌ای قابل محاسبه نبود — قضاوت ممکن نیست")
        elif rep.gini_label == "EXTREME" or (
                rep.coordination_suspected and rep.bot_pattern_suspected):
            rep.label = "MANIPULATED"
        elif rep.warnings:
            rep.label = "SUSPICIOUS"
        else:
            rep.label = "CLEAN"
        return rep

    # ------------------------------------------------------------ store I/O --

    def analyze_from_store(self, discovery, token_id: str, symbol: str = "UNKNOWN",
                           now: float | None = None) -> ForensicsReport:
        """Read the newest clean holder snapshot and analyze it. Read-only."""
        row = None
        try:
            row = discovery.execute(
                """SELECT top_accounts_json, top10_share, top20_share
                     FROM holder_snapshot
                    WHERE token_id = ? AND error_state IS NULL
                 ORDER BY ts DESC LIMIT 1""", (token_id,)).fetchone()
        except Exception:
            row = None

        if row is None:
            rep = ForensicsReport(
                subject=symbol, label="UNKNOWN",
                computed_ts=time.time() if now is None else now)
            rep.unknowns.append(
                "هیچ نمونه‌برداری سالمی از دارندگان ثبت نشده است")
            return rep

        balances = parse_top_accounts(row[0])
        rep = self.analyze(symbol, holder_balances=balances, now=now)
        # Trust the collector's own shares when we could not derive them.
        if rep.top10_share_pct is None and row[1] is not None:
            try:
                rep.top10_share_pct = float(row[1]) * 100.0 \
                    if float(row[1]) <= 1.0 else float(row[1])
            except (TypeError, ValueError):
                pass
        return rep
