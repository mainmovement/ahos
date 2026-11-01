"""BRAIN-01 ranks and vetoes paper tickets. It does not raise a weight or promote."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

BUS_REL = Path("reports") / "grok" / "PAPER" / "charter_bus.jsonl"
STATE_REL = Path("reports") / "grok" / "PAPER" / "brain01_state.json"
DECISION_REL = Path("reports") / "grok" / "PAPER" / "brain01_decision.json"
PAUSE_REL = Path("reports") / "grok" / "PAPER" / "desk_pause.json"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"
MISTAKES_REL = Path("reports") / "grok" / "M58" / "loss_eval_cases.jsonl"
N_TICKETS = 1
SENDER = "AG-01"
RECEIVER = "AG-11"
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

PAUSE_DESK = {
    "US_EQUITIES": "US_EQUITIES",
    "CRYPTO": "CRYPTO",
    "GOLD": "GOLD",
    "OIL": "OIL",
    "ONCHAIN": "PB_TOKEN",
    "NQ": "LISTED_FUTURES",
    "EU_EQUITY": "EU_EQUITIES",
    "ASIA_EQUITY": "ASIA_EQUITIES",
}
CLUSTER = {
    "CRYPTO": "crypto",
    "PB_TOKEN": "crypto",
    "GOLD": "metals",
    "OIL": "energy",
    "US_EQUITIES": "equities",
    "EU_EQUITIES": "equities",
    "ASIA_EQUITIES": "equities",
    "LISTED_FUTURES": "listed_futures",
}
SYMBOL_DESK = {
    "BTC": "CRYPTO", "ETH": "CRYPTO", "SOL": "CRYPTO", "UNI": "PB_TOKEN",
    "XAU": "GOLD", "WTI": "OIL", "BRENT": "OIL",
    "SPX": "US_EQUITIES", "QQQ": "US_EQUITIES", "NDX": "US_EQUITIES",
    "DAX": "EU_EQUITIES", "N225": "ASIA_EQUITIES", "HSI": "ASIA_EQUITIES",
    "NQ": "LISTED_FUTURES", "ES": "LISTED_FUTURES", "GC": "LISTED_FUTURES",
    "CL": "LISTED_FUTURES", "BZ": "LISTED_FUTURES",
}
SUPPORT = {
    "SEC-01": "INSUFFICIENT_EVIDENCE",
    "NEWS-05": "NOT_A_TRADE_INPUT",
    "RDI-01": "NOT_FETCHED",
    "RDI-04": "NOT_ADOPTED",
    "RDI-05": "NOT_ADOPTED",
}


def _utc(moment: datetime | None = None) -> str:
    stamp = moment or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return doc if isinstance(doc, dict) else {}


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def ticket_allowed(root: Path, desk: str) -> bool:
    """A missing decision does not invent a veto. A written decision can only allow a listed desk."""
    doc = _read(Path(root) / DECISION_REL)
    if not doc:
        return True
    allowed = doc.get("allowed")
    return isinstance(allowed, list) and desk in allowed


def brain_line(root: Path) -> str:
    doc = _read(Path(root) / DECISION_REL)
    ranked = int(doc.get("ranked") or 0)
    rejected = int(doc.get("rejected") or 0)
    return f"مغز مرکزی: {str(ranked).translate(_DIGITS)} بلیت رتبه‌بندی شد، {str(rejected).translate(_DIGITS)} رد شد"


def _chain_rows(root: Path) -> list[dict[str, Any]]:
    from architecture.mission.desk_chain_template import load_desks

    rows = []
    for desk, cfg in load_desks(root).items():
        state = _read(Path(root) / str(cfg.get("state_file") or ""))
        rows.append({
            "desk": desk,
            "pause_desk": PAUSE_DESK.get(desk, desk),
            "status": state.get("status"),
            "reasons": list(state.get("reasons") or []),
            "experiment_id": state.get("experiment_id"),
            "symbol": state.get("symbol"),
        })
    return rows


def _occupied_clusters(root: Path) -> set[str]:
    book = _read(Path(root) / POSITIONS_REL)
    found = set()
    for symbol in (book.get("positions") or {}):
        desk = SYMBOL_DESK.get(str(symbol))
        cluster = CLUSTER.get(str(desk or ""))
        if cluster:
            found.add(cluster)
    return found


def _brier(trades: list[dict[str, Any]], desk: str) -> float | None:
    from architecture.learning.calibration import brier_score

    probs: list[float] = []
    outcomes: list[float] = []
    for row in trades:
        if str(row.get("event") or "") != "CLOSE" or str(row.get("desk") or "") != desk:
            continue
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        prob = brain.get("composite")
        pnl = row.get("realized_pnl_usd")
        if isinstance(prob, bool) or isinstance(pnl, bool):
            continue
        if not isinstance(prob, (int, float)) or not isinstance(pnl, (int, float)):
            continue
        probs.append(float(prob))
        outcomes.append(1.0 if float(pnl) > 0 else 0.0)
    if not probs:
        return None
    return brier_score(probs, outcomes)


def _mistake_count(root: Path, desk: str) -> int | None:
    rows = _rows(Path(root) / MISTAKES_REL)
    if not rows:
        return None
    return sum(1 for row in rows if str(row.get("desk") or "") == desk and str(row.get("status") or "") == "UNVERIFIED")


def run_brain(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    pause = _read(root / PAUSE_REL)
    paused = set(pause.get("paused_desks") or [])
    expectancy = {
        str(row.get("desk")): row.get("expectancy_usd")
        for row in (pause.get("desks") or [])
        if isinstance(row, dict)
    }
    trades = _rows(root / TRADES_REL)
    occupied = _occupied_clusters(root)
    chain_rows = _chain_rows(root)
    open_tickets = sum(1 for row in chain_rows if row["status"] == "OPEN")
    ranked_rows = []
    for row in chain_rows:
        blocks = []
        if row["pause_desk"] in paused:
            blocks.append("DESK_EXPECTANCY_PAUSE")
        blocks.extend(str(item) for item in row["reasons"] if item)
        cluster = CLUSTER.get(row["pause_desk"])
        if cluster and cluster in occupied:
            blocks.append("CORRELATED_BOOK")
        qualifies = not blocks and row["status"] == "WAITING" and open_tickets < N_TICKETS
        ranked_rows.append({
            **row,
            "expectancy_usd": expectancy.get(row["pause_desk"]),
            "brier": _brier(trades, row["pause_desk"]),
            "mistake_count": _mistake_count(root, row["pause_desk"]),
            "blocks": blocks,
            "qualifies": qualifies,
        })
    ranked_rows.sort(key=lambda item: (not item["qualifies"], len(item["blocks"]), str(item["desk"])))
    room = max(0, N_TICKETS - open_tickets)
    allowed = [item["desk"] for item in ranked_rows if item["qualifies"]][:room]
    for item in ranked_rows:
        item["verdict"] = "RANKED" if item["desk"] in allowed else "VETO"
    rejected = len(ranked_rows) - len(allowed)
    decision = {
        "schema": "ahos.brain01.v1",
        "paper_only": True,
        "promoted": False,
        "applied_to_live_weights": False,
        "decides": False,
        "live_switch": "UNTOUCHED",
        "n_tickets": N_TICKETS,
        "ranked": len(allowed),
        "rejected": rejected,
        "verdict": "NO_TRADE" if not allowed else "RANKED",
        "allowed": allowed,
        "rows": ranked_rows,
        "support_roles": SUPPORT,
        "pid": os.getpid(),
        "generated_at": _utc(moment),
    }
    path = root / DECISION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    state = _read(root / STATE_REL)
    calls = int(state.get("calls") or 0) + 1
    (root / STATE_REL).write_text(json.dumps({
        "schema": "ahos.brain01_state.v1",
        "calls": calls,
        "pid": os.getpid(),
        "last_verdict": decision["verdict"],
        "ranked": len(allowed),
        "rejected": rejected,
        "generated_at": decision["generated_at"],
        "paper_only": True,
        "promoted": False,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    experiment_id = "brain-" + moment.strftime("%Y%m%dT%H%M%SZ")
    _emit(root, experiment_id, "rank", 1, moment, {
        "verdict": "RANKED" if allowed else "NO_CANDIDATE",
        "allowed": allowed,
        "order": [item["desk"] for item in ranked_rows],
        "reasons": {item["desk"]: item["blocks"] for item in ranked_rows},
    })
    veto = next((item for item in ranked_rows if item["verdict"] == "VETO"), None)
    _emit(root, experiment_id, "no_trade" if not allowed else "veto", 2, moment, {
        "verdict": "NO_TRADE" if not allowed else "VETO",
        "desk": None if veto is None else veto["desk"],
        "reasons": [] if veto is None else veto["blocks"],
        "rejected": rejected,
    })
    _remember(root, decision)
    return decision


def _emit(root: Path, experiment_id: str, step: str, seq: int, moment: datetime, payload: dict[str, Any]) -> None:
    message_id = f"{experiment_id}-{seq:02d}-{step}"
    row = {
        "schema": "ahos.charter_message.v1",
        "message_id": message_id,
        "timestamp_utc": _utc(moment),
        "sender_id": "BRAIN-01",
        "agent_id": SENDER,
        "recipient": "JUDGE-01",
        "receiver_agent": RECEIVER,
        "message_type": "OPPORTUNITY_RANKING" if step == "rank" else "NO_TRADE_DECISION",
        "evidence_status": "INFERENCE",
        "payload": payload,
        "limitations": ["a rank is not a promotion and a veto does not raise a weight"],
        "experiment_id": experiment_id,
        "step": step,
        "promoted": False,
        "paper_only": True,
        "pid": os.getpid(),
        "confidence": 0.6,
    }
    from architecture.security.negahban import scan

    text = json.dumps(row, ensure_ascii=False)
    if scan(text).level == "HALT":
        return
    path = root / BUS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")
    MessageBus(root).deliver(AgentMessage(
        sender=SENDER,
        receiver=RECEIVER,
        evidence=(str(BUS_REL) + "#" + message_id,),
        claim=f"BRAIN-01 {step} {experiment_id}. It does not promote.",
        confidence=0.6,
        required_action=RequiredAction.ABSTAIN if step != "rank" else RequiredAction.OBSERVE,
    ))


def _remember(root: Path, decision: dict[str, Any]) -> None:
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["brain01"] = {
            "verdict": decision["verdict"],
            "ranked": decision["ranked"],
            "rejected": decision["rejected"],
            "allowed": decision["allowed"],
            "pid": decision["pid"],
            "promoted": False,
            "applied_to_live_weights": False,
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-01"})
    except Exception:
        pass
