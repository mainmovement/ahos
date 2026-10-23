"""M33 24-Step DEX Token Hunter Pipeline with Hard Safety Veto (Paper-Only).
Enforces all 24 institutional security, liquidity, holder, creator, and wash-trade checks,
plus the Two-Source Security Witness Law across free public sources (GoPlus, Honeypot.is,
DexScreener, GeckoTerminal, RugCheck). Paid sources (e.g. DEXTools paid tier) or any single
failing/unknown step immediately trigger VETO_UNSAFE.
Strictly PAPER_ONLY = True with zero live execution paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PAPER_ONLY: bool = True
LIVE_TRADING: bool = False

ALLOWED_FREE_SOURCES: frozenset[str] = frozenset(
    {"goplus", "honeypotis", "dexscreener", "geckoterminal", "rugcheck"}
)

_VETO_REASON_FA: dict[str, str] = {
    "01_free_source_policy": "سیاست منبع رایگان: منبع پولی یا ناشناخته رد شد",
    "02_two_source_security_witness": "قانون شاهد دومنبعی امنیتی: کمتر از دو منبع رایگان",
    "03_source_consensus_agreement": "عدم توافق منابع امنیتی (CONFLICT یا غیر PASS)",
    "04_contract_verified": "قرارداد هوشمند تأیید نشده",
    "05_no_honeypot_simulation": "شبیه‌سازی هانی‌پات ناموفق یا توکن تله",
    "06_mint_authority_renounced": "مرجع mint هنوز فعال است",
    "07_freeze_authority_disabled": "مرجع freeze هنوز فعال است",
    "08_no_blacklist_function": "تابع blacklist در قرارداد",
    "09_no_hidden_owner_or_proxy": "مالک پنهان یا پروکسی مشکوک",
    "10_buy_tax_within_cap": "مالیات خرید بالاتر از سقف",
    "11_sell_tax_within_cap": "مالیات فروش بالاتر از سقف",
    "12_tax_immutable": "مالیات قابل تغییر است",
    "13_lp_locked_or_burned_pct": "درصد LP قفل/سوزانده ناکافی",
    "14_lp_lock_duration_days": "مدت قفل LP ناکافی",
    "15_min_liquidity_usd": "نقدینگی USD زیر حداقل",
    "16_top10_holders_concentration": "تمرکز دارندگان top10 بیش از حد",
    "17_creator_balance_cap": "موجودی سازنده بیش از سقف",
    "18_creator_no_prior_rugs": "سابقه rug برای سازنده",
    "19_min_pair_age_hours": "عمر جفت معاملاتی کوتاه",
    "20_volume_to_liquidity_bounds": "نسبت حجم به نقدینگی غیرعادی",
    "21_wash_trade_wallet_diversity": "تنوع کیف پول یا شست‌وشوی معاملات مشکوک",
    "22_slippage_impact_cap": "اسلیپیج ۱k$ بالاتر از سقف",
    "23_oracle_reference_sanity": "مرجع قیمت / اوراکل نامعتبر",
    "24_paper_only_execution_lock": "قفل اجرای کاغذی نقض شد",
}


def format_veto_reasons_fa(veto_reasons: Sequence[str]) -> list[str]:
    """Deterministic Persian labels for M33 veto reason tokens (step_id:detail)."""
    out: list[str] = []
    for raw in veto_reasons:
        text = str(raw)
        step, detail = (text.split(":", 1) + [""])[:2] if ":" in text else (text, "")
        step = step.strip()
        label = _VETO_REASON_FA.get(step, f"رد مرحله {step}")
        out.append(f"{label} — {detail}" if detail else label)
    return out


STEP_NAMES_24: tuple[str, ...] = (
    "01_free_source_policy",
    "02_two_source_security_witness",
    "03_source_consensus_agreement",
    "04_contract_verified",
    "05_no_honeypot_simulation",
    "06_mint_authority_renounced",
    "07_freeze_authority_disabled",
    "08_no_blacklist_function",
    "09_no_hidden_owner_or_proxy",
    "10_buy_tax_within_cap",
    "11_sell_tax_within_cap",
    "12_tax_immutable",
    "13_lp_locked_or_burned_pct",
    "14_lp_lock_duration_days",
    "15_min_liquidity_usd",
    "16_top10_holders_concentration",
    "17_creator_balance_cap",
    "18_creator_no_prior_rugs",
    "19_min_pair_age_hours",
    "20_volume_to_liquidity_bounds",
    "21_wash_trade_wallet_diversity",
    "22_slippage_impact_cap",
    "23_oracle_reference_sanity",
    "24_paper_only_execution_lock",
)


@dataclass(frozen=True, slots=True)
class StepVerdict:
    step_id: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class TokenHunterVerdict:
    symbol: str
    chain: str
    contract_address: str
    state: str  # "PAPER_WATCH_ELIGIBLE" | "VETO_UNSAFE"
    veto_reasons: tuple[str, ...]
    steps_passed: int
    steps_total: int
    step_results: tuple[StepVerdict, ...]
    corroborated_sources: tuple[str, ...]
    paper_only: bool = True
    live: bool = False
    trades: bool = False


def evaluate_token_24_steps(candidate: Mapping[str, Any]) -> TokenHunterVerdict:
    """Run all 24 screening steps on a token candidate; any failure or unknown triggers VETO_UNSAFE."""
    symbol = str(candidate.get("symbol") or "UNKNOWN").upper()
    chain = str(candidate.get("chain") or "solana").lower()
    address = str(candidate.get("contract_address") or "0x0")

    raw_sources = [str(s).strip().lower() for s in (candidate.get("sources") or ())]
    paid_or_unknown = [s for s in raw_sources if s not in ALLOWED_FREE_SOURCES]
    free_sources = tuple(sorted({s for s in raw_sources if s in ALLOWED_FREE_SOURCES}))

    source_verdicts = candidate.get("source_verdicts") or {}
    agreed_safe = (
        len(free_sources) >= 2
        and all(str(source_verdicts.get(s, "UNKNOWN")).upper() == "PASS" for s in free_sources)
    )

    buy_tax = float(candidate.get("buy_tax_pct", 99.0))
    sell_tax = float(candidate.get("sell_tax_pct", 99.0))
    lp_locked_pct = float(candidate.get("lp_locked_pct", 0.0))
    lp_lock_days = float(candidate.get("lp_lock_days", 0.0))
    liquidity_usd = float(candidate.get("liquidity_usd", 0.0))
    top10_pct = float(candidate.get("top10_holders_pct", 100.0))
    creator_pct = float(candidate.get("creator_balance_pct", 100.0))
    pair_age_h = float(candidate.get("pair_age_hours", 0.0))
    vol_24h = float(candidate.get("volume_24h_usd", 0.0))
    unique_traders = int(candidate.get("unique_traders_24h", 0))
    slippage_bps = float(candidate.get("slippage_1k_bps", 9999.0))
    vol_liq_ratio = (vol_24h / liquidity_usd) if liquidity_usd > 0 else 999.0

    checks: list[tuple[str, bool, str]] = [
        (
            "01_free_source_policy",
            len(paid_or_unknown) == 0 and len(free_sources) > 0,
            "free_sources_only" if not paid_or_unknown else f"refused_sources:{','.join(paid_or_unknown)}",
        ),
        (
            "02_two_source_security_witness",
            len(free_sources) >= 2,
            f"sources={len(free_sources)}",
        ),
        (
            "03_source_consensus_agreement",
            agreed_safe,
            "all_sources_PASS" if agreed_safe else "source_conflict_or_non_pass",
        ),
        (
            "04_contract_verified",
            bool(candidate.get("contract_verified") is True),
            f"verified={candidate.get('contract_verified')}",
        ),
        (
            "05_no_honeypot_simulation",
            bool(candidate.get("is_honeypot") is False),
            f"is_honeypot={candidate.get('is_honeypot')}",
        ),
        (
            "06_mint_authority_renounced",
            bool(candidate.get("mint_renounced") is True),
            f"mint_renounced={candidate.get('mint_renounced')}",
        ),
        (
            "07_freeze_authority_disabled",
            bool(candidate.get("freeze_disabled") is True),
            f"freeze_disabled={candidate.get('freeze_disabled')}",
        ),
        (
            "08_no_blacklist_function",
            bool(candidate.get("has_blacklist") is False),
            f"has_blacklist={candidate.get('has_blacklist')}",
        ),
        (
            "09_no_hidden_owner_or_proxy",
            bool(candidate.get("hidden_owner_or_proxy") is False),
            f"hidden_owner_or_proxy={candidate.get('hidden_owner_or_proxy')}",
        ),
        (
            "10_buy_tax_within_cap",
            0.0 <= buy_tax <= 5.0,
            f"buy_tax_pct={buy_tax:.2f}",
        ),
        (
            "11_sell_tax_within_cap",
            0.0 <= sell_tax <= 5.0,
            f"sell_tax_pct={sell_tax:.2f}",
        ),
        (
            "12_tax_immutable",
            bool(candidate.get("tax_modifiable") is False),
            f"tax_modifiable={candidate.get('tax_modifiable')}",
        ),
        (
            "13_lp_locked_or_burned_pct",
            lp_locked_pct >= 95.0,
            f"lp_locked_pct={lp_locked_pct:.1f}",
        ),
        (
            "14_lp_lock_duration_days",
            lp_lock_days >= 180.0,
            f"lp_lock_days={lp_lock_days:.0f}",
        ),
        (
            "15_min_liquidity_usd",
            liquidity_usd >= 50_000.0,
            f"liquidity_usd={liquidity_usd:.0f}",
        ),
        (
            "16_top10_holders_concentration",
            top10_pct <= 30.0,
            f"top10_holders_pct={top10_pct:.1f}",
        ),
        (
            "17_creator_balance_cap",
            creator_pct <= 5.0,
            f"creator_balance_pct={creator_pct:.1f}",
        ),
        (
            "18_creator_no_prior_rugs",
            int(candidate.get("creator_prior_rugs", 99)) == 0,
            f"creator_prior_rugs={candidate.get('creator_prior_rugs')}",
        ),
        (
            "19_min_pair_age_hours",
            pair_age_h >= 24.0,
            f"pair_age_hours={pair_age_h:.1f}",
        ),
        (
            "20_volume_to_liquidity_bounds",
            0.1 <= vol_liq_ratio <= 15.0,
            f"vol_liq_ratio={vol_liq_ratio:.2f}",
        ),
        (
            "21_wash_trade_wallet_diversity",
            unique_traders >= 150 and bool(candidate.get("wash_trade_flag") is False),
            f"unique_traders={unique_traders},wash_flag={candidate.get('wash_trade_flag')}",
        ),
        (
            "22_slippage_impact_cap",
            slippage_bps <= 150.0,
            f"slippage_1k_bps={slippage_bps:.1f}",
        ),
        (
            "23_oracle_reference_sanity",
            bool(candidate.get("oracle_sanity_ok") is True),
            f"oracle_sanity_ok={candidate.get('oracle_sanity_ok')}",
        ),
        (
            "24_paper_only_execution_lock",
            PAPER_ONLY is True and bool(candidate.get("live_order_requested") is not True),
            "paper_only_locked",
        ),
    ]

    step_results = tuple(StepVerdict(step_id=sid, passed=ok, detail=det) for sid, ok, det in checks)
    vetoes = tuple(f"{s.step_id}:{s.detail}" for s in step_results if not s.passed)
    passed_count = sum(1 for s in step_results if s.passed)
    state = "PAPER_WATCH_ELIGIBLE" if len(vetoes) == 0 else "VETO_UNSAFE"

    return TokenHunterVerdict(
        symbol=symbol,
        chain=chain,
        contract_address=address,
        state=state,
        veto_reasons=vetoes,
        steps_passed=passed_count,
        steps_total=len(STEP_NAMES_24),
        step_results=step_results,
        corroborated_sources=free_sources,
        paper_only=True,
        live=False,
        trades=False,
    )


def default_token_hunter_fixtures() -> list[dict[str, Any]]:
    """Canonical screening fixtures demonstrating 24/24 PASS paper-watch vs hard safety vetoes."""
    return [
        {
            "symbol": "AERO",
            "chain": "base",
            "contract_address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
            "sources": ["goplus", "dexscreener", "geckoterminal"],
            "source_verdicts": {"goplus": "PASS", "dexscreener": "PASS", "geckoterminal": "PASS"},
            "contract_verified": True,
            "is_honeypot": False,
            "mint_renounced": True,
            "freeze_disabled": True,
            "has_blacklist": False,
            "hidden_owner_or_proxy": False,
            "buy_tax_pct": 0.0,
            "sell_tax_pct": 0.0,
            "tax_modifiable": False,
            "lp_locked_pct": 99.5,
            "lp_lock_days": 730.0,
            "liquidity_usd": 42_500_000.0,
            "top10_holders_pct": 18.4,
            "creator_balance_pct": 0.8,
            "creator_prior_rugs": 0,
            "pair_age_hours": 4200.0,
            "volume_24h_usd": 18_200_000.0,
            "unique_traders_24h": 4120,
            "wash_trade_flag": False,
            "slippage_1k_bps": 18.0,
            "oracle_sanity_ok": True,
            "live_order_requested": False,
        },
        {
            "symbol": "JUP",
            "chain": "solana",
            "contract_address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "sources": ["rugcheck", "dexscreener", "geckoterminal"],
            "source_verdicts": {"rugcheck": "PASS", "dexscreener": "PASS", "geckoterminal": "PASS"},
            "contract_verified": True,
            "is_honeypot": False,
            "mint_renounced": True,
            "freeze_disabled": True,
            "has_blacklist": False,
            "hidden_owner_or_proxy": False,
            "buy_tax_pct": 0.0,
            "sell_tax_pct": 0.0,
            "tax_modifiable": False,
            "lp_locked_pct": 98.2,
            "lp_lock_days": 365.0,
            "liquidity_usd": 28_900_000.0,
            "top10_holders_pct": 22.1,
            "creator_balance_pct": 1.5,
            "creator_prior_rugs": 0,
            "pair_age_hours": 5100.0,
            "volume_24h_usd": 24_600_000.0,
            "unique_traders_24h": 6850,
            "wash_trade_flag": False,
            "slippage_1k_bps": 22.0,
            "oracle_sanity_ok": True,
            "live_order_requested": False,
        },
        {
            "symbol": "RUGMEME",
            "chain": "ethereum",
            "contract_address": "0xdead00000000000000000000000000000000beef",
            "sources": ["goplus", "honeypotis"],
            "source_verdicts": {"goplus": "FAIL", "honeypotis": "PASS"},
            "contract_verified": False,
            "is_honeypot": True,
            "mint_renounced": False,
            "freeze_disabled": False,
            "has_blacklist": True,
            "hidden_owner_or_proxy": True,
            "buy_tax_pct": 12.0,
            "sell_tax_pct": 45.0,
            "tax_modifiable": True,
            "lp_locked_pct": 10.0,
            "lp_lock_days": 7.0,
            "liquidity_usd": 12_000.0,
            "top10_holders_pct": 78.5,
            "creator_balance_pct": 35.0,
            "creator_prior_rugs": 3,
            "pair_age_hours": 2.5,
            "volume_24h_usd": 950_000.0,
            "unique_traders_24h": 14,
            "wash_trade_flag": True,
            "slippage_1k_bps": 850.0,
            "oracle_sanity_ok": False,
            "live_order_requested": False,
        },
        {
            "symbol": "SINGLE_SRC_TOKEN",
            "chain": "arbitrum",
            "contract_address": "0x1111222233334444555566667777888899990000",
            "sources": ["dexscreener"],
            "source_verdicts": {"dexscreener": "PASS"},
            "contract_verified": True,
            "is_honeypot": False,
            "mint_renounced": True,
            "freeze_disabled": True,
            "has_blacklist": False,
            "hidden_owner_or_proxy": False,
            "buy_tax_pct": 0.5,
            "sell_tax_pct": 0.5,
            "tax_modifiable": False,
            "lp_locked_pct": 99.0,
            "lp_lock_days": 365.0,
            "liquidity_usd": 120_000.0,
            "top10_holders_pct": 21.0,
            "creator_balance_pct": 1.0,
            "creator_prior_rugs": 0,
            "pair_age_hours": 120.0,
            "volume_24h_usd": 85_000.0,
            "unique_traders_24h": 310,
            "wash_trade_flag": False,
            "slippage_1k_bps": 45.0,
            "oracle_sanity_ok": True,
            "live_order_requested": False,
        },
    ]


def screen_token_batch(candidates: Sequence[Mapping[str, Any]] | None = None) -> list[TokenHunterVerdict]:
    rows = candidates if candidates is not None else default_token_hunter_fixtures()
    return [evaluate_token_24_steps(c) for c in rows]
