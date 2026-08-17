#!/usr/bin/env python3
"""AHOS Live AI Council — parallel multi-model advisory with anti-echo synthesis.

WHAT THIS IS
------------
You asked for several AI assistants (Claude, ChatGPT, Gemini, Grok, ...) to each
give an opinion on a token, and for those opinions to converge into one final
answer WITH ITS REASONING. This is that.

HOW IT AVOIDS THE OBVIOUS TRAP
-------------------------------
Naively averaging model outputs produces confident nonsense: five models trained
on the same internet will repeat the same hype in unison, and averaging makes
that echo look like evidence. So:

  1. Every model receives the SAME deterministic evidence packet — the real
     numbers AHOS measured. They are explicitly told to reason only from it.
  2. Answers are parsed into a STRUCTURED verdict (ENTER / AVOID / WAIT +
     confidence + reasons), not free prose.
  3. UNANIMITY IS A WARNING, not a triumph. If every model agrees while the
     deterministic layer found the evidence thin, we flag ECHO_SUSPECTED.
  4. DISAGREEMENT IS A RESULT. Conflict is reported to the user as conflict.
  5. THE DETERMINISTIC VERDICT WINS. Council output is advisory metadata
     attached to a decision the deterministic engine already made. A security
     veto can never be talked out of by any number of language models.

OFFLINE
-------
Zero reachable providers is a fully supported mode: verdict=DETERMINISTIC_ONLY,
council_status=OFFLINE, and AHOS carries on with its own numbers.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .clients import AIClient, AIResponse, build_clients_from_registry

VALID_STANCES = ("ENTER", "WAIT", "AVOID", "UNCLEAR")

SYSTEM_PROMPT = """You are one member of an advisory council analysing an early-stage \
crypto token. You are ADVISORY ONLY — you do not make the decision.

STRICT RULES:
1. Reason ONLY from the evidence packet provided. If a number is not in the packet, \
you do not know it. Never invent prices, holder counts, audit results or partnerships.
2. If the evidence is insufficient to judge, say so — answer UNCLEAR. That is a \
respected answer, not a failure.
3. Never express certainty. No "guaranteed", "sure thing", "can't lose".
4. Security vetoes are absolute. If the packet reports a honeypot, live mint \
authority, or an untradeable exit, your stance MUST be AVOID.
5. Be brief and concrete.

Reply in EXACTLY this format and nothing else:

STANCE: <ENTER|WAIT|AVOID|UNCLEAR>
CONFIDENCE: <LOW|MEDIUM|HIGH>
REASONS:
- <reason grounded in a specific number from the packet>
- <reason>
RISKS:
- <the single biggest way this loses money>
"""


@dataclass
class CouncilVerdict:
    """Synthesized council outcome. Advisory metadata, never a decision."""
    final_stance: str                       # ENTER | WAIT | AVOID | UNCLEAR | DETERMINISTIC_ONLY
    agreement: str                          # UNANIMOUS | MAJORITY | SPLIT | NONE
    council_status: str                     # ONLINE | OFFLINE
    responded: int
    stances: dict[str, str] = field(default_factory=dict)      # provider -> stance
    confidences: dict[str, str] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    echo_suspected: bool = False
    providers_ok: list[str] = field(default_factory=list)
    providers_failed: list[dict[str, Any]] = field(default_factory=list)
    raw_responses: list[dict[str, Any]] = field(default_factory=list)
    advisory_only: bool = True
    computed_ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_stance": self.final_stance, "agreement": self.agreement,
            "council_status": self.council_status, "responded": self.responded,
            "stances": self.stances, "confidences": self.confidences,
            "reasons": self.reasons, "risks": self.risks, "warnings": self.warnings,
            "echo_suspected": self.echo_suspected,
            "providers_ok": self.providers_ok, "providers_failed": self.providers_failed,
            "advisory_only": self.advisory_only, "computed_ts": self.computed_ts,
        }


def parse_structured(text: str) -> dict[str, Any]:
    """Parse the constrained reply format. Unparseable => UNCLEAR (never guessed)."""
    out: dict[str, Any] = {"stance": "UNCLEAR", "confidence": "LOW",
                           "reasons": [], "risks": []}
    if not text:
        return out

    m = re.search(r"STANCE:\s*([A-Z_]+)", text, re.IGNORECASE)
    if m:
        s = m.group(1).strip().upper()
        out["stance"] = s if s in VALID_STANCES else "UNCLEAR"

    m = re.search(r"CONFIDENCE:\s*([A-Z]+)", text, re.IGNORECASE)
    if m:
        c = m.group(1).strip().upper()
        out["confidence"] = c if c in ("LOW", "MEDIUM", "HIGH") else "LOW"

    def _bullets(section: str) -> list[str]:
        m2 = re.search(rf"{section}:\s*(.+?)(?=\n[A-Z]+:|\Z)", text,
                       re.IGNORECASE | re.DOTALL)
        if not m2:
            return []
        return [ln.strip(" -•\t") for ln in m2.group(1).splitlines()
                if ln.strip(" -•\t")][:4]

    out["reasons"] = _bullets("REASONS")
    out["risks"] = _bullets("RISKS")
    return out


def build_evidence_packet(score_report=None, exitability=None, virality=None,
                          whale=None, narrative=None, extra: dict | None = None) -> str:
    """Render AHOS's own measurements into a compact, model-readable packet.

    This is the ONLY information the council is allowed to reason from.
    """
    lines: list[str] = ["=== DETERMINISTIC EVIDENCE PACKET (measured by AHOS) ==="]

    if score_report is not None:
        lines += [
            f"token: {score_report.token_symbol} ({score_report.token_name})",
            f"chain: {score_report.token_chain}",
            f"address: {score_report.token_address}",
            f"deterministic_opportunity_score: {score_report.opportunity_score:.1f}/100",
            f"data_confidence: {score_report.confidence_level}",
            f"risk_level: {score_report.risk_level}",
        ]
        if score_report.positive_reasons:
            lines.append("positive_findings:")
            lines += [f"  - {r}" for r in score_report.positive_reasons[:6]]
        if score_report.risk_deductions:
            lines.append("risk_findings:")
            lines += [f"  - [{r.severity}] {r.description}" for r in score_report.risk_deductions[:6]]
        if score_report.missing_unknowns:
            lines.append("UNKNOWN (not measured — do not assume):")
            lines += [f"  - {u}" for u in score_report.missing_unknowns[:8]]

    if exitability is not None:
        lines += ["--- exit feasibility ---",
                  f"exit_verdict: {exitability.verdict}"]
        if exitability.realizable_fraction is not None:
            lines.append(
                f"realizable_fraction: {exitability.realizable_fraction:.3f} "
                f"(share of displayed value recoverable on exit)")
        if exitability.max_safe_position_usd is not None:
            lines.append(f"max_safe_position_usd: {exitability.max_safe_position_usd}")
        for v in exitability.hard_vetoes:
            lines.append(f"HARD_VETO: {v}")

    if virality is not None:
        lines += ["--- attention ---",
                  f"virality: {virality.label} (score {virality.score})",
                  f"txn_acceleration: {virality.txn_acceleration}",
                  f"volume_acceleration: {virality.volume_acceleration}",
                  f"wash_trading_suspected: {virality.wash_suspected}",
                  f"paid_promotion: {virality.is_paid_promotion}"]

    if whale is not None:
        lines += ["--- holders ---",
                  f"holder_distribution: {whale.label}",
                  f"top10_share_pct: {whale.top10_share_pct}",
                  f"top1_share_pct: {whale.top1_share_pct}"]

    if narrative is not None:
        lines += ["--- narrative ---",
                  f"news_sentiment: {narrative.label} ({narrative.sentiment})",
                  f"mentions: {narrative.mention_count}"]

    if extra:
        lines.append("--- context ---")
        lines += [f"{k}: {v}" for k, v in extra.items()]

    lines.append("=== END PACKET ===")
    return "\n".join(lines)


class LiveCouncil:
    """Queries every available provider in parallel and synthesizes one verdict."""

    def __init__(self, clients: list[AIClient] | None = None,
                 registry_path: str | Path | None = None,
                 max_workers: int = 6):
        if clients is not None:
            self.clients = clients
        elif registry_path is not None:
            self.clients = build_clients_from_registry(registry_path)
        else:
            self.clients = build_clients_from_registry()
        self.max_workers = max_workers

    def deliberate(self, evidence_packet: str,
                   question: str = "Should a retail user enter this token now?",
                   allow_paid: bool = False,
                   deterministic_stance: str | None = None,
                   evidence_is_thin: bool = False,
                   timeout_sec: float = 90.0) -> CouncilVerdict:
        """Ask every reachable provider, then synthesize. Never raises."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{evidence_packet}\n\nQUESTION: {question}"},
        ]

        responses: list[AIResponse] = []
        candidates = [c for c in self.clients if c.has_key() and (allow_paid or not c.is_paid)]

        if candidates:
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {pool.submit(c.ask, messages, 700, allow_paid): c
                           for c in candidates}
                try:
                    for fut in as_completed(futures, timeout=timeout_sec):
                        try:
                            responses.append(fut.result())
                        except Exception as e:
                            c = futures[fut]
                            responses.append(AIResponse(
                                c.name, c.spec.get("model"), "DOWN",
                                error_state={"kind": type(e).__name__, "detail": str(e)[:120]}))
                except TimeoutError:
                    for fut, c in futures.items():
                        if not fut.done():
                            fut.cancel()
                            responses.append(AIResponse(
                                c.name, c.spec.get("model"), "DOWN",
                                error_state={"kind": "council_timeout"}))

        ok = [r for r in responses if r.ok]
        failed = [{"provider": r.provider, "availability": r.availability,
                   "error": r.error_state} for r in responses if not r.ok]

        # ---------------- OFFLINE FLOOR ----------------
        if not ok:
            return CouncilVerdict(
                final_stance="DETERMINISTIC_ONLY", agreement="NONE",
                council_status="OFFLINE", responded=0,
                warnings=["هیچ دستیار هوش مصنوعی در دسترس نبود — سامانه با موتور قطعی خود ادامه می‌دهد"],
                providers_ok=[], providers_failed=failed,
                raw_responses=[r.to_dict() for r in responses],
            )

        # ---------------- PARSE ----------------
        stances: dict[str, str] = {}
        confidences: dict[str, str] = {}
        all_reasons: list[str] = []
        all_risks: list[str] = []

        for r in ok:
            parsed = parse_structured(r.content or "")
            stances[r.provider] = parsed["stance"]
            confidences[r.provider] = parsed["confidence"]
            all_reasons.extend(parsed["reasons"])
            all_risks.extend(parsed["risks"])

        # ---------------- SYNTHESIZE ----------------
        counts: dict[str, int] = {}
        for s in stances.values():
            counts[s] = counts.get(s, 0) + 1
        top_stance, top_n = max(counts.items(), key=lambda kv: kv[1])
        total = len(stances)

        if len(counts) == 1:
            agreement = "UNANIMOUS"
        elif top_n > total / 2:
            agreement = "MAJORITY"
        else:
            agreement = "SPLIT"

        warnings: list[str] = []

        # SAFETY RATCHET: any single AVOID is contagious. One model spotting a
        # reason to stay out outweighs several models feeling optimistic —
        # the downside of a bad entry is total, the cost of a missed one is zero.
        if "AVOID" in counts and top_stance == "ENTER":
            final = "WAIT"
            warnings.append(
                "حداقل یکی از دستیارها هشدار «اجتناب» داد در حالی که بقیه ورود را پیشنهاد کردند — "
                "به‌صورت محافظه‌کارانه به «صبر کن» تنزل داده شد"
            )
        elif agreement == "SPLIT":
            final = "UNCLEAR"
            warnings.append("شورا به اجماع نرسید — اختلاف نظر واقعی وجود دارد")
        else:
            final = top_stance

        # ECHO DETECTION: unanimity on thin evidence is not consensus, it is
        # the same training data talking to itself.
        echo = False
        if agreement == "UNANIMOUS" and total >= 2 and evidence_is_thin:
            echo = True
            warnings.append(
                "اتفاق‌نظر کامل روی شواهد ضعیف — احتمال هم‌آوایی مدل‌ها (echo)، نه تأیید مستقل"
            )

        # DETERMINISTIC SUPREMACY: the measured layer always wins.
        if deterministic_stance == "AVOID" and final != "AVOID":
            warnings.append(
                f"موتور قطعی «اجتناب» را الزام کرد؛ نظر مشورتی شورا ({final}) نادیده گرفته شد"
            )
            final = "AVOID"

        def _dedup(items: list[str], limit: int) -> list[str]:
            seen, out = set(), []
            for x in items:
                k = x.lower().strip()
                if k and k not in seen:
                    seen.add(k)
                    out.append(x)
            return out[:limit]

        return CouncilVerdict(
            final_stance=final, agreement=agreement, council_status="ONLINE",
            responded=len(ok), stances=stances, confidences=confidences,
            reasons=_dedup(all_reasons, 8), risks=_dedup(all_risks, 6),
            warnings=warnings, echo_suspected=echo,
            providers_ok=[r.provider for r in ok], providers_failed=failed,
            raw_responses=[r.to_dict() for r in responses],
        )
