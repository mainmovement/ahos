"""BRAIN-01 can rank and veto. It cannot promote or raise a weight."""
import json
from datetime import datetime, timedelta, timezone

from architecture.mission.brain01 import brain_line, run_brain
from architecture.mission.desk_chain_template import load_desks, run_desk_chain


def _state(root, desk: str, reasons: list[str]) -> None:
    cfg = load_desks(root)[desk]
    path = root / cfg["state_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "experiment_id": f"exp-{desk.lower()}-fixture",
        "status": "WAITING",
        "reasons": reasons,
        "promoted": False,
    }), encoding="utf-8")


def test_brain_ranks_and_issues_no_trade(tmp_path) -> None:
    pause = tmp_path / "reports" / "grok" / "PAPER" / "desk_pause.json"
    pause.parent.mkdir(parents=True)
    pause.write_text(json.dumps({
        "paused_desks": ["OIL", "CRYPTO", "ASIA_EQUITIES"],
        "desks": [{"desk": "OIL", "expectancy_usd": -0.005}, {"desk": "GOLD", "expectancy_usd": -0.02}],
    }), encoding="utf-8")
    _state(tmp_path, "GOLD", ["SESSION_CLOSED"])
    _state(tmp_path, "OIL", [])
    decision = run_brain(tmp_path, now=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc))
    assert decision["verdict"] == "NO_TRADE"
    assert decision["ranked"] == 0
    assert decision["rejected"] >= 2
    assert decision["promoted"] is False
    assert decision["applied_to_live_weights"] is False
    assert decision["live_switch"] == "UNTOUCHED"
    assert decision["support_roles"]["SEC-01"] == "INSUFFICIENT_EVIDENCE"
    oil = next(row for row in decision["rows"] if row["desk"] == "OIL")
    assert "DESK_EXPECTANCY_PAUSE" in oil["blocks"]
    assert oil["verdict"] == "VETO"
    state = json.loads((tmp_path / "reports" / "grok" / "PAPER" / "brain01_state.json").read_text(encoding="utf-8"))
    assert state["calls"] == 1
    steps = [
        json.loads(line)["step"]
        for line in (tmp_path / "reports" / "grok" / "PAPER" / "charter_bus.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert steps == ["rank", "no_trade"]
    line = brain_line(tmp_path)
    assert line.startswith("مغز مرکزی:")
    assert "رد شد" in line
    assert not any(ch.isascii() and ch.isalpha() for ch in line)
    assert not (tmp_path / "reports" / "grok" / "PAPER" / "signal_weights.json").exists()


def test_brain_veto_blocks_a_later_open(tmp_path) -> None:
    book = tmp_path / "reports" / "grok" / "PAPER"
    book.mkdir(parents=True)
    (book / "brain01_decision.json").write_text(json.dumps({"allowed": []}), encoding="utf-8")
    cfg = dict(load_desks(tmp_path)["GOLD"])
    cfg["desk"] = "GOLD"
    closed = datetime(2026, 11, 1, 8, 46, tzinfo=timezone.utc)
    quote = [{
        "symbol": "XAU",
        "price": 4000.0,
        "source": "fixture",
        "market_time": (closed - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }]
    run_desk_chain(tmp_path, cfg, quote, now=closed)
    reopen = datetime(2026, 11, 1, 23, 5, tzinfo=timezone.utc)
    fresh = [{
        "symbol": "XAU",
        "price": 4001.0,
        "source": "fixture",
        "market_time": (reopen - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }]
    second = run_desk_chain(tmp_path, cfg, fresh, now=reopen)
    assert second["status"] == "WAITING"
    assert "BRAIN_VETO" in second["reasons"]
    assert not (book / "paper_trades.jsonl").exists()
