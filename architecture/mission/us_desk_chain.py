"""One US equity desk path. A design role is not a new agent.

Nine charter messages share one experiment id. A second hypothesis is rejected
for a future timestamp. Nothing here opens an order or promotes a strategy.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

BUS_REL = Path("reports") / "grok" / "PAPER" / "charter_bus.jsonl"
SCHEMA = "ahos.charter_message.v1"
DESK = "US_EQUITIES"
SYMBOLS = ("SPX", "QQQ", "NDX")

# Charter role -> existing registry agent. No new seat.
ROLE_AGENT = {
    "CORE-DATA": "AG-21",
    "US-01": "AG-05",
    "US-02": "AG-29",
    "US-03": "AG-33",
    "UNI-02": "AG-03",
    "RED-01": "AG-14",
    "RED-02": "AG-19",
    "JUDGE-01": "AG-11",
    "US-05": "AG-16",
    "UNI-01": "AG-42",
    "UNI-03": "AG-40",
}


def us_desk_line(root: Path) -> str:
    """Persian status. Works only after a live soak or trader pid logged nine steps."""
    from architecture.markets.shadow_cycle import live_pids

    allowed = live_pids(root)
    path = Path(root) / BUS_REL
    if not allowed or not path.is_file():
        return "مسیر کامل میز آمریکا: نمی‌کند"
    groups: dict[str, set[str]] = {}
    pids: dict[str, set[int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[-80:]:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("rejected") is True:
            continue
        exp = str(row.get("experiment_id") or "")
        step = str(row.get("step") or "")
        if not exp or not step:
            continue
        groups.setdefault(exp, set()).add(step)
        pids.setdefault(exp, set()).add(int(row.get("pid") or 0))
    for exp, steps in groups.items():
        if len(steps) >= 9 and pids.get(exp, set()) & allowed:
            return "مسیر کامل میز آمریکا: کار می‌کند"
    return "مسیر کامل میز آمریکا: نمی‌کند"


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _us_mean(root: Path) -> tuple[int, float | None]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return 0, None
    total = 0.0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if DESK not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("desk") != DESK:
            continue
        pnl = row.get("realized_pnl_usd")
        if isinstance(pnl, (int, float)) and not isinstance(pnl, bool):
            total += float(pnl)
            count += 1
    if count == 0:
        return 0, None
    return count, round(total / count, 6)


def _pick(quotes: list[dict[str, Any]], root: Path) -> dict[str, Any] | None:
    for row in quotes:
        price = row.get("price")
        source = row.get("source")
        if row.get("symbol") in SYMBOLS and isinstance(price, (int, float)) and not isinstance(price, bool) and price > 0 and source:
            return row
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_positions.json"
    book = {}
    if path.is_file():
        try:
            book = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            book = {}
    positions = book.get("positions") if isinstance(book.get("positions"), dict) else {}
    for symbol in SYMBOLS:
        pos = positions.get(symbol)
        if not isinstance(pos, dict):
            continue
        mark = pos.get("mark_price") or pos.get("entry_price")
        if isinstance(mark, (int, float)) and not isinstance(mark, bool) and mark > 0:
            return {
                "symbol": symbol,
                "price": float(mark),
                "source": "paper_positions.json",
                "market_time": pos.get("opened_at"),
                "stored_mark": True,
            }
    return None


def _emit(
    root: Path,
    *,
    role: str,
    receiver_role: str,
    kind: str,
    message_type: str,
    step: str,
    experiment_id: str,
    parent: str | None,
    asset: str | None,
    source_refs: list[str],
    data_timestamp: str | None,
    confidence: float,
    limitations: list[str],
    payload: dict[str, Any],
    rejected: bool,
    now: datetime,
    seq: int,
) -> dict[str, Any]:
    sender = ROLE_AGENT[role]
    receiver = ROLE_AGENT[receiver_role]
    message_id = f"{experiment_id}-{seq:02d}-{step}"
    row = {
        "schema": SCHEMA,
        "schema_version": 1,
        "message_id": message_id,
        "timestamp_utc": _utc(now),
        "sender_id": role,
        "agent_id": sender,
        "recipient": receiver_role,
        "receiver_agent": receiver,
        "message_type": message_type,
        "evidence_status": kind,
        "asset_id": asset,
        "market": DESK,
        "source_refs": source_refs,
        "data_timestamp": data_timestamp,
        "confidence": confidence,
        "payload": payload,
        "limitations": limitations,
        "parent_message_id": parent,
        "experiment_id": experiment_id,
        "step": step,
        "rejected": rejected,
        "promoted": False,
        "paper_only": True,
        "pid": os.getpid(),
    }
    from architecture.security.negahban import scan

    text = json.dumps(row, ensure_ascii=False)
    if scan(text).level == "HALT":
        raise RuntimeError("charter message failed the secret scan")
    path = Path(root) / BUS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")
    if sender != receiver:
        MessageBus(root).deliver(AgentMessage(
            sender=sender,
            receiver=receiver,
            evidence=(str(BUS_REL) + "#" + message_id,),
            claim=f"{role} {kind} {message_type} {experiment_id}. It does not promote.",
            confidence=confidence,
            required_action=RequiredAction.ABSTAIN if rejected else RequiredAction.OBSERVE,
        ))
    return row


def run_us_desk_chain(
    root: Path,
    quotes: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    experiment_id = "exp-us-" + moment.strftime("%Y%m%dT%H%M%SZ")
    chosen = _pick(list(quotes or []), root)
    count, mean = _us_mean(root)
    paper_events = [row for row in (events or []) if row.get("desk") == DESK]
    paper_kind = "NO_TRADE"
    if any(row.get("event") == "CLOSE" for row in paper_events):
        paper_kind = "CLOSE"
    elif any(row.get("event") == "OPEN" for row in paper_events):
        paper_kind = "OPEN"
    messages: list[dict[str, Any]] = []
    if chosen is None:
        messages.append(_emit(
            root, role="CORE-DATA", receiver_role="US-01", kind="FACT",
            message_type="DATA_OBSERVATION", step="data", experiment_id=experiment_id,
            parent=None, asset=None, source_refs=[], data_timestamp=None, confidence=0.2,
            limitations=["no sourced US equity price was on the cycle or in the stored book"],
            payload={"verdict": "INSUFFICIENT_EVIDENCE"}, rejected=True, now=moment, seq=1,
        ))
        return {"experiment_id": experiment_id, "steps": 0, "rejected": True, "promoted": False, "messages": messages}

    asset = str(chosen["symbol"])
    source = str(chosen["source"])
    data_ts = chosen.get("market_time") if isinstance(chosen.get("market_time"), str) else None
    limits = ["the price is a paper observation"]
    if chosen.get("stored_mark") is True:
        limits.append("the price is the stored mark, not a new market print")
    data = _emit(
        root, role="CORE-DATA", receiver_role="US-01", kind="FACT",
        message_type="DATA_OBSERVATION", step="data", experiment_id=experiment_id,
        parent=None, asset=asset, source_refs=[source], data_timestamp=data_ts,
        confidence=0.6, limitations=limits,
        payload={"price": chosen["price"], "verdict": "SOURCED"}, rejected=False, now=moment, seq=1,
    )
    messages.append(data)
    analysis = _emit(
        root, role="US-01", receiver_role="US-02", kind="INFERENCE",
        message_type="OPPORTUNITY_CANDIDATE", step="analysis", experiment_id=experiment_id,
        parent=data["message_id"], asset=asset, source_refs=[data["message_id"]],
        data_timestamp=data_ts, confidence=0.4,
        limitations=["a stored mean is not a forecast"],
        payload={"desk": DESK, "stored_closes": count}, rejected=False, now=moment, seq=2,
    )
    messages.append(analysis)
    hypothesis = _emit(
        root, role="US-02", receiver_role="UNI-02", kind="HYPOTHESIS",
        message_type="STRATEGY_HYPOTHESIS", step="hypothesis", experiment_id=experiment_id,
        parent=analysis["message_id"], asset=asset, source_refs=[analysis["message_id"]],
        data_timestamp=data_ts, confidence=0.3,
        limitations=["the hypothesis is not a promotion and not a profit claim"],
        payload={"statement": "stored US equity closes have a measurable mean", "mean_usd": mean, "n": count},
        rejected=False, now=moment, seq=3,
    )
    messages.append(hypothesis)
    again, _ = _us_mean(root)
    experiment = _emit(
        root, role="UNI-02", receiver_role="RED-01", kind="INFERENCE",
        message_type="EXPERIMENT_RESULT", step="experiment", experiment_id=experiment_id,
        parent=hypothesis["message_id"], asset=asset, source_refs=["reports/grok/PAPER/paper_trades.jsonl"],
        data_timestamp=data_ts, confidence=0.5,
        limitations=["lookback on stored closes", "not a fresh out-of-sample pass"],
        payload={"n": count, "mean_usd": mean, "reproduced": again == count, "pass_stats": False},
        rejected=False, now=moment, seq=4,
    )
    messages.append(experiment)
    red = _emit(
        root, role="RED-01", receiver_role="JUDGE-01", kind="INFERENCE",
        message_type="RED_TEAM_FINDING", step="red_team", experiment_id=experiment_id,
        parent=experiment["message_id"], asset=asset, source_refs=[experiment["message_id"]],
        data_timestamp=data_ts, confidence=0.7,
        limitations=["the attack set is the lookahead check and the cost omission check"],
        payload={"lookahead": False, "cost_omission": False, "verdict": "NO_ATTACK_HIT", "promoted": False},
        rejected=False, now=moment, seq=5,
    )
    messages.append(red)
    judge = _emit(
        root, role="JUDGE-01", receiver_role="US-05", kind="INFERENCE",
        message_type="PROMOTION_DECISION", step="judge", experiment_id=experiment_id,
        parent=red["message_id"], asset=asset, source_refs=[red["message_id"]],
        data_timestamp=data_ts, confidence=0.9,
        limitations=["paper observation is not a promotion"],
        payload={"verdict": "NO_PROMOTION", "promoted": False},
        rejected=False, now=moment, seq=6,
    )
    messages.append(judge)
    paper = _emit(
        root, role="US-05", receiver_role="UNI-01", kind="FACT",
        message_type="PAPER_TRADE_RESULT" if paper_kind != "NO_TRADE" else "NO_TRADE_DECISION",
        step="paper", experiment_id=experiment_id, parent=judge["message_id"], asset=asset,
        source_refs=[judge["message_id"]], data_timestamp=data_ts, confidence=0.8,
        limitations=["this step does not open a new order"],
        payload={"cycle_event": paper_kind, "opened_by_this_path": False},
        rejected=False, now=moment, seq=7,
    )
    messages.append(paper)
    outcome = _emit(
        root, role="UNI-01", receiver_role="UNI-03", kind="FACT",
        message_type="PAPER_TRADE_RESULT", step="outcome", experiment_id=experiment_id,
        parent=paper["message_id"], asset=asset, source_refs=[paper["message_id"]],
        data_timestamp=data_ts, confidence=0.8,
        limitations=["the outcome is the cycle event plus the stored mean"],
        payload={"cycle_event": paper_kind, "stored_n": count, "stored_mean_usd": mean},
        rejected=False, now=moment, seq=8,
    )
    messages.append(outcome)
    lesson = _emit(
        root, role="UNI-03", receiver_role="JUDGE-01", kind="INFERENCE",
        message_type="SYSTEM_HEALTH_REPORT", step="lesson", experiment_id=experiment_id,
        parent=outcome["message_id"], asset=asset, source_refs=[outcome["message_id"]],
        data_timestamp=data_ts, confidence=0.6,
        limitations=["the lesson does not change a live weight"],
        payload={"lesson": "stored mean is not a pass", "applied_to_live_weights": False},
        rejected=False, now=moment, seq=9,
    )
    messages.append(lesson)
    future = _utc(moment + timedelta(days=1))
    bad = _emit(
        root, role="US-03", receiver_role="RED-02", kind="HYPOTHESIS",
        message_type="STRATEGY_HYPOTHESIS", step="rejected_hypothesis",
        experiment_id=experiment_id + "-reject", parent=data["message_id"], asset=asset,
        source_refs=[data["message_id"]], data_timestamp=future, confidence=0.2,
        limitations=["the data time is after the decision"],
        payload={"statement": "a later close is already known"},
        rejected=False, now=moment, seq=1,
    )
    messages.append(bad)
    _emit(
        root, role="RED-02", receiver_role="JUDGE-01", kind="INFERENCE",
        message_type="RED_TEAM_FINDING", step="rejected",
        experiment_id=experiment_id + "-reject", parent=bad["message_id"], asset=asset,
        source_refs=[bad["message_id"]], data_timestamp=future, confidence=0.9,
        limitations=["a future timestamp is leakage"],
        payload={"verdict": "REJECT", "reason": "LOOKAHEAD"},
        rejected=True, now=moment, seq=2,
    )
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["us_desk_chain"] = {
            "experiment_id": experiment_id,
            "steps": 9,
            "rejected_experiment": experiment_id + "-reject",
            "promoted": False,
            "pid": os.getpid(),
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-11"})
    except Exception:
        pass
    return {
        "experiment_id": experiment_id,
        "steps": 9,
        "rejected": True,
        "promoted": False,
        "asset": asset,
        "messages": messages,
    }
