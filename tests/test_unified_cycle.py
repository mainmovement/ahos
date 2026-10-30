from datetime import datetime, timezone

import pytest
import yaml

from agent_org.contracts import AgentMessage, RequiredAction
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.mission.unified_cycle import run_unified_cycle, trace_decision
from architecture.mission.world_state import MessageBus, WorldStateStore


NOW = datetime(2026, 10, 30, tzinfo=timezone.utc)


def _registry(root, ids):
    path = root / "config"
    path.mkdir(parents=True)
    doc = {"agents": [{"agent_id": aid, "name": aid, "status": "EXISTS"} for aid in ids]}
    (path / "agent_registry.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")


def test_the_store_versions_and_the_bus_rejects_a_bare_dict(tmp_path):
    store = WorldStateStore(tmp_path)
    first = store.commit({"positions": {"status": "ABSENT", "decides": False}}, {"positions": "AG-16"}, now=NOW)
    second = store.commit({"news": {"status": "ABSENT", "decides": False}}, {"news": "AG-33"}, now=NOW)
    assert first["version"] == 1 and second["version"] == 2
    assert second["decides"] is False and second["sections"]["positions"]["status"] == "ABSENT"
    with pytest.raises(ValueError):
        store.commit({"orders": {}}, {"orders": "AG-16"}, now=NOW)
    bus = MessageBus(tmp_path)
    with pytest.raises(TypeError):
        bus.deliver({"sender": "AG-09", "receiver": "AG-16"})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        AgentMessage("AG-09", "AG-09", ("reports/x",), "self", 1.0, RequiredAction.OBSERVE)


def test_one_cycle_fans_out_didehban_and_negahban_and_names_the_silent_modules(tmp_path):
    _registry(tmp_path, ["AG-09", "AG-16", "AG-33"])
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text(
        '{"event":"NO_TRADE","symbol":"BTC","desk":"CRYPTO","reason":"MULTI_SIGNAL_AGREEMENT"}\n',
        encoding="utf-8",
    )
    receipt = run_unified_cycle(tmp_path, now=NOW)
    assert receipt["decides"] is False
    assert receipt["messages_delivered"] == 4
    assert receipt["message_senders"] == ["AG-09", "AG-33"]
    assert receipt["gaps_closed"] == []
    silent = {row["module"]: row["reason"] for row in receipt["modules_silent"]}
    assert silent["judge"] == "NOT_IN_REGISTRY"
    assert silent["dashboard"] == "NOT_IN_REGISTRY"
    assert "AG-16" in receipt["agents_with_no_outbound"]
    assert "AG-09" not in receipt["agents_with_no_outbound"]
    state = WorldStateStore(tmp_path).read()
    assert state["version"] == 1
    assert state["sections"]["traces"]["n"] == 1
    text = state["sections"]["traces"]["latest"][0]["fa"]
    assert "دو خانواده" in text
    assert "حکم معامله نیست" in text
    rows = MessageBus(tmp_path).read()
    assert all(row["required_action"] == "OBSERVE" and row["decides"] is False for row in rows)
    assert {row["sender"] for row in rows} == {"AG-09", "AG-33"}
    traced = trace_decision({"event": "OPEN", "symbol": "XAU", "desk": "GOLD", "kian_explain_fa": "متن آماده"})
    assert traced["fa"] == "متن آماده" and traced["decides"] is False
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
