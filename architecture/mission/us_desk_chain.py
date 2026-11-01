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


STATE_REL = Path("reports") / "grok" / "PAPER" / "us_chain_state.json"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"
NOTIONAL_USD = 1.0
EXIT_AFTER_S = 600
MAX_QUOTE_AGE_S = 20 * 60
FEE = 0.0003
SLIP = 0.0002
RULE_ID = "us-eq-tiny-v1"


def real_us_line(root: Path) -> str:
    """The real round trip is a later close. A waiting book is not a completed trade."""
    path = Path(root) / STATE_REL
    if not path.is_file():
        return "مسیر واقعی میز آمریکا: هنوز فرصت نبود"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "مسیر واقعی میز آمریکا: هنوز فرصت نبود"
    opened = str(state.get("opened_at") or "")
    closed = str(state.get("closed_at") or "")
    if (
        state.get("status") == "CLOSED"
        and state.get("close_id")
        and opened
        and closed > opened
        and state.get("promoted") is False
    ):
        return "مسیر واقعی میز آمریکا: یک معامله کامل شد"
    return "مسیر واقعی میز آمریکا: هنوز فرصت نبود"


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


def _cycle_quote(quotes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in quotes:
        price = row.get("price")
        source = row.get("source")
        if (
            row.get("symbol") in SYMBOLS
            and isinstance(price, (int, float))
            and not isinstance(price, bool)
            and price > 0
            and source
            and row.get("stored_mark") is not True
        ):
            return row
    return None


def _quote_age(market_time: str | None, moment: datetime) -> float | None:
    if not isinstance(market_time, str) or not market_time:
        return None
    try:
        stamp = datetime.fromisoformat(market_time.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return (moment - stamp.astimezone(timezone.utc)).total_seconds()


def _book(root: Path) -> dict[str, Any]:
    path = Path(root) / POSITIONS_REL
    if not path.is_file():
        return {"positions": {}}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"positions": {}}
    if not isinstance(doc, dict):
        return {"positions": {}}
    if not isinstance(doc.get("positions"), dict):
        doc["positions"] = {}
    return doc


def _blockers(root: Path, quote: dict[str, Any] | None, moment: datetime, own_symbol: str | None) -> list[str]:
    if quote is None:
        return ["NO_SOURCED_PRICE"]
    reasons: list[str] = []
    symbol = str(quote["symbol"])
    from architecture.markets.weekday_session_gate import symbol_session

    if symbol_session(symbol, moment).get("open") is not True:
        reasons.append("SESSION_CLOSED")
    age = _quote_age(quote.get("market_time") if isinstance(quote.get("market_time"), str) else None, moment)
    if age is None or age < 0 or age > MAX_QUOTE_AGE_S:
        reasons.append("QUOTE_STALE")
    positions = _book(root)["positions"]
    if symbol in positions and symbol != own_symbol:
        reasons.append("POSITION_ALREADY_OPEN")
    return reasons


def _load_state(root: Path) -> dict[str, Any] | None:
    path = Path(root) / STATE_REL
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return doc if isinstance(doc, dict) else None


def _save_state(root: Path, state: dict[str, Any]) -> None:
    path = Path(root) / STATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _append_trade(root: Path, row: dict[str, Any]) -> None:
    path = Path(root) / TRADES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _find_close(root: Path, experiment_id: str) -> dict[str, Any] | None:
    path = Path(root) / TRADES_REL
    if not path.is_file():
        return None
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if experiment_id not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") == "CLOSE" and row.get("chain_experiment_id") == experiment_id:
            found = row
    return found


def _open_trade(root: Path, state: dict[str, Any], quote: dict[str, Any], moment: datetime) -> dict[str, Any]:
    symbol = str(quote["symbol"])
    price = float(quote["price"])
    fill = price * (1 + SLIP)
    qty = NOTIONAL_USD / fill
    entry_fee = NOTIONAL_USD * FEE
    opened = _utc(moment)
    trade_id = state["experiment_id"] + "-open"
    row = {
        "ts": opened,
        "event": "OPEN",
        "symbol": symbol,
        "desk": DESK,
        "side": "LONG",
        "paper_only": True,
        "trade_id": trade_id,
        "chain_experiment_id": state["experiment_id"],
        "rule_id": RULE_ID,
        "quote_price": price,
        "fill_price": round(fill, 6),
        "qty": qty,
        "notional_usd": NOTIONAL_USD,
        "fee_usd": round(entry_fee, 6),
        "slippage_pct": SLIP,
        "source": quote.get("source"),
        "market_time": quote.get("market_time"),
        "promoted": False,
    }
    book = _book(root)
    if symbol in book["positions"]:
        raise RuntimeError("refusing to replace an open position")
    book["positions"][symbol] = {
        "side": "LONG",
        "entry_price": round(fill, 6),
        "qty": qty,
        "notional_usd": NOTIONAL_USD,
        "entry_fee_usd": round(entry_fee, 6),
        "opened_at": opened,
        "opened_ts": moment.timestamp(),
        "desk": DESK,
        "stop_pct": 0.5,
        "mark_price": price,
        "chain_experiment_id": state["experiment_id"],
        "entry_brain": {"chain_experiment_id": state["experiment_id"], "composite": 0.3},
    }
    (Path(root) / POSITIONS_REL).write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _append_trade(root, row)
    state.update({
        "status": "OPEN",
        "symbol": symbol,
        "opened_at": opened,
        "entry_price": round(fill, 6),
        "qty": qty,
        "entry_fee_usd": round(entry_fee, 6),
        "open_id": trade_id,
        "reasons": [],
    })
    return row


def _close_trade(root: Path, state: dict[str, Any], quote: dict[str, Any], moment: datetime) -> dict[str, Any]:
    price = float(quote["price"])
    entry = float(state["entry_price"])
    qty = float(state["qty"])
    exit_px = price * (1 - SLIP)
    gross = (exit_px - entry) * qty
    exit_fee = exit_px * qty * FEE
    pnl = round(gross - exit_fee - float(state["entry_fee_usd"]), 6)
    closed = _utc(moment)
    close_id = state["experiment_id"] + "-close"
    row = {
        "ts": closed,
        "event": "CLOSE",
        "symbol": state["symbol"],
        "desk": DESK,
        "side": "LONG",
        "paper_only": True,
        "trade_id": close_id,
        "chain_experiment_id": state["experiment_id"],
        "rule_id": RULE_ID,
        "reason": "TIME_STOP",
        "quote_price": price,
        "fill_price": round(exit_px, 6),
        "entry_price": entry,
        "qty": qty,
        "notional_usd": NOTIONAL_USD,
        "fees_usd": round(exit_fee + float(state["entry_fee_usd"]), 6),
        "opened_at": state["opened_at"],
        "closed_at": closed,
        "realized_pnl_usd": pnl,
        "source": quote.get("source"),
        "market_time": quote.get("market_time"),
        "promoted": False,
        "applied_to_live_weights": False,
    }
    book = _book(root)
    current = book["positions"].get(state["symbol"])
    if isinstance(current, dict) and current.get("chain_experiment_id") == state["experiment_id"]:
        del book["positions"][state["symbol"]]
        (Path(root) / POSITIONS_REL).write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _append_trade(root, row)
    state.update({"status": "CLOSED", "closed_at": closed, "close_id": close_id, "realized_pnl_usd": pnl, "reasons": []})
    return row


def _lesson_from_close(root: Path, state: dict[str, Any], close_row: dict[str, Any]) -> dict[str, Any]:
    from architecture.learning.calibration import brier_score
    from architecture.learning.mistakes import record_losing_close
    from architecture.university.learning_loop import append_university_case

    prior_probs: list[float] = []
    prior_outcomes: list[float] = []
    path = Path(root) / TRADES_REL
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if DESK not in line or "CLOSE" not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("event") != "CLOSE" or row.get("desk") != DESK:
                continue
            if row.get("trade_id") == close_row.get("trade_id"):
                continue
            pnl = row.get("realized_pnl_usd")
            if not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
                continue
            brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
            raw = brain.get("composite")
            if not isinstance(raw, (int, float)) or isinstance(raw, bool):
                continue
            prior_probs.append(max(0.0, min(1.0, abs(float(raw)))))
            prior_outcomes.append(1.0 if float(pnl) > 0 else 0.0)
    before = brier_score(prior_probs, prior_outcomes)
    prob = 0.3
    outcome = 1.0 if float(close_row["realized_pnl_usd"]) > 0 else 0.0
    after = brier_score(prior_probs + [prob], prior_outcomes + [outcome])
    case = append_university_case(root, close_row)
    mistake = record_losing_close(
        root,
        case_id=str(close_row["trade_id"]),
        pnl_usd=float(close_row["realized_pnl_usd"]),
        symbol=str(close_row["symbol"]),
        desk=DESK,
        closed_at=str(close_row["closed_at"]),
    )
    return {
        "close_id": close_row["trade_id"],
        "realized_pnl_usd": close_row["realized_pnl_usd"],
        "opened_at": close_row.get("opened_at"),
        "closed_at": close_row.get("closed_at"),
        "brier_before": None if before is None else round(float(before), 4),
        "brier_after": None if after is None else round(float(after), 4),
        "university_case": case.get("outcome"),
        "mistake_status": mistake.get("status"),
        "applied_to_live_weights": False,
    }


def _remember(root: Path, state: dict[str, Any]) -> None:
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["us_desk_chain"] = {
            "experiment_id": state.get("experiment_id"),
            "status": state.get("status"),
            "reasons": state.get("reasons") or [],
            "close_id": state.get("close_id"),
            "opened_at": state.get("opened_at"),
            "closed_at": state.get("closed_at"),
            "realized_pnl_usd": state.get("realized_pnl_usd"),
            "promoted": False,
            "pid": os.getpid(),
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-11"})
    except Exception:
        pass


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
    quote = _cycle_quote(list(quotes or []))
    state = _load_state(root)
    if state is None:
        experiment_id = "exp-us-" + moment.strftime("%Y%m%dT%H%M%SZ")
        asset = None if quote is None else str(quote["symbol"])
        source = [] if quote is None else [str(quote.get("source"))]
        data_ts = quote.get("market_time") if quote and isinstance(quote.get("market_time"), str) else None
        data = _emit(
            root, role="CORE-DATA", receiver_role="US-01", kind="FACT",
            message_type="DATA_OBSERVATION", step="data", experiment_id=experiment_id,
            parent=None, asset=asset, source_refs=source, data_timestamp=data_ts,
            confidence=0.6 if quote else 0.2,
            limitations=["a stored mark is not an entry quote"],
            payload={"verdict": "SOURCED" if quote else "NO_SOURCED_PRICE", "price": None if quote is None else quote["price"]},
            rejected=quote is None, now=moment, seq=1,
        )
        analysis = _emit(
            root, role="US-01", receiver_role="US-02", kind="INFERENCE",
            message_type="OPPORTUNITY_CANDIDATE", step="analysis", experiment_id=experiment_id,
            parent=data["message_id"], asset=asset, source_refs=[data["message_id"]],
            data_timestamp=data_ts, confidence=0.4,
            limitations=["the rule is pre-registered and is not a forecast"],
            payload={"rule_id": RULE_ID}, rejected=False, now=moment, seq=2,
        )
        hypothesis = _emit(
            root, role="US-02", receiver_role="UNI-02", kind="HYPOTHESIS",
            message_type="STRATEGY_HYPOTHESIS", step="hypothesis", experiment_id=experiment_id,
            parent=analysis["message_id"], asset=asset, source_refs=[analysis["message_id"]],
            data_timestamp=data_ts, confidence=0.3,
            limitations=["one tiny paper round trip, and only if the rule matches"],
            payload={"statement": "a fresh NYSE session can hold one one-dollar long", "rule_id": RULE_ID},
            rejected=False, now=moment, seq=3,
        )
        experiment = _emit(
            root, role="UNI-02", receiver_role="RED-01", kind="INFERENCE",
            message_type="EXPERIMENT_RESULT", step="experiment", experiment_id=experiment_id,
            parent=hypothesis["message_id"], asset=asset, source_refs=[RULE_ID],
            data_timestamp=data_ts, confidence=0.5,
            limitations=["the exit is a later time stop, not this same call"],
            payload={
                "rule_id": RULE_ID, "notional_usd": NOTIONAL_USD, "exit_after_s": EXIT_AFTER_S,
                "pass_stats": False, "promoted": False,
            },
            rejected=False, now=moment, seq=4,
        )
        red = _emit(
            root, role="RED-01", receiver_role="JUDGE-01", kind="INFERENCE",
            message_type="RED_TEAM_FINDING", step="red_team", experiment_id=experiment_id,
            parent=experiment["message_id"], asset=asset, source_refs=[experiment["message_id"]],
            data_timestamp=data_ts, confidence=0.7,
            limitations=["a future price is not an entry"],
            payload={"lookahead": False, "verdict": "NO_ATTACK_HIT", "promoted": False},
            rejected=False, now=moment, seq=5,
        )
        reasons = _blockers(root, quote, moment, None)
        judge = _emit(
            root, role="JUDGE-01", receiver_role="US-05", kind="INFERENCE",
            message_type="PROMOTION_DECISION", step="judge", experiment_id=experiment_id,
            parent=red["message_id"], asset=asset, source_refs=[red["message_id"]],
            data_timestamp=data_ts, confidence=0.9,
            limitations=["a paper entry is not a promotion"],
            payload={"verdict": "NO_PROMOTION", "paper_entry": "ALLOWED" if not reasons else "WAITING", "reasons": reasons},
            rejected=False, now=moment, seq=6,
        )
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
        _emit(
            root, role="RED-02", receiver_role="JUDGE-01", kind="INFERENCE",
            message_type="RED_TEAM_FINDING", step="rejected",
            experiment_id=experiment_id + "-reject", parent=bad["message_id"], asset=asset,
            source_refs=[bad["message_id"]], data_timestamp=future, confidence=0.9,
            limitations=["a future timestamp is leakage"],
            payload={"verdict": "REJECT", "reason": "LOOKAHEAD"},
            rejected=True, now=moment, seq=2,
        )
        state = {
            "experiment_id": experiment_id,
            "status": "WAITING",
            "judge_id": judge["message_id"],
            "seq": 7,
            "reasons": reasons,
            "promoted": False,
            "rule_id": RULE_ID,
            "pid": os.getpid(),
        }
        if not reasons and quote is not None:
            opened = _open_trade(root, state, quote, moment)
            _emit(
                root, role="US-05", receiver_role="UNI-01", kind="FACT",
                message_type="PAPER_TRADE_RESULT", step="paper", experiment_id=experiment_id,
                parent=judge["message_id"], asset=asset, source_refs=[opened["trade_id"]],
                data_timestamp=data_ts, confidence=0.8,
                limitations=["the exit is still in the future"],
                payload={"trade_id": opened["trade_id"], "opened_at": state["opened_at"], "notional_usd": NOTIONAL_USD},
                rejected=False, now=moment, seq=7,
            )
            state["seq"] = 8
        else:
            _emit(
                root, role="US-05", receiver_role="UNI-01", kind="FACT",
                message_type="NO_TRADE_DECISION", step="no_setup", experiment_id=experiment_id,
                parent=judge["message_id"], asset=asset, source_refs=[judge["message_id"]],
                data_timestamp=data_ts, confidence=0.8,
                limitations=["no order was opened"],
                payload={"verdict": "NO_SETUP", "reasons": reasons},
                rejected=False, now=moment, seq=7,
            )
            state["seq"] = 8
        _save_state(root, state)
        _remember(root, state)
        return {"experiment_id": experiment_id, "status": state["status"], "reasons": reasons, "promoted": False}

    if state.get("status") == "CLOSED":
        return {"experiment_id": state.get("experiment_id"), "status": "CLOSED", "promoted": False, "close_id": state.get("close_id")}

    experiment_id = str(state["experiment_id"])
    asset = None if quote is None else str(quote["symbol"])
    data_ts = quote.get("market_time") if quote and isinstance(quote.get("market_time"), str) else None
    if state.get("status") == "OPEN":
        found = _find_close(root, experiment_id)
        held = 0.0
        if state.get("opened_at"):
            opened_at = datetime.fromisoformat(str(state["opened_at"]).replace("Z", "+00:00"))
            held = (moment - opened_at).total_seconds()
        exit_quote_ok = quote is not None and str(quote.get("symbol")) == state.get("symbol") and "QUOTE_STALE" not in _blockers(root, quote, moment, state.get("symbol"))
        if found is None and held >= EXIT_AFTER_S and exit_quote_ok and quote is not None:
            found = _close_trade(root, state, quote, moment)
        if found is None:
            state["reasons"] = ["WAITING_FOR_EXIT"]
            _save_state(root, state)
            _remember(root, state)
            return {"experiment_id": experiment_id, "status": "OPEN", "reasons": ["WAITING_FOR_EXIT"], "promoted": False}
        if str(found.get("closed_at") or "") <= str(found.get("opened_at") or state.get("opened_at") or ""):
            state["reasons"] = ["CLOSE_NOT_LATER_THAN_ENTRY"]
            _save_state(root, state)
            return {"experiment_id": experiment_id, "status": "OPEN", "reasons": state["reasons"], "promoted": False}
        lesson = _lesson_from_close(root, state, found)
        seq = int(state.get("seq") or 8)
        outcome = _emit(
            root, role="UNI-01", receiver_role="UNI-03", kind="FACT",
            message_type="PAPER_TRADE_RESULT", step="outcome", experiment_id=experiment_id,
            parent=state.get("judge_id"), asset=str(found.get("symbol")), source_refs=[str(found.get("trade_id"))],
            data_timestamp=data_ts, confidence=0.9,
            limitations=["the close is the ledger row, after costs"],
            payload={
                "close_id": found.get("trade_id"),
                "realized_pnl_usd": found.get("realized_pnl_usd"),
                "opened_at": found.get("opened_at") or state.get("opened_at"),
                "closed_at": found.get("closed_at"),
            },
            rejected=False, now=moment, seq=seq,
        )
        _emit(
            root, role="UNI-03", receiver_role="JUDGE-01", kind="INFERENCE",
            message_type="SYSTEM_HEALTH_REPORT", step="lesson", experiment_id=experiment_id,
            parent=outcome["message_id"], asset=str(found.get("symbol")), source_refs=[str(found.get("trade_id"))],
            data_timestamp=data_ts, confidence=0.7,
            limitations=["the lesson does not change a live weight"],
            payload=lesson, rejected=False, now=moment, seq=seq + 1,
        )
        state["status"] = "CLOSED"
        state["close_id"] = found.get("trade_id")
        state["closed_at"] = found.get("closed_at")
        state["opened_at"] = found.get("opened_at") or state.get("opened_at")
        state["realized_pnl_usd"] = found.get("realized_pnl_usd")
        state["reasons"] = []
        state["promoted"] = False
        _save_state(root, state)
        _remember(root, state)
        return {"experiment_id": experiment_id, "status": "CLOSED", "close_id": state["close_id"], "promoted": False, "lesson": lesson}

    reasons = _blockers(root, quote, moment, None)
    seq = int(state.get("seq") or 7)
    _emit(
        root, role="US-05", receiver_role="UNI-01", kind="FACT",
        message_type="NO_TRADE_DECISION", step="no_setup", experiment_id=experiment_id,
        parent=state.get("judge_id"), asset=asset, source_refs=[str(state.get("judge_id"))],
        data_timestamp=data_ts, confidence=0.8,
        limitations=["no order was opened"],
        payload={"verdict": "NO_SETUP", "reasons": reasons},
        rejected=False, now=moment, seq=seq,
    )
    state["seq"] = seq + 1
    state["reasons"] = reasons
    state["pid"] = os.getpid()
    if not reasons and quote is not None:
        opened = _open_trade(root, state, quote, moment)
        _emit(
            root, role="US-05", receiver_role="UNI-01", kind="FACT",
            message_type="PAPER_TRADE_RESULT", step="paper", experiment_id=experiment_id,
            parent=state.get("judge_id"), asset=asset, source_refs=[opened["trade_id"]],
            data_timestamp=data_ts, confidence=0.8,
            limitations=["the exit is still in the future"],
            payload={"trade_id": opened["trade_id"], "opened_at": state["opened_at"], "notional_usd": NOTIONAL_USD},
            rejected=False, now=moment, seq=state["seq"],
        )
        state["seq"] += 1
    _save_state(root, state)
    _remember(root, state)
    return {"experiment_id": experiment_id, "status": state["status"], "reasons": state.get("reasons") or [], "promoted": False}
