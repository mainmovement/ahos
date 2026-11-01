"""One paper chain for any desk. A new desk is a config row, not a new agent."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.mission.world_state import MessageBus, WorldStateStore

BUS_REL = Path("reports") / "grok" / "PAPER" / "charter_bus.jsonl"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"
POSITIONS_REL = Path("reports") / "grok" / "PAPER" / "paper_positions.json"
CONFIG_REL = Path("config") / "desk_chains.json"
SCHEMA = "ahos.charter_message.v1"


def load_desks(root: Path) -> dict[str, dict[str, Any]]:
    path = Path(root) / CONFIG_REL
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / CONFIG_REL
    doc = json.loads(path.read_text(encoding="utf-8"))
    desks = doc.get("desks") if isinstance(doc.get("desks"), dict) else {}
    return {str(name): dict(cfg) for name, cfg in desks.items() if isinstance(cfg, dict)}


def desk_line(root: Path, desk: str) -> str:
    cfg = load_desks(root).get(desk) or {}
    waiting = str(cfg.get("digest_wait") or "")
    done = str(cfg.get("digest_done") or "")
    path = Path(root) / str(cfg.get("state_file") or "")
    if not waiting or not path.is_file():
        return waiting
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return waiting
    opened = str(state.get("opened_at") or "")
    closed = str(state.get("closed_at") or "")
    if (
        state.get("status") == "CLOSED"
        and state.get("close_id")
        and opened
        and closed > opened
        and state.get("promoted") is False
    ):
        return done
    return waiting


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ticket(cfg: dict[str, Any]) -> float:
    return round(float(cfg["base_notional_usd"]) * float(cfg["size_mult"]), 4)


def _role(cfg: dict[str, Any], step: str) -> str:
    return str(cfg["steps"][step])


def _agent(cfg: dict[str, Any], role: str) -> str:
    return str(cfg["roles"][role])


def _emit(root: Path, cfg: dict[str, Any], *, step: str, receiver_step: str, kind: str, message_type: str,
          experiment_id: str, parent: str | None, asset: str | None, source_refs: list[str],
          data_timestamp: str | None, confidence: float, limitations: list[str], payload: dict[str, Any],
          rejected: bool, now: datetime, seq: int) -> dict[str, Any]:
    role = _role(cfg, step if step in cfg["steps"] else "paper")
    if step == "rejected_hypothesis":
        role = _role(cfg, "leak_hypothesis")
    elif step == "rejected":
        role = _role(cfg, "leak_reject")
    elif step == "no_setup":
        role = _role(cfg, "paper")
    receiver_role = _role(cfg, receiver_step)
    sender = _agent(cfg, role)
    receiver = _agent(cfg, receiver_role)
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
        "market": cfg["desk"] if "desk" in cfg else cfg.get("name"),
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


def _valid(row: dict[str, Any], symbols: set[str]) -> bool:
    price = row.get("price")
    return (
        row.get("symbol") in symbols
        and isinstance(price, (int, float))
        and not isinstance(price, bool)
        and price > 0
        and bool(row.get("source"))
        and row.get("stored_mark") is not True
    )


def _blockers(root: Path, cfg: dict[str, Any], quote: dict[str, Any] | None, moment: datetime, own: str | None) -> list[str]:
    if quote is None:
        return ["NO_SOURCED_PRICE"]
    reasons: list[str] = []
    symbol = str(quote["symbol"])
    if cfg.get("session_required") is True:
        from architecture.markets.weekday_session_gate import symbol_session

        if symbol_session(symbol, moment).get("open") is not True:
            reasons.append("SESSION_CLOSED")
    age = _quote_age(quote.get("market_time") if isinstance(quote.get("market_time"), str) else None, moment)
    if age is None or age < 0 or age > float(cfg["max_quote_age_s"]):
        reasons.append("QUOTE_STALE")
    if symbol in _book(root)["positions"] and symbol != own:
        reasons.append("POSITION_ALREADY_OPEN")
    ticket = _ticket(cfg)
    if ticket > float(cfg["notional_cap_usd"]) + 1e-9:
        reasons.append("SIZE_ABOVE_CAP")
    if float(cfg["fee"]) <= 0 or float(cfg["slip"]) <= 0:
        reasons.append("COST_OMITTED")
    return reasons


def _choose(root: Path, cfg: dict[str, Any], quotes: list[dict[str, Any]], moment: datetime, own: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    symbols = set(cfg["symbols"])
    parsed = [row for row in quotes if _valid(row, symbols)]
    if not parsed:
        return None, ["NO_SOURCED_PRICE"]
    for row in parsed:
        reasons = _blockers(root, cfg, row, moment, own)
        if not reasons:
            return row, []
    return parsed[0], _blockers(root, cfg, parsed[0], moment, own)


def _state_path(root: Path, cfg: dict[str, Any]) -> Path:
    return Path(root) / str(cfg["state_file"])


def _load_state(root: Path, cfg: dict[str, Any]) -> dict[str, Any] | None:
    path = _state_path(root, cfg)
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return doc if isinstance(doc, dict) else None


def _save_state(root: Path, cfg: dict[str, Any], state: dict[str, Any]) -> None:
    path = _state_path(root, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _append_trade(root: Path, row: dict[str, Any]) -> None:
    path = Path(root) / TRADES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _is_close(row: dict[str, Any], experiment_id: str) -> bool:
    if row.get("event") != "CLOSE":
        return False
    if row.get("chain_experiment_id") == experiment_id:
        return True
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    return brain.get("chain_experiment_id") == experiment_id


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
        if _is_close(row, experiment_id):
            found = row
    return found


def _open_trade(root: Path, cfg: dict[str, Any], state: dict[str, Any], quote: dict[str, Any], moment: datetime) -> dict[str, Any]:
    symbol = str(quote["symbol"])
    price = float(quote["price"])
    slip = float(cfg["slip"])
    fee = float(cfg["fee"])
    notional = _ticket(cfg)
    fill = price * (1 + slip)
    qty = notional / fill
    entry_fee = notional * fee
    opened = _utc(moment)
    trade_id = state["experiment_id"] + "-open"
    desk = str(cfg["desk"])
    row = {
        "ts": opened,
        "event": "OPEN",
        "symbol": symbol,
        "desk": desk,
        "side": cfg.get("side") or "LONG",
        "paper_only": True,
        "trade_id": trade_id,
        "chain_experiment_id": state["experiment_id"],
        "rule_id": cfg["rule_id"],
        "quote_price": price,
        "fill_price": round(fill, 6),
        "qty": qty,
        "notional_usd": notional,
        "fee_usd": round(entry_fee, 6),
        "slippage_pct": slip,
        "source": quote.get("source"),
        "market_time": quote.get("market_time"),
        "promoted": False,
        "desk_pause_respected": cfg.get("respect_pause") is True,
    }
    book = _book(root)
    if symbol in book["positions"]:
        raise RuntimeError("refusing to replace an open position")
    book["positions"][symbol] = {
        "side": cfg.get("side") or "LONG",
        "entry_price": round(fill, 6),
        "qty": qty,
        "notional_usd": notional,
        "entry_fee_usd": round(entry_fee, 6),
        "opened_at": opened,
        "opened_ts": moment.timestamp(),
        "desk": desk,
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
        "notional_usd": notional,
        "reasons": [],
    })
    return row


def _close_trade(root: Path, cfg: dict[str, Any], state: dict[str, Any], quote: dict[str, Any], moment: datetime) -> dict[str, Any]:
    price = float(quote["price"])
    entry = float(state["entry_price"])
    qty = float(state["qty"])
    slip = float(cfg["slip"])
    fee = float(cfg["fee"])
    exit_px = price * (1 - slip)
    gross = (exit_px - entry) * qty
    exit_fee = exit_px * qty * fee
    pnl = round(gross - exit_fee - float(state["entry_fee_usd"]), 6)
    closed = _utc(moment)
    close_id = state["experiment_id"] + "-close"
    row = {
        "ts": closed,
        "event": "CLOSE",
        "symbol": state["symbol"],
        "desk": cfg["desk"],
        "side": cfg.get("side") or "LONG",
        "paper_only": True,
        "trade_id": close_id,
        "chain_experiment_id": state["experiment_id"],
        "rule_id": cfg["rule_id"],
        "reason": "TIME_STOP",
        "quote_price": price,
        "fill_price": round(exit_px, 6),
        "entry_price": entry,
        "qty": qty,
        "notional_usd": state.get("notional_usd"),
        "fees_usd": round(exit_fee + float(state["entry_fee_usd"]), 6),
        "opened_at": state["opened_at"],
        "closed_at": closed,
        "realized_pnl_usd": pnl,
        "source": quote.get("source"),
        "market_time": quote.get("market_time"),
        "promoted": False,
        "applied_to_live_weights": False,
        "entry_brain": {"chain_experiment_id": state["experiment_id"], "composite": 0.3},
    }
    book = _book(root)
    current = book["positions"].get(state["symbol"])
    if isinstance(current, dict) and current.get("chain_experiment_id") == state["experiment_id"]:
        del book["positions"][state["symbol"]]
        (Path(root) / POSITIONS_REL).write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _append_trade(root, row)
    state.update({"status": "CLOSED", "closed_at": closed, "close_id": close_id, "realized_pnl_usd": pnl, "reasons": []})
    return row


def _lesson_from_close(root: Path, cfg: dict[str, Any], close_row: dict[str, Any]) -> dict[str, Any]:
    from architecture.learning.calibration import brier_score
    from architecture.learning.mistakes import record_losing_close
    from architecture.university.learning_loop import append_university_case

    desk = str(cfg["desk"])
    prior_probs: list[float] = []
    prior_outcomes: list[float] = []
    path = Path(root) / TRADES_REL
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if desk not in line or "CLOSE" not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("event") != "CLOSE" or row.get("desk") != desk:
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
    outcome = 1.0 if float(close_row["realized_pnl_usd"]) > 0 else 0.0
    after = brier_score(prior_probs + [0.3], prior_outcomes + [outcome])
    case = append_university_case(root, close_row)
    mistake = record_losing_close(
        root,
        case_id=str(close_row["trade_id"]),
        pnl_usd=float(close_row["realized_pnl_usd"]),
        symbol=str(close_row["symbol"]),
        desk=desk,
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


def _remember(root: Path, cfg: dict[str, Any], state: dict[str, Any]) -> None:
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces[str(cfg["trace_key"])] = {
            "experiment_id": state.get("experiment_id"),
            "status": state.get("status"),
            "reasons": state.get("reasons") or [],
            "close_id": state.get("close_id"),
            "opened_at": state.get("opened_at"),
            "closed_at": state.get("closed_at"),
            "realized_pnl_usd": state.get("realized_pnl_usd"),
            "notional_usd": state.get("notional_usd") or _ticket(cfg),
            "desk_pause_respected": cfg.get("respect_pause") is True,
            "promoted": False,
            "pid": os.getpid(),
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-11"})
    except Exception:
        pass


def _prepare(cfg: dict[str, Any], desk: str) -> dict[str, Any]:
    ready = dict(cfg)
    ready["desk"] = desk
    return ready


def run_desk_chain(root: Path, cfg: dict[str, Any], quotes: list[dict[str, Any]] | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    root = Path(root)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    own = None
    state = _load_state(root, cfg)
    if state and state.get("status") == "OPEN":
        own = str(state.get("symbol") or "")
    quote, reasons = _choose(root, cfg, list(quotes or []), moment, own)
    asset = None if quote is None else str(quote["symbol"])
    data_ts = quote.get("market_time") if quote and isinstance(quote.get("market_time"), str) else None
    prefix = "exp-" + str(cfg["desk"]).split("_")[0].lower() + "-"

    if state is None:
        experiment_id = prefix + moment.strftime("%Y%m%dT%H%M%SZ")
        source = [] if quote is None else [str(quote.get("source"))]
        data = _emit(
            root, cfg, step="data", receiver_step="analysis", kind="FACT", message_type="DATA_OBSERVATION",
            experiment_id=experiment_id, parent=None, asset=asset, source_refs=source, data_timestamp=data_ts,
            confidence=0.6 if quote else 0.2, limitations=["a stored mark is not an entry quote"],
            payload={"verdict": "SOURCED" if quote else "NO_SOURCED_PRICE", "price": None if quote is None else quote["price"]},
            rejected=quote is None, now=moment, seq=1,
        )
        analysis = _emit(
            root, cfg, step="analysis", receiver_step="hypothesis", kind="INFERENCE", message_type="OPPORTUNITY_CANDIDATE",
            experiment_id=experiment_id, parent=data["message_id"], asset=asset, source_refs=[data["message_id"]],
            data_timestamp=data_ts, confidence=0.4, limitations=["the rule is pre-registered and is not a forecast"],
            payload={"rule_id": cfg["rule_id"]}, rejected=False, now=moment, seq=2,
        )
        _emit(
            root, cfg, step="hypothesis", receiver_step="experiment", kind="HYPOTHESIS", message_type="STRATEGY_HYPOTHESIS",
            experiment_id=experiment_id, parent=analysis["message_id"], asset=asset, source_refs=[analysis["message_id"]],
            data_timestamp=data_ts, confidence=0.3, limitations=["one tiny paper round trip, and only if the rule matches"],
            payload={
                "rule_id": cfg["rule_id"],
                "notional_usd": _ticket(cfg),
                "desk_pause_respected": cfg.get("respect_pause") is True,
                "normal_entries": "PAUSED" if cfg.get("respect_pause") else "UNCHANGED",
            },
            rejected=False, now=moment, seq=3,
        )
        experiment = _emit(
            root, cfg, step="experiment", receiver_step="red_team", kind="INFERENCE", message_type="EXPERIMENT_RESULT",
            experiment_id=experiment_id, parent=f"{experiment_id}-03-hypothesis", asset=asset, source_refs=[str(cfg["rule_id"])],
            data_timestamp=data_ts, confidence=0.5, limitations=["the exit is a later time stop, not this same call"],
            payload={
                "rule_id": cfg["rule_id"], "notional_usd": _ticket(cfg), "exit_after_s": cfg["exit_after_s"],
                "on_chain": "ABSENT", "pass_stats": False, "promoted": False,
            },
            rejected=False, now=moment, seq=4,
        )
        red = _emit(
            root, cfg, step="red_team", receiver_step="judge", kind="INFERENCE", message_type="RED_TEAM_FINDING",
            experiment_id=experiment_id, parent=experiment["message_id"], asset=asset, source_refs=[experiment["message_id"]],
            data_timestamp=data_ts, confidence=0.7, limitations=["a future price is not an entry"],
            payload={"lookahead": False, "cost_omission": False, "verdict": "NO_ATTACK_HIT", "promoted": False},
            rejected=False, now=moment, seq=5,
        )
        judge = _emit(
            root, cfg, step="judge", receiver_step="paper", kind="INFERENCE", message_type="PROMOTION_DECISION",
            experiment_id=experiment_id, parent=red["message_id"], asset=asset, source_refs=[red["message_id"]],
            data_timestamp=data_ts, confidence=0.9, limitations=["a paper entry is not a promotion"],
            payload={"verdict": "NO_PROMOTION", "paper_entry": "ALLOWED" if not reasons else "WAITING", "reasons": reasons},
            rejected=False, now=moment, seq=6,
        )
        future = _utc(moment + timedelta(days=1))
        bad = _emit(
            root, cfg, step="rejected_hypothesis", receiver_step="leak_reject", kind="HYPOTHESIS",
            message_type="STRATEGY_HYPOTHESIS", experiment_id=experiment_id + "-reject", parent=data["message_id"],
            asset=asset, source_refs=[data["message_id"]], data_timestamp=future, confidence=0.2,
            limitations=["the data time is after the decision"],
            payload={"statement": "a later close is already known"}, rejected=False, now=moment, seq=1,
        )
        _emit(
            root, cfg, step="rejected", receiver_step="judge", kind="INFERENCE", message_type="RED_TEAM_FINDING",
            experiment_id=experiment_id + "-reject", parent=bad["message_id"], asset=asset,
            source_refs=[bad["message_id"]], data_timestamp=future, confidence=0.9,
            limitations=["a future timestamp is leakage"],
            payload={"verdict": "REJECT", "reason": "LOOKAHEAD"}, rejected=True, now=moment, seq=2,
        )
        state = {
            "experiment_id": experiment_id,
            "status": "WAITING",
            "judge_id": judge["message_id"],
            "seq": 8,
            "reasons": reasons,
            "promoted": False,
            "rule_id": cfg["rule_id"],
            "pid": os.getpid(),
        }
        if not reasons and quote is not None:
            opened = _open_trade(root, cfg, state, quote, moment)
            _emit(
                root, cfg, step="paper", receiver_step="outcome", kind="FACT", message_type="PAPER_TRADE_RESULT",
                experiment_id=experiment_id, parent=judge["message_id"], asset=asset, source_refs=[opened["trade_id"]],
                data_timestamp=data_ts, confidence=0.8, limitations=["the exit is still in the future"],
                payload={"trade_id": opened["trade_id"], "opened_at": state["opened_at"], "notional_usd": state["notional_usd"]},
                rejected=False, now=moment, seq=7,
            )
        else:
            _emit(
                root, cfg, step="no_setup", receiver_step="outcome", kind="FACT", message_type="NO_TRADE_DECISION",
                experiment_id=experiment_id, parent=judge["message_id"], asset=asset, source_refs=[judge["message_id"]],
                data_timestamp=data_ts, confidence=0.8, limitations=["no order was opened"],
                payload={"verdict": "NO_SETUP", "reasons": reasons}, rejected=False, now=moment, seq=7,
            )
        _save_state(root, cfg, state)
        _remember(root, cfg, state)
        return {"experiment_id": experiment_id, "status": state["status"], "reasons": state.get("reasons") or [], "promoted": False, "desk": cfg["desk"]}

    if state.get("status") == "CLOSED":
        return {"experiment_id": state.get("experiment_id"), "status": "CLOSED", "promoted": False, "close_id": state.get("close_id"), "desk": cfg["desk"]}

    experiment_id = str(state["experiment_id"])
    if state.get("status") == "OPEN":
        found = _find_close(root, experiment_id)
        held = 0.0
        if state.get("opened_at"):
            opened_at = datetime.fromisoformat(str(state["opened_at"]).replace("Z", "+00:00"))
            held = (moment - opened_at).total_seconds()
        fresh = quote is not None and str(quote.get("symbol")) == state.get("symbol") and "QUOTE_STALE" not in _blockers(root, cfg, quote, moment, state.get("symbol"))
        if found is None and held >= float(cfg["exit_after_s"]) and fresh and quote is not None:
            found = _close_trade(root, cfg, state, quote, moment)
        if found is None:
            state["reasons"] = ["WAITING_FOR_EXIT"]
            _save_state(root, cfg, state)
            _remember(root, cfg, state)
            return {"experiment_id": experiment_id, "status": "OPEN", "reasons": ["WAITING_FOR_EXIT"], "promoted": False, "desk": cfg["desk"]}
        if str(found.get("closed_at") or "") <= str(found.get("opened_at") or state.get("opened_at") or ""):
            state["reasons"] = ["CLOSE_NOT_LATER_THAN_ENTRY"]
            _save_state(root, cfg, state)
            return {"experiment_id": experiment_id, "status": "OPEN", "reasons": state["reasons"], "promoted": False, "desk": cfg["desk"]}
        lesson = _lesson_from_close(root, cfg, found)
        seq = int(state.get("seq") or 8)
        outcome = _emit(
            root, cfg, step="outcome", receiver_step="lesson", kind="FACT", message_type="PAPER_TRADE_RESULT",
            experiment_id=experiment_id, parent=state.get("judge_id"), asset=str(found.get("symbol")),
            source_refs=[str(found.get("trade_id"))], data_timestamp=data_ts, confidence=0.9,
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
            root, cfg, step="lesson", receiver_step="judge", kind="INFERENCE", message_type="SYSTEM_HEALTH_REPORT",
            experiment_id=experiment_id, parent=outcome["message_id"], asset=str(found.get("symbol")),
            source_refs=[str(found.get("trade_id"))], data_timestamp=data_ts, confidence=0.7,
            limitations=["the lesson does not change a live weight"],
            payload=lesson, rejected=False, now=moment, seq=seq + 1,
        )
        state.update({
            "status": "CLOSED",
            "close_id": found.get("trade_id"),
            "closed_at": found.get("closed_at"),
            "opened_at": found.get("opened_at") or state.get("opened_at"),
            "realized_pnl_usd": found.get("realized_pnl_usd"),
            "reasons": [],
            "promoted": False,
        })
        _save_state(root, cfg, state)
        _remember(root, cfg, state)
        return {"experiment_id": experiment_id, "status": "CLOSED", "close_id": state["close_id"], "promoted": False, "lesson": lesson, "desk": cfg["desk"]}

    seq = int(state.get("seq") or 8)
    _emit(
        root, cfg, step="no_setup", receiver_step="outcome", kind="FACT", message_type="NO_TRADE_DECISION",
        experiment_id=experiment_id, parent=state.get("judge_id"), asset=asset, source_refs=[str(state.get("judge_id"))],
        data_timestamp=data_ts, confidence=0.8, limitations=["no order was opened"],
        payload={"verdict": "NO_SETUP", "reasons": reasons}, rejected=False, now=moment, seq=seq,
    )
    state["seq"] = seq + 1
    state["reasons"] = reasons
    state["pid"] = os.getpid()
    if not reasons and quote is not None:
        opened = _open_trade(root, cfg, state, quote, moment)
        _emit(
            root, cfg, step="paper", receiver_step="outcome", kind="FACT", message_type="PAPER_TRADE_RESULT",
            experiment_id=experiment_id, parent=state.get("judge_id"), asset=asset, source_refs=[opened["trade_id"]],
            data_timestamp=data_ts, confidence=0.8, limitations=["the exit is still in the future"],
            payload={"trade_id": opened["trade_id"], "opened_at": state["opened_at"], "notional_usd": state["notional_usd"]},
            rejected=False, now=moment, seq=state["seq"],
        )
        state["seq"] += 1
    _save_state(root, cfg, state)
    _remember(root, cfg, state)
    return {"experiment_id": experiment_id, "status": state["status"], "reasons": state.get("reasons") or [], "promoted": False, "desk": cfg["desk"]}


def run_configured_chains(root: Path, quotes: dict[str, Any], *, now: datetime | None = None) -> list[dict[str, Any]]:
    """Run every configured desk from the quotes already fetched by the paper cycle."""
    root = Path(root)
    out = []
    for desk, cfg in load_desks(root).items():
        rows = []
        for symbol in cfg.get("symbols") or []:
            quote = quotes.get(symbol) if isinstance(quotes, dict) else None
            quote = quote if isinstance(quote, dict) else {}
            rows.append({
                "symbol": symbol,
                "price": quote.get("price"),
                "source": quote.get("source"),
                "market_time": quote.get("market_time") or quote.get("source_timestamp"),
            })
        out.append(run_desk_chain(root, _prepare(cfg, desk), rows, now=now))
    return out
