#!/usr/bin/env python3
"""AHOS W11 Lane-B — Control Plane engine (contract control_plane_contract_v1).

ONE operator surface: START / STOP / STATUS / SAFE_HALT / RESUME — idempotent, ledger-resumable.

Laws implemented:
- Idempotent START: identical intent (sha of config+registry+intent) returns the SAME run;
  a component is activated at most once per run (activation ledger).
- Resume-from-ledger: RESUME inspects durable state, skips completed phases, continues; a
  restart never means blind restart.
- Honest health: no prober result => UNKNOWN; UNKNOWN on a CRITICAL component => SAFE_HALT
  (NO VALID EVIDENCE -> NO CONFIDENT DECISION, applied to boot).
- Status: CRITICAL fail => SAFE_HALT; NON_CRITICAL/ADVISORY fail => SYSTEM_DEGRADED;
  OPTIONAL never affects status; otherwise SYSTEM_ONLINE.
- Agents: only operability.implemented AND orchestrated agents are started; the rest are
  REPORTED (REGISTERED / NOT_IMPLEMENTED), never pretended-running (W10 honesty law).
- Append-only run-ledger (UPDATE/DELETE-abort triggers), single-active-run lock with
  stale-lock SAFE_HALT record; graceful STOP in reverse dependency order.
- Fully injectable: probers + clock injected => tests are deterministic; no Lane-A imports
  (lane isolation test-pinned).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CP_CONFIG = ROOT / "config" / "control_plane.yaml"
AGENT_REGISTRY = ROOT / "config" / "agent_registry.yaml"
CONTRACT_PATH = ROOT / "contracts" / "control_plane_contract_v1.json"

SYSTEM_STATES = ("BOOTING", "SYSTEM_ONLINE", "SYSTEM_DEGRADED", "SAFE_HALT", "RECOVERING", "HALTED")

DDL = """
CREATE TABLE IF NOT EXISTS run (
  run_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL, intent TEXT NOT NULL,
  start_ts REAL NOT NULL, end_ts REAL, final_status TEXT,
  config_sha TEXT NOT NULL, registry_sha TEXT NOT NULL, evidence TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS phase_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, phase TEXT NOT NULL,
  ts REAL NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS activation (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, component TEXT NOT NULL,
  ts REAL NOT NULL, lifecycle TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
  UNIQUE(run_id, component));
CREATE TABLE IF NOT EXISTS locks (
  name TEXT PRIMARY KEY, held_by TEXT NOT NULL, ts REAL NOT NULL, heartbeat_ts REAL NOT NULL);
CREATE TRIGGER IF NOT EXISTS run_no_update BEFORE UPDATE ON run BEGIN SELECT RAISE(ABORT,'append-only: run'); END;
CREATE TRIGGER IF NOT EXISTS run_no_delete BEFORE DELETE ON run BEGIN SELECT RAISE(ABORT,'append-only: run'); END;
CREATE TRIGGER IF NOT EXISTS pe_no_update BEFORE UPDATE ON phase_event BEGIN SELECT RAISE(ABORT,'append-only: phase_event'); END;
CREATE TRIGGER IF NOT EXISTS pe_no_delete BEFORE DELETE ON phase_event BEGIN SELECT RAISE(ABORT,'append-only: phase_event'); END;
CREATE TRIGGER IF NOT EXISTS act_no_update BEFORE UPDATE ON activation BEGIN SELECT RAISE(ABORT,'append-only: activation'); END;
CREATE TRIGGER IF NOT EXISTS act_no_delete BEFORE DELETE ON activation BEGIN SELECT RAISE(ABORT,'append-only: activation'); END;
"""


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def load_config(path: str | Path = CP_CONFIG) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def load_agents(path: str | Path = AGENT_REGISTRY) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def build_graph(cfg: dict, reg: dict) -> dict[str, list[str]]:
    """Dependency graph: infra components (from control_plane.yaml) + agents (ops blocks).
    Infra deps come from phase ordering (each comp's `requires` is empty today — phases sequence them);
    agent deps are agent ids. Cycles are FATAL to boot (returned, detected by topo)."""
    graph: dict[str, list[str]] = {}
    for comp in cfg.get("infrastructure", []):
        graph[comp["component"]] = [d for d in comp.get("requires", [])]
    for a in reg.get("agents", []):
        ops = a.get("ops") or {}
        deps = [d for d in (ops.get("startup_policy") or {}).get("depends_on", [])]
        graph[a["agent_id"]] = [d for d in deps if isinstance(d, str)]
    return graph


def topo_sort(graph: dict[str, list[str]]) -> tuple[list[str], list[list[str]]]:
    """Kahn. Returns (order, cycles)."""
    indeg = {n: 0 for n in graph}
    for n, deps in graph.items():
        for d in deps:
            if d in indeg:
                indeg[n] += 1
    ready = sorted([n for n, dg in indeg.items() if dg == 0])
    order, seen = [], set()
    while ready:
        n = ready.pop(0)
        order.append(n)
        seen.add(n)
        for m, deps in graph.items():
            if n in deps and m not in seen:
                indeg[m] -= 1
                if indeg[m] == 0:
                    ready.append(m)
                    ready.sort()
    leftover = [n for n in graph if n not in seen]
    cycles = [[n] for n in leftover] if leftover else []
    return order, cycles


class Ledger:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(DDL)

    def event(self, run_id: str, phase: str, ts: float, event: str, detail: str = "") -> None:
        self.conn.execute("INSERT INTO phase_event(run_id,phase,ts,event,detail) VALUES (?,?,?,?,?)",
                          (run_id, phase, ts, event, detail))
        self.conn.commit()

    def phases_done(self, run_id: str) -> set[str]:
        return {r[0] for r in self.conn.execute(
            "SELECT DISTINCT phase FROM phase_event WHERE run_id=? AND event='PHASE_OK'", (run_id,))}

    def close(self) -> None:
        self.conn.close()


class ControlPlane:
    def __init__(self, *, cfg: dict | None = None, reg: dict | None = None,
                 ledger_path: str | Path = ":memory:", probers: dict | None = None,
                 clock=time.time):
        self.cfg = cfg or load_config()
        self.reg = reg or load_agents()
        self.probers = probers or {}
        self.clock = clock
        self.ledger = Ledger(ledger_path)
        self.config_sha = _sha(self.cfg)
        self.registry_sha = _sha(self.reg)

    # ---------- health ----------
    def probe(self, name: str, now: float) -> tuple[str, str]:
        fn = self.probers.get(name)
        if fn is None:
            return "UNKNOWN", "no prober result (never fabricated)"
        try:
            status, detail = fn(now)
        except Exception as e:  # prober crash = unhealthy, honestly
            return "UNHEALTHY", f"prober exception: {type(e).__name__}"
        return status, detail

    # ---------- idempotency ----------
    def idempotency_key(self, intent: str) -> str:
        return _sha({"config": self.config_sha, "registry": self.registry_sha, "intent": intent})

    def _final_status_of(self, run_id: str) -> str | None:
        row = self.ledger.conn.execute(
            "SELECT event FROM phase_event WHERE run_id=? AND event LIKE 'FINAL_STATUS=%' ORDER BY id DESC LIMIT 1",
            (run_id,)).fetchone()
        return row[0].split("=", 1)[1] if row else None

    def _existing_run(self, key: str, intent: str):
        """Latest run for this (key, intent); status derived from append-only events (run rows
        are never mutated — FINAL_STATUS is an event, not an UPDATE)."""
        row = self.ledger.conn.execute(
            "SELECT run_id, start_ts FROM run WHERE idempotency_key=? AND intent=? ORDER BY start_ts DESC LIMIT 1",
            (key, intent)).fetchone()
        if not row:
            return None
        return (row[0], self._final_status_of(row[0]), row[1])

    # ---------- locks ----------
    def _acquire_lock(self, run_id: str, now: float, ttl: float) -> tuple[bool, str]:
        row = self.ledger.conn.execute("SELECT held_by, heartbeat_ts FROM locks WHERE name='global'").fetchone()
        if row:
            held_by, hb = row
            if held_by == run_id:
                return True, "lock already ours"
            if now - hb <= ttl:
                return False, f"REFUSED: active lock held by {held_by}"
            self.ledger.event(run_id, "locks", now, "STALE_LOCK_STOLEN",
                              f"previous holder {held_by} heartbeat aged {now - hb:.0f}s — recorded as SAFE_HALT precedent")
            self.ledger.conn.execute("DELETE FROM locks WHERE name='global'")
        self.ledger.conn.execute("INSERT INTO locks(name,held_by,ts,heartbeat_ts) VALUES ('global',?,?,?)",
                                 (run_id, now, now))
        self.ledger.conn.commit()
        return True, "lock acquired"

    def _release_lock(self, now: float) -> None:
        self.ledger.conn.execute("DELETE FROM locks WHERE name='global'")
        self.ledger.conn.commit()

    # ---------- run bookkeeping ----------
    def _open_run(self, run_id: str, key: str, intent: str, now: float) -> None:
        self.ledger.conn.execute(
            "INSERT OR IGNORE INTO run(run_id,idempotency_key,intent,start_ts,config_sha,registry_sha) VALUES (?,?,?,?,?,?)",
            (run_id, key, intent, now, self.config_sha, self.registry_sha))
        self.ledger.conn.commit()

    def _close_run(self, key: str, intent: str, status: str, now: float, evidence: list[str]) -> None:
        # run is append-only; closure is a NEW phase_event row + final_status written at insert-time.
        # final_status kept NULL during run; a terminal audit row records the outcome (no UPDATE).
        run_id = self._existing_run(key, intent)[0]
        self.ledger.event(run_id, "health_verify", now, f"FINAL_STATUS={status}",
                          json.dumps({"evidence": evidence}))

    # ---------- the phases ----------
    def _component_outcomes(self, now: float) -> dict[str, dict]:
        outcomes = {}
        for comp in self.cfg.get("infrastructure", []):
            name = comp["component"]
            status, detail = self.probe(name, now)
            outcomes[name] = {"boot_class": comp.get("boot_class", "OPTIONAL"),
                              "health": status, "detail": detail,
                              "availability": comp.get("availability", "UNKNOWN")}
        return outcomes

    def _agent_outcomes(self, now: float) -> dict[str, dict]:
        out = {}
        for a in self.reg.get("agents", []):
            ops = a.get("ops") or {}
            oper = ops.get("operability") or {}
            if not oper.get("implemented"):
                out[a["agent_id"]] = {"lifecycle": "REGISTERED", "boot_class": ops.get("boot_class", "NON_CRITICAL"),
                                      "detail": f"NOT_IMPLEMENTED (status={a['status']}) — reported, never pretended"}
                continue
            if not oper.get("orchestrated"):
                out[a["agent_id"]] = {"lifecycle": "REGISTERED", "boot_class": ops.get("boot_class", "NON_CRITICAL"),
                                      "detail": "implemented but orchestrated=false (not wired to runtime yet)"}
                continue
            status, detail = self.probe(a["agent_id"], now)
            lifecycle = {"HEALTHY": "RUNNING", "UNHEALTHY": "DEGRADED",
                         "UNAVAILABLE": "DEGRADED", "UNKNOWN": "HEALTH_CHECK"}[status]
            self.ledger.conn.execute(
                "INSERT OR IGNORE INTO activation(run_id,component,ts,lifecycle,detail) VALUES (?,?,?,?,?)",
                (self._run_id, a["agent_id"], now, lifecycle, detail))
            self.ledger.conn.commit()
            out[a["agent_id"]] = {"lifecycle": lifecycle, "boot_class": ops.get("boot_class", "NON_CRITICAL"),
                                  "detail": detail}
        return out

    @staticmethod
    def _status_from(comp: dict[str, dict], agents: dict[str, dict]) -> str:
        worst = "SYSTEM_ONLINE"
        for name, o in comp.items():
            bc, h = o["boot_class"], o["health"]
            if bc == "OPTIONAL":
                continue
            if h != "HEALTHY" and bc == "CRITICAL":
                return "SAFE_HALT"
            if h == "UNHEALTHY" or h == "UNAVAILABLE":
                worst = "SYSTEM_DEGRADED"
        for aid, o in agents.items():
            bc, lc = o["boot_class"], o["lifecycle"]
            # UNKNOWN readiness on an orchestrated CRITICAL agent = failed verification => halt
            failed = lc in ("DEGRADED", "CIRCUIT_OPEN") or (lc == "HEALTH_CHECK" and bc == "CRITICAL")
            if not failed:
                continue
            if bc == "CRITICAL":
                return "SAFE_HALT"
            worst = "SYSTEM_DEGRADED"
        return worst

    # ---------- operator surface ----------
    def start(self, *, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        key = self.idempotency_key("START")
        existing = self._existing_run(key, "START")
        if existing and existing[1] in ("SYSTEM_ONLINE", "SYSTEM_DEGRADED"):
            return {"run_id": existing[0], "status": existing[1], "idempotent_replay": True,
                    "note": "identical START already completed — no duplicate activation"}
        if existing and existing[1] in (None, "BOOTING"):
            run_id = existing[0]  # genuine RESUME: continue the in-flight run
            resumed = True
        else:
            run_id = f"run-{_sha({'k': key, 't': now})[:16]}"  # new attempt after SAFE_HALT/HALTED
            resumed = False
        self._run_id = run_id
        ledger_status = "RECOVERING" if resumed else "BOOTING"
        self.ledger.event(run_id, "env_validation", now, f"RUN_STATE={ledger_status}", key)
        self._open_run(run_id, key, "START", now)
        ttl = (self.cfg.get("ledger") or {}).get("heartbeat_ttl_s", 120)
        ok, why = self._acquire_lock(run_id, now, ttl)
        order, cycles = topo_sort(build_graph(self.cfg, self.reg))
        done = self.ledger.phases_done(run_id)
        comp: dict[str, dict] = {}
        agents: dict[str, dict] = {}
        phases = self.cfg.get("phases", [])
        for ph in phases:
            skipped = ph in done
            if skipped:
                self.ledger.event(run_id, ph, now, "PHASE_SKIPPED_RESUME", "already completed")
            if ph == "locks" and not ok and not skipped:
                self.ledger.event(run_id, ph, now, "PHASE_FAIL", why)
                self._close_run(key, "START", "SAFE_HALT", now, [why])
                return {"run_id": run_id, "status": "SAFE_HALT", "why": why}
            if ph == "dependency_graph" and cycles:
                detail = json.dumps({"cycles": cycles})
                if not skipped:
                    self.ledger.event(run_id, ph, now, "PHASE_FAIL", detail)
                    self._close_run(key, "START", "SAFE_HALT", now, [detail])
                return {"run_id": run_id, "status": "SAFE_HALT", "why": "dependency cycle", "cycles": cycles}
            if ph == "agent_startup":
                agents = self._agent_outcomes(now)  # always re-evaluated (health is now), activations idempotent
                if not skipped:
                    self.ledger.event(run_id, ph, now, "PHASE_OK",
                                      f"orchestrated agents: {sum(1 for a in agents.values() if a['lifecycle']=='RUNNING')}")
                continue
            if ph in ("postgres_health", "temporal_health", "engine_health", "n8n_health",
                      "optional_redis_health", "optional_bus_health", "infra_discovery"):
                comp = comp or self._component_outcomes(now)  # re-probe current health even on resume
                if not skipped:
                    self.ledger.event(run_id, ph, now, "PHASE_OK", "component health snapshot taken")
                continue
            if ph == "health_verify":
                continue  # final status computed after loop
            if not skipped:
                self.ledger.event(run_id, ph, now, "PHASE_OK", "")
        self._release_lock(now)
        status = self._status_from(comp, agents)
        self.ledger.event(run_id, "health_verify", now, "PHASE_OK", status)
        self._close_run(key, "START", status, now,
                        [f"graph_order={len(order)}", f"agents={len(agents)}"])
        return {"run_id": run_id, "status": status, "components": comp, "agents": agents,
                "boot_order": order, "idempotent_replay": False}

    def resume(self, *, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        key = self.idempotency_key("START")
        row = self._existing_run(key, "START")
        self.ledger.event(row[0] if row else "none", "locks", now, "RESUME_REQUEST",
                          "inspect durable state -> last valid state -> resume (never blind restart)")
        return self.start(now=now)

    def stop(self, *, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        order, _ = topo_sort(build_graph(self.cfg, self.reg))
        run_id = f"stop-{int(now)}"
        for comp in reversed(order):
            self.ledger.event(run_id, "shutdown", now, "STOP", comp)
        self._release_lock(now)
        self.ledger.event(run_id, "shutdown", now, "HALTED", "graceful reverse-order shutdown")
        return {"status": "HALTED", "shutdown_order": list(reversed(order))}

    def safe_halt(self, reason: str, *, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        self.ledger.event("operator", "locks", now, "SAFE_HALT", reason)
        self._release_lock(now)
        return {"status": "SAFE_HALT", "reason": reason}

    def status(self, *, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        cur = self.ledger.conn.execute(
            "SELECT event, detail FROM phase_event WHERE event LIKE 'FINAL_STATUS=%' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last_ok = self.ledger.conn.execute(
            "SELECT phase, MAX(ts) FROM phase_event WHERE event='PHASE_OK' GROUP BY phase").fetchall()
        fails = self.ledger.conn.execute(
            "SELECT phase, detail FROM phase_event WHERE event='PHASE_FAIL'").fetchall()
        running = [p for p, _ in last_ok]
        run_count = self.ledger.conn.execute("SELECT COUNT(*) FROM run").fetchone()[0]
        return {"system": cur[0].split("=", 1)[1] if cur else "HALTED",
                "running": running,
                "failed": [p for p, _ in fails],
                "why": [d for _, d in fails if d],
                "evidence": ["control_plane_ledger rows (append-only)"],
                "last_valid_state": {"phases_ok": running},
                "resumable": run_count > 0}
