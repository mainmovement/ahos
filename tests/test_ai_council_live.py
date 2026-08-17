#!/usr/bin/env python3
"""Tests for the live multi-model AI council.

The council exists to get several opinions and reconcile them. These tests pin
the safety properties that stop it from becoming a hype amplifier:

  - zero providers => DETERMINISTIC_ONLY (a supported mode, not an error)
  - paid providers excluded unless explicitly allowed ($0 law)
  - a single AVOID outweighs a majority of ENTER (safety ratchet)
  - unanimity on thin evidence is flagged as ECHO, not celebrated
  - the deterministic layer can always overrule the council
  - a provider that returns junk degrades to UNCLEAR, never crashes
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.ai.clients import (  # noqa: E402
    AIClient, AIResponse, build_clients_from_registry, load_registry,
)
from architecture.ai.council_live import (  # noqa: E402
    LiveCouncil, parse_structured, build_evidence_packet, VALID_STANCES,
)

REGISTRY = ROOT / "config" / "ai_council_providers.yaml"


def _reply(stance: str, confidence: str = "HIGH") -> str:
    return (f"STANCE: {stance}\nCONFIDENCE: {confidence}\n"
            f"REASONS:\n- liquidity is $120,000\n- exit fraction 0.96\n"
            f"RISKS:\n- early token volatility")


def _mock(name: str, stance: str, confidence: str = "HIGH", paid: bool = False) -> AIClient:
    c = AIClient(name, {"model": "m", "cost": "paid" if paid else "free",
                        "base_url": "http://mock"})
    c.ask = lambda messages, max_tokens=700, allow_paid=False, _s=stance, _c=confidence: \
        AIResponse(name, "m", "OK", content=_reply(_s, _c))
    return c


def _dead(name: str) -> AIClient:
    c = AIClient(name, {"model": "m", "cost": "free", "base_url": "http://mock"})
    c.ask = lambda messages, max_tokens=700, allow_paid=False: \
        AIResponse(name, "m", "DOWN", error_state={"kind": "URLError"})
    return c


# ============================== REGISTRY ===================================

def test_registry_is_valid_and_free_first():
    reg = load_registry(REGISTRY)
    providers = reg["providers"]
    assert providers, "registry must declare providers"

    names = list(providers)
    first_paid = next((i for i, n in enumerate(names)
                       if str(providers[n].get("cost", "")).startswith("paid")), len(names))
    last_free = max((i for i, n in enumerate(names)
                     if not str(providers[n].get("cost", "")).startswith("paid")), default=-1)
    assert last_free < first_paid, "all free providers must precede paid ones"

    # The local provider must be first — it is the only Iran-immune option.
    assert "ollama" in names[0].lower()


def test_registry_covers_the_requested_assistants():
    """The user asked specifically for Claude, ChatGPT, Gemini and Grok."""
    reg = load_registry(REGISTRY)
    blob = " ".join(reg["providers"]).lower()
    for expected in ("claude", "gpt", "gemini", "grok"):
        assert expected in blob, f"{expected} missing from the council registry"


def test_clients_build_from_registry():
    clients = build_clients_from_registry(REGISTRY)
    assert len(clients) >= 5
    assert all(isinstance(c, AIClient) for c in clients)


def test_paid_client_refuses_without_permission():
    c = AIClient("paid_one", {"model": "m", "cost": "paid",
                              "base_url": "http://x", "key_env": None})
    r = c.ask([{"role": "user", "content": "hi"}], allow_paid=False)
    assert r.availability == "SKIPPED_PAID"
    assert r.ok is False


def test_client_without_key_is_skipped_not_called():
    called = []

    def transport(req, timeout=None):
        called.append(req)
        raise AssertionError("must not be called without a key")

    c = AIClient("keyed", {"model": "m", "cost": "free", "base_url": "http://x",
                           "key_env": "AHOS_DEFINITELY_UNSET_KEY_12345"},
                 transport=transport)
    r = c.ask([{"role": "user", "content": "hi"}])
    assert r.availability == "NO_KEY"
    assert called == []


# ============================== PARSING ====================================

def test_parse_structured_extracts_all_fields():
    p = parse_structured(_reply("ENTER", "MEDIUM"))
    assert p["stance"] == "ENTER"
    assert p["confidence"] == "MEDIUM"
    assert len(p["reasons"]) == 2
    assert p["risks"]


@pytest.mark.parametrize("junk", ["", "I think you should buy!", "STANCE: MAYBE", None])
def test_unparseable_reply_degrades_to_unclear(junk):
    p = parse_structured(junk)
    assert p["stance"] == "UNCLEAR"
    assert p["stance"] in VALID_STANCES


# ============================== COUNCIL ====================================

def test_no_providers_yields_deterministic_only():
    v = LiveCouncil(clients=[]).deliberate("packet")
    assert v.final_stance == "DETERMINISTIC_ONLY"
    assert v.council_status == "OFFLINE"
    assert v.responded == 0
    assert v.warnings


def test_all_providers_down_yields_deterministic_only():
    v = LiveCouncil([_dead("a"), _dead("b")]).deliberate("packet")
    assert v.final_stance == "DETERMINISTIC_ONLY"
    assert v.council_status == "OFFLINE"
    assert len(v.providers_failed) == 2


def test_unanimous_enter_is_reported_as_enter():
    v = LiveCouncil([_mock("a", "ENTER"), _mock("b", "ENTER"),
                     _mock("c", "ENTER")]).deliberate("packet")
    assert v.final_stance == "ENTER"
    assert v.agreement == "UNANIMOUS"
    assert v.responded == 3
    assert v.advisory_only is True


def test_single_avoid_downgrades_a_majority_enter():
    """THE SAFETY RATCHET: one credible objection beats a hopeful majority."""
    v = LiveCouncil([_mock("a", "ENTER"), _mock("b", "ENTER"),
                     _mock("c", "AVOID")]).deliberate("packet")
    assert v.agreement == "MAJORITY"
    assert v.final_stance == "WAIT", "an AVOID vote must never be averaged away"
    assert v.warnings


def test_even_split_is_reported_as_disagreement():
    v = LiveCouncil([_mock("a", "ENTER"), _mock("b", "AVOID")]).deliberate("packet")
    assert v.agreement == "SPLIT"
    assert v.final_stance in ("UNCLEAR", "WAIT")
    assert v.warnings


def test_echo_detected_when_unanimous_on_thin_evidence():
    v = LiveCouncil([_mock("a", "ENTER"), _mock("b", "ENTER")]).deliberate(
        "packet", evidence_is_thin=True)
    assert v.echo_suspected is True
    assert any("echo" in w.lower() or "هم‌آوایی" in w for w in v.warnings)


def test_no_echo_flag_when_evidence_is_solid():
    v = LiveCouncil([_mock("a", "ENTER"), _mock("b", "ENTER")]).deliberate(
        "packet", evidence_is_thin=False)
    assert v.echo_suspected is False


def test_deterministic_avoid_overrules_the_entire_council():
    """No amount of AI enthusiasm may overturn a measured veto."""
    v = LiveCouncil([_mock(n, "ENTER") for n in "abcde"]).deliberate(
        "packet", deterministic_stance="AVOID")
    assert v.final_stance == "AVOID"
    assert v.warnings


def test_partial_availability_still_produces_a_verdict():
    v = LiveCouncil([_mock("a", "ENTER"), _dead("b"), _mock("c", "ENTER")]).deliberate("packet")
    assert v.council_status == "ONLINE"
    assert v.responded == 2
    assert len(v.providers_failed) == 1
    assert v.final_stance == "ENTER"


def test_reasons_are_deduplicated_and_bounded():
    v = LiveCouncil([_mock(n, "ENTER") for n in "abcdef"]).deliberate("packet")
    assert len(v.reasons) <= 8
    assert len(v.reasons) == len(set(r.lower() for r in v.reasons))


def test_council_never_claims_authority():
    v = LiveCouncil([_mock("a", "ENTER")]).deliberate("packet")
    assert v.advisory_only is True
    assert v.to_dict()["advisory_only"] is True


# ============================ EVIDENCE PACKET ==============================

def test_evidence_packet_includes_unknowns_and_vetoes():
    class _Exit:
        verdict = "TRAPPED"
        realizable_fraction = 0.2
        max_safe_position_usd = 10.0
        hard_vetoes = ["honeypot detected"]

    packet = build_evidence_packet(exitability=_Exit())
    assert "TRAPPED" in packet
    assert "HARD_VETO" in packet
    assert "honeypot detected" in packet


def test_evidence_packet_is_a_string_even_when_empty():
    packet = build_evidence_packet()
    assert isinstance(packet, str)
    assert "EVIDENCE PACKET" in packet
