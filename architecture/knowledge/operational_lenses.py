#!/usr/bin/env python3
"""AHOS Operational Expert Lenses — ROLE frameworks, not person impersonation.

The historical-thinker data cards in `lenses.py` stay as an epistemic library.
This module is the *operational* council surface the vision asked for:

    Market Analyst, Quant, Risk Manager, Security Auditor, Smart Money Analyst,
    On-chain Analyst, Tokenomics Analyst, News Analyst, Social Analyst,
    Narrative Analyst, Macro Analyst, Contrarian, Bull, Bear, Fraud Hunter,
    Exitability Specialist, Data Quality Auditor, Adversarial Reviewer,
    Historian, Arbitrator

Laws
----
  * DATA CARDS / ROLE MANDATES only — never conversational personas.
  * Advisory: a lens never DECIDES and never writes a trade order.
  * Missing required evidence ⇒ ABSTAIN / UNKNOWN, never a fabricated veto
    or a fabricated confirm. False-on-missing is forbidden.
  * Extensible: register extra lenses without a parallel subsystem.
  * Disagreement is preserved; no averaging of verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Iterable

from ..intelligence.evidence import (
    EvidenceBundle,
    bool_value,
    numeric_value,
    require_evidence_bundle,
    text_value,
)

VERDICTS = ("SUPPORT", "CAUTION", "VETO", "ABSTAIN", "UNKNOWN")


@dataclass(frozen=True)
class OperationalLens:
    lens_id: str
    role: str
    mandate: str
    questions: tuple[str, ...]
    required_evidence_keys: tuple[str, ...]
    documented_failures: tuple[str, ...]
    domain: str
    version: str = "1.0.0"


@dataclass
class LensOpinion:
    lens_id: str
    role: str
    verdict: str
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    confidence: str = "UNKNOWN"          # OBSERVED | DERIVED | UNKNOWN

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _missing(bundle: EvidenceBundle, keys: Iterable[str]) -> list[str]:
    out: list[str] = []
    for k in keys:
        item = bundle.get(k)
        if item is None or not item.is_known():
            out.append(k)
    return out


def _opinion(lens: OperationalLens, verdict: str, rationale: str,
             refs: list[str], unknowns: list[str],
             confidence: str) -> LensOpinion:
    if verdict not in VERDICTS:
        raise ValueError(f"invalid verdict {verdict!r}")
    return LensOpinion(
        lens_id=lens.lens_id, role=lens.role, verdict=verdict,
        rationale=rationale, evidence_refs=refs, unknowns=unknowns,
        confidence=confidence,
    )


def _abstain(lens: OperationalLens, missing: list[str]) -> LensOpinion:
    return _opinion(
        lens, "ABSTAIN",
        f"required evidence missing: {', '.join(missing)} — UNKNOWN, not a verdict",
        [], missing, "UNKNOWN",
    )


# ---- evaluators (pure functions of EvidenceBundle) -------------------------

def _eval_market_analyst(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    miss = _missing(b, lens.required_evidence_keys)
    if miss:
        return _abstain(lens, miss)
    liq = numeric_value(b.get("liquidity_usd"))
    vol = numeric_value(b.get("volume_1h"))
    refs = ["liquidity_usd", "volume_1h"]
    if liq is not None and liq >= 10000 and vol is not None and vol >= 5000:
        return _opinion(lens, "SUPPORT",
                        f"tradable depth (${liq:,.0f}) with active 1h volume (${vol:,.0f})",
                        refs, [], "OBSERVED")
    if liq is not None and liq < 2000:
        return _opinion(lens, "CAUTION", "thin book — market structure is fragile",
                        refs, [], "OBSERVED")
    return _opinion(lens, "CAUTION", "depth/volume present but not a strong tape",
                    refs, [], "OBSERVED")


def _eval_quant(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    miss = _missing(b, ("volume_1h",))
    # Quant abstains rather than inventing a probability.
    vel = numeric_value(b.get("volume_velocity"))
    buys = numeric_value(b.get("txns_1h_buys"))
    sells = numeric_value(b.get("txns_1h_sells"))
    if vel is None and (buys is None or sells is None):
        return _abstain(lens, miss + ["volume_velocity", "txns_1h_buys", "txns_1h_sells"])
    reasons = []
    if vel is not None and vel >= 8:
        reasons.append(f"extreme volume velocity {vel:.1f}x (manipulation watch)")
        return _opinion(lens, "CAUTION", "; ".join(reasons),
                        ["volume_velocity"], [], "OBSERVED")
    if buys is not None and sells is not None:
        total = buys + sells
        if total > 20 and buys / total < 0.45:
            return _opinion(lens, "CAUTION", "sell-side transaction dominance",
                            ["txns_1h_buys", "txns_1h_sells"], [], "OBSERVED")
    return _opinion(lens, "ABSTAIN",
                    "no calibrated probability is claimed; score remains a score",
                    [], ["calibrated_probability"], "UNKNOWN")


def _eval_risk(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    hp = bool_value(b.get("is_honeypot"))
    liq = numeric_value(b.get("liquidity_usd"))
    if hp is True:
        return _opinion(lens, "VETO", "honeypot observed — ruin path open",
                        ["is_honeypot"], [], "OBSERVED")
    unknowns = []
    if hp is None:
        unknowns.append("is_honeypot")
    if liq is None:
        unknowns.append("liquidity_usd")
    if unknowns:
        return _abstain(lens, unknowns)
    if liq is not None and liq < 2000:
        return _opinion(lens, "VETO", "liquidity below trapped-capital floor",
                        ["liquidity_usd"], [], "OBSERVED")
    return _opinion(lens, "CAUTION", "no hard ruin flag in observed risk fields",
                    ["is_honeypot", "liquidity_usd"], [], "OBSERVED")


def _eval_security(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    hp = bool_value(b.get("is_honeypot"))
    mint = bool_value(b.get("has_mint_authority"))
    freeze = bool_value(b.get("has_freeze_authority"))
    if hp is True:
        return _opinion(lens, "VETO", "honeypot = True", ["is_honeypot"], [], "OBSERVED")
    if mint is True or freeze is True:
        return _opinion(lens, "VETO", "mint/freeze authority still active",
                        [k for k, v in (("has_mint_authority", mint),
                                        ("has_freeze_authority", freeze)) if v is True],
                        [], "OBSERVED")
    missing = [k for k, v in (("is_honeypot", hp), ("has_mint_authority", mint),
                              ("has_freeze_authority", freeze)) if v is None]
    if missing:
        return _abstain(lens, missing)
    return _opinion(lens, "SUPPORT", "hard security flags observed-clear",
                    ["is_honeypot", "has_mint_authority", "has_freeze_authority"],
                    [], "OBSERVED")


def _eval_smart_money(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    label = text_value(b.get("whale_label"))
    flow = numeric_value(b.get("whale_net_flow_1h")) or numeric_value(b.get("whale_net_flow_observed"))
    if label is None and flow is None:
        return _abstain(lens, ["whale_label", "whale_net_flow_1h"])
    if label and label.upper() in ("DISTRIBUTION", "EXITING", "DUMP"):
        return _opinion(lens, "CAUTION", f"whale label={label}",
                        ["whale_label"], [], "DERIVED")
    return _opinion(lens, "ABSTAIN",
                    "wallet classification without identity evidence is refused",
                    ["whale_label"] if label else [],
                    ["wallet_identity"] if label else ["whale_label"],
                    "UNKNOWN")


def _eval_onchain(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    buys = numeric_value(b.get("txns_1h_buys"))
    sells = numeric_value(b.get("txns_1h_sells"))
    if buys is None or sells is None:
        return _abstain(lens, ["txns_1h_buys", "txns_1h_sells"])
    total = buys + sells
    if total < 10:
        return _opinion(lens, "ABSTAIN", f"sample too small ({total} txns)",
                        ["txns_1h_buys", "txns_1h_sells"], ["sample_size"], "OBSERVED")
    ratio = buys / total
    if ratio >= 0.65:
        return _opinion(lens, "SUPPORT", f"buy share {ratio:.0%}",
                        ["txns_1h_buys", "txns_1h_sells"], [], "OBSERVED")
    if ratio < 0.45:
        return _opinion(lens, "CAUTION", f"sell share {1-ratio:.0%}",
                        ["txns_1h_buys", "txns_1h_sells"], [], "OBSERVED")
    return _opinion(lens, "ABSTAIN", "balanced tape — no directional claim",
                    ["txns_1h_buys", "txns_1h_sells"], [], "OBSERVED")


def _eval_tokenomics(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    mint = bool_value(b.get("has_mint_authority"))
    conc = numeric_value(b.get("top10_concentration"))
    if mint is None and conc is None:
        return _abstain(lens, ["has_mint_authority", "top10_concentration"])
    if mint is True:
        return _opinion(lens, "VETO", "uncapped mint authority",
                        ["has_mint_authority"], [], "OBSERVED")
    if conc is not None and conc >= 50:
        return _opinion(lens, "CAUTION", f"top-10 concentration {conc:.0f}%",
                        ["top10_concentration"], [], "OBSERVED")
    unknowns = [k for k, v in (("has_mint_authority", mint),
                               ("top10_concentration", conc)) if v is None]
    return _opinion(lens, "CAUTION" if unknowns else "SUPPORT",
                    "observed tokenomics flags",
                    [k for k in ("has_mint_authority", "top10_concentration")
                     if b.get(k) and b.get(k).is_known()],
                    unknowns, "OBSERVED" if not unknowns else "UNKNOWN")


def _eval_news(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    label = text_value(b.get("narrative_label"))
    if label is None or label == "UNKNOWN":
        return _abstain(lens, ["narrative_label"])
    if label == "BEARISH":
        return _opinion(lens, "CAUTION", "bearish narrative evidence",
                        ["narrative_label"], [], "DERIVED")
    return _opinion(lens, "ABSTAIN",
                    f"narrative={label}; news cannot create an opportunity",
                    ["narrative_label"], [], "DERIVED")


def _eval_social(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    viral = text_value(b.get("virality_label"))
    social = b.get("social_presence")
    if (viral is None or viral == "UNKNOWN") and (social is None or not social.is_known()):
        return _abstain(lens, ["virality_label", "social_presence"])
    if viral and viral.upper() == "VIRAL":
        return _opinion(lens, "CAUTION",
                        "viral attention is not organic-demand proof",
                        ["virality_label"], [], "DERIVED")
    return _opinion(lens, "ABSTAIN",
                    "social evidence present but cannot justify selection",
                    ["virality_label"] if viral else ["social_presence"],
                    [], "DERIVED")


def _eval_narrative(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    return _eval_news(lens, b)


def _eval_macro(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    # Macro regime is not persisted at scoring time (calibration honesty).
    return _abstain(lens, ["macro_regime"])


def _eval_contrarian(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    viral = text_value(b.get("virality_label"))
    vol = numeric_value(b.get("volume_1h"))
    liq = numeric_value(b.get("liquidity_usd"))
    if viral and viral.upper() == "VIRAL" and vol is not None and liq is not None and vol > 5 * max(liq, 1):
        return _opinion(lens, "CAUTION",
                        "crowd is loud relative to depth — second-level caution",
                        ["virality_label", "volume_1h", "liquidity_usd"], [], "DERIVED")
    if viral is None and vol is None:
        return _abstain(lens, ["virality_label", "volume_1h"])
    return _opinion(lens, "ABSTAIN", "no crowd-extremes observed",
                    [], [], "UNKNOWN")


def _eval_bull(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    """Bull lens is a challenge slot, not a cheerleader. Needs evidence."""
    liq = numeric_value(b.get("liquidity_usd"))
    vol = numeric_value(b.get("volume_1h"))
    hp = bool_value(b.get("is_honeypot"))
    if hp is True:
        return _opinion(lens, "ABSTAIN", "bull slot yields to security veto",
                        ["is_honeypot"], [], "OBSERVED")
    if liq is None or vol is None:
        return _abstain(lens, [k for k, v in (("liquidity_usd", liq), ("volume_1h", vol)) if v is None])
    if liq >= 50000 and vol >= 25000 and hp is False:
        return _opinion(lens, "SUPPORT", "depth + volume + honeypot-clear (bull case)",
                        ["liquidity_usd", "volume_1h", "is_honeypot"], [], "OBSERVED")
    return _opinion(lens, "ABSTAIN", "bull case not evidenced",
                    ["liquidity_usd", "volume_1h"], [], "OBSERVED")


def _eval_bear(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    hp = bool_value(b.get("is_honeypot"))
    wash = bool_value(b.get("wash_suspected"))
    if hp is True or wash is True:
        return _opinion(lens, "VETO" if hp is True else "CAUTION",
                        "bear case evidenced by security/wash flags",
                        [k for k, v in (("is_honeypot", hp), ("wash_suspected", wash)) if v is True],
                        [], "OBSERVED")
    conc = numeric_value(b.get("top10_concentration"))
    if conc is not None and conc >= 60:
        return _opinion(lens, "CAUTION", f"holder concentration {conc:.0f}%",
                        ["top10_concentration"], [], "OBSERVED")
    missing = [k for k, v in (("is_honeypot", hp), ("wash_suspected", wash),
                              ("top10_concentration", conc)) if v is None]
    if len(missing) == 3:
        return _abstain(lens, missing)
    return _opinion(lens, "ABSTAIN", "no bear evidence observed",
                    [], missing, "UNKNOWN")


def _eval_fraud(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    hp = bool_value(b.get("is_honeypot"))
    rugs = numeric_value(b.get("deployer_past_rug_count"))
    wash = bool_value(b.get("wash_suspected"))
    if hp is True or (rugs is not None and rugs >= 1):
        return _opinion(lens, "VETO", "fraud indicators observed",
                        [k for k, v in (("is_honeypot", hp),
                                        ("deployer_past_rug_count", rugs is not None and rugs >= 1))
                         if v],
                        [], "OBSERVED")
    if wash is True:
        return _opinion(lens, "CAUTION", "wash-trading suspected",
                        ["wash_suspected"], [], "DERIVED")
    missing = [k for k, v in (("is_honeypot", hp),
                              ("deployer_past_rug_count", rugs),
                              ("wash_suspected", wash)) if v is None]
    if missing:
        return _abstain(lens, missing)
    return _opinion(lens, "ABSTAIN", "no fraud indicator observed (not a clean bill)",
                    ["is_honeypot"], [], "OBSERVED")


def _eval_exit(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    verdict = text_value(b.get("exit_verdict"))
    frac = numeric_value(b.get("realizable_fraction"))
    if verdict is None and frac is None:
        # Fall back to liquidity as a weak proxy, but label it UNKNOWN confidence
        liq = numeric_value(b.get("liquidity_usd"))
        if liq is None:
            return _abstain(lens, ["exit_verdict", "realizable_fraction", "liquidity_usd"])
        if liq < 2000:
            return _opinion(lens, "VETO",
                            "no exitability report; liquidity below $2k (proxy, not a measurement)",
                            ["liquidity_usd"], ["exit_verdict"], "UNKNOWN")
        return _opinion(lens, "ABSTAIN",
                        "exitability not measured; liquidity is not an exit proof",
                        ["liquidity_usd"], ["exit_verdict"], "UNKNOWN")
    if verdict in ("UNEXITABLE", "TRAPPED") or (frac is not None and frac < 0.2):
        return _opinion(lens, "VETO", f"exit_verdict={verdict} realizable={frac}",
                        [k for k in ("exit_verdict", "realizable_fraction") if b.get(k)],
                        [], "DERIVED")
    if verdict == "EXITABLE" or (frac is not None and frac >= 0.7):
        return _opinion(lens, "SUPPORT", "exit path evidenced",
                        [k for k in ("exit_verdict", "realizable_fraction") if b.get(k)],
                        [], "DERIVED")
    return _opinion(lens, "CAUTION", "partial / unknown exit quality",
                    [k for k in ("exit_verdict", "realizable_fraction") if b.get(k)],
                    [], "DERIVED")


def _eval_data_quality(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    required = ("liquidity_usd", "volume_1h", "is_honeypot", "top10_concentration")
    missing = _missing(b, required)
    if not missing:
        return _opinion(lens, "SUPPORT", "canonical four evidence keys present",
                        list(required), [], "OBSERVED")
    if len(missing) >= 3:
        return _opinion(lens, "CAUTION",
                        f"{len(missing)}/4 canonical keys UNKNOWN — do not over-interpret",
                        [], missing, "OBSERVED")
    return _opinion(lens, "CAUTION", f"partial canonical coverage; missing {missing}",
                    [k for k in required if k not in missing], missing, "OBSERVED")


def _eval_adversarial(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    hp = bool_value(b.get("is_honeypot"))
    wash = bool_value(b.get("wash_suspected"))
    paid = bool_value(b.get("is_paid_promotion"))
    viral = text_value(b.get("virality_label"))
    if hp is True:
        return _opinion(lens, "VETO", "adversarial: honeypot",
                        ["is_honeypot"], [], "OBSERVED")
    if viral and viral.upper() in ("VIRAL", "BUILDING") and (wash is True or paid is True):
        return _opinion(lens, "VETO", "adversarial: manufactured hype",
                        ["virality_label"] + [k for k, v in (("wash_suspected", wash),
                                                             ("is_paid_promotion", paid)) if v],
                        [], "DERIVED")
    if viral and viral.upper() == "VIRAL" and hp is None:
        return _opinion(lens, "CAUTION",
                        "adversarial: virality with UNKNOWN honeypot",
                        ["virality_label"], ["is_honeypot"], "DERIVED")
    return _opinion(lens, "ABSTAIN", "no adversarial pattern evidenced",
                    [], [k for k, v in (("is_honeypot", hp), ("wash_suspected", wash)) if v is None],
                    "UNKNOWN")


def _eval_historian(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    created = numeric_value(b.get("pair_created_ts"))
    rugs = numeric_value(b.get("deployer_past_rug_count"))
    if created is None and rugs is None:
        return _abstain(lens, ["pair_created_ts", "deployer_past_rug_count"])
    if rugs is not None and rugs >= 1:
        return _opinion(lens, "VETO", f"deployer prior rugs={rugs}",
                        ["deployer_past_rug_count"], [], "OBSERVED")
    return _opinion(lens, "ABSTAIN", "history incomplete — no clean-bill claim",
                    ["pair_created_ts"] if created is not None else [],
                    ["deployer_past_rug_count"] if rugs is None else [],
                    "UNKNOWN")


def _eval_arbitrator(lens: OperationalLens, b: EvidenceBundle) -> LensOpinion:
    """Arbitrator does not vote; it only records that arbitration is downstream."""
    return _opinion(lens, "ABSTAIN",
                    "arbitration is a later council stage; this lens does not vote",
                    [], ["council_disagreement"], "UNKNOWN")


EVALUATORS: dict[str, Callable[[OperationalLens, EvidenceBundle], LensOpinion]] = {
    "LENS-ROLE-MARKET-ANALYST": _eval_market_analyst,
    "LENS-ROLE-QUANT": _eval_quant,
    "LENS-ROLE-RISK-MANAGER": _eval_risk,
    "LENS-ROLE-SECURITY-AUDITOR": _eval_security,
    "LENS-ROLE-SMART-MONEY": _eval_smart_money,
    "LENS-ROLE-ONCHAIN": _eval_onchain,
    "LENS-ROLE-TOKENOMICS": _eval_tokenomics,
    "LENS-ROLE-NEWS": _eval_news,
    "LENS-ROLE-SOCIAL": _eval_social,
    "LENS-ROLE-NARRATIVE": _eval_narrative,
    "LENS-ROLE-MACRO": _eval_macro,
    "LENS-ROLE-CONTRARIAN": _eval_contrarian,
    "LENS-ROLE-BULL": _eval_bull,
    "LENS-ROLE-BEAR": _eval_bear,
    "LENS-ROLE-FRAUD-HUNTER": _eval_fraud,
    "LENS-ROLE-EXITABILITY": _eval_exit,
    "LENS-ROLE-DATA-QUALITY": _eval_data_quality,
    "LENS-ROLE-ADVERSARIAL": _eval_adversarial,
    "LENS-ROLE-HISTORIAN": _eval_historian,
    "LENS-ROLE-ARBITRATOR": _eval_arbitrator,
}


def _card(lens_id: str, role: str, mandate: str, questions: tuple[str, ...],
          required: tuple[str, ...], failures: tuple[str, ...],
          domain: str) -> OperationalLens:
    return OperationalLens(
        lens_id=lens_id, role=role, mandate=mandate, questions=questions,
        required_evidence_keys=required, documented_failures=failures, domain=domain,
    )


OPERATIONAL_LENS_REGISTRY: dict[str, OperationalLens] = {
    "LENS-ROLE-MARKET-ANALYST": _card(
        "LENS-ROLE-MARKET-ANALYST", "Market Analyst",
        "Read tape quality (depth, volume) without predicting price.",
        ("Is the book deep enough to be a market?", "Is 1h volume real activity?"),
        ("liquidity_usd", "volume_1h"),
        ("Cannot see hidden liquidity or off-DEX inventory.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-QUANT": _card(
        "LENS-ROLE-QUANT", "Quant",
        "Refuse probability claims until calibration evidence exists.",
        ("Is there a calibrated probability, or only a score?",),
        ("volume_1h",),
        ("Without outcomes, any p-value is a costume.",),
        "MATHEMATICS",
    ),
    "LENS-ROLE-RISK-MANAGER": _card(
        "LENS-ROLE-RISK-MANAGER", "Risk Manager",
        "Ruin first. Veto honeypots and trapped-capital setups.",
        ("Can this position ruin the book?",),
        ("is_honeypot", "liquidity_usd"),
        ("Unknown honeypot is not 'safe'.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-SECURITY-AUDITOR": _card(
        "LENS-ROLE-SECURITY-AUDITOR", "Security Auditor",
        "Hard contract flags: honeypot, mint, freeze. UNKNOWN ≠ PASS.",
        ("Is the contract a trap?", "Can supply be inflated?"),
        ("is_honeypot",),
        ("Bytecode not disassembled here; relies on provider security atoms.",),
        "CYBERSECURITY",
    ),
    "LENS-ROLE-SMART-MONEY": _card(
        "LENS-ROLE-SMART-MONEY", "Smart Money Analyst",
        "Wallet labels require evidence. No classification without identity.",
        ("Is this whale, smart money, insider, deployer, LP, or MM?",),
        ("whale_label",),
        ("Cluster labels without clustering evidence are rejected.",),
        "ON_CHAIN_ANALYTICS",
    ),
    "LENS-ROLE-ONCHAIN": _card(
        "LENS-ROLE-ONCHAIN", "On-chain Analyst",
        "Transaction tape only. Small samples abstain.",
        ("What is the observed buy/sell tape?",),
        ("txns_1h_buys", "txns_1h_sells"),
        ("Counts ≠ unique wallets.",),
        "ON_CHAIN_ANALYTICS",
    ),
    "LENS-ROLE-TOKENOMICS": _card(
        "LENS-ROLE-TOKENOMICS", "Tokenomics Analyst",
        "Mint authority and holder concentration. No FDV fiction.",
        ("Can supply change?", "Who holds the float?"),
        ("has_mint_authority", "top10_concentration"),
        ("FDV/market-cap often UNKNOWN on new pairs — not invented.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-NEWS": _card(
        "LENS-ROLE-NEWS", "News Analyst",
        "Narrative is evidence, never proof.",
        ("Is there matching headline coverage?",),
        ("narrative_label",),
        ("Lexicon sentiment is coarse; sarcasm is invisible.",),
        "BEHAVIORAL_ECONOMICS",
    ),
    "LENS-ROLE-SOCIAL": _card(
        "LENS-ROLE-SOCIAL", "Social Analyst",
        "Attention ≠ demand. Social cannot create SELECT.",
        ("Is attention observed, and is it organic?",),
        ("virality_label",),
        ("Most social platforms are COST_BLOCKED / OUT_OF_POLICY.",),
        "BEHAVIORAL_ECONOMICS",
    ),
    "LENS-ROLE-NARRATIVE": _card(
        "LENS-ROLE-NARRATIVE", "Narrative Analyst",
        "Story coherence across headlines. Still not a buy signal.",
        ("What story is being told, with what evidence?",),
        ("narrative_label",),
        ("Single-source narrative is monoculture.",),
        "BEHAVIORAL_ECONOMICS",
    ),
    "LENS-ROLE-MACRO": _card(
        "LENS-ROLE-MACRO", "Macro Analyst",
        "Regime-dependence. Honest ABSTAIN until a regime atom exists.",
        ("What macro/crypto regime are we in?",),
        ("macro_regime",),
        ("Opportunity-type / market-regime not persisted at prediction time.",),
        "COMPLEX_SYSTEMS",
    ),
    "LENS-ROLE-CONTRARIAN": _card(
        "LENS-ROLE-CONTRARIAN", "Contrarian",
        "Mandatory challenge slot: crowd extremes vs depth.",
        ("If everyone is already in, what is left?",),
        ("volume_1h",),
        ("Contrarian ≠ automatically short.",),
        "BEHAVIORAL_ECONOMICS",
    ),
    "LENS-ROLE-BULL": _card(
        "LENS-ROLE-BULL", "Bull",
        "State the long case only from observed depth/volume/security.",
        ("What is the evidenced upside case?",),
        ("liquidity_usd", "volume_1h"),
        ("Bull without security clearance is fan fiction.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-BEAR": _card(
        "LENS-ROLE-BEAR", "Bear",
        "State the short/avoid case from observed traps and concentration.",
        ("What is the evidenced downside case?",),
        ("is_honeypot",),
        ("Bear without data is mood.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-FRAUD-HUNTER": _card(
        "LENS-ROLE-FRAUD-HUNTER", "Fraud Hunter",
        "Honeypot, deployer rugs, wash. No clean-bill from silence.",
        ("Are there fraud fingerprints?",),
        ("is_honeypot",),
        ("Absence of a flag is not innocence.",),
        "CYBERSECURITY",
    ),
    "LENS-ROLE-EXITABILITY": _card(
        "LENS-ROLE-EXITABILITY", "Exitability Specialist",
        "If I buy, can I get out? Liquidity is a proxy, not a proof.",
        ("What fraction is realizable?",),
        ("exit_verdict",),
        ("No on-chain sell simulation is run here.",),
        "MARKET_MICROSTRUCTURE",
    ),
    "LENS-ROLE-DATA-QUALITY": _card(
        "LENS-ROLE-DATA-QUALITY", "Data Quality Auditor",
        "Canonical evidence completeness. UNKNOWN growth is a finding.",
        ("Which of the four canonical atoms are actually known?",),
        ("liquidity_usd",),
        ("Does not judge provider honesty beyond presence.",),
        "INFORMATION_THEORY",
    ),
    "LENS-ROLE-ADVERSARIAL": _card(
        "LENS-ROLE-ADVERSARIAL", "Adversarial Reviewer",
        "Assume the other side is extracting. Manufactured hype → VETO.",
        ("What would a rugger want me to believe?",),
        ("is_honeypot",),
        ("Cannot see private chat coordination.",),
        "GAME_THEORY",
    ),
    "LENS-ROLE-HISTORIAN": _card(
        "LENS-ROLE-HISTORIAN", "Historian",
        "Deployer past and pair age. No history → no clean bill.",
        ("Has this deployer done this before?",),
        ("deployer_past_rug_count",),
        ("New wallets have empty history, which is not innocence.",),
        "ON_CHAIN_ANALYTICS",
    ),
    "LENS-ROLE-ARBITRATOR": _card(
        "LENS-ROLE-ARBITRATOR", "Arbitrator",
        "Does not vote. Records that disagreement is a first-class verdict.",
        ("Where do the lenses conflict?",),
        (),
        ("Arbitration without a council transcript is empty.",),
        "INFORMATION_THEORY",
    ),
}


class OperationalLensLibrary:
    """Role-lens registry + deterministic deliberation over EvidenceBundle."""

    def __init__(self, lenses: dict[str, OperationalLens] | None = None):
        self._lenses = dict(lenses or OPERATIONAL_LENS_REGISTRY)

    def register(self, lens: OperationalLens,
                 evaluator: Callable[[OperationalLens, EvidenceBundle], LensOpinion] | None = None) -> None:
        """Extension point: add a lens without a parallel subsystem."""
        self._lenses[lens.lens_id] = lens
        if evaluator is not None:
            EVALUATORS[lens.lens_id] = evaluator

    def list_lenses(self) -> list[OperationalLens]:
        return [self._lenses[k] for k in sorted(self._lenses)]

    def get(self, lens_id: str) -> OperationalLens | None:
        return self._lenses.get(lens_id)

    def deliberate(self, evidence: EvidenceBundle) -> list[LensOpinion]:
        require_evidence_bundle(evidence, "OperationalLensLibrary.deliberate")
        opinions: list[LensOpinion] = []
        for lens_id in sorted(self._lenses):
            lens = self._lenses[lens_id]
            fn = EVALUATORS.get(lens_id)
            if fn is None:
                opinions.append(_abstain(lens, ["no_evaluator"]))
                continue
            opinions.append(fn(lens, evidence))
        return opinions

    def synthesize(self, opinions: list[LensOpinion]) -> dict[str, Any]:
        """Preserve disagreement. Never average. Never decide."""
        by = {v: [o.lens_id for o in opinions if o.verdict == v] for v in VERDICTS}
        vetoes = by["VETO"]
        supports = by["SUPPORT"]
        if vetoes and supports:
            consensus = "DISAGREEMENT"
        elif vetoes:
            consensus = "VETO"
        elif not any(by[v] for v in ("SUPPORT", "CAUTION", "VETO")):
            consensus = "INSUFFICIENT_EVIDENCE"
        elif by["CAUTION"] and not supports:
            consensus = "CAUTION"
        elif supports and not vetoes:
            consensus = "SUPPORT_WITH_DISSENT" if by["CAUTION"] else "SUPPORT"
        else:
            consensus = "DISAGREEMENT"
        return {
            "schema": "ahos.operational_lens_synthesis.v1",
            "consensus": consensus,
            "advisory_only": True,
            "verdict_sets": by,
            "dissent": {
                "vetoes": vetoes,
                "supports": supports,
                "abstain": by["ABSTAIN"],
                "unknown": by["UNKNOWN"],
            },
            "note": "lenses are advisory; security veto in the deterministic "
                    "floor still precedes any opportunity score",
        }
