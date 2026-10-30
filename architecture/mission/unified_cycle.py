"""One paper cycle that projects existing files into the world state and the bus.

It does not fetch, does not open a trade, and does not replace the mission
ledger. A module with no registry id is reported as silent. Kian has no AG
id in the registry (deferred to M35.1), so the Persian trace is a document
for him, not a message from him.
"""
from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

REGISTRY_REL = Path("config") / "agent_registry.yaml"
RECEIPT_REL = Path("reports") / "grok" / "PAPER" / "unified_cycle.json"
DECISION_EVENTS = frozenset({"OPEN", "CLOSE", "SKIP", "NO_TRADE"})

# Registry ids that already exist. Judge (Soroush) and the dashboard (Kian) are not seats.
MODULE_SENDERS = {
    "desks": "AG-16",
    "families": "AG-04",
    "university": "AG-41",
    "research": "AG-03",
    "didehban": "AG-33",
    "negahban": "AG-09",
    "council": "AG-11",
    "kill_switch": "AG-08",
}
SERVE_ALL = ("didehban", "negahban")
SILENT_MODULES = {
    "judge": "NOT_IN_REGISTRY",
    "dashboard": "NOT_IN_REGISTRY",
}

REASON_FA = {
    "MULTI_SIGNAL_AGREEMENT": "دو خانوادهٔ مستقل هم‌جهت نبودند.",
    "ALLOCATION_EXHAUSTED": "سقف اندازهٔ کاغذی پر بود.",
    "FEE_DRAG": "سود مورد انتظار به دو برابر کارمزد نرسید.",
    "TOKEN_SAFETY_VETO": "بررسی ایمنی توکن اجازه نداد.",
    "PUMP_NEWS_ALONE": "خبر به‌تنهایی مجاز به باز کردن معامله نیست.",
    "PUMP_NEWS_NEEDS_SAFETY": "خبر پامپ بدون عبور از بررسی ایمنی توکن مانده است.",
    "WITNESS_CONFLICT": "دو منبع قیمت با هم نمی‌خواندند.",
    "CONTRACT_ROLL": "قرارداد نزدیک رول بود.",
    "CONTRACT_MONTH_UNKNOWN": "ماه قرارداد معلوم نبود.",
}


def _utc(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _absent(source: str) -> dict[str, Any]:
    return {"status": "ABSENT", "source": source, "paper_only": True, "decides": False}


def registry_ids(root: Path) -> list[str]:
    path = Path(root) / REGISTRY_REL
    if not path.is_file():
        return []
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return []
    ids = []
    for agent in (doc or {}).get("agents") or []:
        aid = str((agent or {}).get("agent_id") or "")
        if aid.startswith("AG-"):
            ids.append(aid)
    return ids


def _tail_decisions(root: Path, limit: int = 30) -> list[dict[str, Any]]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return []
    kept: deque[dict[str, Any]] = deque(maxlen=limit)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("event") in DECISION_EVENTS:
            kept.append(row)
    return list(kept)


def _reason_fa(reason: str) -> str:
    text = str(reason or "")
    if text in REASON_FA:
        return REASON_FA[text]
    head = text.split(":", 1)[0]
    if head in REASON_FA:
        return REASON_FA[head] + f" جزئیات ثبت‌شده: {text}."
    if not text:
        return "دلیلی در این ردیف ثبت نشده است."
    return f"دلیل ثبت‌شده: {text}. ترجمهٔ فارسی این کد از پیش ثبت نشده است."


def trace_decision(event: dict[str, Any]) -> dict[str, Any]:
    """Persian chain for one logged decision. Reuses kian_explain_fa when the row already has it."""
    brain = event.get("brain") if isinstance(event.get("brain"), dict) else {}
    if not brain and isinstance(event.get("entry_brain"), dict):
        brain = event["entry_brain"]
    votes = event.get("independent_votes") if isinstance(event.get("independent_votes"), dict) else {}
    if not votes and isinstance(brain.get("independent_votes"), dict):
        votes = brain["independent_votes"]
    families = votes.get("votes") if isinstance(votes.get("votes"), list) else []
    research = event.get("research_predictions")
    if research is None:
        research = brain.get("research_predictions")
    existing = event.get("kian_explain_fa")
    symbol = str(event.get("symbol") or "")
    event_name = str(event.get("event") or "")
    if isinstance(existing, str) and existing.strip():
        fa = existing.strip()
    else:
        fa = "\n".join([
            f"ردیف {event_name} برای {symbol or 'نماد نامشخص'} روی میز {event.get('desk') or 'نامشخص'}.",
            _reason_fa(str(event.get("reason") or "")),
            "این متن از لاگ کاغذی خوانده شده و حکم معامله نیست.",
            "وضعیت لبه: UNPROVEN_EDGE.",
        ])
    risk_bits = []
    if event.get("reason"):
        risk_bits.append(_reason_fa(str(event.get("reason"))))
    veto = brain.get("token_safety_veto") if isinstance(brain.get("token_safety_veto"), dict) else None
    if veto is not None:
        risk_bits.append(f"بررسی ایمنی توکن: allowed={veto.get('allowed')}.")
    return {
        "event": event_name,
        "symbol": symbol,
        "desk": event.get("desk"),
        "fa": fa,
        "families": [
            {"family": row.get("family"), "vote": row.get("vote")}
            for row in families if isinstance(row, dict)
        ],
        "lessons": "درس جدا در این ردیف نیست." if not event.get("lesson") else str(event.get("lesson")),
        "research": research if research else None,
        "risk": risk_bits,
        "decides": False,
        "paper_only": True,
    }


def _count_jsonl(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except OSError:
        return None


def project_sections(root: Path) -> dict[str, Any]:
    root = Path(root)
    paper = root / "reports" / "grok" / "PAPER"
    status = _load(paper / "paper_trader_status.json")
    positions = _load(paper / "paper_positions.json")
    scorecard = _load(paper / "weekly_family_vote_scorecard.json")
    research = _load(paper / "research_weekly.json")
    newsroom = _load(root / "reports" / "grok" / "M18" / "newsroom_snapshot.json")
    desk_news_n = _count_jsonl(paper / "desk_news.jsonl")
    negahban = _load(root / "reports" / "grok" / "CONTINUATION" / "scheduled_runs" / "AHOS_negahban_daily.json")
    lessons_n = _count_jsonl(paper / "university_cases.jsonl")
    traces = [trace_decision(row) for row in _tail_decisions(root)]
    regime = None
    if isinstance(status, dict):
        regime = {"edge_status": status.get("edge_status"), "halted": status.get("halted"), "source": "paper_trader_status.json"}
    sections = {
        "positions": {
            "status": "PRESENT" if isinstance(positions, dict) else "ABSENT",
            "source": "reports/grok/PAPER/paper_positions.json",
            "n": len(positions) if isinstance(positions, dict) else 0,
            "decides": False,
        },
        "signals": {
            "status": "PRESENT" if isinstance(status, dict) else "ABSENT",
            "weights_version": (status or {}).get("weights_version") if isinstance(status, dict) else None,
            "shadow_n": len((status or {}).get("shadow_signals") or []) if isinstance(status, dict) else None,
            "decides": False,
        },
        "family_votes": {
            "status": "PRESENT" if isinstance(scorecard, dict) else "ABSENT",
            "source": "reports/grok/PAPER/weekly_family_vote_scorecard.json",
            "decides": False,
        },
        "regime": regime or _absent("reports/grok/PAPER/paper_trader_status.json"),
        "news": {
            "status": "PRESENT" if isinstance(newsroom, dict) or desk_news_n else "ABSENT",
            "newsroom": "reports/grok/M18/newsroom_snapshot.json" if isinstance(newsroom, dict) else None,
            "desk_news_rows": desk_news_n,
            "decides": False,
            "weight": 0,
        },
        "risk": {
            "status": "PRESENT" if isinstance(status, dict) else "ABSENT",
            "source": "reports/grok/PAPER/paper_trader_status.json",
            "decides": False,
        },
        "lessons": {
            "status": "PRESENT" if lessons_n else "ABSENT",
            "university_case_rows": lessons_n,
            "exam": "reports/grok/PAPER/weekly_agent_exam.json",
            "reliability": "reports/grok/PAPER/reliability_shadow.json",
            "calibration": "reports/grok/PAPER/calibration_weekly.json",
            "intelligence": "reports/grok/PAPER/intelligence_metric.json",
            "diagnosis": "reports/grok/PAPER/daily_diagnosis.json",
            "decides": False,
        },
        "hypotheses": {
            "status": "PRESENT" if isinstance(research, dict) else "ABSENT",
            "source": "reports/grok/PAPER/research_weekly.json",
            "decides": False,
        },
        "council": _absent("no council snapshot on the shared path; the paper brain keeps council_debate on the trade row"),
        "security": {
            "status": "PRESENT" if isinstance(negahban, dict) else "ABSENT",
            "source": "reports/grok/CONTINUATION/scheduled_runs/AHOS_negahban_daily.json",
            "job_status": (negahban or {}).get("status") if isinstance(negahban, dict) else None,
            "decides": False,
        },
        "kill_switch": {
            "status": "PRESENT" if isinstance(status, dict) else "ABSENT",
            "halted": (status or {}).get("halted") if isinstance(status, dict) else None,
            "halt_reason": (status or {}).get("halt_reason") if isinstance(status, dict) else None,
            "kill_switch": (status or {}).get("kill_switch") if isinstance(status, dict) else None,
            "kill_reason": (status or {}).get("kill_reason") if isinstance(status, dict) else None,
            "decides": False,
        },
        "traces": {"n": len(traces), "latest": traces[-8:], "decides": False},
    }
    return sections


def _observe(sender: str, receiver: str, claim: str, evidence: tuple[str, ...]) -> AgentMessage:
    return AgentMessage(
        sender=sender,
        receiver=receiver,
        evidence=evidence,
        claim=claim,
        confidence=1.0 if evidence else 0.0,
        required_action=RequiredAction.OBSERVE,
    )


def run_unified_cycle(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    try:
        from architecture.markets.paper_account import load_paper_trades
        from architecture.university.behaviour_learning import publish_learning
        from architecture.university.self_diagnosis import export_daily

        closes = load_paper_trades(root)
        publish_learning(root, closes)
        if closes:
            day = max(str(row.get("closed_at") or "")[:10] for row in closes)
            if day:
                export_daily(root, closes, day)
    except Exception:
        pass
    sections = project_sections(root)
    writers = {
        "positions": MODULE_SENDERS["desks"],
        "signals": MODULE_SENDERS["families"],
        "family_votes": MODULE_SENDERS["families"],
        "regime": MODULE_SENDERS["desks"],
        "news": MODULE_SENDERS["didehban"],
        "risk": MODULE_SENDERS["kill_switch"],
        "lessons": MODULE_SENDERS["university"],
        "hypotheses": MODULE_SENDERS["research"],
        "council": MODULE_SENDERS["council"],
        "security": MODULE_SENDERS["negahban"],
        "kill_switch": MODULE_SENDERS["kill_switch"],
        "traces": MODULE_SENDERS["desks"],
    }
    state = WorldStateStore(root).commit(sections, writers, now=now)
    bus = MessageBus(root)
    ids = registry_ids(root)
    sent: set[str] = set()
    received: set[str] = set()
    delivered = 0
    for module in SERVE_ALL:
        sender = MODULE_SENDERS[module]
        claim = f"{module} wrote its section on world state v{state['version']}. Evidence only. It does not decide."
        evidence = (f"reports/grok/PAPER/world_state.json#v{state['version']}",)
        for receiver in ids:
            if receiver == sender:
                continue
            bus.deliver(_observe(sender, receiver, claim, evidence), now=now)
            sent.add(sender)
            received.add(receiver)
            delivered += 1
    fired = sorted(MODULE_SENDERS)
    silent = [
        {"module": name, "reason": reason, "messages_sent": 0}
        for name, reason in SILENT_MODULES.items()
    ]
    no_outbound = [aid for aid in ids if aid not in sent]
    receipt = {
        "schema": "ahos.unified_cycle.v1",
        "generated_at": _utc(now),
        "paper_only": True,
        "decides": False,
        "live_trading": False,
        "world_state_version": state["version"],
        "messages_delivered": delivered,
        "modules_fired": fired,
        "message_senders": sorted(sent),
        "modules_silent": silent,
        "agents_with_no_outbound": no_outbound,
        "critique": {
            "level_1": "The cycle reads files already on disk, versions one world state, and logs AgentMessage envelopes from Didehban and Negahban to every other registry id.",
            "level_2": "Other modules still write their own files. This store does not replace the mission ledger and does not make a silent seat live. The design-only communication protocol envelope is not this bus.",
        },
        "gaps_closed": [],
    }
    out = root / RECEIPT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    return receipt
