#!/usr/bin/env python3
"""W9/P1 tests — cognitive matrix integrity, contract validation, agent registry,
lane isolation. Honesty lint: an agent marked EXISTS must point at evidence that exists."""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture import contracts, registry  # noqa: E402

MATRIX = yaml.safe_load((ROOT / "config" / "cognitive_principles.yaml").read_text())
REG = yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text())


def test_contract_schema_has_all_10_fields():
    s = contracts.load_schema()
    assert set(s["fields"]) == {"input", "output", "state", "error", "evidence", "confidence",
                                "timestamp", "provenance", "version", "health"}
    assert all(m.get("required") for m in s["fields"].values())


def test_matrix_every_principle_complete():
    # W11 schema v2 (W10 §14 mandated): new field names + extended status enum.
    req = {"principle_id", "source_thinker_or_school", "domain", "principle",
           "agent_capability", "probe", "contract", "test", "evidence_requirement",
           "status", "authority_level", "failure_mode", "ahos_application"}
    assert len(MATRIX["principles"]) >= 30
    statuses = {"EXISTING", "PARTIAL", "DEFINED", "UNTESTED", "REFUTED", "SUPPORTED"}
    for p in MATRIX["principles"]:
        assert req <= set(p), f"{p.get('principle_id')} missing fields"
        assert p["status"] in statuses
        assert p["failure_mode"] and p["evidence_requirement"]     # P0 law: falsifiable


def test_matrix_no_personality_simulation():
    """Anti-impersonation lint: no fictional quotes, no 'thinks like', attribution only."""
    banned = ("\"i ", "i believe", "would say", "thinks like", "personality", "in my own words")
    for p in MATRIX["principles"]:
        src = str(p["source_thinker_or_school"]).lower()
        assert not any(b in src for b in banned), f"{p['principle_id']} impersonation risk"


def test_matrix_existing_status_requires_anchor():
    """EXISTING/SUPPORTED must name a real anchor (test file / probe id); DEFINED must honestly
    admit no test. Never mark an unimplemented capability as operational."""
    for p in MATRIX["principles"]:
        if p["status"] in ("EXISTING", "SUPPORTED"):
            assert p["test"] and "none" not in str(p["test"]).lower(), \
                f"{p['principle_id']} claims {p['status']} without anchor"
        if p["status"] == "DEFINED":
            assert "none" in str(p["test"]).lower() or "spec" in str(p["test"]).lower()


def test_matrix_domains_cover_six():
    doms = {p["domain"] for p in MATRIX["principles"]}
    assert doms == {"crypto", "security", "mathematics", "engineering", "falsification", "product"}


def test_registry_agents_and_spec_conformance():
    agents = REG["agents"]
    assert len(agents) == 25                                      # 24 + AG-25 (W12 PART F)
    assert registry.validate_registry(REG) == {}                  # zero spec violations
    counts = {a["agent_id"] for a in agents}
    assert len(counts) == 25                                      # no duplicate ids
    assert REG["totals"]["agents"] == 25
    by_status = {}
    for a in agents:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
    for k, v in by_status.items():
        if k in REG["totals"]:
            assert REG["totals"][k] == v                          # totals block is truthful


def test_exists_agents_have_real_evidence_paths():
    """Honesty lint: status EXISTS ⇒ the cited evidence artifact must exist on disk."""
    for a in REG["agents"]:
        if a["status"] != "EXISTS":
            continue
        ev = a["evidence"]
        m = re.findall(r"[\w/{}_.-]+\.(?:py|json|yaml|sqlite|md|sql)", ev)
        assert m, f"{a['agent_id']} EXISTS but evidence cites no file: {ev}"
        for path in m[:2]:
            cleaned = path.replace("{", "").replace("}", "").split(",")[0]
            if "/" in cleaned:
                assert (ROOT / cleaned).exists(), f"{a['agent_id']} evidence missing: {cleaned}"


def test_authority_model_enforced():
    for a in REG["agents"]:
        if "AI" in a.get("capabilities", []) or a["agent_id"] in ("AG-11", "AG-12"):
            assert set(a["allowed_authority"]) <= {"ANALYZE", "ADVISE", "CHALLENGE"}
        assert not set(a["allowed_authority"]) & set(a["forbidden_authority"])
    deciders = [a["agent_id"] for a in REG["agents"] if "DECIDE" in a["allowed_authority"]]
    assert set(deciders) == {"AG-15", "AG-16"}                   # only deterministic engines decide


def test_registry_build_isolated_idempotent_append_only(tmp_path):
    store = tmp_path / "architecture_registry.sqlite"
    r1 = registry.build_registry(store, now=1_800_000_000.0)
    assert r1["built"] and r1["agents"] == 25 and r1["inserted_new"] == 25
    r2 = registry.build_registry(store, now=1_800_000_100.0)
    assert r2["inserted_new"] == 0 and r2["total_rows"] == 25    # idempotent, append-only
    conn = sqlite3.connect(store)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE agent SET status='MISSING'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM agent")
    conn.close()
    # isolation: registry store is NOT one of the experiment stores
    assert "architecture_registry" in r1["store"]
    assert "e01_discovery" not in r1["store"] and "paper_trading" not in r1["store"]


def test_envelope_validation_rules():
    T = 1_800_000_000.0
    good = contracts.make_envelope(agent_version="PT-X3-v2", output={"action": "HOLD"},
                                   evidence=["obs-123"], lane="A",
                                   confidence="SUPPORTED", ts=T)
    assert contracts.validate_envelope(good) == []
    bad = dict(good); bad.pop("error")
    assert any("error" in e for e in contracts.validate_envelope(bad))
    noev = contracts.make_envelope(agent_version="x", output=None, evidence=[], lane="B",
                                   confidence="UNKNOWN", error="NONE", ts=T)
    assert any("evidence" in e for e in contracts.validate_envelope(noev))  # no-claim law
    badconf = dict(good, confidence="LOOKS_GREAT")
    assert any("confidence" in e for e in contracts.validate_envelope(badconf))


def test_error_and_confidence_enums_cover_laws():
    s = contracts.load_schema()
    for e in ("NO_DATA", "STALE", "PROVIDER_DOWN", "VETO", "BUDGET", "CONTRACT_BREAK"):
        assert e in s["fields"]["error"]["values"]
    for c in ("PROVEN", "SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "UNKNOWN",
              "INSUFFICIENT_SAMPLE", "REFUTED", "CONTAMINATED"):
        assert c in s["fields"]["confidence"]["values"]


def test_lane_isolation_static():
    """architecture/ must never import experiment packages (Lane-B contamination guard)."""
    bad = []
    for f in (ROOT / "architecture").glob("*.py"):
        for pat in ("discovery", "paper_trading", "research", "telegram_ai", "engine"):
            if re.search(rf"^\s*(from|import)\s+{pat}(\.|$|\s)", f.read_text(), re.M):
                bad.append(f.name)
    assert bad == []


def test_violation_reporting_is_explicit():
    s = dict(REG["agents"][0]); s.pop("capabilities")
    errs = contracts.validate_spec(s)
    assert errs and "missing spec field: capabilities" in errs
    conflict = dict(REG["agents"][0], allowed_authority=["OBSERVE", "DECIDE"])
    assert any("self-conflict" in e for e in contracts.validate_spec(conflict))
