"""Component model for the one-click launcher.

Five components, in start order (dependency reality from the M9 capability
graph, not prose):

    stores      CRITICAL   Lane-B SQLite stores (engine cannot run without them)
    db_backend  OPTIONAL   Postgres/PGlite backend the gateway reads
    gateway     OPTIONAL   Next.js API + dashboard (degrades gracefully)
    telegram    OPTIONAL   run_bot.py poller (owner interaction edge)
    engine      CRITICAL   architecture.runtime daemon, PAPER mode

The gateway/db/telegram boot classes are OPTIONAL (not CRITICAL) on purpose:
the engine is the intelligence surface and runs on SQLite alone, so a missing
dashboard is SYSTEM_DEGRADED, not SAFE_HALT. That matches what the gateway
already implements (fail-closed read model, honest 200-with-error responses).
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

from config.paths import get_data_dir, get_local_db_path, get_paper_trading_db_path, \
    get_discovery_db_path, get_knowledge_db_path, get_project_root

import launcher.processkit as pk

# --------------------------------------------------------------------- types ---
HEALTHY = "HEALTHY"
UNHEALTHY = "UNHEALTHY"
UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"

START_ORDER = ["stores", "db_backend", "gateway", "telegram", "engine"]
CRITICAL = {"stores", "engine"}

# The daemon must never be able to talk to anything but paper mode.
ENGINE_ENV_HARD = {
    "AHOS_PAPER_ONLY": "1",
    "AHOS_EVIDENCE_SOURCE": "local",
    # run_bot.py owns the Telegram getUpdates poll; the daemon would otherwise
    # poll the same token inline and re-deliver unconfirmed updates.
    "AHOS_TELEGRAM_POLL": "0",
    "PYTHONIOENCODING": "utf-8",
}


@dataclass
class ComponentResult:
    name: str
    status: str  # HEALTHY | UNHEALTHY | UNAVAILABLE | UNKNOWN | SKIPPED
    detail: str = ""
    pid: int | None = None
    started_ts: float | None = None
    evidence: dict = field(default_factory=dict)
    # True only when THIS run spawned/initialised the component (as opposed to
    # finding it already healthy). Rollback uses it to stop exactly the stack we
    # brought up and never a service that was running before us.
    fresh: bool = False


# ------------------------------------------------------------- env resolution ---
def _load_gateway_port_module():
    """scripts/gateway_port.py is the single source of truth for the gateway
    URL (GM-05) and is not a package — load it by path rather than duplicating
    its resolution order here."""
    mod_path = Path(get_project_root()) / "scripts" / "gateway_port.py"
    spec = importlib.util.spec_from_file_location("_ahos_gateway_port", mod_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def resolve_gateway(env: dict) -> dict:
    """Resolved gateway url/host/port + warnings, delegated to gateway_port.py."""
    gwp = _load_gateway_port_module()
    return gwp.resolve_gateway(env)


def dashboard_url(env: dict) -> str:
    info = resolve_gateway(env)
    host = info.get("host") or "127.0.0.1"
    port = info.get("port") or 3000
    return f"http://{host}:{int(port)}/"


def database_target(env: dict) -> dict:
    """Resolve the configured DB backend WITHOUT exposing any credential.

    Only the scheme, host and port are returned — the URL itself (which carries
    the password) is never echoed into logs or status reports.
    """
    raw = (env.get("DATABASE_URL") or "").strip()
    if not raw:
        return {"scheme": "none", "host": None, "port": None, "configured": False}
    try:
        parsed = urllib.parse.urlparse(raw)
    except ValueError:
        return {"scheme": "invalid", "host": None, "port": None, "configured": True}
    scheme = (parsed.scheme or "unknown").lower()
    if scheme.startswith("pglite"):
        host = parsed.hostname
        port = parsed.port
        return {"scheme": "pglite",
                "host": host or "127.0.0.1", "port": port or 5432,
                "data_dir": parsed.path.lstrip("/\\") or None,
                "configured": True}
    if scheme.startswith("postgres"):
        return {"scheme": "postgres", "host": parsed.hostname or "127.0.0.1",
                "port": parsed.port or 5432, "configured": True}
    return {"scheme": scheme, "host": parsed.hostname, "port": parsed.port,
            "configured": True}


# Only the keys the launcher itself resolves. Tokens and *_KEY/*_SECRET values
# stay in .env and are read by the processes that own them, never by us.
REPO_ENV_KEYS = ("DATABASE_URL", "AHOS_GATEWAY_URL", "AHOS_GATEWAY_PORT",
                 "AHOS_GATEWAY_MODE")


def load_repo_env(root: Path, env: dict | None = None) -> dict:
    """Merge the launcher-relevant keys from .env (process env wins).

    Deliberately narrow: this never reads TELEGRAM_BOT_TOKEN or any credential
    line, and nothing it reads is printed. It exists so that the launcher's own
    backend/port resolution matches what the gateway resolves for itself.
    """
    out = dict(os.environ if env is None else env)
    dotenv = root / ".env"
    if not dotenv.exists():
        return out
    try:
        text = dotenv.read_text(encoding="utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in REPO_ENV_KEYS:
            continue
        value = value.strip().strip('"').strip("'")
        out.setdefault(key, value)  # real environment wins
    return out


def repo_root_marker(root: Path) -> bool:
    """What identifies *this* checkout (no pyproject.toml here)."""
    return (root / "config" / "paths.py").exists() and (root / "run_bot.py").exists()


def venv_python(root: Path) -> Path | None:
    cand = root / ".venv" / "Scripts" / "python.exe"
    return cand if cand.exists() else None


def node_present(root: Path) -> bool:
    return (root / "node_modules" / ".package-lock.json").exists() or \
        (root / "node_modules" / "next" / "package.json").exists()


def build_stale(root: Path) -> tuple[bool, str]:
    """True if the .next production build is older than the app/db/lib sources."""
    build_id = root / ".next" / "BUILD_ID"
    if not build_id.exists():
        return True, "no .next/BUILD_ID"
    srcs = []
    for pat in ("app", "db", "lib", "schema.ts", "next.config.ts"):
        base = root / pat
        if base.is_dir():
            srcs.extend(p for p in base.rglob("*") if p.suffix in (".ts", ".tsx"))
        elif base.is_file():
            srcs.append(base)
    stale = [str(p.relative_to(root)) for p in srcs
             if p.stat().st_mtime > build_id.stat().st_mtime]
    if stale:
        return True, f"{len(stale)} source files newer than build ({stale[:3]})"
    return False, "build is current"


# ------------------------------------------------------------------ commands ---
def _npm_cmd(script: str) -> list[str]:
    if os.name == "nt":
        return ["cmd", "/c", f"npm run {script} --silent"]
    return ["npm", "run", script, "--silent"]


def gateway_command(root: Path, mode: str = "prod") -> list[str]:
    """(argv) for the gateway in the given mode (prod = `next start`, dev = `next dev`).

    Reuses the existing package.json scripts (no second server entry point).
    PORT honours the resolved gateway port.
    """
    return _npm_cmd("start" if mode == "prod" else "dev")


def engine_command(python: Path) -> list[str]:
    return [str(python), "-m", "architecture.runtime",
            "--daemon", "--interval-sec", "60", "--observation-cycle",
            "--evidence-source", "local"]


def telegram_command(python: Path) -> list[str]:
    # run_bot.py loads .env itself; the launcher never reads the token.
    return [str(python), "run_bot.py"]


def stores_command(python: Path) -> list[str]:
    return [str(python), "scripts/init_databases.py", "--with-guards", "--json"]


# ------------------------------------------------------------- child env ---
def child_env(root: Path, env: dict | None = None, *, telegram_owner: bool = True) -> dict:
    """Environment for launcher children: paper-only hard, URL resolved once."""
    out = dict(os.environ if env is None else env)
    out.update(ENGINE_ENV_HARD)
    info = resolve_gateway(out)
    if info.get("url"):
        out["AHOS_GATEWAY_URL"] = info["url"]
    port = info.get("port")
    if port:
        out["PORT"] = str(port)
    out.setdefault("PYTHONIOENCODING", "utf-8")
    out.setdefault("PYTHONUNBUFFERED", "1")
    return out


# ------------------------------------------------------------- health probes ---
def _sqlite_files() -> list[Path]:
    # the get_*_db_path helpers return str (they double as env values)
    return [Path(p) for p in (get_discovery_db_path(), get_paper_trading_db_path(),
                              get_local_db_path(), get_knowledge_db_path())]


def probe_stores(now: float) -> tuple[str, str]:
    missing = [str(p) for p in _sqlite_files() if not p.exists() or p.stat().st_size == 0]
    if missing:
        return UNAVAILABLE, "missing/empty stores: " + ", ".join(missing)
    return HEALTHY, f"{len(_sqlite_files())} Lane-B stores present"


def probe_db_backend(target: dict, now: float) -> tuple[str, str]:
    if not target["configured"]:
        return UNKNOWN, "DATABASE_URL not configured; gateway will fail closed"
    if target["scheme"] == "pglite":
        ddir = target.get("data_dir")
        if not ddir:
            return UNHEALTHY, "pglite scheme without a data dir"
        p = Path(ddir)
        return (HEALTHY if p.exists() and any(p.iterdir())
                else UNAVAILABLE, f"pglite data dir {p} not initialised")
    if target["scheme"] in ("postgres", "postgresql"):
        host, port = target["host"], int(target["port"] or 5432)
        if pk.port_in_use(host, port):
            return HEALTHY, f"Postgres reachable on {host}:{port}"
        return UNAVAILABLE, f"Postgres not listening on {host}:{port}"
    return UNKNOWN, f"unsupported DATABASE_URL scheme: {target['scheme']}"


def probe_gateway(url: str, now: float) -> tuple[str, str]:
    base = url.rsplit("/api/", 1)[0] if "/api/" in url else url
    ok, code, reason = pk.http_ok(base, timeout=5.0)
    if ok:
        return HEALTHY, f"gateway answers HTTP {code} on {base}"
    return UNAVAILABLE, f"gateway not answering on {base} ({reason})"


def probe_process(pid_info: dict | None, marker: str) -> tuple[str, str]:
    if not pid_info:
        return UNAVAILABLE, "no launcher pid record (never started by us)"
    pid = pid_info.get("pid")
    if not pk.pid_is_ours(pid, marker):
        return UNAVAILABLE, f"recorded pid {pid} is not a live AHOS process"
    return HEALTHY, f"pid {pid} alive"


def engine_heartbeat_age(db_path: str, component: str = "DAEMON_CYCLE") -> float | None:
    """Seconds since the daemon's scheduler heartbeat — real evidence, not a ping."""
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT last_heartbeat_ts FROM scheduler_heartbeats WHERE component=?",
            (component,)).fetchone()
        conn.close()
    except Exception:
        return None
    if not row or not row[0]:
        return None
    return time.time() - float(row[0])


def engine_cycle_state(db_path: str, schedule: str = "DAEMON_CYCLE") \
        -> tuple[str | None, float | None]:
    """The daemon's latest scheduler run: ``(status, started_ts)``.

    The scheduler beats once per cycle, at the top of
    ``execute_scheduled_cycle``; an observation cycle can legitimately run for
    many minutes, so a stale heartbeat alone does not mean the engine is sick.
    A ``RUNNING`` row started by *this* process is real evidence it is working.
    """
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, started_ts FROM scheduler_runs WHERE schedule_name=? "
            "ORDER BY started_ts DESC LIMIT 1", (schedule,)).fetchone()
        conn.close()
    except Exception:
        return None, None
    if not row:
        return None, None
    started = None
    if row[1]:
        try:
            started = float(row[1])
        except Exception:
            started = None
    return (row[0] if isinstance(row[0], str) else None), started


# A daemon cycle may legitimately run this long before the next heartbeat lands.
MAX_CYCLE_SEC = 3600.0


def probe_engine(pid_info: dict | None, marker: str, *,
                 heartbeat_age: float | None, max_age: float = 200.0,
                 cycle: tuple[str | None, float | None] | None = None,
                 pid_started_ts: float | None = None,
                 max_cycle_sec: float = MAX_CYCLE_SEC) -> tuple[str, str]:
    base, detail = probe_process(pid_info, marker)
    if base != HEALTHY:
        return base, detail
    pid = pid_info["pid"]
    if heartbeat_age is None:
        # starting up: the first DAEMON_CYCLE has not landed yet
        return UNHEALTHY, f"pid {pid} alive but no scheduler heartbeat yet (still booting)"
    if heartbeat_age <= max_age:
        return HEALTHY, f"pid {pid} alive, heartbeat {heartbeat_age:.0f}s ago"
    # Stale heartbeat. The scheduler beats once per cycle, so a long cycle ages
    # it; a RUNNING cycle begun by this very process is evidence it is working,
    # not hung. A RUNNING row left behind by a *previous* (killed) daemon must
    # not count: tie the row to this pid by requiring it started after the pid.
    cycle = cycle or (None, None)
    cycle_status, cycle_started = cycle
    own = (pid_started_ts is None or cycle_started is None
           or cycle_started >= pid_started_ts - 30.0)
    if cycle_status == "RUNNING" and cycle_started is not None and own:
        cycle_age = time.time() - cycle_started
        if cycle_age <= max_cycle_sec:
            return HEALTHY, (f"pid {pid} alive, in scheduler cycle for "
                             f"{cycle_age:.0f}s (heartbeat {heartbeat_age:.0f}s ago)")
        return UNHEALTHY, (f"pid {pid} alive but its scheduler cycle has run for "
                           f"{cycle_age:.0f}s without beating (wedged)")
    return UNHEALTHY, f"pid {pid} alive but heartbeat is {heartbeat_age:.0f}s stale"


# ---------------------------------------------------------------- preflight ---
@dataclass
class Preflight:
    ok: bool
    checks: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def preflight(root: Path, env: dict | None = None) -> Preflight:
    """Hard requirements only; soft findings become warnings (never fatal)."""
    env = load_repo_env(root, env)
    pf = Preflight(ok=True)
    check = pf.checks

    def add(name: str, ok: bool, detail: str, *, fatal: bool = True):
        check.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            if fatal:
                pf.ok = False
            else:
                pf.warnings.append(detail)

    add("repo", repo_root_marker(root), f"workspace root {root}")
    py = venv_python(root)
    add("venv", py is not None, ".venv\\Scripts\\python.exe")
    add("node_modules", node_present(root), "node_modules")
    add("scheduler_config", (root / "architecture" / "scheduling" / "engine.py").exists(),
        "existing scheduler (n8n replacement)")

    target = database_target(env)
    if target["configured"] and target["scheme"] in ("postgres", "postgresql"):
        listening = pk.port_in_use(target["host"], int(target["port"] or 5432))
        add("db_reachable", listening,
            f"{target['scheme']} on {target['host']}:{target['port']}", fatal=False)
    elif target["configured"] and target["scheme"] == "pglite":
        add("db_reachable", True, "embedded pglite (no network port)", fatal=False)
    else:
        add("db_reachable", False, "no DATABASE_URL configured", fatal=False)

    # Credential Manager: PRESENCE ONLY. The value is never read or printed.
    add("gemini_cred", pk.credential_present("AHOS/ai/gemini"),
        "Credential Manager AHOS/ai/gemini (presence only)", fatal=False)

    return pf
