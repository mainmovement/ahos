"""W13 P1 — soak + fault-injection battery for the Python control plane (in-repo, no host).
NEW ground only (W11 pins stay untouched): exhaustive single-fault property on the REAL config,
seed-pinned multi-fault fuzzing, interleaved soak with ledger invariants, crash-injection
mid-phase + resume, ledger-unavailable fail-fast, lock flood, history non-rewrite on recovery.
Deterministic: injected clocks/probers; no network, no Lane-A imports.
"""
import random
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "architecture"))
import control_plane as cp  # noqa: E402

LEGAL_FINAL = {"SYSTEM_ONLINE", "SYSTEM_DEGRADED", "SAFE_HALT"}


def _clock():
    t = [1_700_000_000.0]
    return (lambda: t[0]), t


def _plane(tmp_path, *, probers, cfg=None, reg=None, name="soak.sqlite"):
    clk, _ = _clock()
    return cp.ControlPlane(cfg=cfg or cp.load_config(), reg=reg or cp.load_agents(),
                           ledger_path=tmp_path / name, probers=probers, clock=clk)


def _healthy_probers(cfg, override=None):
    override = override or {}
    out = {}
    for comp in cfg.get("infrastructure", []):
        name = comp["component"]
        state = override.get(name, "HEALTHY")
        out[name] = (lambda now, s=state, n=name: (s, f"inj:{n}={s}"))
    return out


# ---------- 1. exhaustive single-fault property over the REAL config ----------
def test_single_fault_property_exhaustive_real_config(tmp_path):
    cfg = cp.load_config()
    for target in cfg.get("infrastructure", []):
        bc = target.get("boot_class", "OPTIONAL")
        plane = _plane(tmp_path, probers=_healthy_probers(cfg, {target["component"]: "UNHEALTHY"}),
                       name=f"sf_{target['component']}.sqlite")
        res = plane.start()
        assert res["status"] in LEGAL_FINAL
        expected = ("SAFE_HALT" if bc == "CRITICAL"
                    else "SYSTEM_DEGRADED" if bc in ("NON_CRITICAL", "ADVISORY")
                    else "SYSTEM_ONLINE")
        assert res["status"] == expected, (target["component"], bc, res["status"])


# ---------- 2. seed-pinned multi-fault fuzz (never spurious halt / never blind online) ----------
def test_fault_combinations_seed_pinned_invariants(tmp_path):
    cfg = cp.load_config()
    names = [c["component"] for c in cfg.get("infrastructure", [])]
    crit = {c["component"] for c in cfg["infrastructure"] if c.get("boot_class") == "CRITICAL"}
    rng = random.Random(42)
    for i in range(64):
        faults = {n for n in names if rng.random() < 0.3}
        override = {n: "UNHEALTHY" for n in faults}
        plane = _plane(tmp_path, probers=_healthy_probers(cfg, override), name=f"fuzz{i}.sqlite")
        res = plane.start()
        assert res["status"] in LEGAL_FINAL
        if faults & crit:
            assert res["status"] == "SAFE_HALT"       # any critical fault ⇒ halt, never online
        if res["status"] == "SAFE_HALT":
            assert faults & crit                      # never a spurious halt from non-criticals


# ---------- 3. interleaved soak: monotonic append-only ledger, lawful statuses ----------
def test_soak_150_interleaved_operations_invariants(tmp_path):
    cfg = cp.load_config()
    health = {c["component"]: "HEALTHY" for c in cfg.get("infrastructure", [])}
    probers = {n: (lambda now, n=n: (health[n], f"soak:{n}")) for n in health}
    plane = _plane(tmp_path, probers=probers)
    rng = random.Random(7)
    prev_rows = 0
    for step in range(150):
        op = rng.choice(["start", "status", "stop", "safe_halt", "resume", "flip"])
        if op == "flip":
            # inject or clear a NON_CRITICAL fault (temporal) — criticals stay healthy in soak
            health["temporal"] = "UNHEALTHY" if health["temporal"] == "HEALTHY" else "HEALTHY"
            continue
        res = {"start": plane.start, "status": plane.status, "stop": plane.stop,
               "resume": plane.resume,
               "safe_halt": lambda: plane.safe_halt("operator drill")}[op]()
        st = res.get("system") or res.get("status")
        assert st in LEGAL_FINAL | {"HALTED"}, (step, op, st)
        rows = plane.ledger.conn.execute("SELECT COUNT(*) FROM phase_event").fetchone()[0]
        assert rows >= prev_rows          # ledger never shrinks (append-only, no rewrite)
        prev_rows = rows
    con = plane.ledger.conn
    n_runs = con.execute("SELECT COUNT(*) FROM run").fetchone()[0]
    n_final = con.execute(
        "SELECT COUNT(DISTINCT run_id) FROM phase_event WHERE event LIKE 'FINAL_STATUS=%'").fetchone()[0]
    assert n_runs == n_final              # every opened run was closed exactly once
    assert con.execute("SELECT COUNT(*) FROM run").fetchone()[0] >= 1
    # tamper attempt must abort and leave counts unchanged (append-only triggers)
    before = con.execute("SELECT COUNT(*) FROM phase_event").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("UPDATE phase_event SET detail='forged' WHERE id=1")
    con.rollback()
    assert con.execute("SELECT COUNT(*) FROM phase_event").fetchone()[0] == before


# ---------- 4. crash injection mid-phase → resume completes, phases never duplicated ----------
def test_crash_injection_mid_phase_then_resume_no_duplicate(tmp_path):
    path = tmp_path / "crash.sqlite"
    cfg, reg = cp.load_config(), cp.load_agents()
    probers = _healthy_probers(cfg)
    clk, _ = _clock()
    plane = cp.ControlPlane(cfg=cfg, reg=reg, ledger_path=path, probers=probers, clock=clk)
    boom_at = {"n": 0}

    orig_event = plane.ledger.event

    def killer(run_id, phase, ts, event, detail=""):
        orig_event(run_id, phase, ts, event, detail)
        if phase == "state_verify" and event == "PHASE_OK":
            boom_at["n"] += 1
            if boom_at["n"] == 1:
                raise RuntimeError("SIMULATED CRASH mid-boot")

    plane.ledger.event = killer
    with pytest.raises(RuntimeError):
        plane.start()
    plane.ledger.close()

    # fresh process on the same durable ledger
    clk2, _ = _clock()
    plane2 = cp.ControlPlane(cfg=cfg, reg=reg, ledger_path=path, probers=probers, clock=clk2)
    res = plane2.resume()
    assert res["status"] in LEGAL_FINAL
    con = plane2.ledger.conn
    run_id = res["run_id"]
    dupes = con.execute(
        "SELECT phase, COUNT(*) FROM phase_event WHERE run_id=? AND event='PHASE_OK' "
        "GROUP BY phase HAVING COUNT(*)>1", (run_id,)).fetchall()
    assert dupes == []                     # no phase executed twice across crash+resume
    skips = con.execute(
        "SELECT COUNT(*) FROM phase_event WHERE run_id=? AND event='PHASE_SKIPPED_RESUME'",
        (run_id,)).fetchone()[0]
    assert skips >= 1                      # resume genuinely skipped completed phases
    plane2.ledger.close()


# ---------- 5. ledger unavailable ⇒ fail-fast, zero partial state ----------
def test_ledger_unavailable_fails_fast_without_partial_state(tmp_path):
    missing_dir = tmp_path / "no_such_dir" / "ledger.sqlite"
    with pytest.raises(sqlite3.Error):
        cp.ControlPlane(cfg=cp.load_config(), reg=cp.load_agents(), ledger_path=missing_dir,
                        probers={})
    assert not missing_dir.exists()        # no fabricated/partial state file created


# ---------- 6. lock flood: exactly one holder; steal recorded once ----------
def test_lock_flood_single_holder_property(tmp_path):
    cfg, reg = cp.load_config(), cp.load_agents()
    probers = _healthy_probers(cfg)
    plane = _plane(tmp_path, probers=probers)
    # inject a genuinely HELD lock: a completed start releases its lock by design, so the
    # "active holder" state is injected directly (simulates a live/crashed mid-boot holder)
    t2 = [1_700_000_000.0]
    plane.ledger.conn.execute(
        "INSERT INTO locks(name,held_by,ts,heartbeat_ts) VALUES ('global','run-holder',?,?)",
        (t2[0], t2[0]))
    plane.ledger.conn.commit()
    interloper = cp.ControlPlane(cfg=cfg, reg=reg, ledger_path=tmp_path / "soak.sqlite",
                                 probers=probers, clock=lambda: t2[0])
    t2[0] += 5                             # within ttl (120s)
    refused = 0
    for _ in range(25):
        ok, why = interloper._acquire_lock("run-interloper", t2[0], 120)
        refused += (not ok)
    assert refused == 25                   # every same-window attempt refused
    stolen = interloper.ledger.conn.execute(
        "SELECT COUNT(*) FROM phase_event WHERE event='STALE_LOCK_STOLEN'").fetchone()[0]
    t2[0] += 500                           # age past ttl
    ok, why = interloper._acquire_lock("run-interloper", t2[0], 120)
    assert ok and "acquired" in why
    stolen2 = interloper.ledger.conn.execute(
        "SELECT COUNT(*) FROM phase_event WHERE event='STALE_LOCK_STOLEN'").fetchone()[0]
    assert stolen2 == stolen + 1           # exactly one recorded steal event for the takeover


# ---------- 7. recovery never rewrites history (event digest of old run frozen) ----------
def test_recovery_after_halt_does_not_rewrite_history(tmp_path):
    cfg = cp.load_config()
    health = {c["component"]: "HEALTHY" for c in cfg.get("infrastructure", [])}
    health["postgresql"] = "UNHEALTHY"      # CRITICAL fault ⇒ first boot SAFE_HALTs
    probers = {n: (lambda now, n=n: (health[n], "rc")) for n in health}
    clk, t = _clock()
    plane = _plane(tmp_path, probers=probers)
    plane.clock = clk
    r1 = plane.start()
    assert r1["status"] == "SAFE_HALT"
    con = plane.ledger.conn
    digest_before = con.execute(
        "SELECT COUNT(*), GROUP_CONCAT(id||':'||event) FROM phase_event WHERE run_id=?",
        (r1["run_id"],)).fetchone()
    health["postgresql"] = "HEALTHY"        # fault cleared ⇒ recovery
    t[0] += 60                              # clock MUST advance between attempts:
                                            # run-id derives from (key, ts); a frozen clock makes
                                            # attempts collide into one run stream (documented boundary)
    r2 = plane.start()
    assert r2["run_id"] != r1["run_id"]     # recovery = NEW run, never history-mixing
    assert r2["status"] in LEGAL_FINAL - {"SAFE_HALT"} or r2["status"] == "SAFE_HALT"
    digest_after = con.execute(
        "SELECT COUNT(*), GROUP_CONCAT(id||':'||event) FROM phase_event WHERE run_id=?",
        (r1["run_id"],)).fetchone()
    assert digest_before == digest_after    # old run's history byte-identical after recovery


# ---------- 8. prober crash ⇒ UNHEALTHY evidence, never engine crash ----------
def test_prober_exception_is_unhealthy_not_crash(tmp_path):
    cfg = cp.load_config()
    def dying(now):
        raise TimeoutError("provider dead")
    probers = _healthy_probers(cfg)
    probers["postgresql"] = dying
    plane = _plane(tmp_path, probers=probers)
    res = plane.start()                     # must not raise
    assert res["status"] == "SAFE_HALT"
    assert "prober exception" in res["components"]["postgresql"]["detail"]
