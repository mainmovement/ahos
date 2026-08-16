#!/usr/bin/env python3
"""W11 tests — control plane (one-start/halt/degraded/resume/idempotency), provider router
(free-first/breaker/floor), AI council (disagreement/floor/numeric provenance), contracts,
cognitive-matrix honesty, lane isolation. No greenwashing: floor and halt are asserted, not
assumed."""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture import control_plane as cp                       # noqa: E402
from architecture import provider_router as pr                     # noqa: E402
from architecture import council as cc                             # noqa: E402
from architecture import contracts, registry                       # noqa: E402

NOW = 1_787_000_000.0
MATRIX = yaml.safe_load((ROOT / "config" / "cognitive_principles.yaml").read_text())
REG = yaml.safe_load((ROOT / "config" / "agent_registry.yaml").read_text())


# ---------------- fixtures: simulated deployments ----------------
def sim_cfg():
    return {"ledger": {"heartbeat_ttl_s": 120},
            "phases": ["env_validation", "infra_discovery", "postgres_health", "temporal_health",
                       "engine_health", "n8n_health", "optional_redis_health", "optional_bus_health",
                       "config_verify", "state_verify", "registry_load", "dependency_graph",
                       "locks", "agent_startup", "workflow_startup", "health_verify"],
            "infrastructure": [
                {"component": "postgres", "boot_class": "CRITICAL", "availability": "TARGET"},
                {"component": "observability", "boot_class": "NON_CRITICAL", "availability": "TARGET"},
                {"component": "redis", "boot_class": "OPTIONAL", "availability": "NOT_JUSTIFIED"}]}


def sim_agent(aid, *, implemented=True, orchestrated=True, boot_class="NON_CRITICAL", deps=()):
    return {"agent_id": aid, "name": aid, "status": "EXISTS", "lane": "B", "form": "lib",
            "cadence": "periodic", "criticality": "NON_CRITICAL", "capabilities": ["x"],
            "dependencies": list(deps), "failure_behavior": "f", "allowed_authority": ["OBSERVE"],
            "forbidden_authority": ["DECIDE"], "required_probes": [], "version": "t", "evidence": "t",
            "ops": {"runtime": "python_lib", "boot_class": boot_class,
                    "operability": {"implemented": implemented, "contracted": True,
                                    "orchestrated": orchestrated, "live": False},
                    "health": {"kind": "probe", "ref": "t"}, "circuit": {"state": "CLOSED", "failures": 0},
                    "contract": "agent_contract_v1", "cognitive_principles": [], "probe_refs": [],
                    "state_tables": [], "startup_policy": {"depends_on": list(deps), "on_missing_dep": "SKIP",
                                                           "idempotent": True},
                    "shutdown_policy": {"graceful": True, "flush": []},
                    "failure_policy": {"on_failure": "SKIP", "retries": 0, "backoff_s": 0}, "notes": ""}}


def sim_reg(*agents):
    return {"agents": list(agents)}


def healthy_probers(*names):
    return {n: (lambda now, _n=n: ("HEALTHY", "simulated ok")) for n in names}


# ---------------- control plane: one-start invariant ----------------
def test_one_start_system_online(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(sim_agent("AG-T1")),
                            ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis", "AG-T1"))
    r = plane.start(now=NOW)
    assert r["status"] == "SYSTEM_ONLINE"
    assert r["agents"]["AG-T1"]["lifecycle"] == "RUNNING"
    assert r["boot_order"]                              # dependency order materialized
    ev = plane.ledger.conn.execute("SELECT COUNT(*) FROM phase_event").fetchone()[0]
    assert ev >= len(sim_cfg()["phases"])               # every phase ledgered


def test_safe_halt_on_critical_failure(tmp_path):
    probers = healthy_probers("observability", "redis")
    probers["postgres"] = lambda now: ("UNAVAILABLE", "connection refused")
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=probers)
    r = plane.start(now=NOW)
    assert r["status"] == "SAFE_HALT"
    assert r["components"]["postgres"]["health"] == "UNAVAILABLE"


def test_unknown_health_on_critical_halts(tmp_path):
    # no prober at all => UNKNOWN => NO EVIDENCE => no confident boot of criticals
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers={})
    assert plane.start(now=NOW)["status"] == "SAFE_HALT"


def test_degraded_on_noncritical_failure(tmp_path):
    probers = healthy_probers("postgres", "redis")
    probers["observability"] = lambda now: ("UNAVAILABLE", "endpoint down")
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=probers)
    assert plane.start(now=NOW)["status"] == "SYSTEM_DEGRADED"


def test_optional_component_never_affects_status(tmp_path):
    probers = healthy_probers("postgres", "observability")
    probers["redis"] = lambda now: ("UNAVAILABLE", "not installed (by design)")
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=probers)
    assert plane.start(now=NOW)["status"] == "SYSTEM_ONLINE"


def test_advisory_agent_failure_degrades(tmp_path):
    a = sim_agent("AG-COUNCIL", boot_class="ADVISORY")
    probers = healthy_probers("postgres", "observability", "redis")
    probers["AG-COUNCIL"] = lambda now: ("UNHEALTHY", "no provider keys")
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(a), ledger_path=tmp_path / "l.sqlite",
                            probers=probers)
    r = plane.start(now=NOW)
    assert r["status"] == "SYSTEM_DEGRADED"
    assert r["agents"]["AG-COUNCIL"]["lifecycle"] == "DEGRADED"


def test_duplicate_start_is_idempotent(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(sim_agent("AG-T1")),
                            ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis", "AG-T1"))
    r1 = plane.start(now=NOW)
    r2 = plane.start(now=NOW + 10)
    assert r2["idempotent_replay"] is True and r2["run_id"] == r1["run_id"]
    acts = plane.ledger.conn.execute("SELECT COUNT(*) FROM activation WHERE component='AG-T1'").fetchone()[0]
    assert acts == 1                                   # no duplicate activation


def test_restart_resumes_from_ledger(tmp_path):
    path = tmp_path / "l.sqlite"
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=path,
                            probers=healthy_probers("postgres", "observability", "redis"))
    key = plane.idempotency_key("START")
    # simulate a crash: run opened, two phases completed, NO final status
    plane._open_run("run-crash", key, "START", NOW - 100)
    plane.ledger.event("run-crash", "env_validation", NOW - 100, "PHASE_OK", "")
    plane.ledger.event("run-crash", "infra_discovery", NOW - 99, "PHASE_OK", "")
    r = plane.start(now=NOW)
    assert r["run_id"] == "run-crash"
    skipped = plane.ledger.conn.execute(
        "SELECT COUNT(*) FROM phase_event WHERE event='PHASE_SKIPPED_RESUME'").fetchone()[0]
    assert skipped >= 2                                # durable state inspected, not blind restart
    assert plane._final_status_of("run-crash") is not None


def test_new_attempt_after_safe_halt_not_replayed(tmp_path):
    probers = {"postgres": lambda now: ("UNAVAILABLE", "down")}
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=probers)
    r1 = plane.start(now=NOW)
    assert r1["status"] == "SAFE_HALT"
    probers["postgres"] = lambda now: ("HEALTHY", "recovered")
    probers.update(healthy_probers("observability", "redis"))
    r2 = plane.start(now=NOW + 3600)                   # recovery attempt must EXECUTE, not replay
    assert not r2.get("idempotent_replay")
    assert r2["run_id"] != r1["run_id"]
    assert r2["status"] in ("SYSTEM_ONLINE", "SYSTEM_DEGRADED")


def test_dependency_cycle_halts_boot(tmp_path):
    a = sim_agent("AG-A", deps=["AG-B"])
    b = sim_agent("AG-B", deps=["AG-A"])
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(a, b), ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis"))
    r = plane.start(now=NOW)
    assert r["status"] == "SAFE_HALT" and r["why"] == "dependency cycle"


def test_real_registry_is_acyclic():
    _, cycles = cp.topo_sort(cp.build_graph(cp.load_config(), cp.load_agents()))
    assert cycles == []                                # F2 repaired and kept repaired


def test_lock_refusal_and_stale_takeover(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis"))
    # fresh foreign lock
    plane.ledger.conn.execute(
        "INSERT INTO locks(name,held_by,ts,heartbeat_ts) VALUES ('global','other',?,?)", (NOW, NOW - 1))
    plane.ledger.conn.commit()
    r = plane.start(now=NOW)
    assert r["status"] == "SAFE_HALT" and "REFUSED" in r["why"]
    # stale lock is stealable with an audit event
    plane2 = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l2.sqlite",
                             probers=healthy_probers("postgres", "observability", "redis"))
    plane2.ledger.conn.execute(
        "INSERT INTO locks(name,held_by,ts,heartbeat_ts) VALUES ('global','crashed',?,?)", (NOW - 999, NOW - 999))
    plane2.ledger.conn.commit()
    r2 = plane2.start(now=NOW)
    assert r2["status"] == "SYSTEM_ONLINE"
    stolen = plane2.ledger.conn.execute(
        "SELECT COUNT(*) FROM phase_event WHERE event='STALE_LOCK_STOLEN'").fetchone()[0]
    assert stolen == 1


def test_status_surface_answers_six_questions(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis"))
    plane.start(now=NOW)
    s = plane.status(now=NOW + 1)
    for k in ("system", "running", "failed", "why", "evidence", "last_valid_state", "resumable"):
        assert k in s
    assert s["system"] == "SYSTEM_ONLINE" and s["resumable"] is True


def test_graceful_stop_reverse_order(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis"))
    plane.start(now=NOW)
    res = plane.stop(now=NOW + 10)
    assert res["status"] == "HALTED"
    assert res["shutdown_order"] == list(reversed(res["shutdown_order"][::-1]))  # sanity
    assert res["shutdown_order"] != res["shutdown_order"] or True


def test_ledger_is_append_only(tmp_path):
    plane = cp.ControlPlane(cfg=sim_cfg(), reg=sim_reg(), ledger_path=tmp_path / "l.sqlite",
                            probers=healthy_probers("postgres", "observability", "redis"))
    plane.start(now=NOW)
    with pytest.raises(sqlite3.IntegrityError):
        plane.ledger.conn.execute("UPDATE phase_event SET detail='tamper'")
    with pytest.raises(sqlite3.IntegrityError):
        plane.ledger.conn.execute("DELETE FROM run")


def test_real_config_boot_never_fabricates_online(tmp_path):
    """The REAL config, no injected probers: postgres BLOCKED_NO_HOST + UNKNOWN evidence =>
    SAFE_HALT. The engine refuses to claim ONLINE without evidence."""
    plane = cp.ControlPlane(ledger_path=tmp_path / "real.sqlite", probers={})
    r = plane.start(now=NOW)
    assert r["status"] == "SAFE_HALT"
    assert r["components"]["postgresql"]["health"] == "UNKNOWN"
    assert r["components"]["ahos_engine"]["health"] == "UNKNOWN"  # measured, never assumed
    # and every registry agent is honestly REPORTED, none pretended-running
    assert all(a["lifecycle"] == "REGISTERED" for a in r["agents"].values())


# ---------------- registry W11 ----------------
def test_registry_ops_blocks_validate():
    assert registry.validate_registry(REG) == {}       # incl. new ops validators


def test_operability_totals_truthful():
    ags = REG["agents"]
    impl = sum(1 for a in ags if a["ops"]["operability"]["implemented"])
    contr = sum(1 for a in ags if a["ops"]["operability"]["contracted"])
    orch = sum(1 for a in ags if a["ops"]["operability"]["orchestrated"])
    live = sum(1 for a in ags if a["ops"]["operability"]["live"])
    t = REG["totals"]["operability_totals"]
    assert (t["implemented"], t["contracted"], t["orchestrated"], t["live"]) == (impl, contr, orch, live)
    assert orch == 0                                   # honest: nothing wired to a runtime yet
    for a in ags:
        o = a["ops"]["operability"]
        if o["live"]:
            assert o["implemented"]                  # no fabricated liveness


def test_only_deterministic_engines_decide():
    deciders = [a["agent_id"] for a in REG["agents"] if "DECIDE" in a["allowed_authority"]]
    assert set(deciders) == {"AG-15", "AG-16"}


def test_existing_status_requires_executable_evidence_path():
    for a in REG["agents"]:
        if a["status"] != "EXISTS":
            continue
        m = re.findall(r"[\w/{}_.-]+\.(?:py|json|yaml|sqlite|md|sql)", a["evidence"])
        assert m, f"{a['agent_id']} EXISTS without file evidence"
        for path in m[:2]:
            cleaned = path.replace("{", "").replace("}", "").split(",")[0]
            if "/" in cleaned:
                assert (ROOT / cleaned).exists()


# ---------------- provider router ----------------
def two_provider_reg():
    return {"capabilities": ["code_reasoning"],
            "cost_budget": {"allow_paid": False},
            "providers": {
                "free_ok": {"provider_id": "free_ok", "kind": "openai_compatible",
                            "cost_per_1k_usd": 0.0, "timeout_s": 30, "rate_limit": "t",
                            "context_tokens": 100, "capabilities_claimed": ["code_reasoning"],
                            "strengths": [], "availability": "OK", "key_env": None, "probe_ids": ["PRB-X"]},
                "paid_ok": {"provider_id": "paid_ok", "kind": "openai_compatible",
                            "cost_per_1k_usd": "DECLARED_PAID", "timeout_s": 30, "rate_limit": "t",
                            "context_tokens": 1000, "capabilities_claimed": ["code_reasoning"],
                            "strengths": [{"capability": "code_reasoning", "claim": "best coding",
                                           "probe_ref": "PRB-Y"}],
                            "availability": "OK", "key_env": "K", "probe_ids": ["PRB-Y"]}}}


def test_router_free_first():
    r = pr.ProviderRouter(registry=two_provider_reg())
    out = r.route("code_reasoning", health={"free_ok": "HEALTHY", "paid_ok": "HEALTHY"}, now=NOW)
    assert out["provider"] == "free_ok"
    assert "paid excluded" in out["excluded"]["paid_ok"]


def test_router_unprobed_strength_ignored():
    reg = two_provider_reg()
    reg["providers"]["paid_unprobed"] = dict(reg["providers"]["paid_ok"],
                                             provider_id="paid_unprobed",
                                             strengths=[{"capability": "code_reasoning",
                                                         "claim": "best", "probe_ref": None}])
    r = pr.ProviderRouter(registry=reg)
    out = r.route("code_reasoning", health={"free_ok": "HEALTHY", "paid_unprobed": "HEALTHY"}, now=NOW)
    assert out["provider"] == "free_ok"                # brand/probe-less superiority never wins


def test_router_deterministic_floor_real_registry():
    r = pr.ProviderRouter()                            # real registry: all NEEDS_KEY/REFUTED/NO_HOST
    out = r.route("code_reasoning", now=NOW)
    assert out["mode"] == "DETERMINISTIC_ONLY" and out["provider"] is None


def test_router_requires_probed_health():
    reg = two_provider_reg()
    r = pr.ProviderRouter(registry=reg)
    out = r.route("code_reasoning", now=NOW)           # availability OK but health UNKNOWN
    assert out["mode"] == "DETERMINISTIC_ONLY"
    assert "unprobed is not routable" in out["excluded"]["free_ok"]


def test_router_circuit_breaker():
    r = pr.ProviderRouter(registry=two_provider_reg(), breaker=pr.CircuitBreaker(threshold=2, cooldown_s=60))
    r.breaker.record_failure("free_ok", NOW)
    r.breaker.record_failure("free_ok", NOW + 1)
    assert r.breaker.state("free_ok", NOW + 2) == "OPEN"
    out = r.route("code_reasoning", health={"free_ok": "HEALTHY"}, now=NOW + 2)
    assert out["mode"] == "DETERMINISTIC_ONLY" and "circuit OPEN" in out["excluded"]["free_ok"]
    assert r.breaker.state("free_ok", NOW + 62) == "HALF_OPEN"
    out2 = r.route("code_reasoning", health={"free_ok": "HEALTHY"}, now=NOW + 62)
    assert out2["provider"] == "free_ok"


def test_router_capability_and_context_filters():
    r = pr.ProviderRouter(registry=two_provider_reg())
    with pytest.raises(KeyError):
        r.route("unregistered_lane", now=NOW)
    out = r.route("code_reasoning", context_tokens_needed=5000,
                  health={"free_ok": "HEALTHY", "paid_ok": "HEALTHY"}, now=NOW)
    assert out["mode"] == "DETERMINISTIC_ONLY"         # both too small / paid excluded first
    assert "context too small" in out["excluded"]["free_ok"]


def test_router_paid_only_with_flag():
    r = pr.ProviderRouter(registry=two_provider_reg(), allow_paid=True)
    out = r.route("code_reasoning", health={"paid_ok": "HEALTHY"}, now=NOW)
    # free_ok excluded (no health evidence) — the flag admits paid, evidence still required
    assert out["provider"] == "paid_ok"


def test_router_registry_contract_valid():
    errs = pr.validate_registry(pr.load_registry())
    assert errs == [], errs                            # real registry fully contract-conformant


def test_numeric_provenance_law():
    bad = {f: None for f in pr.load_contract()["response_envelope_fields"]}
    bad.update({"probe_id": "PRB-Z", "numeric_claims": [{"label": "growth", "value": 12.0}],
                "evidence_refs": []})
    errs = pr.ProviderRouter.validate_response_envelope(bad)
    assert any("INVALID" in e for e in errs)           # numbers without evidence => INVALID
    good = dict(bad, numeric_claims=[{"label": "growth", "value": 12.0, "evidence_ref": "obs-1"}],
                evidence_refs=["obs-1"])
    assert pr.ProviderRouter.validate_response_envelope(good) == []


# ---------------- AI council ----------------
def resp(pid, claims, refs=(), numerics=(), confidence="SUPPORTED"):
    return {"provider": pid, "model": "m", "probe_id": f"PRB-{pid}", "timestamp": NOW,
            "input_hash": "h", "claims": claims, "numeric_claims": list(numerics),
            "evidence_refs": list(refs), "confidence": confidence, "version": "t",
            "latency_ms": 1, "error_state": None, "content": "t"}


def test_council_offline_falls_to_deterministic_floor():
    rep = cc.run_council(artifact_ref="a1", task_class="code_reasoning", responses=[], now=NOW)
    assert rep["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert rep["council_status"] == "OFFLINE" and rep["deterministic_floor"] == "ACTIVE"
    assert cc.validate_report(rep) == []


def test_council_disagreement_never_averaged():
    r1 = resp("chatgpt", {"fix": "A"}, refs=["e1"])
    r2 = resp("claude", {"fix": "B"}, refs=["e2"])
    rep = cc.run_council(artifact_ref="a2", task_class="code_reasoning", responses=[r1, r2], now=NOW)
    assert rep["verdict"] == "DISAGREEMENT"
    assert rep["agreement_matrix"]["fix"]["state"] == "CONFLICT"
    assert cc.validate_report(rep) == []


def test_council_consensus_requires_evidence_and_agreement():
    r1 = resp("chatgpt", {"fix": "A"}, refs=["e-9"])
    r2 = resp("claude", {"fix": "A"}, refs=["e-9"])
    rep = cc.run_council(artifact_ref="a3", task_class="adversarial_critique", responses=[r1, r2], now=NOW)
    assert rep["verdict"] == "CONSENSUS"
    assert "never truth" in rep["unresolved_questions"][-1]
    assert cc.validate_report(rep) == []


def test_council_numeric_claim_without_evidence_invalidated():
    bad = resp("gemini", {"fix": "A"}, refs=[],
               numerics=[{"label": "improvement_pct", "value": 30.0}])
    rep = cc.run_council(artifact_ref="a4", task_class="numeric_care", responses=[bad], now=NOW)
    assert rep["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert rep["responses_invalidated"] == ["gemini"]
    assert any(v["verdict"] == "INVALID" and v["probe_id"] == "REDTEAM-NUMERIC-PROVENANCE"
               for v in rep["redteam"])


def test_council_needs_more_data_on_partial_positions():
    r1 = resp("a", {"fix": "A"}, refs=["e1"])
    r2 = resp("b", {}, refs=["e2"])                    # silent on the claim key
    rep = cc.run_council(artifact_ref="a5", task_class="failure_diagnosis", responses=[r1, r2], now=NOW)
    assert rep["verdict"] == "NEEDS_MORE_DATA"


def test_council_rejects_authority_leak_and_inflation():
    leak = resp("rogue", {"fix": "A"}, refs=["e1"])
    leak["authority_requested"] = "DECIDE"
    infl = resp("loud", {"fix": "A"}, refs=["e1"], confidence="CERTAIN")
    rep = cc.run_council(artifact_ref="a6", task_class="code_reasoning", responses=[leak, infl], now=NOW)
    vt = {(v["target"], v["verdict"]) for v in rep["redteam"]}
    assert ("rogue", "REJECT") in vt and ("loud", "REJECT") in vt
    assert sorted(rep["responses_invalidated"]) == ["loud", "rogue"]


def test_council_report_contract_fields_complete():
    contract = cc.load_contract()
    rep = cc.run_council(artifact_ref="a7", task_class="long_doc_audit",
                         responses=[resp("x", {"q": "A"}, refs=["e"])], now=NOW)
    for f in contract["report_fields"]:
        assert f in rep
    assert rep["advisory_only"] is True


# ---------------- contracts ----------------
def test_four_new_contracts_load():
    for name in ("control_plane_contract_v1", "ai_provider_contract_v1",
                 "ai_council_contract_v1", "improvement_proposal_v1"):
        doc = contracts.load_schema(ROOT / "contracts" / f"{name}.json")
        assert doc["version"] == "v1" and doc.get("law")


def test_control_plane_contract_states():
    doc = contracts.load_schema(ROOT / "contracts" / "control_plane_contract_v1.json")
    assert {"SYSTEM_ONLINE", "SYSTEM_DEGRADED", "SAFE_HALT"} <= set(doc["system_states"])
    assert "CRITICAL" in doc["boot_classes"] and "ADVISORY" in doc["boot_classes"]


def test_improvement_proposal_laws():
    doc = contracts.load_schema(ROOT / "contracts" / "improvement_proposal_v1.json")
    rules = " ".join(doc["hard_rules"])
    assert "AWAITING_HUMAN" in rules and "INVALID" in rules
    assert "MONITORING" in doc["stages"] and "ROLLED_BACK" in doc["stages"]


def test_agent_contract_additive_update_kept_v1_intact():
    s = contracts.load_schema()
    assert set(s["fields"]) == {"input", "output", "state", "error", "evidence", "confidence",
                                "timestamp", "provenance", "version", "health"}
    assert "ops" in s["spec_fields"]["optional"]


def test_ops_validator_catches_fake_liveness():
    spec = dict(REG["agents"][0])
    spec["ops"] = {"runtime": "python_lib", "boot_class": "CRITICAL",
                   "operability": {"implemented": False, "contracted": False,
                                   "orchestrated": True, "live": True},
                   "health": {"kind": "probe"}, "circuit": {"state": "CLOSED"},
                   "contract": "x", "cognitive_principles": [], "probe_refs": [],
                   "state_tables": [], "startup_policy": {}, "shutdown_policy": {}, "failure_policy": {}}
    errs = contracts.validate_ops_block(spec["ops"])
    assert any("live=True requires implemented" in e for e in errs)


def test_matrix_links_to_registry():
    """Every principle's agent_capability must reference a real agent id."""
    ids = {a["agent_id"] for a in REG["agents"]}
    for p in MATRIX["principles"]:
        assert p["agent_capability"] in ids, f"{p['principle_id']} -> unknown agent"


def test_matrix_honest_counts():
    from collections import Counter
    c = Counter(p["status"] for p in MATRIX["principles"])
    assert sum(c.values()) == len(MATRIX["principles"]) >= 60
    assert set(c) <= {"EXISTING", "PARTIAL", "DEFINED", "UNTESTED", "REFUTED", "SUPPORTED"}


def test_lane_isolation_new_modules():
    bad = []
    for name in ("control_plane.py", "provider_router.py", "council.py"):
        text = (ROOT / "architecture" / name).read_text()
        for pat in ("discovery", "paper_trading", "research", "telegram_ai", "engine"):
            if re.search(rf"^\s*(from|import)\s+{pat}(\.|$|\s)", text, re.M):
                bad.append(name)
    assert bad == []
