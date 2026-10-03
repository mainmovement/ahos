#!/usr/bin/env python3
"""Single source of truth for the local Conversation Gateway URL (GM-05).

Resolution order (first non-empty wins):
  1. ``AHOS_GATEWAY_URL``  - full URL (existing operator contract, unchanged)
  2. ``AHOS_GATEWAY_PORT`` - port only; URL = http://127.0.0.1:<port>/api/chat
  3. default              - http://127.0.0.1:3000/api/chat (Next.js default)

The default stays 3000 on purpose: ~40 repo references, tests and launchers
use it. Running the gateway elsewhere (e.g. ``next dev -p 3500``) is an
operator choice expressed through one of the two variables above.

Diagnostic (read-only, loopback only): reports whether the configured port
has a listener and which candidate ports do::

    CONFIGURED_PORT_LISTENING     - configured port accepts TCP
    CONFIGURED_PORT_NO_LISTENER   - nothing there, but a candidate port does
    NO_GATEWAY_LISTENING          - nothing on the configured or candidate ports
    NON_LOCAL_URL_NOT_PROBED      - configured host is not loopback; no probe

This module never writes ``.env`` and never starts/stops anything.

The launcher additionally calls ``select_port()`` (see below): the same
resolution, plus a REAL ``bind`` test, so on a host where the configured port is
Windows-reserved the launcher walks the non-secret ``config/gateway_ports.json``
candidate list and picks the first port it can actually hold. The chosen port is
recorded in ``reports/launcher/status.json`` and pushed to the gateway/Telegram/
engine children as ``AHOS_GATEWAY_URL``/``PORT`` — so one resolver stays the
source of truth for every consumer.

CLI::

    python scripts/gateway_port.py              # human summary
    python scripts/gateway_port.py --json       # machine-readable diagnosis
    python scripts/gateway_port.py --url-only   # print the resolved URL
    python scripts/gateway_port.py --select     # which port the launcher would use, and why
    python scripts/gateway_port.py --env-file .env   # read keys from .env (read-only)
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlsplit

DEFAULT_GATEWAY_HOST = "127.0.0.1"
DEFAULT_GATEWAY_PORT = 3000
CHAT_PATH = "/api/chat"
DEFAULT_CANDIDATE_PORTS = (3000, 3500)
# In-repo, non-secret fallback list. ``candidate_ports()`` only reads it when a
# caller explicitly passes the file (the launcher does); the bare default stays
# (3000, 3500) so standalone diagnostics and their tests are unaffected.
GATEWAY_PORTS_CONFIG = Path(__file__).resolve().parent.parent / "config" / "gateway_ports.json"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
GATEWAY_ENV_KEYS = ("AHOS_GATEWAY_URL", "AHOS_GATEWAY_PORT", "AHOS_GATEWAY_CANDIDATE_PORTS")


def _parse_port(raw: str | None) -> int | None:
    s = (raw or "").strip()
    if not s.isdigit():
        return None
    p = int(s)
    return p if 1 <= p <= 65535 else None


def default_gateway_url(port: int = DEFAULT_GATEWAY_PORT) -> str:
    return f"http://{DEFAULT_GATEWAY_HOST}:{port}{CHAT_PATH}"


def resolve_gateway(env: Mapping[str, str] | None = None) -> dict:
    """Resolve the gateway URL. Pure: reads only the given mapping."""
    env = os.environ if env is None else env
    warnings: list[str] = []
    raw_url = (env.get("AHOS_GATEWAY_URL") or "").strip()
    raw_port = (env.get("AHOS_GATEWAY_PORT") or "").strip()
    port_override = _parse_port(raw_port)
    if raw_port and port_override is None:
        warnings.append("AHOS_GATEWAY_PORT_INVALID_IGNORED")

    if raw_url:
        parts = urlsplit(raw_url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            warnings.append("AHOS_GATEWAY_URL_UNPARSEABLE")
            return {"url": raw_url, "host": None, "port": None,
                    "source": "AHOS_GATEWAY_URL", "warnings": warnings}
        try:
            url_port = parts.port or (443 if parts.scheme == "https" else 80)
        except ValueError:
            warnings.append("AHOS_GATEWAY_URL_UNPARSEABLE")
            return {"url": raw_url, "host": parts.hostname, "port": None,
                    "source": "AHOS_GATEWAY_URL", "warnings": warnings}
        if port_override is not None and port_override != url_port:
            # URL wins (existing contract); surface the disagreement loudly.
            warnings.append("AHOS_GATEWAY_PORT_DISAGREES_WITH_URL")
        return {"url": raw_url, "host": parts.hostname, "port": url_port,
                "source": "AHOS_GATEWAY_URL", "warnings": warnings}

    if port_override is not None:
        return {"url": default_gateway_url(port_override), "host": DEFAULT_GATEWAY_HOST,
                "port": port_override, "source": "AHOS_GATEWAY_PORT", "warnings": warnings}

    return {"url": default_gateway_url(), "host": DEFAULT_GATEWAY_HOST,
            "port": DEFAULT_GATEWAY_PORT, "source": "DEFAULT", "warnings": warnings}


def candidate_ports(env: Mapping[str, str] | None = None,
                    config_file: Path | str | None = None) -> tuple[int, ...]:
    """Ordered fallback list. Env ``AHOS_GATEWAY_CANDIDATE_PORTS`` wins, then the
    non-secret config file (when a caller passes one), then the in-code default.

    ``config_file`` is opt-in on purpose: this module is also ``exec``'d by path
    from ``launcher/components.py`` and used as a read-only diagnostic, so its
    default behaviour must not depend on a config file being present.
    """
    env = os.environ if env is None else env
    raw = (env.get("AHOS_GATEWAY_CANDIDATE_PORTS") or "").strip()
    if raw:
        ports = tuple(p for p in (_parse_port(x) for x in raw.split(",")) if p is not None)
        if ports:
            return ports
    if config_file is not None:
        configured = _read_candidate_config(Path(config_file))
        if configured:
            return configured
    return DEFAULT_CANDIDATE_PORTS


def _read_candidate_config(path: Path) -> tuple[int, ...]:
    """The candidate_ports list from a non-secret JSON config, or () if absent.

    Malformed JSON or a bad shape is ignored (never raises): a broken config
    file must not make port selection fail, it only shrinks the fallback list.
    """
    try:
        if not path.is_file():
            return ()
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    if not isinstance(raw, dict):
        return ()
    vals = raw.get("candidate_ports")
    if not isinstance(vals, list):
        return ()
    ports = tuple(p for p in (_parse_port(str(x)) for x in vals) if p is not None)
    return ports


def can_bind(host: str, port: int) -> bool:
    """Can THIS process actually listen on host:port? A real ``bind``.

    A TCP ``connect`` probe is not enough on Windows: wide port ranges are
    reserved for Hyper-V/WSL and ``bind`` fails with ``WinError 10013`` while a
    connect probe reports the port as free. No ``SO_REUSEADDR`` here — on Windows
    it permits a duplicate bind and would silently weaken the caller's squat test.
    """
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    s = socket.socket(family, socket.SOCK_STREAM)
    try:
        s.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        s.close()


def select_port(env: Mapping[str, str] | None = None,
                *, config_file: Path | str | None = GATEWAY_PORTS_CONFIG,
                probe: Callable[[str, int], bool] | None = None) -> dict:
    """The port the gateway will actually use on THIS host (real bind test).

    The configured port (``AHOS_GATEWAY_URL`` > ``AHOS_GATEWAY_PORT`` > default)
    is kept when it is usable — either because we can ``bind`` it now, or because
    something is already listening on it (almost certainly our own gateway from a
    previous start; the launcher reuses it rather than fighting itself). Only
    when it is neither bindable nor listening does the walk down
    ``candidate_ports`` begin, and the first port that binds wins.

    This is the *launcher* entry point; ``resolve_gateway`` stays the pure URL
    resolver everything else uses. Returns::

        {host, port, url, source, configured_port, chosen_via,
         tried: [...], notes: [...], warnings: [...]}

    Never raises: if nothing binds at all, the configured port is returned with
    a warning so the gateway fails with its own honest error instead of a made-up
    one, and the caller reports the real situation.
    """
    env = os.environ if env is None else env
    probe = probe or port_listening
    res = resolve_gateway(env)
    warnings = list(res["warnings"])
    notes: list[str] = []
    tried: list[dict] = []
    host = res["host"] or DEFAULT_GATEWAY_HOST
    port = res["port"]
    if host.lower() not in LOOPBACK_HOSTS:
        # Non-loopback configured URL: the owner pointed the gateway at another
        # machine. We cannot and should not bind-test it.
        return {"host": host, "port": port, "url": res["url"],
                "source": res["source"], "configured_port": port,
                "chosen_via": "NON_LOCAL_CONFIGURED_NOT_PROBED",
                "tried": tried, "notes": ["configured host is not loopback; no bind test"],
                "warnings": warnings}
    if port is None:
        port = DEFAULT_GATEWAY_PORT
        notes.append("configured URL had no parseable port; using the default")
    bind_host = DEFAULT_GATEWAY_HOST if host.lower() == "localhost" else host

    def _usable(p: int) -> tuple[bool, str]:
        if can_bind(bind_host, p):
            return True, "bindable"
        if probe(bind_host, p):
            return True, "already_listening"
        return False, "unusable"

    ok, how = _usable(int(port))
    tried.append({"port": int(port), "bindable": ok and how == "bindable",
                  "listening": ok and how == "already_listening"})
    if ok:
        return {"host": bind_host, "port": int(port), "url": res["url"],
                "source": res["source"], "configured_port": int(port),
                "chosen_via": "CONFIGURED_" + how.upper(),
                "tried": tried, "notes": notes, "warnings": warnings}

    notes.append(f"configured port {port} is not bindable and has no listener on {bind_host}")
    for cand in candidate_ports(env, config_file=config_file):
        if cand == int(port):
            continue
        # Candidates must be BINDABLE, not merely "has a listener": a listener we
        # cannot bind past is someone else's process, and handing the gateway that
        # port would just reproduce the original bind failure. (Reuse of our own
        # already-running gateway is handled by the configured-port case above,
        # because the launcher feeds its recorded choice back as the configured
        # port on the next start.)
        ok = can_bind(bind_host, cand)
        tried.append({"port": cand, "bindable": ok, "listening": probe(bind_host, cand)})
        if ok:
            notes.append(f"selected candidate port {cand} (bindable)")
            return {"host": bind_host, "port": cand,
                    "url": default_gateway_url(cand), "source": "CANDIDATE_PORT",
                    "configured_port": int(port), "chosen_via": "CANDIDATE_BINDABLE",
                    "tried": tried, "notes": notes, "warnings": warnings}
    warnings.append("NO_BINDABLE_PORT")
    notes.append("no candidate port could be bound; keeping the configured port "
                 "so the gateway reports its own real bind failure")
    return {"host": bind_host, "port": int(port), "url": res["url"],
            "source": res["source"], "configured_port": int(port),
            "chosen_via": "CONFIGURED_UNUSABLE_KEPT_ANYWAY",
            "tried": tried, "notes": notes, "warnings": warnings}


def port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    """TCP connect probe. Callers must only pass loopback hosts.

    Note this reports a Windows-reserved port (Hyper-V/WSL exclusion range) as
    free while ``bind`` fails — use ``can_bind`` whenever the question is "can
    *I* listen here" rather than "is something already there".
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def diagnose(env: Mapping[str, str] | None = None,
             probe: Callable[[str, int], bool] | None = None) -> dict:
    env = os.environ if env is None else env
    probe = probe or port_listening
    res = resolve_gateway(env)
    out = {
        "schema": "ahos.gateway_port_diagnosis.v1",
        "configured_url": res["url"],
        "configured_port": res["port"],
        "source": res["source"],
        "warnings": list(res["warnings"]),
        "configured_listening": None,
        "listening_candidates": [],
        "verdict": None,
        "hint": None,
    }
    host = (res["host"] or "").lower()
    if host not in LOOPBACK_HOSTS or res["port"] is None:
        out["verdict"] = "NON_LOCAL_URL_NOT_PROBED"
        return out
    probe_host = DEFAULT_GATEWAY_HOST if host == "localhost" else host
    out["configured_listening"] = bool(probe(probe_host, res["port"]))
    others = [p for p in candidate_ports(env) if p != res["port"]]
    out["listening_candidates"] = [p for p in others if probe(probe_host, p)]
    if out["configured_listening"]:
        out["verdict"] = "CONFIGURED_PORT_LISTENING"
    elif out["listening_candidates"]:
        out["verdict"] = "CONFIGURED_PORT_NO_LISTENER"
        alt = out["listening_candidates"][0]
        out["hint"] = (
            f"Configured {res['url']} has no listener but 127.0.0.1:{alt} does. "
            f"OWNER_ACTION: either start the gateway on {res['port']} or set "
            f"AHOS_GATEWAY_URL={default_gateway_url(alt)} (or AHOS_GATEWAY_PORT={alt}). "
            "This tool does not change .env."
        )
    else:
        out["verdict"] = "NO_GATEWAY_LISTENING"
        out["hint"] = "No local gateway listener found; start 'npm run dev' (OWNER_ACTION)."
    return out


def read_env_file(path: Path) -> dict[str, str]:
    """Read only the gateway keys from a dotenv file (never writes)."""
    vals: dict[str, str] = {}
    if not path.is_file():
        return vals
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        t = line.strip()
        if not t or t.startswith("#") or "=" not in t:
            continue
        k, _, v = t.partition("=")
        k = k.strip()
        if k not in GATEWAY_ENV_KEYS:
            continue
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        vals[k] = v
    return vals


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS gateway URL resolution + read-only port diagnosis")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--url-only", action="store_true")
    ap.add_argument("--select", action="store_true",
                    help="show which port the launcher would bind on this host and why")
    ap.add_argument("--env-file", default="", help="read gateway keys from this dotenv file (read-only; overrides process env like the gate does)")
    args = ap.parse_args(argv)
    env: dict[str, str] = {k: v for k, v in os.environ.items() if k in GATEWAY_ENV_KEYS}
    if args.env_file:
        env.update(read_env_file(Path(args.env_file)))
    if args.url_only:
        print(resolve_gateway(env)["url"])
        return 0
    if args.select:
        sel = select_port(env)
        print(json.dumps(sel, indent=2))
        return 0
    d = diagnose(env)
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        print(f"gateway_url={d['configured_url']} source={d['source']} verdict={d['verdict']}")
        if d["listening_candidates"]:
            print("listening_candidates=" + ",".join(str(p) for p in d["listening_candidates"]))
        for w in d["warnings"]:
            print(f"warning={w}")
        if d["hint"]:
            print(f"hint={d['hint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
