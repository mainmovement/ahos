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
import re
import shutil
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


def candidate_ports(env: dict, config_file: Path | str | None = None) -> tuple[int, ...]:
    """Ordered gateway fallback list, delegated to gateway_port.py.

    Non-secret: ``AHOS_GATEWAY_CANDIDATE_PORTS`` env, then ``config/gateway_ports.json``
    (when a caller passes it), then the in-code default. Exposed so the smoke and
    any other launcher-side caller walk the same list the resolver does.
    """
    gwp = _load_gateway_port_module()
    return gwp.candidate_ports(env, config_file=config_file)


# The non-secret candidate-port list, and the config file it is read from. The
# resolver in gateway_port.py owns the path; re-exporting it here keeps the
# orchestrator and the smoke from re-hardcoding "config/gateway_ports.json".
GATEWAY_PORTS_CONFIG = _load_gateway_port_module().GATEWAY_PORTS_CONFIG


def select_gateway(env: dict) -> dict:
    """The gateway the launcher will *actually* use on this host.

    ``resolve_gateway`` is the pure URL resolver; this is the launcher entry
    point that adds a real ``bind`` test; on a host where the configured port is
    Windows-reserved (Hyper-V/WSL exclusion range) it walks the non-secret
    ``config/gateway_ports.json`` candidate list and picks the first port it can
    hold. The choice is recorded in the status report and pushed to every child
    as ``AHOS_GATEWAY_URL``/``PORT``, so one resolver stays the source of truth
    for every consumer and children never disagree about the gateway address.
    """
    gwp = _load_gateway_port_module()
    return gwp.select_port(env)


def dashboard_url(env: dict) -> str:
    info = resolve_gateway(env)
    host = info.get("host") or "127.0.0.1"
    port = info.get("port") or 3000
    return f"http://{host}:{int(port)}/"


def gateway_url_at(host: str, port: int) -> str:
    """The gateway API URL for an explicit host/port pair.

    ``resolve_gateway`` reads the configured URL; this builds one for a port the
    launcher discovered at runtime (e.g. adopted from its own live listener),
    where there is no configuration to resolve.
    """
    return f"http://{host}:{int(port)}/api/chat"


def pglite_data_dir(raw: str) -> str | None:
    """dataDir of a ``pglite:<dataDir>`` URL; mirrors ``db/index.ts::pgliteDataDir``.

    ``pglite:G:/x``, ``pglite:/G:/x``, ``pglite://G:/x`` -> ``G:/x`` (Windows
    drive); ``pglite:/abs`` and ``pglite:///abs`` stay POSIX absolute;
    ``pglite:rel`` stays relative. Stripping every leading slash made a POSIX
    absolute store look cwd-relative, so the probe inspected the wrong place.
    """
    if not raw.lower().startswith("pglite:"):
        return None
    d = raw[len("pglite:"):]
    if d.startswith("//"):
        d = d[2:]
    if re.match(r"^[/\\]+[A-Za-z]:", d):
        d = d.lstrip("/\\")
    return d or None


BOOT_FILE_NAME = "dashboard_boot.json"
BOOT_TOKEN_TTL_S = 300.0
BOOT_MAX_ENTRIES = 8


def dashboard_boot_file(state_dir: Path) -> Path:
    return Path(state_dir) / BOOT_FILE_NAME


def issue_dashboard_boot_token(path: Path, *, ttl: float = BOOT_TOKEN_TTL_S,
                               now: float | None = None) -> str:
    """Create a fresh single-use token, store its hash, return the token.

    Expired entries are pruned and at most ``BOOT_MAX_ENTRIES`` live tokens are
    kept (oldest dropped). The file is replaced atomically and is owner-only
    where the OS supports it. Format (shared with chat_auth.ts):
    ``{"version": 1, "tokens": [{"sha256", "expires_ts", "issued_ts"}]}``.
    """
    import hashlib
    import json
    import secrets

    t = time.time() if now is None else float(now)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        entries = [e for e in doc.get("tokens", [])
                   if isinstance(e, dict) and isinstance(e.get("sha256"), str)
                   and isinstance(e.get("expires_ts"), (int, float)) and e["expires_ts"] > t]
    except (OSError, ValueError, AttributeError):
        entries = []
    token = secrets.token_hex(32)
    entries.append({"sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                    "expires_ts": t + float(ttl), "issued_ts": t})
    entries = entries[-BOOT_MAX_ENTRIES:]
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "tokens": entries}, fh)
    os.replace(tmp, path)
    return token


def bootstrap_url(dashboard_url: str, token: str) -> str:
    """The dashboard URL with the token in the fragment (never sent in the page
    request, so it cannot land in a server access log)."""
    return dashboard_url.split("#", 1)[0] + "#boot=" + token


# ------------------------------------------------------------- health probes ---


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
    """The repo venv interpreter: ``Scripts/python.exe`` on Windows, ``bin/python``
    elsewhere (``run_ahos.sh`` and review boxes run the same launcher)."""
    if os.name == "nt":
        cand = root / ".venv" / "Scripts" / "python.exe"
    else:
        cand = root / ".venv" / "bin" / "python"
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
    """One-shot foreground scripts (``next build``, ``db:restore-pglite``).

    Long-lived components are NOT started through npm: the ``cmd /c npm``
    wrapper exits and reparents its child, so the pid we record is a stub whose
    own command line carries nothing identifying (M11.3). The gateway is spawned
    directly via ``gateway_command`` for that reason; npm stays for the scripts
    that finish and exit on their own.
    """
    if os.name == "nt":
        return ["cmd", "/c", f"npm run {script} --silent"]
    return ["npm", "run", script, "--silent"]


def node_executable() -> str | None:
    """node on PATH — the interpreter npm would hand ``next`` to.

    ``npm run start`` resolves to ``node node_modules/next/dist/bin/next``, so
    this is the same binary the package.json scripts use, found the same way.
    ``None`` when node is not on PATH at all, in which case npm could not work
    either and the caller reports UNAVAILABLE rather than silently degrading.
    """
    return shutil.which("node")


def next_cli(root: Path) -> Path | None:
    """The CLI script ``npm run start`` resolves to (``node_modules/next/dist/bin/next``).

    ``None`` when next is not installed; ``preflight``'s ``node_modules`` check
    covers that before we get here, but the argv is never built on an assumption.
    """
    cli = Path(root) / "node_modules" / "next" / "dist" / "bin" / "next"
    return cli if cli.exists() else None


def gateway_command(root: Path, mode: str = "prod") -> list[str]:
    """(argv) for the gateway in the given mode (prod = `next start`, dev = `next dev`).

    Spawned directly as ``[node, <next cli>, start|dev, --hostname, 127.0.0.1]``
    — the argv ``npm run start`` / ``npm run dev`` resolve to, including the
    loopback flag from package.json — so the pid we record IS the server and its
    own command line carries the marker. The package.json scripts stay the human
    entry point; the launcher just skips the ``cmd /c npm`` wrapper whose exit
    reparents ``next`` and leaves a listener no pid record can name (M11.3).

    ``[]`` when node or the next CLI is missing: the caller reports UNAVAILABLE
    with the reason rather than falling back to the wrapper this function exists
    to avoid. ``PORT`` still honours the resolved gateway port (``child_env``).
    """
    node = node_executable()
    if node is None:
        return []
    cli = next_cli(Path(root))
    if cli is None:
        return []
    return [node, str(cli), "start" if mode == "prod" else "dev",
            "--hostname", "127.0.0.1"]


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
def child_env(root: Path, env: dict | None = None, *,
              telegram_owner: bool = True,
              gateway: dict | None = None) -> dict:
    """Environment for launcher children: paper-only hard, URL resolved once.

    ``gateway`` is the *selected* gateway (``select_gateway``) — the port this
    host can actually bind, which need not be the configured one. Passing it in
    keeps every child on the same address the launcher recorded; when it is
    omitted the pure resolver is used, which is what pre-M11.1 callers and the
    tests exercise.
    """
    out = dict(os.environ if env is None else env)
    out.update(ENGINE_ENV_HARD)
    info = gateway if gateway is not None else resolve_gateway(out)
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
        if p.exists() and any(p.iterdir()):
            return HEALTHY, f"pglite data dir {p} initialised"
        return UNAVAILABLE, f"pglite data dir {p} not initialised"
    if target["scheme"] in ("postgres", "postgresql"):
        host, port = target["host"], int(target["port"] or 5432)
        if pk.port_in_use(host, port):
            return HEALTHY, f"Postgres reachable on {host}:{port}"
        return UNAVAILABLE, f"Postgres not listening on {host}:{port}"
    return UNKNOWN, f"unsupported DATABASE_URL scheme: {target['scheme']}"


def probe_gateway(url: str, now: float) -> tuple[str, str]:
    # Probe the status route, not the page root. ``/`` is the heaviest compile in
    # the app (page plus client bundles): on a slow filesystem its first compile
    # can outlast the whole health budget while the server has been listening and
    # answering API requests for minutes, so a healthy gateway was reported
    # UNAVAILABLE and a restart turned into a ~2 minute wait for nothing.
    # /api/launcher is the route the dashboard polls every few seconds and costs
    # a fraction of the compile; http_ok counts its 401/403 as "listening", so the
    # probe still passes before the dashboard's own auth is set up. A 404 is
    # *not* counted as listening: see the branch below.
    base = (url.rsplit("/api/", 1)[0] if "/api/" in url else url).rstrip("/")
    probe = f"{base}/api/launcher"
    ok, code, reason = pk.http_ok(probe, timeout=15.0)
    if not ok:
        return UNAVAILABLE, f"gateway not answering on {probe} ({reason})"
    if code == 404:
        # A Next server *is* answering (http_ok reached it), but this route is
        # not registered in the server that holds the port. That is not a boot
        # delay — an unregistered route is never compiled on demand into a
        # running server — it means the listener is not our app: a stale server
        # left over from an older build or another checkout, or a foreign
        # program that happens to render our 404 page. Reporting it HEALTHY
        # makes the dashboard announce ONLINE while every control is dead, and
        # a restart then waits its whole budget for an audit line that can
        # never be written. Call it what it is.
        return UNAVAILABLE, (f"server on {probe} answers 404: a Next server is "
                             f"up but this route is not registered in it "
                             f"(stale build, another checkout, or a foreign "
                             f"listener holds the port)")
    return HEALTHY, f"gateway answers HTTP {code} on {probe}"


def probe_process(pid_info: dict | None, marker: str) -> tuple[str, str]:
    if not pid_info:
        return UNAVAILABLE, "no launcher pid record (never started by us)"
    pid = pid_info.get("pid")
    if not pk.pid_is_ours(pid, marker):
        return UNAVAILABLE, f"recorded pid {pid} is not a live AHOS process"
    return HEALTHY, f"pid {pid} alive"


# The line run_bot.py prints once its own preflight has passed and the long-poll
# loop is actually serving (see run_bot.run_polling). It is a readiness signal
# rather than a liveness one: a bot whose tunnel drops mid-poll is still alive
# and still has this line in its log, while a bot that failed preflight never
# printed it. Substring of a fixed Persian line, so nothing here reads the token.
TELEGRAM_READY_MARK = "AHOS در حال گوش دادن است"

# A pid alive this soon after spawn proves only that the interpreter started.
# run_bot.py runs its own preflight first (token presence and format, the Lane-B
# stores, a live get_me() against api.telegram.org that can take many seconds
# through a filtered tunnel) and exits the moment it fails, so a probe that asks
# only "is the pid ours?" reports HEALTHY in the instant the child spawns. The
# launcher then announced ONLINE for a bot that was already dying (M11.4).
# HEALTHY now requires the process to have survived this long as well.
TELEGRAM_STABLE_SEC = 8.0


def read_log_tail(log_path: str | Path, lines: int = 3) -> str:
    """The last ``lines`` of a component log, "" when it cannot be read.

    Component logs are opened in append-binary mode and never truncated, so a
    record of every boot survives. Reading only the tail keeps the size bounded
    when a log has grown across many restarts.
    """
    try:
        path = Path(log_path)
        if not path.exists():
            return ""
        data = path.read_bytes()[-4000:]
        return "\n".join(data.decode("utf-8", errors="replace").strip().splitlines()[-lines:])
    except Exception:
        return ""


def redact_log(text: str) -> tuple[str, list[str]]:
    """Run the project's two existing secret patterns over owner-facing log text.

    ``architecture.security.hygiene`` is the canonical security boundary and
    carries the Telegram token shape; ``architecture.mission.ledger`` adds the
    assignment form (``KEY=value``) a preflight echo can print. Both are loaded
    lazily so the launcher's import graph stays out of Lane B's module-load
    timing. Returns the redacted text and the kinds it found (empty = nothing
    needed redacting). Idempotent: ledger's ASSIGNED rule carries a
    ``(?![REDACTED)`` guard and hygiene's REDACTED text matches nothing.
    """
    if not text:
        return text, []
    try:
        from architecture.security.hygiene import sanitize_secrets
        text = sanitize_secrets(text)
    except Exception:
        pass
    kinds: list[str] = []
    try:
        from architecture.mission.ledger import redact_secrets
        text, kinds = redact_secrets(text)
    except Exception:
        pass
    return text, (list(kinds) if kinds else [])


def probe_telegram(pid_info: dict | None, marker: str, *,
                   now: float | None = None,
                   min_uptime: float = TELEGRAM_STABLE_SEC,
                   ready_mark: str = TELEGRAM_READY_MARK,
                   require_ready: bool = True) -> tuple[str, str]:
    """Telegram health = a stable, polling bot — not a pid alive at spawn.

    ``run_bot.py`` runs its own preflight before it ever polls Telegram and
    exits when it fails (no token, no stores, no tunnel). The child is *alive*
    for every one of those seconds, so ``probe_process`` reported HEALTHY the
    moment the launcher spawned it and a start announced ONLINE for a bot that
    was already on its way out (M11.4). HEALTHY now requires the process to have
    been alive for ``min_uptime`` seconds and, in the boot window, to have
    printed its readiness line — the mark ``run_bot.py`` emits once the poll
    loop starts. Anything less is UNHEALTHY ("still booting / preflight"), never
    HEALTHY, so a start never reports ONLINE for a bot in preflight.

    ``require_ready`` is the stability/robustness trade-off. The fresh-spawn
    boot window always demands the mark: the log is new there and the question
    is precisely "did the bot reach the poll loop?". A read-only ``status`` poll
    does not: a bot that has served for hours can have had its log rotated or
    removed by hand, and reporting a working bot as sick would be worse than
    the disease. The pid-record liveness and stability checks apply in both.

    Never reads the token. The mark is a fixed Persian substring and the log is
    only ever surfaced through ``redact_log``; callers that must show the owner
    a tail do that themselves.
    """
    base, detail = probe_process(pid_info, marker)
    if base != HEALTHY:
        return base, detail
    pid = pid_info["pid"]
    started = pid_info.get("started_ts")
    if not isinstance(started, (int, float)) or isinstance(started, bool):
        # A pid record without a start time predates this rule; the pid is alive
        # and ours, so this is not the boot window the stability rule guards.
        return HEALTHY, f"pid {pid} alive"
    now = time.time() if now is None else float(now)
    uptime = max(0.0, now - float(started))
    if uptime < min_uptime:
        return UNHEALTHY, (f"pid {pid} alive for {uptime:.0f}s, still in its own "
                           f"preflight (needs {min_uptime:.0f}s to count as stable)")
    log_path = pid_info.get("log")
    if require_ready and log_path:
        # Only the text written after THIS spawn counts: the log is append-only
        # across restarts, so a mark from a previous run would satisfy a naive
        # whole-file search while this bot is still failing preflight. The pid
        # record carries the offset the spawn saw.
        if not _log_contains(log_path, ready_mark, pid_info.get("log_offset") or 0):
            return UNHEALTHY, (f"pid {pid} alive for {uptime:.0f}s but has not printed "
                               f"its readiness line yet (poll loop not started)")
    return HEALTHY, f"pid {pid} alive for {uptime:.0f}s and polling"


def _log_contains(log_path: str | Path, needle: str, offset: int) -> bool:
    """Does ``log_path`` contain ``needle`` at or after ``offset`` bytes?"""
    try:
        path = Path(log_path)
        if not path.exists():
            return False
        with open(path, "rb") as fh:
            fh.seek(max(0, int(offset)))
            return needle.encode("utf-8") in fh.read()
    except Exception:
        return False


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
    add("venv", py is not None,
        ".venv\\Scripts\\python.exe" if os.name == "nt" else ".venv/bin/python")
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
