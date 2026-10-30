import pytest

from agent_org.contracts import (
    AgentLifecycleState,
    RequiredAction,
    parse_agent_message,
    transition_agent_lifecycle,
)
from architecture.mission.org_lifecycle import build_org_lifecycle, classify_agent


def test_message_rejects_promote_and_missing_evidence():
    with pytest.raises(ValueError):
        parse_agent_message({
            "sender": "AG-03",
            "receiver": "AG-16",
            "evidence": ["reports/grok/M28/batch5_research.json"],
            "claim": "shadow only",
            "confidence": 0.2,
            "required_action": "PROMOTE",
        })
    with pytest.raises(ValueError):
        parse_agent_message({
            "sender": "AG-03",
            "receiver": "AG-16",
            "evidence": [],
            "claim": "x",
            "confidence": 0.2,
            "required_action": "ADVISE",
        })


def test_message_accepts_advisory_envelope():
    msg = parse_agent_message({
        "sender": "AG-18",
        "receiver": "AG-16",
        "evidence": ["reports/grok/M58/loss_eval_cases.jsonl"],
        "claim": "loss cases stay UNVERIFIED",
        "confidence": 0.4,
        "required_action": "OBSERVE",
    })
    assert msg.required_action is RequiredAction.OBSERVE
    assert msg.as_dict()["decides"] is False


def test_illegal_lifecycle_transition():
    with pytest.raises(ValueError):
        transition_agent_lifecycle(AgentLifecycleState.ABSENT, AgentLifecycleState.LIVE_OBSERVED)
    assert transition_agent_lifecycle(AgentLifecycleState.DESIGNED, AgentLifecycleState.ARTIFACT_PRESENT) is AgentLifecycleState.ARTIFACT_PRESENT


def test_planned_seat_is_not_a_filled_exists_seat():
    agent = {"status": "PLANNED", "evidence": "design", "ops": {"operability": {"implemented": False, "live": False}}}
    state = classify_agent(agent, artifact_exists=True)
    assert state is AgentLifecycleState.ARTIFACT_PRESENT
    assert agent["status"] != "EXISTS"


def test_live_registry_lists_unfilled_seats():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    doc = build_org_lifecycle(root)
    assert doc["registry_agents"] == 43
    assert doc["filled_seats"] < 43
    ids = {row["agent_id"] for row in doc["unfilled_seats"]}
    assert "AG-01" in ids
    assert all(row["why_unfilled"] for row in doc["unfilled_seats"])
